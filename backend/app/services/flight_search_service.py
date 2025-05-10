#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
航班搜尋服務模組 - 處理航班搜尋的核心業務邏輯
"""

import logging
import asyncpg
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple, Union
from decimal import Decimal
from marshmallow import ValidationError

from ..models import Airline, Airport, Flight, TicketPrice
from ..schemas.flight_schema import FlightSchema, FlightSearchArgsSchema, FlightSearchResultSchema
from ..database.db import init_asyncpg_pool
from .db_utils import execute_db_operation, execute_query, normalize_cabin_class, get_price_field_by_cabin_class
from ..scripts.constants import POPULAR_DOMESTIC_ROUTES_TUPLES, POPULAR_INTERNATIONAL_ROUTES_TUPLES # 確保導入

logger = logging.getLogger(__name__)

# 實例化 Schema (many=True)
flights_search_result_schema = FlightSearchResultSchema(many=True)

class FlightSearchService:
    """航班搜尋服務 - 專注於航班搜尋功能"""
    
    @staticmethod
    async def search_flights(
        departure_code: str,
        arrival_code: str,
        date_str: str,
        airline_code: Optional[Union[str, List[str]]] = None,
        return_date_str: Optional[str] = None,
        price_min: Optional[int] = None,
        price_max: Optional[int] = None,
        cabin_class: str = "經濟艙",
        passengers: int = 1,
        max_results: int = 20,
        sort_by: str = "price"
    ) -> Dict[str, List[Dict[str, Any]]]: 
        """
        執行航班搜索 - 只返回請求艙等的列表
        
        Args:
            departure_code: 出發地IATA代碼
            arrival_code: 目的地IATA代碼
            date_str: 去程日期 (YYYY-MM-DD)
            airline_code: 航空公司IATA代碼，可選
            return_date_str: 回程日期 (YYYY-MM-DD)，可選
            price_min: 最低價格，可選
            price_max: 最高價格，可選
            cabin_class: 艙位類型 (來自請求)
            passengers: 乘客數量
            max_results: 每個方向的最大結果數
            sort_by: 排序方式
        
        Returns:
            Dict[str, List[Dict[str, Any]]]: 包含 'departure' 和可選 'return' 航班列表的字典
        """
        async def _search_flight_internal(conn, direction, dep, arr, date, airline, p_min, p_max):
            # 查詢航班 (資料包含所有艙位價格)
            flights_raw = await FlightSearchService._query_flights(
                conn,
                dep, arr, date,
                airline, p_min, p_max,
                cabin_class,
                max_results, sort_by
            )
            # 只格式化請求的艙等
            return await FlightSearchService._format_flights(flights_raw, cabin_class)
        
        try:
            # 記錄所有傳入參數
            logger.info(f"搜索航班參數: departure={departure_code}, arrival={arrival_code}, date={date_str}, "
                       f"airline={airline_code}, return_date={return_date_str}, price_min={price_min}, "
                       f"price_max={price_max}, cabin_class='{cabin_class}', passengers={passengers}, "
                       f"max_results={max_results}, sort_by={sort_by}")
            
            # 用 execute_db_operation 包裝資料庫操作
            async def search_operation(conn):
                # 查詢去程航班
                outbound_flights_formatted = await _search_flight_internal(
                    conn, "outbound", departure_code, arrival_code, date_str, 
                    airline_code, price_min, price_max
                )
                
                # 準備結果字典
                result = {
                    "departure": outbound_flights_formatted
                }
                
                # 如果提供了回程日期，也查詢回程航班
                if return_date_str:
                    inbound_flights_formatted = await _search_flight_internal(
                        conn, "inbound", arrival_code, departure_code, return_date_str,
                        airline_code, price_min, price_max
                    )
                    result["return"] = inbound_flights_formatted
                
                return result
            
            # 執行包裝後的操作
            pool = await init_asyncpg_pool()
            conn = await pool.acquire()
            try:
                return await search_operation(conn)
            finally:
                if conn:
                    await pool.release(conn)

        except Exception as e:
            logger.error(f"執行航班搜索查詢時發生錯誤: {e}", exc_info=True)
            raise

    @staticmethod
    async def _query_flights(
        conn, # 接收 conn 而不是 db
        departure_code: str,
        arrival_code: str,
        date_str: str,
        airline_code: Optional[Union[str, List[str]]] = None,
        price_min: Optional[int] = None,
        price_max: Optional[int] = None,
        cabin_class: str = "經濟艙",
        max_results: int = 20,
        sort_by: str = "price"
    ) -> List[Dict[str, Any]]:
        """
        查詢航班
        
        Args:
            conn: asyncpg 連接對象
            departure_code: 出發地機場ID
            arrival_code: 目的地機場ID
            date_str: 日期字符串 (YYYY-MM-DD)
            airline_code: 航空公司ID或ID列表，可選
            price_min: 最低價格，可選
            price_max: 最高價格，可選
            cabin_class: 艙位類型 (影響價格欄位選擇)
            max_results: 最大結果數
            sort_by: 排序方式
        
        Returns:
            List[Dict[str, Any]]: 航班列表
        """
        # 解析日期
        try:
            flight_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            start_of_day = datetime.combine(flight_date, datetime.min.time())
            end_of_day = datetime.combine(flight_date, datetime.max.time())
            logger.info(f"查詢日期範圍: {start_of_day} 到 {end_of_day}")
        except ValueError:
            logger.error(f"日期格式錯誤: {date_str}")
            return []
        
        # 標準化艙等名稱
        normalized_cabin_class = normalize_cabin_class(cabin_class)
        
        # 根據艙等選擇價格欄位
        price_field = get_price_field_by_cabin_class(normalized_cabin_class)
            
        # 構建 SQL 查詢 - 使用機場ID
        sql = """
        WITH RankedFlights AS (
            SELECT 
                f.flight_id, 
                f.flight_number, 
                f.scheduled_departure,
                f.scheduled_arrival,
                f.aircraft, 
                f.departure_terminal, 
                f.arrival_terminal, 
                a_dep.airport_id as departure_airport_id, 
                a_dep.airport_id as departure_code,
                a_dep.name_zh as departure_name,
                a_dep.city as departure_city,
                a_dep.country as departure_country,
                a_arr.airport_id as arrival_airport_id, 
                a_arr.airport_id as arrival_code,
                a_arr.name_zh as arrival_name,
                a_arr.city as arrival_city,
                a_arr.country as arrival_country,
                al.airline_id as airline_id, 
                al.airline_id as airline_iata, -- Use airline_id as IATA
                al.name_zh as airline_name_zh,
                al.name_en as airline_name_en,
                al.is_domestic as airline_is_domestic, 
                al.logo_path, -- Use model column name directly
                tp.economy_price,
                tp.business_price,
                tp.first_price,
                tp.available_seats, 
                tp.price_updated_at, -- Use model column name directly
                -- 使用 COALESCE 處理 NULL 價格，給予一個極大值以便排序
                COALESCE(tp.{price_field}, 99999999) as sort_price,
                -- 計算排序用的時間戳或數值
                EXTRACT(EPOCH FROM f.scheduled_departure) as sort_departure_time,
                -- 計算時間差（秒）用於排序
                EXTRACT(EPOCH FROM (f.scheduled_arrival - f.scheduled_departure)) as sort_duration, 
                -- Corrected duration calculation alias
                EXTRACT(EPOCH FROM (f.scheduled_arrival - f.scheduled_departure)) / 60 as duration_minutes, 
                ROW_NUMBER() OVER (
                    PARTITION BY f.flight_number, f.scheduled_departure::date -- 按航班號和日期分區
                    ORDER BY tp.price_updated_at DESC 
                ) as rn
            FROM flights f
            JOIN airports a_dep ON f.departure_airport_id = a_dep.airport_id
            JOIN airports a_arr ON f.arrival_airport_id = a_arr.airport_id
            JOIN airlines al ON f.airline_id = al.airline_id
            LEFT JOIN ticket_prices tp ON f.flight_id = tp.flight_id
            WHERE f.departure_airport_id = $1 
              AND f.arrival_airport_id = $2
              AND f.scheduled_departure >= $3
              AND f.scheduled_departure <= $4
              {airline_filter} -- 航空公司過濾條件將插入這裡
              {price_filter}   -- 價格過濾條件將插入這裡
        )
        SELECT * 
        FROM RankedFlights 
        WHERE rn = 1 -- 只選取每個航班號和日期最新的價格記錄
          AND {price_field} IS NOT NULL -- 確保所選艙等有價格
          AND available_seats > 0 -- 確保有可用座位
        {sort_order} -- 排序條件將插入這裡
        LIMIT {limit_placeholder}; -- 結果數量限制
        """

        params = [departure_code, arrival_code, start_of_day, end_of_day]
        param_index = len(params) # 從 4 開始 (索引從 1 開始)

        # 航空公司過濾
        airline_filter_sql = ""
        if airline_code:
            if isinstance(airline_code, list):
                if airline_code: # 確保列表不為空
                    airline_placeholders = ', '.join(f'${i+1}' for i in range(param_index, param_index + len(airline_code)))
                    airline_filter_sql = f" AND al.airline_id IN ({airline_placeholders})"
                    params.extend(airline_code)
                    param_index += len(airline_code)
            elif isinstance(airline_code, str):
                airline_filter_sql = f" AND al.airline_id = ${param_index + 1}"
                params.append(airline_code)
                param_index += 1
        
        # 價格過濾 (基於指定艙等價格)
        price_filter_sql = ""
        if price_min is not None:
            price_filter_sql += f" AND tp.{price_field} >= ${param_index + 1}"
            params.append(price_min)
            param_index += 1
        if price_max is not None:
            price_filter_sql += f" AND tp.{price_field} <= ${param_index + 1}"
            params.append(price_max)
            param_index += 1
            
        # 排序條件
        sort_order_sql = ""
        if sort_by == "price":
            sort_order_sql = " ORDER BY sort_price ASC, sort_departure_time ASC" # 價格優先，然後起飛時間
        elif sort_by == "duration":
            sort_order_sql = " ORDER BY sort_duration ASC, sort_price ASC" # 時長優先，然後價格
        elif sort_by == "departure_time":
            sort_order_sql = " ORDER BY sort_departure_time ASC, sort_price ASC" # 起飛時間優先，然後價格
        else: # 默認按價格排序
            sort_order_sql = " ORDER BY sort_price ASC, sort_departure_time ASC"

        # 添加結果數量限制參數
        limit_param_index = param_index + 1 # LIMIT 的參數索引
        params.append(max_results) # 將 max_results 添加到列表末尾

        # 格式化最終 SQL
        final_sql = sql.format(
            price_field=price_field,  # 替換價格欄位
            airline_filter=airline_filter_sql,
            price_filter=price_filter_sql,
            sort_order=sort_order_sql,
            limit_placeholder=f"${limit_param_index}" # 使用計算出的索引
        )
        
        try:
            logger.debug(f"Executing SQL: {final_sql} with params: {params}")
            # 使用 conn 執行查詢
            rows = await conn.fetch(final_sql, *params)
            logger.debug(f"Raw rows from DB: {rows}")
            logger.info(f"查詢到 {len(rows)} 條艙等為 {normalized_cabin_class} 的航班記錄")
            # 將 asyncpg Row 對象轉換為字典列表
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"查詢航班時發生錯誤: {e}\\nSQL: {final_sql}\\nParams: {params}", exc_info=True)
            return []

    @staticmethod
    async def _format_flights(flights: List[Dict[str, Any]], cabin_class: str = '經濟艙') -> List[Dict[str, Any]]:
        """
        格式化航班信息 (使用 FlightSearchResultSchema)
        
        Args:
            flights: 從 _query_flights 返回的原始航班數據列表 (字典列表)
            cabin_class: 請求的艙位類型 (用於選擇顯示哪個價格)
        
        Returns:
            List[Dict[str, Any]]: 格式化後用於 API 響應的航班信息列表
        """
        prepared_data = []
        
        # 標準化艙等，默認為經濟艙
        normalized_cabin_class = normalize_cabin_class(cabin_class)
        
        logger.debug(f"原始艙等: '{cabin_class}', 標準化後: '{normalized_cabin_class}'")
        logger.info(f"格式化航班數據: 傳入艙等='{cabin_class}', 標準化艙等='{normalized_cabin_class}', 航班數量={len(flights)}")

        for flight in flights:
            logger.debug(f"處理航班 {flight.get('flight_id')}, 座位數={flight.get('available_seats')}")
            logger.debug(f"價格數據: 經濟艙={flight.get('economy_price')}, 商務艙={flight.get('business_price')}, 頭等艙={flight.get('first_price')}")

            # 1. 選擇價格 - 使用標準化後的艙等
            price = None
            available_seats = flight.get('available_seats', 0)
            
            if normalized_cabin_class == '經濟艙':
                price = flight.get('economy_price')
            elif normalized_cabin_class == '商務艙':
                price = flight.get('business_price')
            elif normalized_cabin_class == '頭等艙':
                price = flight.get('first_price')
                
            # 確保價格存在且座位數大於0，否則跳過此航班
            if price is None or available_seats <= 0:
                logger.debug(f"跳過航班 {flight.get('flight_id')}: 價格={price}, 可用座位={available_seats}")
                continue
                
            # 所有檢查都通過，設置為可用
            isAvailable = True
            logger.debug(f"航班 {flight.get('flight_id')} 艙等: {normalized_cabin_class}, 價格: {price}, 可用座位: {available_seats}, 票價可用: {isAvailable}")

            if isinstance(price, Decimal):
                price = float(price)

            # 2. 計算飛行時間 (如果 SQL 沒算好)
            duration_minutes = flight.get('duration_minutes')
            if duration_minutes is not None:
                try:
                    duration_minutes = int(duration_minutes)
                except (ValueError, TypeError):
                    logger.warning(f"無法將 duration_minutes '{duration_minutes}' 轉換為整數，航班 ID: {flight.get('flight_id')}")
                    duration_minutes = None
            else:
                 # 如果 SQL 沒算，嘗試從時間計算
                departure_time_obj = flight.get('scheduled_departure')
                arrival_time_obj = flight.get('scheduled_arrival')
                if departure_time_obj and arrival_time_obj:
                    duration_delta = arrival_time_obj - departure_time_obj
                    duration_minutes = int(duration_delta.total_seconds() / 60)
                else:
                    duration_minutes = None

            # 3. 準備傳遞給 Schema 的數據字典
            #    鍵名需要匹配 Schema 字段名，或嵌套 Schema 的 attribute 指定的鍵名
            data_for_schema = {
                'flight_id': flight.get('flight_id'),
                'flight_number': flight.get('flight_number'),
                'aircraft': flight.get('aircraft'),
                'available_seats': flight.get('available_seats'),
                'price_updated_at': flight.get('price_updated_at').isoformat() if flight.get('price_updated_at') else None,
                'duration_minutes': duration_minutes,
                'price': { # 價格嵌套
                    'amount': price,
                    'currency': 'TWD',
                    'cabin_class': normalized_cabin_class,  # 使用標準化後的艙等
                    'isAvailable': isAvailable  # 添加可用性標誌
                },
                'airline': { # 航空公司嵌套
                    'code': flight.get('airline_iata'), # Schema 期望 'code'
                    'name_zh': flight.get('airline_name_zh'),
                    'name_en': flight.get('airline_name_en'),
                    'logo_path': flight.get('logo_path'),
                    'is_domestic': flight.get('airline_is_domestic')
                },
                'departure': { # 出發地嵌套
                    'code': flight.get('departure_code'),
                    'name': flight.get('departure_name'), # *** 修改：使用 'name' 鍵 ***
                    'city': flight.get('departure_city'),
                    'country': flight.get('departure_country'),
                    'terminal': flight.get('departure_terminal'),
                    'time': flight.get('scheduled_departure').isoformat() if flight.get('scheduled_departure') else None
                },
                'arrival': { # 目的地嵌套
                    'code': flight.get('arrival_code'),
                    'name': flight.get('arrival_name'), # *** 修改：使用 'name' 鍵 ***
                    'city': flight.get('arrival_city'),
                    'country': flight.get('arrival_country'),
                    'terminal': flight.get('arrival_terminal'),
                    'time': flight.get('scheduled_arrival').isoformat() if flight.get('scheduled_arrival') else None
                }
            }
            prepared_data.append(data_for_schema)

        # 4. 使用 Schema 進行序列化
        try:
            result = flights_search_result_schema.dump(prepared_data)
            logger.debug(f"Schema serialized result: {result}")
            return result
        except ValidationError as err:
            logger.error(f"序列化航班數據時出錯: {err.messages}")
            # 在生產環境中可能需要更健壯的錯誤處理
            # 例如，返回部分成功或特定的錯誤響應
            return [] # 或者 raise err
        except Exception as e:
            logger.error(f"序列化過程中發生意外錯誤: {e}", exc_info=True)
            return []

    @staticmethod
    async def search_flights_from_taiwan(
        arrival_airport_id: Optional[str] = None,
        date: Optional[datetime.date] = None,
        airlines: Optional[List[str]] = None,
        price_min: Optional[int] = None, 
        price_max: Optional[int] = None,
        cabin_class: str = 'ECONOMY',
        passengers: int = 1,
        max_results: int = 10,
        sort_by: str = 'price',
        sort_order: str = 'asc'
    ) -> List[Dict[str, Any]]:
        """
        從台灣機場出發到指定目的地的航班搜索
        
        Args:
            arrival_airport_id: 到達機場ID
            date: 出發日期
            airlines: 航空公司IATA代碼列表
            price_min: 最低價格
            price_max: 最高價格
            cabin_class: 艙位等級 (英文)
            passengers: 乘客數量
            max_results: 最大結果數
            sort_by: 排序方式，'price' 或 'departure_time'
            sort_order: 排序順序，'asc' 或 'desc'
            
        Returns:
            List[Dict[str, Any]]: 航班列表
        """
        
        async def fetch_taiwan_airports(conn):
            # 查詢台灣機場 ID 列表
            query = """
                SELECT airport_id 
                FROM airports 
                WHERE country = 'Taiwan' 
                ORDER BY airport_id;
            """
            rows = await conn.fetch(query)
            return [row['airport_id'] for row in rows]
        
        async def perform_search(conn):
            # 獲取台灣機場ID列表
            taiwan_airport_ids = await fetch_taiwan_airports(conn)
            if not taiwan_airport_ids:
                logger.error("無法獲取台灣機場列表")
                return []
            
            # 構建查詢條件
            conditions = ["f.departure_airport_id = ANY($1)"]
            params = [taiwan_airport_ids]
            
            param_index = 2
            
            if arrival_airport_id:
                conditions.append(f"f.arrival_airport_id = ${param_index}")
                params.append(arrival_airport_id)
                param_index += 1
            
            if date:
                conditions.append(f"DATE(f.scheduled_departure) = ${param_index}")
                params.append(date)
                param_index += 1
            
            if airlines and len(airlines) > 0:
                placeholders = []
                for airline in airlines:
                    placeholders.append(f"${param_index}")
                    params.append(airline)
                    param_index += 1
                conditions.append(f"al.airline_id IN ({', '.join(placeholders)})")
            
            # 根據請求的 cabin_class 選擇價格過濾欄位
            price_filter_field = get_price_field_by_cabin_class(cabin_class)
                
            if price_min is not None:
                conditions.append(f"{price_filter_field} >= ${param_index}")
                params.append(price_min)
                param_index += 1
            
            if price_max is not None:
                conditions.append(f"{price_filter_field} <= ${param_index}")
                params.append(price_max)
                param_index += 1
                
            # 決定排序方式
            sort_column = price_filter_field # 按請求艙等的價格排序
            if sort_by == 'departure_time':
                 sort_column = "f.scheduled_departure"
            
            sort_direction = "ASC" if sort_order.lower() == 'asc' else "DESC"
            
            # 構建 CTE 查詢
            query = f"""
            WITH RankedFlights AS (
                SELECT 
                    f.flight_id,
                    f.flight_number,
                    f.scheduled_departure,
                    f.scheduled_arrival,
                    f.aircraft,
                    f.departure_terminal,
                    f.arrival_terminal,
                    EXTRACT(EPOCH FROM (f.scheduled_arrival - f.scheduled_departure)) / 60 AS duration_minutes,
                    al.airline_id as airline_iata,
                    al.name_zh as airline_name_zh,
                    al.name_en as airline_name_en, 
                    COALESCE(al.is_domestic, FALSE) as airline_is_domestic,
                    al.logo_path as logo_path,
                    dep.airport_id as departure_airport_id,
                    dep.name_zh as departure_name,
                    dep.city as departure_city,
                    dep.country as departure_country,
                    arr.airport_id as arrival_airport_id,
                    arr.name_zh as arrival_name,
                    arr.city as arrival_city,
                    arr.country as arrival_country,
                    tp.economy_price,
                    tp.business_price,
                    tp.first_price,
                    tp.available_seats,
                    tp.price_updated_at,
                    {sort_column} as sort_key,
                    ROW_NUMBER() OVER (PARTITION BY f.flight_number, DATE(f.scheduled_departure) ORDER BY {sort_column} {sort_direction}, tp.price_updated_at DESC) as rank
                FROM 
                    flights f
                JOIN 
                    airports dep ON f.departure_airport_id = dep.airport_id
                JOIN 
                    airports arr ON f.arrival_airport_id = arr.airport_id
                JOIN 
                    airlines al ON f.airline_id = al.airline_id
                LEFT JOIN
                    ticket_prices tp ON f.flight_id = tp.flight_id
                WHERE 
                    {" AND ".join(conditions)}
            )
            SELECT * FROM RankedFlights 
            WHERE rank = 1
            ORDER BY sort_key {sort_direction}
            LIMIT ${param_index};
            """
            
            params.append(max_results)
            
            try:
                rows = await conn.fetch(query, *params)
                flights_raw = [dict(row) for row in rows]
                
                # 使用 _format_flights 格式化數據，傳入請求的 cabin_class
                formatted_flights = await FlightSearchService._format_flights(flights_raw, cabin_class)
                logger.info(f"成功搜索到 {len(formatted_flights)} 個台灣出發航班")
                return formatted_flights

            except asyncpg.exceptions.PostgresError as e:
                logger.error(f"搜索台灣出發航班數據庫錯誤: {e}\nSQL: {query}\nParams: {params}", exc_info=True)
                raise
            except Exception as e:
                logger.error(f"搜索台灣出發航班時發生錯誤: {e}", exc_info=True)
                raise
        
        # 使用 execute_db_operation 包裝資料庫操作
        pool = await init_asyncpg_pool()
        conn = await pool.acquire()
        try:
            return await perform_search(conn)
        finally:
            if conn:
                await pool.release(conn)

    @staticmethod
    async def get_flights_from_taiwan(
        arrival_iata: str,
        date_str: str,
        max_results: int = 50,
        cabin_class: str = "經濟艙"
    ) -> List[Dict[str, Any]]:
        """
        從所有台灣機場獲取飛往特定目的地的航班
        
        注意: 此方法與 search_flights_from_taiwan 功能重疊，建議使用後者以獲得更多過濾選項。
        保留此方法是為了向後兼容性。

        Args:
            arrival_iata (str): 目的地機場ID
            date_str (str): 日期 (YYYY-MM-DD)
            max_results (int, optional): 最大結果數，默認為50
            cabin_class (str, optional): 艙位類型，默認為"經濟"

        Returns:
            List[Dict[str, Any]]: 格式化後的航班列表
        """
        logger.warning("調用了 get_flights_from_taiwan，建議使用 search_flights_from_taiwan 以獲得更多過濾選項。")
        # 將中文艙等轉換為英文以調用 search_flights_from_taiwan
        cabin_class_en = 'ECONOMY'
        if cabin_class == "商務艙":
            cabin_class_en = 'BUSINESS'
        elif cabin_class == "頭等艙":
            cabin_class_en = 'FIRST'
            
        # 將日期字符串轉換為 date 對象
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            logger.error(f"無效的日期格式: {date_str}")
            return []
            
        return await FlightSearchService.search_flights_from_taiwan(
            arrival_airport_id=arrival_iata,
            date=date_obj, # 傳遞 date 對象
            cabin_class=cabin_class_en, # 傳遞英文艙等
            max_results=max_results,
            sort_by="price" # 默認按價格排序
        ) 

    @staticmethod
    async def get_flight_details_by_id(conn, flight_id: str) -> Optional[Dict[str, Any]]:
        """
        根據航班 ID 獲取航班詳細信息，包含關聯數據。
        Args:
            conn: asyncpg 連接對象。
            flight_id: 航班的 UUID。
        Returns:
            包含航班詳細信息的字典，如果未找到則返回 None。
        """
        query = """
            SELECT
                f.flight_id,
                f.flight_number,
                f.scheduled_departure,
                f.scheduled_arrival,
                f.departure_terminal,
                f.arrival_terminal,
                f.aircraft,
                f.created_at,
                f.updated_at,
                
                al.airline_id AS airline_code, -- For AirlineBasicSchema
                al.name_zh AS airline_name_zh,
                al.name_en AS airline_name_en,
                al.logo_path AS airline_logo_path,
                al.is_domestic AS airline_is_domestic,
                
                dep_ap.airport_id AS departure_airport_code, -- For AirportBasicSchema
                dep_ap.name_zh AS departure_airport_name_zh,
                dep_ap.city AS departure_airport_city,
                dep_ap.country AS departure_airport_country,
                
                arr_ap.airport_id AS arrival_airport_code, -- For AirportBasicSchema
                arr_ap.name_zh AS arrival_airport_name_zh,
                arr_ap.city AS arrival_airport_city,
                arr_ap.country AS arrival_airport_country,
                
                tp.economy_price,
                tp.business_price,
                tp.first_price,
                tp.available_seats,
                tp.price_updated_at
            FROM flights f
            LEFT JOIN airlines al ON f.airline_id = al.airline_id
            LEFT JOIN airports dep_ap ON f.departure_airport_id = dep_ap.airport_id
            LEFT JOIN airports arr_ap ON f.arrival_airport_id = arr_ap.airport_id
            LEFT JOIN ticket_prices tp ON f.flight_id = tp.flight_id
            WHERE f.flight_id = $1;
        """
        try:
            row = await conn.fetchrow(query, flight_id)
            if row:
                # 準備數據以匹配 FlightSchema (包括嵌套的 AirlineBasicSchema 和 AirportBasicSchema)
                flight_data = {
                    "flight_id": row['flight_id'],
                    "flight_number": row['flight_number'],
                    "scheduled_departure": row['scheduled_departure'],
                    "scheduled_arrival": row['scheduled_arrival'],
                    "actual_departure": None, # Set to None as column does not exist
                    "actual_arrival": None,   # Set to None as column does not exist
                    "departure_terminal": row['departure_terminal'],
                    "arrival_terminal": row['arrival_terminal'],
                    "aircraft": row['aircraft'],
                    "created_at": row['created_at'],
                    "updated_at": row['updated_at'],
                    "airline_rel": { # 匹配 FlightSchema 中 attribute="airline_rel"
                        "code": row['airline_code'],
                        "name_zh": row['airline_name_zh'],
                        "name_en": row['airline_name_en'],
                        "logo_path": row['airline_logo_path'],
                        "is_domestic": row['airline_is_domestic']
                    },
                    "departure_airport_rel": { # 匹配 FlightSchema 中 attribute="departure_airport_rel"
                        "code": row['departure_airport_code'],
                        "name": row['departure_airport_name_zh'], # AirportBasicSchema 期望 'name'
                        "city": row['departure_airport_city'],
                        "country": row['departure_airport_country']
                        # AirportBasicSchema 中沒有 terminal 和 time, 在此處不填充
                    },
                    "arrival_airport_rel": { # 匹配 FlightSchema 中 attribute="arrival_airport_rel"
                        "code": row['arrival_airport_code'],
                        "name": row['arrival_airport_name_zh'], # AirportBasicSchema 期望 'name'
                        "city": row['arrival_airport_city'],
                        "country": row['arrival_airport_country']
                        # AirportBasicSchema 中沒有 terminal 和 time, 在此處不填充
                    },
                    # 可以在這裡添加價格信息的處理，如果 FlightSchema 需要直接包含價格
                    # 例如，將 row['economy_price'] 等構建成 prices_rel (如果 FlightSchema 有此字段)
                }
                logger.info(f"成功獲取航班 {flight_id} 的詳細信息。")
                return flight_data
            else:
                logger.warning(f"在數據庫中未找到航班 ID: {flight_id}")
                return None
        except Exception as e:
            logger.error(f"根據 ID ({flight_id}) 獲取航班詳細信息時出錯: {e}", exc_info=True)
            return None 

    @staticmethod
    async def get_popular_flights(
        max_results: int = 20,
        cabin_class: str = "經濟艙",
        days_ahead: int = 30  # 查詢未來多少天的航班
    ) -> List[Dict[str, Any]]:
        """
        獲取預定義熱門航線上的未來航班。

        Args:
            max_results (int): 返回的最大航班數量。
            cabin_class (str): 艙等，用於格式化價格。
            days_ahead (int): 從今天起，查詢未來多少天內的航班。

        Returns:
            List[Dict[str, Any]]: 熱門航班列表。
        """
        logger.info(f"開始獲取熱門航班: max_results={max_results}, cabin_class='{cabin_class}', days_ahead={days_ahead}")
        
        all_popular_flights_raw = []
        today = datetime.now().date()
        
        # 合併國內和國際熱門航線
        popular_routes = POPULAR_DOMESTIC_ROUTES_TUPLES + POPULAR_INTERNATIONAL_ROUTES_TUPLES

        pool = await init_asyncpg_pool()
        conn = await pool.acquire()
        
        try:
            for departure_code, arrival_code in popular_routes: # <--- 已修正此處
                logger.debug(f"查詢熱門航線: {departure_code} -> {arrival_code} 在未來 {days_ahead} 天的航班")
                # 遍歷未來N天
                for i in range(days_ahead):
                    query_date = today + timedelta(days=i)
                    date_str = query_date.strftime("%Y-%m-%d")
                    
                    try:
                        flights_on_date_raw = await FlightSearchService._query_flights(
                            conn,
                            departure_code=departure_code.upper(),
                            arrival_code=arrival_code.upper(),
                            date_str=date_str,
                            cabin_class=cabin_class,
                            max_results=max_results 
                        )
                        if flights_on_date_raw:
                            all_popular_flights_raw.extend(flights_on_date_raw)
                            logger.debug(f"在 {date_str} 找到 {len(flights_on_date_raw)} 個 {departure_code}->{arrival_code} 航班")
                        
                        if len(all_popular_flights_raw) >= max_results * 2: 
                            logger.info(f"已收集到足夠的潛在熱門航班 ({len(all_popular_flights_raw)}個)，提前部分中止查詢。")
                            break 
                    except Exception as e_query_daily:
                        logger.error(f"查詢熱門航線 {departure_code}->{arrival_code} 在 {date_str} 時出錯: {e_query_daily}")
                        continue
                if len(all_popular_flights_raw) >= max_results * 2: 
                    break

            if not all_popular_flights_raw:
                logger.info("未找到任何熱門航線上的未來航班。")
                return []

            logger.info(f"原始查詢到的熱門航班數量: {len(all_popular_flights_raw)}")

            # 格式化所有收集到的航班 (價格等)
            formatted_flights = await FlightSearchService._format_flights(
                all_popular_flights_raw, cabin_class
            )
            
            logger.info(f"格式化後的熱門航班數量: {len(formatted_flights)}")

            # 修正篩選邏輯：檢查 price 字典及其 amount 是否有效
            valid_price_flights = [
                f for f in formatted_flights 
                if f.get('price') and f['price'].get('amount') is not None and f['price'].get('isAvailable') is True
            ]
            
            logger.info(f"經過價格有效性篩選後的航班數量: {len(valid_price_flights)}")

            # 修正排序邏輯：按價格升序排序，然後按出發時間升序
            # 確保從正確的嵌套結構中獲取價格和時間
            valid_price_flights.sort(key=lambda x: (
                x.get('price', {}).get('amount', float('inf')), 
                datetime.fromisoformat(x['departure']['time']).timestamp() if x.get('departure') and x['departure'].get('time') and isinstance(x['departure']['time'], str) else float('inf')
            ))
            
            logger.info(f"排序後且有有效價格的熱門航班數量: {len(valid_price_flights)}")
            
            # 限制最終結果數量
            final_results = valid_price_flights[:max_results]
            logger.info(f"最終返回 {len(final_results)} 個熱門航班。")
            
            return final_results

        except Exception as e:
            logger.error(f"獲取熱門航班時發生整體錯誤: {e}", exc_info=True)
            return [] 
        finally:
            if conn:
                await pool.release(conn) 