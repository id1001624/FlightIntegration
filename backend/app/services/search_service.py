#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
飛行搜索服務模組 - 處理航班搜尋的業務邏輯
"""

import logging
import asyncpg  # 添加 asyncpg 導入
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple, Union
from sqlalchemy.sql import text, func
from sqlalchemy import or_ # 導入 or_ 用於多航線篩選
from decimal import Decimal
from marshmallow import ValidationError # 導入 ValidationError

# 導入 asyncpg 連接池初始化函數
from ..database.db import init_asyncpg_pool
# 這些模型現在僅用於類型提示
from ..models import Airline, Airport, Flight, TicketPrice
from ..schemas.flight_schema import FlightSchema, FlightSearchArgsSchema, FlightSearchResultSchema
from ..schemas.airline_schema import AirlineBasicSchema
from ..schemas.airport_schema import AirportBasicSchema
from ..utils.api_client import ApiClient
from ..utils.cache_manager import CacheManager
from ..scripts.constants import COMBINED_POPULAR_ROUTES_TUPLES, TAIWAN_AIRPORTS # 導入常量

logger = logging.getLogger(__name__)

# 實例化 Schema (many=True)
flights_search_result_schema = FlightSearchResultSchema(many=True)

class SearchService:
    """搜索服務 - 處理航班搜索的業務邏輯"""
    
    @staticmethod
    async def search_flights(
        conn: asyncpg.Connection, # Accept connection as argument
        departure_code: str,
        arrival_code: str,
        date_str: str,
        airline_code: Optional[Union[str, List[str]]] = None,
        return_date_str: Optional[str] = None,
        price_min: Optional[int] = None,
        price_max: Optional[int] = None,
        cabin_class: str = "經濟艙", # 預設值改為 經濟艙
        passengers: int = 1,
        max_results: int = 20,
        sort_by: str = "price"
    ) -> Dict[str, List[Dict[str, Any]]]: 
        """
        執行航班搜索 (需要傳入數據庫連接) - **已修改為只返回請求艙等的列表**
        
        Args:
            conn: Active asyncpg database connection
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
        try:
            # 記錄所有傳入參數，特別是cabin_class
            logger.info(f"搜索航班參數: departure={departure_code}, arrival={arrival_code}, date={date_str}, " 
                       f"airline={airline_code}, return_date={return_date_str}, price_min={price_min}, "
                       f"price_max={price_max}, cabin_class='{cabin_class}', passengers={passengers}, "
                       f"max_results={max_results}, sort_by={sort_by}")
            
            # 查詢去程航班 (數據包含所有艙位價格)
            outbound_flights_raw = await SearchService._query_flights(
                conn,
                departure_code, arrival_code, date_str,
                airline_code, price_min, price_max,
                cabin_class, # 雖然傳入，但 query 主要看經濟艙排序
                max_results, sort_by
            )

            # **只格式化請求的艙等**
            outbound_flights_formatted = await SearchService._format_flights(outbound_flights_raw, cabin_class)

            # 準備結果字典
            result = {
                "departure": outbound_flights_formatted
            }

            # 如果提供了回程日期，也查詢並格式化回程航班
            if return_date_str:
                inbound_flights_raw = await SearchService._query_flights(
                    conn,
                    arrival_code, departure_code, return_date_str,
                    airline_code, price_min, price_max,
                    cabin_class,
                    max_results, sort_by
                )
                inbound_flights_formatted = await SearchService._format_flights(inbound_flights_raw, cabin_class)
                result["return"] = inbound_flights_formatted

            return result # 返回簡化後的結構

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
        cabin_class: str = "經濟艙", # 使用 cabin_class 選擇相應的價格欄位
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
        cabin_class = cabin_class.lower() if isinstance(cabin_class, str) else ''
        cabin_class_map = {
            'economy': '經濟艙',
            'business': '商務艙',
            'first': '頭等艙',
            '經濟艙': '經濟艙',
            '商務艙': '商務艙', 
            '頭等艙': '頭等艙',
            '經濟': '經濟艙',
            '商務': '商務艙',
            '頭等': '頭等艙'
        }
        normalized_cabin_class = cabin_class_map.get(cabin_class, '經濟艙')
        
        # 根據艙等選擇價格欄位
        price_field = "economy_price"
        if normalized_cabin_class == "商務艙": 
            price_field = "business_price"
        elif normalized_cabin_class == "頭等艙":
            price_field = "first_price"
            
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
            logger.debug(f"Raw rows from DB: {rows}") # Log raw rows
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

        # 添加英文和中文艙等的映射
        cabin_class = cabin_class.lower() if isinstance(cabin_class, str) else ''
        
        # 英文艙等轉換為標準化的中文艙等
        cabin_class_map = {
            'economy': '經濟艙',
            'business': '商務艙',
            'first': '頭等艙',
            # 如果已經是中文，保持不變
            '經濟艙': '經濟艙',
            '商務艙': '商務艙', 
            '頭等艙': '頭等艙',
            # 處理簡化的中文
            '經濟': '經濟艙',
            '商務': '商務艙',
            '頭等': '頭等艙'
        }
        
        # 標準化艙等，默認為經濟艙
        normalized_cabin_class = cabin_class_map.get(cabin_class, '經濟艙')
        
        logger.debug(f"原始艙等: '{cabin_class}', 標準化後: '{normalized_cabin_class}'")
        logger.info(f"格式化航班數據: 傳入艙等='{cabin_class}', 標準化艙等='{normalized_cabin_class}', 航班數量={len(flights)}")

        for flight in flights:
            logger.debug(f"處理航班 {flight.get('flight_id')}, 座位數={flight.get('available_seats')}")
            logger.debug(f"價格數據: 經濟艙={flight.get('economy_price')}, 商務艙={flight.get('business_price')}, 頭等艙={flight.get('first_price')}")

            # 1. 選擇價格 - ***使用標準化後的艙等***
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
    async def get_low_fare_calendar(
        departure_code: str,
        arrival_code: str,
        start_date: str,
        end_date: str,
        cabin_class: str = "經濟"
    ) -> Dict[str, Any]:
        """
        獲取指定時間範圍內的低價日曆
        
        Args:
            departure_code: 出發地機場ID
            arrival_code: 目的地機場ID
            start_date: 開始日期 (YYYY-MM-DD)
            end_date: 結束日期 (YYYY-MM-DD)
            cabin_class: 艙位類型
            
        Returns:
            Dict[str, Any]: 低價日曆資料
        """
        pool = None
        conn = None
        
        try:
            # 嘗試解析日期
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
            
            # 確保日期範圍合理
            if (end_date_obj - start_date_obj).days > 90:  # 限制最多90天
                end_date_obj = start_date_obj + timedelta(days=90)
                logger.warning(f"日期範圍過大，已限制為90天: {start_date} 到 {end_date_obj.strftime('%Y-%m-%d')}")
            
            # 獲取連接池
            pool = await init_asyncpg_pool()
            
            # 根據艙等選擇對應的價格欄位
            price_field = "economy_price"
            if cabin_class == "商務":
                price_field = "business_price"
            elif cabin_class == "頭等":
                price_field = "first_price"
            
            try:
                conn = await pool.acquire()
                
                sql = f"""
                WITH DailyMinPrices AS (
                    SELECT 
                        DATE(f.scheduled_departure) AS flight_date,
                        MIN(tp.{price_field}) AS min_price
                    FROM flights f
                    JOIN airports a_dep ON f.departure_airport_id = a_dep.airport_id
                    JOIN airports a_arr ON f.arrival_airport_id = a_arr.airport_id
                    JOIN ticket_prices tp ON f.flight_id = tp.flight_id
                    WHERE a_dep.airport_id = $1 
                      AND a_arr.airport_id = $2
                      AND f.scheduled_departure BETWEEN $3 AND $4
                      AND tp.{price_field} IS NOT NULL
                    GROUP BY DATE(f.scheduled_departure)
                )
                SELECT 
                    TO_CHAR(flight_date, 'YYYY-MM-DD') AS date,
                    min_price AS price
                FROM DailyMinPrices
                ORDER BY flight_date;
                """
                
                # 執行查詢
                rows = await conn.fetch(
                    sql, 
                    departure_code, 
                    arrival_code, 
                    start_date_obj, 
                    end_date_obj + timedelta(days=1)  # 包含結束日期
                )
                
                # 格式化結果
                calendar_data = [{"date": row["date"], "price": float(row["price"])} for row in rows]
                
                # 檢查是否有缺失的日期，並以 null 價格補充
                date_set = {item["date"] for item in calendar_data}
                current_date = start_date_obj
                while current_date <= end_date_obj:
                    date_str = current_date.strftime("%Y-%m-%d")
                    if date_str not in date_set:
                        calendar_data.append({"date": date_str, "price": None})
                    current_date += timedelta(days=1)
                
                # 確保按日期排序
                calendar_data.sort(key=lambda x: x["date"])
                
                return {
                    "departure": departure_code,
                    "arrival": arrival_code,
                    "cabin_class": cabin_class,
                    "start_date": start_date,
                    "end_date": end_date_obj.strftime("%Y-%m-%d"),  # 使用可能調整後的結束日期
                    "data": calendar_data
                }
            
            finally:
                # 確保連接被釋放，即使發生錯誤
                if conn:
                    try:
                        await pool.release(conn)
                    except (RuntimeError, asyncpg.exceptions.InterfaceError) as e:
                        # 忽略特定異常
                        logger.warning(f"在釋放連接時發生可忽略的異常: {e}")
                    except Exception as e:
                        logger.error(f"在釋放連接時發生未預期的異常: {e}", exc_info=True)
                
        except Exception as e:
            logger.error(f"獲取低價日曆時發生錯誤: {e}", exc_info=True)
            return {
                "error": f"獲取低價日曆失敗: {str(e)}",
                "departure": departure_code,
                "arrival": arrival_code
            }

    @staticmethod
    async def get_fare_trends(
        departure_code: str,
        arrival_code: str,
        start_date: str, # 指定趨勢的起始日期
        cabin_class: str = "經濟",
        days_before: int = 30 # 預設查詢趨勢開始日期前30天
    ) -> Dict[str, Any]:
        """
        獲取特定航線的票價趨勢
        
        Args:
            departure_code: 出發地機場ID
            arrival_code: 目的地機場ID
            start_date: 趨勢起始日期
            cabin_class: 艙位類型
            days_before: 查詢多少天前的數據
            
        Returns:
            Dict[str, Any]: 票價趨勢數據
        """
        pool = None
        conn = None
        
        try:
            # 解析日期
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
            
            # 計算查詢的開始日期
            history_start_date = start_date_obj - timedelta(days=days_before)
            
            # 根據艙等選擇價格欄位
            price_field = "economy_price"
            if cabin_class == "商務":
                price_field = "business_price"
            elif cabin_class == "頭等":
                price_field = "first_price"
            
            # 獲取連接池
            pool = await init_asyncpg_pool()
            
            try:
                conn = await pool.acquire()
                
                # 查詢歷史票價記錄
                sql = f"""
                WITH DailyAvgPrices AS (
                    SELECT 
                        DATE(tp.created_at) AS record_date,
                        AVG(tp.{price_field}) AS avg_price
                    FROM ticket_prices tp
                    JOIN flights f ON tp.flight_id = f.flight_id
                    JOIN airports a_dep ON f.departure_airport_id = a_dep.airport_id
                    JOIN airports a_arr ON f.arrival_airport_id = a_arr.airport_id
                    WHERE a_dep.airport_id = $1 
                      AND a_arr.airport_id = $2
                      AND DATE(f.scheduled_departure) = $3
                      AND tp.created_at >= $4
                      AND tp.{price_field} IS NOT NULL
                    GROUP BY DATE(tp.created_at)
                    ORDER BY DATE(tp.created_at)
                )
                SELECT 
                    TO_CHAR(record_date, 'YYYY-MM-DD') AS date,
                    avg_price
                FROM DailyAvgPrices;
                """
                
                # 執行查詢
                rows = await conn.fetch(
                    sql, 
                    departure_code, 
                    arrival_code, 
                    start_date_obj,
                    history_start_date
                )
                
                # 整理數據
                trend_data = [
                    {
                        "date": row["date"],
                        "price": float(row["avg_price"])
                    }
                    for row in rows
                ]
                
                # 計算百分比變化
                if len(trend_data) >= 2:
                    first_price = trend_data[0]["price"]
                    last_price = trend_data[-1]["price"]
                    price_change = last_price - first_price
                    price_change_percent = (price_change / first_price) * 100 if first_price > 0 else 0
                else:
                    price_change = 0
                    price_change_percent = 0
                
                return {
                    "departure": departure_code,
                    "arrival": arrival_code,
                    "cabin_class": cabin_class,
                    "flight_date": start_date,
                    "trend_start_date": history_start_date.strftime("%Y-%m-%d"),
                    "data": trend_data,
                    "price_change": round(price_change, 2),
                    "price_change_percent": round(price_change_percent, 2)
                }
                
            finally:
                # 確保連接被釋放，即使發生錯誤
                if conn:
                    try:
                        await pool.release(conn)
                    except (RuntimeError, asyncpg.exceptions.InterfaceError) as e:
                        # 忽略特定異常
                        logger.warning(f"在釋放連接時發生可忽略的異常: {e}")
                    except Exception as e:
                        logger.error(f"在釋放連接時發生未預期的異常: {e}", exc_info=True)
                
        except Exception as e:
            logger.error(f"獲取票價趨勢時發生錯誤: {e}", exc_info=True)
            return {
                "error": f"獲取票價趨勢失敗: {str(e)}",
                "departure": departure_code,
                "arrival": arrival_code
            }

    @staticmethod
    async def get_route_stats(departure_code: str, arrival_code: str) -> Dict[str, Any]:
        """
        獲取航線統計信息
        
        Args:
            departure_code: 出發地機場ID
            arrival_code: 目的地機場ID
            
        Returns:
            Dict[str, Any]: 航線統計數據
        """
        pool = None
        conn = None
        
        try:
            # 獲取連接池
            pool = await init_asyncpg_pool()
            
            try:
                conn = await pool.acquire()
                
                # 查詢航線基本統計信息
                stats_sql = """
                WITH PriceStats AS (
                    SELECT 
                        MIN(tp.economy_price) AS min_economy,
                        AVG(tp.economy_price) AS avg_economy,
                        MIN(tp.business_price) AS min_business,
                        AVG(tp.business_price) AS avg_business,
                        MIN(tp.first_price) AS min_first,
                        AVG(tp.first_price) AS avg_first
                    FROM flights f
                    JOIN airports a_dep ON f.departure_airport_id = a_dep.airport_id
                    JOIN airports a_arr ON f.arrival_airport_id = a_arr.airport_id
                    JOIN ticket_prices tp ON f.flight_id = tp.flight_id
                    WHERE a_dep.airport_id = $1 
                      AND a_arr.airport_id = $2
                      AND f.scheduled_departure >= CURRENT_DATE
                ),
                FlightStats AS (
                    SELECT 
                        COUNT(DISTINCT f.flight_id) AS flight_count,
                        AVG(f.duration) AS avg_duration,
                        COUNT(DISTINCT al.airline_id) AS airline_count
                    FROM flights f
                    JOIN airports a_dep ON f.departure_airport_id = a_dep.airport_id
                    JOIN airports a_arr ON f.arrival_airport_id = a_arr.airport_id
                    JOIN airlines al ON f.airline_id = al.airline_id
                    WHERE a_dep.airport_id = $1 
                      AND a_arr.airport_id = $2
                      AND f.scheduled_departure >= CURRENT_DATE
                ),
                TopAirlines AS (
                    SELECT 
                        al.airline_id,
                        al.name_zh,
                        COUNT(f.flight_id) AS flight_count
                    FROM flights f
                    JOIN airports a_dep ON f.departure_airport_id = a_dep.airport_id
                    JOIN airports a_arr ON f.arrival_airport_id = a_arr.airport_id
                    JOIN airlines al ON f.airline_id = al.airline_id
                    WHERE a_dep.airport_id = $1 
                      AND a_arr.airport_id = $2
                      AND f.scheduled_departure >= CURRENT_DATE
                    GROUP BY al.airline_id, al.name_zh
                    ORDER BY flight_count DESC
                    LIMIT 5
                )
                SELECT 
                    p.min_economy, p.avg_economy,
                    p.min_business, p.avg_business,
                    p.min_first, p.avg_first,
                    f.flight_count, f.avg_duration, f.airline_count
                FROM PriceStats p, FlightStats f;
                """
                
                # 執行查詢
                stats_row = await conn.fetchrow(stats_sql, departure_code, arrival_code)
                
                # 查詢熱門航空公司
                airlines_sql = """
                SELECT 
                    al.airline_id,
                    al.name_zh,
                    COUNT(f.flight_id) AS flight_count
                FROM flights f
                JOIN airports a_dep ON f.departure_airport_id = a_dep.airport_id
                JOIN airports a_arr ON f.arrival_airport_id = a_arr.airport_id
                JOIN airlines al ON f.airline_id = al.airline_id
                WHERE a_dep.airport_id = $1 
                  AND a_arr.airport_id = $2
                  AND f.scheduled_departure >= CURRENT_DATE
                GROUP BY al.airline_id, al.name_zh
                ORDER BY flight_count DESC
                LIMIT 5;
                """
                
                airlines_rows = await conn.fetch(airlines_sql, departure_code, arrival_code)
                
                # 整理統計數據
                if stats_row:
                    stats = {
                        "prices": {
                            "economy": {
                                "min": float(stats_row["min_economy"]) if stats_row["min_economy"] else None,
                                "avg": round(float(stats_row["avg_economy"]), 2) if stats_row["avg_economy"] else None
                            },
                            "business": {
                                "min": float(stats_row["min_business"]) if stats_row["min_business"] else None,
                                "avg": round(float(stats_row["avg_business"]), 2) if stats_row["avg_business"] else None
                            },
                            "first": {
                                "min": float(stats_row["min_first"]) if stats_row["min_first"] else None,
                                "avg": round(float(stats_row["avg_first"]), 2) if stats_row["avg_first"] else None
                            }
                        },
                        "flights": {
                            "count": stats_row["flight_count"],
                            "avg_duration": round(stats_row["avg_duration"] / 60, 1) if stats_row["avg_duration"] else None, # 將秒轉換為分鐘
                            "airline_count": stats_row["airline_count"]
                        },
                        "top_airlines": [
                            {
                                "code": row["airline_id"],
                                "name": row["name_zh"],
                                "flight_count": row["flight_count"]
                            }
                            for row in airlines_rows
                        ]
                    }
                else:
                    stats = {
                        "prices": {"economy": {}, "business": {}, "first": {}},
                        "flights": {},
                        "top_airlines": []
                    }
                
                return {
                    "departure": departure_code,
                    "arrival": arrival_code,
                    "stats": stats
                }
                
            finally:
                # 確保連接被釋放，即使發生錯誤
                if conn:
                    try:
                        await pool.release(conn)
                    except (RuntimeError, asyncpg.exceptions.InterfaceError) as e:
                        # 忽略特定異常
                        logger.warning(f"在釋放連接時發生可忽略的異常: {e}")
                    except Exception as e:
                        logger.error(f"在釋放連接時發生未預期的異常: {e}", exc_info=True)
                
        except Exception as e:
            logger.error(f"獲取航線統計時發生錯誤: {e}", exc_info=True)
            return {
                "error": f"獲取航線統計失敗: {str(e)}",
                "departure": departure_code,
                "arrival": arrival_code
            }

    @staticmethod
    async def get_available_airlines():
        """
        獲取數據庫中所有可用航空公司的基本信息
        
        Returns:
            List[Dict[str, Any]]: 航空公司列表
        """
        pool = None
        conn = None
        
        try:
            pool = await init_asyncpg_pool()
            try:
                conn = await pool.acquire()
                
                sql = """
                SELECT airline_id, iata_code, name_zh, name_en, logo_url 
                FROM airlines 
                ORDER BY name_zh
                """
                rows = await conn.fetch(sql)
                logger.info(f"獲取到 {len(rows)} 家航空公司")
                # 使用 Pydantic 模型進行驗證和序列化 (可選，如果需要嚴格格式)
                # return [AirlineBasicSchema.from_orm(row).dict() for row in rows]
                # 直接返回字典列表
                return [dict(row) for row in rows]
                
            finally:
                # 確保連接被釋放，即使發生錯誤
                if conn:
                    try:
                        await pool.release(conn)
                    except (RuntimeError, asyncpg.exceptions.InterfaceError) as e:
                        # 忽略特定異常
                        logger.warning(f"在釋放連接時發生可忽略的異常: {e}")
                    except Exception as e:
                        logger.error(f"在釋放連接時發生未預期的異常: {e}", exc_info=True)
                        
        except Exception as e:
            logger.error(f"獲取可用航空公司時出錯: {e}", exc_info=True)
            return [] # 返回空列表表示錯誤或無數據

    @staticmethod
    async def get_taiwan_airports() -> List[Dict[str, Any]]:
        """
        獲取台灣所有機場列表
        
        Returns:
            List[Dict[str, Any]]: 台灣機場列表
        """
        pool = None
        conn = None
        try:
            pool = await init_asyncpg_pool()
            try:
                conn = await pool.acquire()
                
                # 查詢台灣所有機場（注意：資料庫沒有 iata_code 欄位，使用 airport_id）
                sql = """
                SELECT 
                    airport_id,
                    name_zh,
                    city,
                    country
                FROM airports
                WHERE country = '台灣'
                ORDER BY city, name_zh;
                """
                
                rows = await conn.fetch(sql)
                airports = [dict(row) for row in rows]
                logger.info(f"成功獲取台灣機場列表, 共 {len(airports)} 個機場")
                return airports
                
            finally:
                # 確保連接被釋放，即使發生錯誤
                if conn:
                    try:
                        await pool.release(conn)
                    except (RuntimeError, asyncpg.exceptions.InterfaceError) as e:
                        # 忽略特定異常
                        logger.warning(f"在釋放連接時發生可忽略的異常: {e}")
                    except Exception as e:
                        logger.error(f"在釋放連接時發生未預期的異常: {e}", exc_info=True)
        
        except Exception as e:
            logger.error(f"獲取台灣機場列表時出錯: {e}", exc_info=True)
            return []

    @staticmethod
    async def get_available_destinations(departure_airport: str, 
                                         date: str = None, 
                                         limit: int = 100) -> List[Dict[str, Any]]:
        """
        獲取從指定台灣機場出發可到達的目的地機場列表
        
        Args:
            departure_airport_id (str): 出發機場的 ID (IATA 代碼)
            date (str, optional): 過濾日期 (YYYY-MM-DD 格式)，若提供則只返回該日期有航班的目的地
            limit (int, optional): 返回結果的最大數量，預設為 100
            
        Returns:
            List[Dict[str, Any]]: 目的地機場資訊列表，包含代碼、名稱、城市、國家、航班數量和最低價格
            如果出錯則返回空列表
        """
        pool = None
        conn = None
        
        try:
            # 獲取連接池
            pool = await init_asyncpg_pool()
            conn = await pool.acquire()
            
            # 轉換參數
            departure_airport = departure_airport.upper()
            
            # 構建 SQL 查詢，根據是否有日期參數調整
            params = [departure_airport, limit]
            
            if date:
                # 如果提供了日期參數，只返回該日期有航班的目的地
                sql = """
                SELECT DISTINCT 
                    arr.airport_id,
                    arr.name_zh, -- 改回 name_zh，移除 airport_name 別名
                    arr.city,
                    arr.country,
                    COUNT(f.flight_id) AS flight_count,
                    MIN(tp.economy_price) AS min_price
                FROM 
                    flights f
                JOIN 
                    airports dep ON f.departure_airport_id = dep.airport_id
                JOIN 
                    airports arr ON f.arrival_airport_id = arr.airport_id
                LEFT JOIN
                    ticket_prices tp ON f.flight_id = tp.flight_id
                WHERE 
                    dep.airport_id = $1
                    AND tp.economy_price IS NOT NULL
                    AND DATE(f.scheduled_departure) = $3 -- 比較日期部分
                GROUP BY 
                    arr.airport_id, arr.name_zh, arr.city, arr.country
                ORDER BY 
                    arr.city
                LIMIT $2
                """
                # 將日期字串轉換為 date 物件，以便 asyncpg 正確處理
                try:
                    date_obj = datetime.strptime(date, '%Y-%m-%d').date()
                    params.append(date_obj)
                except ValueError:
                    # 如果日期格式在控制器層已驗證，這裡理論上不會發生
                    # 但為保險起見，記錄錯誤並返回空列表
                    logger.error(f"在服務層遇到無效的日期格式: {date}")
                    return []
            else:
                # 不過濾日期，返回所有目的地
                sql = """
                SELECT DISTINCT
                    arr.airport_id,
                    arr.name_zh, -- 改回 name_zh，移除 airport_name 別名
                    arr.city,
                    arr.country,
                    COUNT(f.flight_id) AS flight_count,
                    MIN(tp.economy_price) AS min_price
                FROM 
                    flights f
                JOIN 
                    airports dep ON f.departure_airport_id = dep.airport_id
                JOIN 
                    airports arr ON f.arrival_airport_id = arr.airport_id
                LEFT JOIN
                    ticket_prices tp ON f.flight_id = tp.flight_id
                WHERE 
                    dep.airport_id = $1
                    AND tp.economy_price IS NOT NULL
                GROUP BY 
                    arr.airport_id, arr.name_zh, arr.city, arr.country
                ORDER BY 
                    arr.city
                LIMIT $2
                """
            
            # 執行查詢
            rows = await conn.fetch(sql, *params)
            destinations = [dict(row) for row in rows]
            
            # 添加日誌記錄返回的數據
            logger.info(f"從機場ID {departure_airport} 查詢到的目的地數據: {destinations}")
            
            logger.info(f"成功獲取從機場ID {departure_airport} 出發的目的地，共 {len(destinations)} 個目的地 {' (過濾日期: ' + date + ')' if date else ''}")
            return destinations
                
        except Exception as e:
            logger.error(f"獲取從機場ID {departure_airport} 出發的目的地時出錯: {e}", exc_info=True)
            return []
            
        finally:
            # 確保連接被釋放，即使發生錯誤
            if conn and pool:
                try:
                    await pool.release(conn)
                except (RuntimeError, asyncpg.exceptions.InterfaceError) as e:
                    # 忽略特定異常
                    logger.warning(f"在釋放連接時發生可忽略的異常: {e}")
                except Exception as e:
                    logger.error(f"在釋放連接時發生未預期的異常: {e}", exc_info=True)

    @staticmethod
    async def get_flight_details_by_id(flight_id: str) -> Optional[Dict[str, Any]]:
        """
        通過 flight_id 獲取詳細航班信息
        
        Args:
            flight_id: 航班ID
            
        Returns:
            Optional[Dict[str, Any]]: 航班詳細信息
        """
        pool = None
        conn = None
        try:
            pool = await init_asyncpg_pool()
            try:
                conn = await pool.acquire()
                
                # SQL 查詢獲取航班詳細信息，包括機場、航空公司數據
                sql = """
                SELECT 
                    f.flight_id, 
                    f.flight_number,
                    f.scheduled_departure, 
                    f.scheduled_arrival,
                    f.departure_terminal,
                    f.arrival_terminal,
                    a1.airport_id as departure_airport_id,
                    a1.name_zh as departure_airport_name_zh,
                    a1.city as departure_city,
                    a1.country as departure_country,
                    a2.airport_id as arrival_airport_id,
                    a2.name_zh as arrival_airport_name_zh,
                    a2.city as arrival_city,
                    a2.country as arrival_country,
                    al.airline_id as airline_iata,
                    al.name_zh as airline_name_zh,
                    EXTRACT(EPOCH FROM (f.scheduled_arrival - f.scheduled_departure)) / 60 AS duration_minutes,
                    tp.available_seats,
                    tp.class_type
                FROM flights f
                JOIN airports a1 ON f.departure_airport_id = a1.airport_id
                JOIN airports a2 ON f.arrival_airport_id = a2.airport_id
                JOIN airlines al ON f.airline_id = al.airline_id
                LEFT JOIN ticket_prices tp ON f.flight_id = tp.flight_id -- 添加 JOIN
                WHERE f.flight_id = $1;
                """
                
                row = await conn.fetchrow(sql, flight_id)
                if not row:
                    logger.warning(f"航班ID {flight_id} 未找到")
                    return None
                    
                logger.info(f"成功獲取航班ID {flight_id} 的詳細信息")
                # 轉換為字典並返回
                flight_details = dict(row)
                # 添加可用座位信息 - 由於資料庫中只有一個 available_seats 欄位
                # 所以我們把同一個值用於所有艙位，但保持原有的嵌套結構格式
                available_seats = flight_details.pop('available_seats', None)
                class_type = flight_details.pop('class_type', '經濟') # 獲取艙位類型，預設為經濟艙
                
                # 根據艙位類型設置對應的座位數
                economy_seats = None
                business_seats = None
                first_seats = None
                
                if class_type == '經濟':
                    economy_seats = available_seats
                elif class_type == '商務':
                    business_seats = available_seats
                elif class_type == '頭等':
                    first_seats = available_seats
                
                flight_details['available_seats'] = {
                    'economy': economy_seats,
                    'business': business_seats,
                    'first': first_seats
                }
                return flight_details
                
            finally:
                # 確保連接被釋放，即使發生錯誤
                if conn and pool:
                    try:
                        await pool.release(conn)
                    except (RuntimeError, asyncpg.exceptions.InterfaceError) as e:
                        # 忽略特定異常
                        logger.warning(f"在釋放連接時發生可忽略的異常: {e}")
                    except Exception as e:
                        logger.error(f"在釋放連接時發生未預期的異常: {e}", exc_info=True)
        
        except Exception as e:
            logger.error(f"獲取航班ID {flight_id} 的詳細信息時出錯: {e}", exc_info=True)
            return None

    @classmethod
    async def search_flights_from_taiwan(
        cls,
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
        pool = None
        conn = None
        try:
            # 獲取台灣機場ID列表
            taiwan_airports = await cls.get_taiwan_airports()
            if not taiwan_airports:
                logger.error("無法獲取台灣機場列表")
                return []
            
            taiwan_airport_ids = [airport['airport_id'] for airport in taiwan_airports]
            
            pool = await init_asyncpg_pool()
            conn = await pool.acquire()
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
            price_filter_field = "tp.economy_price"
            if cabin_class.upper() == 'BUSINESS':
                price_filter_field = "tp.business_price"
            elif cabin_class.upper() == 'FIRST':
                price_filter_field = "tp.first_price"
                
            if price_min is not None:
                conditions.append(f"{price_filter_field} >= ${param_index}")
                params.append(price_min)
                param_index += 1
            
            if price_max is not None:
                conditions.append(f"{price_filter_field} <= ${param_index}")
                params.append(price_max)
                param_index += 1
                
            # 決定排序方式
            sort_column = "tp.economy_price" # 默認按經濟艙排序
            if sort_by == 'price':
                sort_column = price_filter_field # 按請求艙等的價格排序
            elif sort_by == 'departure_time':
                 sort_column = "f.scheduled_departure"
            # 可以添加 duration 等其他排序選項
            
            sort_direction = "ASC" if sort_order.lower() == 'asc' else "DESC"
            
            # 構建 CTE 查詢，確保在 RankedFlights 中包含所有需要的欄位
            # 添加所有艙等的價格欄位以供 _format_flights 使用
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
                    al.airline_id as airline_iata, # 注意: 模型是 airline_id
                    al.name_zh as airline_name_zh,
                    al.name_en as airline_name_en, 
                    COALESCE(al.is_domestic, FALSE) as airline_is_domestic,
                    al.logo_path as logo_path, # 修正：使用正確的欄位名
                    dep.airport_id as departure_airport_id,
                    dep.name_zh as departure_name, # 修正：使用 name_zh
                    dep.city as departure_city,
                    dep.country as departure_country,
                    arr.airport_id as arrival_airport_id,
                    arr.name_zh as arrival_name, # 修正：使用 name_zh
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
                LEFT JOIN -- 改為 LEFT JOIN 以包含可能沒有價格的航班
                    ticket_prices tp ON f.flight_id = tp.flight_id
                WHERE 
                    {" AND ".join(conditions)}
            )
            SELECT * FROM RankedFlights 
            WHERE rank = 1
            ORDER BY sort_key {sort_direction}
            LIMIT ${param_index};
            """
            
            params.append(max_results) # 將 max_results 添加到參數列表
            
            try:
                rows = await conn.fetch(query, *params)
                flights_raw = [dict(row) for row in rows]
                
                # 使用 _format_flights 格式化數據，傳入請求的 cabin_class
                formatted_flights = await cls._format_flights(flights_raw, cabin_class)
                logger.info(f"成功搜索到 {len(formatted_flights)} 個台灣出發航班")
                return formatted_flights

            except asyncpg.exceptions.PostgresError as e:
                logger.error(f"搜索台灣出發航班數據庫錯誤: {e}\nSQL: {query}\nParams: {params}", exc_info=True) # 添加 SQL 和參數到日誌
                raise
            except Exception as e:
                logger.error(f"搜索台灣出發航班時發生錯誤: {e}", exc_info=True)
                raise
        finally:
             # 確保連接被釋放，即使發生錯誤
             if conn and pool:
                 try:
                     await pool.release(conn)
                 except (RuntimeError, asyncpg.exceptions.InterfaceError) as e:
                     logger.warning(f"在釋放連接時發生可忽略的異常: {e}")
                 except Exception as e:
                     logger.error(f"在釋放連接時發生未預期的異常: {e}", exc_info=True)

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
            
        return await SearchService.search_flights_from_taiwan(
            arrival_airport_id=arrival_iata,
            date=date_obj, # 傳遞 date 對象
            cabin_class=cabin_class_en, # 傳遞英文艙等
            max_results=max_results,
            sort_by="price" # 默認按價格排序
        )

    @staticmethod
    async def get_flights_by_route(dep_airport: str, arr_airport: str, 
                                   from_date: str = None, to_date: str = None,
                                   limit: int = 100) -> List[Dict[str, Any]]:
        """
        根據出發和到達機場獲取航班信息
        
        Args:
            dep_airport (str): 出發機場 ID
            arr_airport (str): 到達機場 ID
            from_date (str, optional): 開始日期 (YYYY-MM-DD)
            to_date (str, optional): 結束日期 (YYYY-MM-DD)
            limit (int, optional): 返回結果的最大數量，默認為 100
            
        Returns:
            List[Dict[str, Any]]: 航班信息列表
        """
        pool = None
        conn = None
        
        try:
            pool = await init_asyncpg_pool()
            conn = await pool.acquire()
            
            params = [dep_airport, arr_airport]
            date_condition = ""
            
            if from_date:
                date_condition += " AND f.scheduled_departure >= $3"
                params.append(from_date)
            
            if to_date:
                # 確保結束日期包含當天
                to_date_end_of_day = datetime.strptime(to_date, "%Y-%m-%d") + timedelta(days=1) - timedelta(microseconds=1)
                date_condition += f" AND f.scheduled_departure <= ${len(params) + 1}"
                params.append(to_date_end_of_day)
            
            sql = f"""
            SELECT 
                f.flight_id,
                f.flight_number,
                al.airline_id, # 修正：使用 airline_id
                al.name_zh AS airline_name,
                a_dep.airport_id AS departure_airport,
                a_dep.name_zh AS departure_airport_name,
                a_dep.city AS departure_city,
                a_arr.airport_id AS arrival_airport,
                a_arr.name_zh AS arrival_airport_name,
                a_arr.city AS arrival_city,
                f.scheduled_departure AS departure_time,
                f.scheduled_arrival AS arrival_time,
                EXTRACT(EPOCH FROM (f.scheduled_arrival - f.scheduled_departure)) / 60 AS duration_minutes,
                tp.economy_price,
                tp.business_price,
                tp.first_price,
                tp.available_seats
            FROM flights f
            JOIN airlines al ON f.airline_id = al.airline_id
            JOIN airports a_dep ON f.departure_airport_id = a_dep.airport_id
            JOIN airports a_arr ON f.arrival_airport_id = a_arr.airport_id
            LEFT JOIN ticket_prices tp ON f.flight_id = tp.flight_id
            WHERE a_dep.airport_id = $1 
            AND a_arr.airport_id = $2
            {date_condition}
            ORDER BY f.scheduled_departure
            LIMIT ${len(params) + 1}
            """
            
            # 添加 limit 參數
            params.append(limit)
            
            rows = await conn.fetch(sql, *params)
            flights = [dict(row) for row in rows]
            
            logger.info(f"成功獲取從機場ID {dep_airport} 到機場ID {arr_airport} 的航班，共 {len(flights)} 個航班")
            return flights
                
        except Exception as e: # 更廣泛的異常捕獲
            logger.error(f"獲取從機場ID {dep_airport} 到機場ID {arr_airport} 的航班時出錯: {e}", exc_info=True)
            return [] 
        finally:
            # 確保連接被釋放，即使發生錯誤
            if conn and pool:
                try:
                    await pool.release(conn)
                except (RuntimeError, asyncpg.exceptions.InterfaceError) as e:
                    # 忽略特定異常
                    logger.warning(f"在釋放連接時發生可忽略的異常: {e}")
                except Exception as e:
                    logger.error(f"在釋放連接時發生未預期的異常: {e}", exc_info=True) 