#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
飛行搜索服務模組 - 處理航班搜尋的業務邏輯
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple, Union
from sqlalchemy.sql import text, func
from sqlalchemy import or_ # 導入 or_ 用於多航線篩選

# 導入 asyncpg 連接池初始化函數
from ..database.db import init_asyncpg_pool
# 這些模型現在僅用於類型提示
from ..models import Airline, Airport, Flight, TicketPrice
from ..schemas.flight_schema import FlightSchema, FlightSearchArgsSchema
from ..schemas.airline_schema import AirlineBasicSchema
from ..schemas.airport_schema import AirportBasicSchema
from ..utils.api_client import ApiClient
from ..utils.cache_manager import CacheManager
from ..scripts.constants import FRONTEND_POPULAR_ROUTES_TUPLES, TAIWAN_AIRPORTS # 導入常量

logger = logging.getLogger(__name__)

class SearchService:
    """搜索服務 - 處理航班搜索的業務邏輯"""
    
    @staticmethod
    async def search_flights(
        departure_code: str,
        arrival_code: str,
        date_str: str,
        airline_code: Optional[Union[str, List[str]]] = None,
        return_date_str: Optional[str] = None,
        price_min: Optional[int] = None,
        price_max: Optional[int] = None,
        cabin_class: str = "經濟",
        passengers: int = 1,
        max_results: int = 20,
        sort_by: str = "price"
    ) -> Dict[str, Any]:
        """
        執行航班搜索
        
        Args:
            departure_code: 出發地IATA代碼
            arrival_code: 目的地IATA代碼
            date_str: 去程日期 (YYYY-MM-DD)
            airline_code: 航空公司IATA代碼，可選
            return_date_str: 回程日期 (YYYY-MM-DD)，可選
            price_min: 最低價格，可選
            price_max: 最高價格，可選
            cabin_class: 艙位類型
            passengers: 乘客數量
            max_results: 每個方向的最大結果數
            sort_by: 排序方式
        
        Returns:
            Dict[str, Any]: 搜索結果
        """
        pool = None # 初始化 pool
        try:
            # 獲取數據庫連接池
            pool = await init_asyncpg_pool()
            
            async with pool.acquire() as conn: # 使用連接池獲取連接
                # 查詢去程航班
                outbound_flights = await SearchService._query_flights(
                    conn, # 傳遞 conn 而不是 db
                    departure_code, arrival_code, date_str, 
                    airline_code, price_min, price_max, 
                    cabin_class, max_results, sort_by
                )
                
                # 生成三種艙等的航班數據
                outbound_results = {
                    "economy": await SearchService._format_flights(outbound_flights, "經濟"),
                    "business": await SearchService._format_flights(outbound_flights, "商務"),
                    "first": await SearchService._format_flights(outbound_flights, "頭等")
                }
                
                # 如果提供了回程日期，也查詢回程航班
                inbound_results = None
                if return_date_str:
                    inbound_flights = await SearchService._query_flights(
                        conn, # 傳遞 conn 而不是 db
                        arrival_code, departure_code, return_date_str, 
                        airline_code, price_min, price_max, 
                        cabin_class, max_results, sort_by
                    )
                    inbound_results = {
                        "economy": await SearchService._format_flights(inbound_flights, "經濟"),
                        "business": await SearchService._format_flights(inbound_flights, "商務"),
                        "first": await SearchService._format_flights(inbound_flights, "頭等")
                    }
            
            # 準備結果 (連接已在 async with 區塊結束時自動釋放)
            result = {
                "all_cabins": {
                    "departure": { # 將去程放入 departure
                        "economy": {
                            "name": "經濟艙",
                            "flights": outbound_results["economy"]
                        },
                        "business": {
                            "name": "商務艙",
                            "flights": outbound_results["business"]
                        },
                        "first": {
                            "name": "頭等艙",
                            "flights": outbound_results["first"]
                        }
                    }
                }
            }
            
            if inbound_results:
                result["all_cabins"]["return"] = { # 將回程放入 return
                    "economy": {
                        "name": "經濟艙",
                        "flights": inbound_results["economy"]
                    },
                    "business": {
                        "name": "商務艙",
                        "flights": inbound_results["business"]
                    },
                    "first": {
                        "name": "頭等艙",
                        "flights": inbound_results["first"]
                    }
                }
                
            return result # 成功時返回包含 outbound/inbound 的字典

        except Exception as e:
            logger.error(f"執行航班搜索時發生未預期錯誤: {e}", exc_info=True)
            # 發生錯誤時，返回一個包含錯誤信息的字典，而不是列表
            return {"error": f"搜索服務內部錯誤: {str(e)}"} 
    
    @staticmethod
    async def _query_flights(
        conn, # 接收 conn 而不是 db
        departure_code: str,
        arrival_code: str,
        date_str: str,
        airline_code: Optional[Union[str, List[str]]] = None,
        price_min: Optional[int] = None,
        price_max: Optional[int] = None,
        cabin_class: str = "經濟", # 雖然 cabin_class 傳入，但目前SQL主要按最低價，需確認 _format_flights 是否處理艙等價格
        max_results: int = 20,
        sort_by: str = "price"
    ) -> List[Dict[str, Any]]:
        """
        查詢航班 (使用 asyncpg 連接)
        
        Args:
            conn: asyncpg 連接對象
            departure_code: 出發地機場IATA代碼
            arrival_code: 目的地機場IATA代碼
            date_str: 日期字符串 (YYYY-MM-DD)
            airline_code: 航空公司IATA代碼或代碼列表，可選
            price_min: 最低價格，可選
            price_max: 最高價格，可選
            cabin_class: 艙位類型 (目前主要影響格式化，查詢基於最低價)
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
        
        # 構建 SQL 查詢 - 使用IATA代碼
        sql = """
        WITH RankedFlights AS (
            SELECT 
                f.flight_id, 
                f.flight_number, 
                f.scheduled_departure, 
                f.scheduled_arrival, 
                a_dep.iata_code as departure_iata, 
                a_dep.name_zh as departure_name,
                a_dep.city as departure_city,
                a_dep.country as departure_country,
                a_arr.iata_code as arrival_iata, 
                a_arr.name_zh as arrival_name,
                a_arr.city as arrival_city,
                a_arr.country as arrival_country,
                al.iata_code as airline_iata, 
                al.name_zh as airline_name_zh,
                al.name_en as airline_name_en,
                al.logo_url as airline_logo_url,
                f.duration,
                f.aircraft_type,
                f.status,
                tp.price_economy,
                tp.price_business,
                tp.price_first,
                tp.currency,
                tp.last_updated as price_last_updated,
                -- 使用 COALESCE 處理 NULL 價格，給予一個極大值以便排序
                COALESCE(tp.price_economy, 99999999) as sort_price,
                -- 計算排序用的時間戳或數值
                EXTRACT(EPOCH FROM f.scheduled_departure) as sort_departure_time,
                f.duration as sort_duration,
                ROW_NUMBER() OVER (
                    PARTITION BY f.flight_number, f.scheduled_departure::date -- 按航班號和日期分區
                    ORDER BY tp.last_updated DESC -- 每個分區內按價格更新時間排序，取最新的
                ) as rn
            FROM flights f
            JOIN airports a_dep ON f.departure_airport_id = a_dep.airport_id
            JOIN airports a_arr ON f.arrival_airport_id = a_arr.airport_id
            JOIN airlines al ON f.airline_id = al.airline_id
            LEFT JOIN ticket_prices tp ON f.flight_id = tp.flight_id
            WHERE a_dep.iata_code = $1 
              AND a_arr.iata_code = $2
              AND f.scheduled_departure >= $3
              AND f.scheduled_departure <= $4
              {airline_filter} -- 航空公司過濾條件將插入這裡
              {price_filter}   -- 價格過濾條件將插入這裡
        )
        SELECT * 
        FROM RankedFlights 
        WHERE rn = 1 -- 只選取每個航班號和日期最新的價格記錄
        {sort_order} -- 排序條件將插入這裡
        LIMIT $5; -- 結果數量限制
        """

        params = [departure_code, arrival_code, start_of_day, end_of_day]
        param_index = 5 # LIMIT 是第5個參數 ($5)

        # 航空公司過濾
        airline_filter_sql = ""
        if airline_code:
            if isinstance(airline_code, list):
                if airline_code: # 確保列表不為空
                    airline_placeholders = ', '.join(f'${i}' for i in range(param_index + 1, param_index + 1 + len(airline_code)))
                    airline_filter_sql = f" AND al.iata_code IN ({airline_placeholders})"
                    params.extend(airline_code)
                    param_index += len(airline_code)
            elif isinstance(airline_code, str):
                airline_filter_sql = f" AND al.iata_code = ${param_index + 1}"
                params.append(airline_code)
                param_index += 1
        
        # 價格過濾 (基於經濟艙價格)
        price_filter_sql = ""
        if price_min is not None:
            price_filter_sql += f" AND tp.price_economy >= ${param_index + 1}"
            params.append(price_min)
            param_index += 1
        if price_max is not None:
            price_filter_sql += f" AND tp.price_economy <= ${param_index + 1}"
            params.append(price_max)
            param_index += 1
            
        # 排序條件
        sort_order_sql = ""
        if sort_by == "price":
            sort_order_sql = " ORDER BY sort_price ASC, f.scheduled_departure ASC" # 價格優先，然後起飛時間
        elif sort_by == "duration":
            sort_order_sql = " ORDER BY sort_duration ASC, sort_price ASC" # 時長優先，然後價格
        elif sort_by == "departure_time":
            sort_order_sql = " ORDER BY sort_departure_time ASC, sort_price ASC" # 起飛時間優先，然後價格
        else: # 默認按價格排序
            sort_order_sql = " ORDER BY sort_price ASC, f.scheduled_departure ASC"

        # 添加結果數量限制參數
        params.append(max_results)

        # 格式化最終 SQL
        final_sql = sql.format(
            airline_filter=airline_filter_sql,
            price_filter=price_filter_sql,
            sort_order=sort_order_sql
        )
        
        try:
            logger.debug(f"Executing SQL: {final_sql} with params: {params}")
            # 使用 conn 執行查詢
            rows = await conn.fetch(final_sql, *params)
            logger.info(f"查詢到 {len(rows)} 條航班記錄")
            # 將 asyncpg Row 對象轉換為字典列表
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"查詢航班時發生錯誤: {e}\nSQL: {final_sql}\nParams: {params}", exc_info=True)
            return []

    @staticmethod
    async def _format_flights(flights: List[Dict[str, Any]], cabin_class: str) -> List[Dict[str, Any]]:
        """
        格式化航班列表為API響應格式，並從數據庫獲取票價數據
        
        Args:
            flights: 從數據庫獲取的航班列表
            cabin_class: 目標艙位等級
        
        Returns:
            List[Dict[str, Any]]: 格式化後的航班列表，包含票價
        """
        formatted = []
        if not flights:
            return []
        
        # 一次性獲取所有相關航班的票價
        flight_ids = [f['flight_id'] for f in flights]
        # 假設有異步方法可以獲取票價
        from app.services.price_service import PriceService
        # 修改：調用新的批量方法
        prices = await PriceService.get_prices_for_flights_batch(flight_ids)
        
        for flight in flights:
            # 查找此航班和艙位的價格 - 使用批量獲取的結果
            flight_price_info = prices.get(str(flight['flight_id']), {}).get(cabin_class)
            
            # 如果找不到指定艙位價格，則跳過此航班（或設置為None，取決於需求）
            if not flight_price_info:
                # logger.debug(f"航班 {flight['flight_number']} ({flight['flight_id']}) 找不到艙位 '{cabin_class}' 的價格信息，跳過。")
                continue
                
            # 計算飛行時長（如果數據庫查詢未提供）
            # 假設 scheduled_departure 和 scheduled_arrival 已經在 flight 字典中
            duration_minutes = None
            dep_time = flight.get('scheduled_departure')
            arr_time = flight.get('scheduled_arrival')
            if dep_time and arr_time:
                try:
                    duration = arr_time - dep_time
                    duration_minutes = int(duration.total_seconds() / 60)
                except TypeError as e:
                    logger.warning(f"無法計算航班 {flight['flight_number']} ({flight['flight_id']}) 的時長: {e}")
            
            formatted_flight = {
                'flight_id': str(flight['flight_id']), # 確保是字符串
                'flight_number': flight['flight_number'],
                # --- 添加時間日期欄位 --- 
                'scheduled_departure': flight.get('scheduled_departure'), 
                'scheduled_arrival': flight.get('scheduled_arrival'),
                # -----------------------
                'duration_minutes': duration_minutes,
                'airline': {
                    'code': flight['airline_iata'],
                    'name_zh': flight['airline_name_zh'],
                    'name_en': flight['airline_name_en'],
                    'is_domestic': flight['airline_is_domestic'],
                    'logo_path': flight['airline_logo_url']
                },
                'departure_airport': {
                    'airport_id': flight.get('departure_airport_id'),
                    'code': flight.get('departure_iata'),
                    'name': flight.get('departure_name'),
                    'city': flight.get('departure_city'),
                    'country': flight.get('departure_country')
                },
                'arrival_airport': {
                    'airport_id': flight.get('arrival_airport_id'),
                    'code': flight.get('arrival_iata'),
                    'name': flight.get('arrival_name'),
                    'city': flight.get('arrival_city'),
                    'country': flight.get('arrival_country')
                },
                'price': { # 使用從 PriceService 獲取的價格信息
                    'amount': flight_price_info['amount'],
                    'cabin_class': flight_price_info['cabin_class'],
                    'available_seats': flight_price_info['available_seats']
                }
                # 可以在這裡添加其他需要的字段
            }
            formatted.append(formatted_flight)
            
        return formatted
    
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
            departure_code: 出發地IATA代碼
            arrival_code: 目的地IATA代碼
            start_date: 開始日期 (YYYY-MM-DD)
            end_date: 結束日期 (YYYY-MM-DD)
            cabin_class: 艙位類型
            
        Returns:
            Dict[str, Any]: 低價日曆資料
        """
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
            price_field = "price_economy"
            if cabin_class == "商務":
                price_field = "price_business"
            elif cabin_class == "頭等":
                price_field = "price_first"
            
            # 構建 SQL 查詢
            async with pool.acquire() as conn:
                sql = f"""
                WITH DailyMinPrices AS (
                    SELECT 
                        DATE(f.scheduled_departure) AS flight_date,
                        MIN(tp.{price_field}) AS min_price
                    FROM flights f
                    JOIN airports a_dep ON f.departure_airport_id = a_dep.airport_id
                    JOIN airports a_arr ON f.arrival_airport_id = a_arr.airport_id
                    JOIN ticket_prices tp ON f.flight_id = tp.flight_id
                    WHERE a_dep.iata_code = $1 
                      AND a_arr.iata_code = $2
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
            departure_code: 出發地IATA代碼
            arrival_code: 目的地IATA代碼
            start_date: 趨勢起始日期
            cabin_class: 艙位類型
            days_before: 查詢多少天前的數據
            
        Returns:
            Dict[str, Any]: 票價趨勢數據
        """
        try:
            # 解析日期
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
            
            # 計算查詢的開始日期
            history_start_date = start_date_obj - timedelta(days=days_before)
            
            # 根據艙等選擇價格欄位
            price_field = "price_economy"
            if cabin_class == "商務":
                price_field = "price_business"
            elif cabin_class == "頭等":
                price_field = "price_first"
            
            # 獲取連接池
            pool = await init_asyncpg_pool()
            
            async with pool.acquire() as conn:
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
                    WHERE a_dep.iata_code = $1 
                      AND a_arr.iata_code = $2
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
            departure_code: 出發地IATA代碼
            arrival_code: 目的地IATA代碼
            
        Returns:
            Dict[str, Any]: 航線統計數據
        """
        try:
            # 獲取連接池
            pool = await init_asyncpg_pool()
            
            async with pool.acquire() as conn:
                # 查詢航線基本統計信息
                stats_sql = """
                WITH PriceStats AS (
                    SELECT 
                        MIN(tp.price_economy) AS min_economy,
                        AVG(tp.price_economy) AS avg_economy,
                        MIN(tp.price_business) AS min_business,
                        AVG(tp.price_business) AS avg_business,
                        MIN(tp.price_first) AS min_first,
                        AVG(tp.price_first) AS avg_first
                    FROM flights f
                    JOIN airports a_dep ON f.departure_airport_id = a_dep.airport_id
                    JOIN airports a_arr ON f.arrival_airport_id = a_arr.airport_id
                    JOIN ticket_prices tp ON f.flight_id = tp.flight_id
                    WHERE a_dep.iata_code = $1 
                      AND a_arr.iata_code = $2
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
                    WHERE a_dep.iata_code = $1 
                      AND a_arr.iata_code = $2
                      AND f.scheduled_departure >= CURRENT_DATE
                ),
                TopAirlines AS (
                    SELECT 
                        al.airline_id,
                        al.name_zh,
                        al.iata_code,
                        COUNT(f.flight_id) AS flight_count
                    FROM flights f
                    JOIN airports a_dep ON f.departure_airport_id = a_dep.airport_id
                    JOIN airports a_arr ON f.arrival_airport_id = a_arr.airport_id
                    JOIN airlines al ON f.airline_id = al.airline_id
                    WHERE a_dep.iata_code = $1 
                      AND a_arr.iata_code = $2
                      AND f.scheduled_departure >= CURRENT_DATE
                    GROUP BY al.airline_id, al.name_zh, al.iata_code
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
                    al.iata_code,
                    al.name_zh,
                    COUNT(f.flight_id) AS flight_count
                FROM flights f
                JOIN airports a_dep ON f.departure_airport_id = a_dep.airport_id
                JOIN airports a_arr ON f.arrival_airport_id = a_arr.airport_id
                JOIN airlines al ON f.airline_id = al.airline_id
                WHERE a_dep.iata_code = $1 
                  AND a_arr.iata_code = $2
                  AND f.scheduled_departure >= CURRENT_DATE
                GROUP BY al.iata_code, al.name_zh
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
                                "code": row["iata_code"],
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
        獲取數據庫中所有可用航空公司的基本信息 (使用 asyncpg)
        
        Returns:
            List[Dict[str, Any]]: 航空公司列表
        """
        pool = None
        try:
            pool = await init_asyncpg_pool()
            async with pool.acquire() as conn:
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
        except Exception as e:
            logger.error(f"獲取可用航空公司時出錯: {e}", exc_info=True)
            return [] # 返回空列表表示錯誤或無數據

    @staticmethod
    async def get_taiwan_airports():
        """
        獲取數據庫中所有台灣機場的基本信息 (使用 asyncpg)
        
        注意: 在我們的資料庫設計中，airport_id 欄位實際上存儲的是機場的IATA代碼 (如TPE、TSA)
        同樣地，airline_id 欄位實際上存儲的是航空公司的代碼 (如CI、BR)
        這些ID直接作為識別符使用，不需要額外的iata_code欄位
        
        Returns:
            List[Dict[str, Any]]: 機場列表
        """
        pool = None
        try:
            pool = await init_asyncpg_pool()
            async with pool.acquire() as conn:
                sql = """
                SELECT airport_id, name_zh, city, country 
                FROM airports 
                WHERE country = '台灣' OR country = 'Taiwan' OR airport_id = ANY($1::text[]) -- 包括常量列表中的機場
                ORDER BY 
                    CASE 
                        WHEN airport_id IN ('TPE', 'TSA', 'RMQ', 'KHH') THEN 0 -- 主要國際/國內機場優先
                        ELSE 1 
                    END,
                    city, name_zh -- 然後按城市和名稱排序
                """
                # 從 constants 導入台灣機場列表
                from ..scripts.constants import TAIWAN_AIRPORTS 
                
                rows = await conn.fetch(sql, TAIWAN_AIRPORTS)
                logger.info(f"獲取到 {len(rows)} 個台灣機場")
                # 使用 Pydantic 模型 (可選)
                # return [AirportBasicSchema.from_orm(row).dict() for row in rows]
                # 直接返回字典列表
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"獲取台灣機場時出錯: {e}", exc_info=True)
            return []

    @staticmethod
    async def get_available_destinations(departure_iata: str, date_str: Optional[str] = None):
        """
        獲取從指定台灣機場出發可到達的目的地機場列表 (使用 asyncpg)
        
        Args:
            departure_iata: 出發機場的機場ID (應為台灣機場之一)
            date_str: 可選的日期 (YYYY-MM-DD)，用於過濾特定日期的航班 (目前未使用，保留兼容性)

        Returns:
            List[Dict[str, Any]]: 目的地機場列表
        """
        # 檢查 departure_iata 是否為台灣機場 (可選，增加健壯性)
        # from ..scripts.constants import TAIWAN_AIRPORTS
        # if departure_iata not in TAIWAN_AIRPORTS:
        #     logger.warning(f"請求的目的地查詢出發點 {departure_iata} 非台灣機場")
        #     # 可以選擇返回錯誤或空列表
        #     # return {"error": "出發點必須是台灣機場"}
        #     # return []

        pool = None
        try:
            pool = await init_asyncpg_pool()
            async with pool.acquire() as conn:
                # SQL 查詢從指定機場出發的所有航班的不重複目的地
                sql = """
                SELECT DISTINCT 
                    a_arr.airport_id, 
                    a_arr.name_zh, 
                    a_arr.city, 
                    a_arr.country
                FROM flights f
                JOIN airports a_dep ON f.departure_airport_id = a_dep.airport_id
                JOIN airports a_arr ON f.arrival_airport_id = a_arr.airport_id
                WHERE a_dep.airport_id = $1
                ORDER BY a_arr.country, a_arr.city, a_arr.name_zh; -- 按國家、城市、名稱排序
                """
                params = [departure_iata]
                
                # 如果提供了 date_str，可以添加日期過濾 (但需求中未明確要求)
                # if date_str:
                #     try:
                #         flight_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                #         start_of_day = datetime.combine(flight_date, datetime.min.time())
                #         end_of_day = datetime.combine(flight_date, datetime.max.time())
                #         sql = sql.replace("WHERE a_dep.airport_id = $1", 
                #                           "WHERE a_dep.airport_id = $1 AND f.scheduled_departure >= $2 AND f.scheduled_departure <= $3")
                #         params.extend([start_of_day, end_of_day])
                #     except ValueError:
                #         logger.warning(f"獲取目的地時日期格式錯誤: {date_str}，將忽略日期過濾")

                rows = await conn.fetch(sql, *params)
                logger.info(f"從 {departure_iata} 獲取到 {len(rows)} 個可用目的地")
                # 使用 Pydantic 模型 (可選)
                # return [AirportBasicSchema.from_orm(row).dict() for row in rows]
                # 直接返回字典列表
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"獲取從 {departure_iata} 出發的目的地時出錯: {e}", exc_info=True)
            return []


    @staticmethod
    async def get_flight_details_by_id(flight_id: str) -> Optional[Dict[str, Any]]:
        """
        根據 flight_id 獲取航班詳細信息 (使用 asyncpg)
        包括航班基本信息、起降機場、航空公司以及所有艙等的價格。

        Args:
            flight_id: 航班的UUID字符串

        Returns:
            Optional[Dict[str, Any]]: 包含航班詳細信息的字典，如果找不到則返回 None
        """
        pool = None
        try:
            pool = await init_asyncpg_pool()
            async with pool.acquire() as conn:
                # 構建 SQL 查詢
                sql = """
                SELECT 
                    f.flight_id, 
                    f.flight_number, 
                    f.scheduled_departure, 
                    f.scheduled_arrival, 
                    f.actual_departure, 
                    f.actual_arrival, 
                    f.status, 
                    f.duration, 
                    f.aircraft_type, 
                    f.notes,
                    -- 出發機場信息
                    a_dep.airport_id as departure_airport_id,
                    a_dep.iata_code as departure_iata,
                    a_dep.icao_code as departure_icao,
                    a_dep.name_zh as departure_name_zh,
                    a_dep.name_en as departure_name_en,
                    a_dep.city as departure_city,
                    a_dep.country as departure_country,
                    a_dep.latitude as departure_latitude,
                    a_dep.longitude as departure_longitude,
                    a_dep.timezone as departure_timezone,
                    -- 到達機場信息
                    a_arr.airport_id as arrival_airport_id,
                    a_arr.iata_code as arrival_iata,
                    a_arr.icao_code as arrival_icao,
                    a_arr.name_zh as arrival_name_zh,
                    a_arr.name_en as arrival_name_en,
                    a_arr.city as arrival_city,
                    a_arr.country as arrival_country,
                    a_arr.latitude as arrival_latitude,
                    a_arr.longitude as arrival_longitude,
                    a_arr.timezone as arrival_timezone,
                    -- 航空公司信息
                    al.airline_id,
                    al.iata_code as airline_iata,
                    al.icao_code as airline_icao,
                    al.name_zh as airline_name_zh,
                    al.name_en as airline_name_en,
                    al.callsign as airline_callsign,
                    al.country as airline_country,
                    al.logo_url as airline_logo_url,
                    al.is_active as airline_is_active,
                    al.is_domestic as airline_is_domestic,
                    al.fleet_size as airline_fleet_size,
                    al.website as airline_website,
                    -- 價格信息 (使用 LEFT JOIN 保留沒有價格的航班)
                    tp.ticket_price_id,
                    tp.price_economy,
                    tp.price_business,
                    tp.price_first,
                    tp.currency,
                    tp.last_updated as price_last_updated,
                    tp.booking_url,
                    tp.source as price_source
                FROM flights f
                JOIN airports a_dep ON f.departure_airport_id = a_dep.airport_id
                JOIN airports a_arr ON f.arrival_airport_id = a_arr.airport_id
                JOIN airlines al ON f.airline_id = al.airline_id
                LEFT JOIN ticket_prices tp ON f.flight_id = tp.flight_id
                WHERE f.flight_id = $1
                -- 如果一個航班有多條價格記錄，取最新的
                ORDER BY tp.last_updated DESC 
                LIMIT 1; 
                """
                
                params = [flight_id]
                logger.debug(f"Executing flight details SQL: {sql} with params: {params}")
                
                row = await conn.fetchrow(sql, *params)
                
                if not row:
                    logger.warning(f"未找到 flight_id 為 {flight_id} 的航班")
                    return None

                # 將 Row 對象轉換為字典
                flight_details = dict(row)
                logger.info(f"成功獲取 flight_id {flight_id} 的詳細信息")
                
                # 這裡可以進一步處理或格式化數據，例如將價格信息提取到嵌套字典中
                # formatted_details = {
                #     "flight_info": {k: v for k, v in flight_details.items() if not k.startswith(('departure_', 'arrival_', 'airline_', 'price_'))},
                #     "departure_airport": {k.replace('departure_', ''): v for k, v in flight_details.items() if k.startswith('departure_')},
                #     "arrival_airport": {k.replace('arrival_', ''): v for k, v in flight_details.items() if k.startswith('arrival_')},
                #     "airline": {k.replace('airline_', ''): v for k, v in flight_details.items() if k.startswith('airline_')},
                #     "ticket_price": {k.replace('price_', ''): v for k, v in flight_details.items() if k.startswith('price_') or k == 'currency' or k == 'ticket_price_id' or k == 'booking_url'}
                # }
                # return formatted_details
                
                # 或者直接返回扁平化的字典
                return flight_details

        except Exception as e:
            logger.error(f"獲取航班詳細信息 (ID: {flight_id}) 時出錯: {e}", exc_info=True)
            return None # 表示獲取失敗

    @staticmethod
    async def search_flights_from_taiwan(
        arrival_iata: str,
        date_str: str,
        airlines: Optional[List[str]] = None,
        price_min: Optional[float] = None, # Use float for price
        price_max: Optional[float] = None,
        class_type: str = "經濟",
        passengers: int = 1, # Added passengers, though not used in query yet
        max_results_total: int = 50, # Limit total results
        sort_by: str = "price"
    ) -> List[Dict[str, Any]]:
        """
        從所有台灣機場搜索飛往特定目的地的航班 (使用 asyncpg)

        Args:
            arrival_iata: 目的地機場的ID
            date_str: 日期 (YYYY-MM-DD)
            airlines: 航空公司ID列表，可選
            price_min: 最低價格，可選
            price_max: 最高價格，可選
            class_type: 艙位類型
            passengers: 乘客數量 (目前未直接用於 SQL 查詢)
            max_results_total: 總最大結果數
            sort_by: 排序方式 ("price", "duration", "departure_time")

        Returns:
            List[Dict[str, Any]]: 格式化後的航班列表
        """
        pool = None
        try:
            # 解析日期
            flight_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            start_of_day = datetime.combine(flight_date, datetime.min.time())
            end_of_day = datetime.combine(flight_date, datetime.max.time())
            logger.info(f"台灣出發查詢日期範圍: {start_of_day} 到 {end_of_day}")
        except ValueError:
            logger.error(f"台灣出發搜索日期格式錯誤: {date_str}")
            return []

        pool = await init_asyncpg_pool()
        async with pool.acquire() as conn:
            try:
                # 從 constants 導入台灣機場列表
                from ..scripts.constants import TAIWAN_AIRPORTS

                # 構建 SQL 查詢
                sql = """
                WITH RankedFlights AS (
                    SELECT 
                        f.flight_id, 
                        f.flight_number, 
                        f.scheduled_departure, 
                        f.scheduled_arrival, 
                        a_dep.airport_id as departure_airport_id, 
                        a_dep.name_zh as departure_name,
                        a_dep.city as departure_city,
                        a_dep.country as departure_country,
                        a_arr.airport_id as arrival_airport_id, 
                        a_arr.name_zh as arrival_name,
                        a_arr.city as arrival_city,
                        a_arr.country as arrival_country,
                        al.airline_id as airline_id, 
                        al.name_zh as airline_name_zh,
                        al.name_en as airline_name_en,
                        al.logo_path as airline_logo_url,
                        f.duration,
                        f.aircraft_type,
                        f.status,
                        tp.price_economy,
                        tp.price_business,
                        tp.price_first,
                        tp.currency,
                        tp.last_updated as price_last_updated,
                        -- 價格排序 (使用 COALESCE 處理 NULL)
                        CASE $1 -- $1 是 class_type
                            WHEN '商務' THEN COALESCE(tp.price_business, 99999999)
                            WHEN '頭等' THEN COALESCE(tp.price_first, 99999999)
                            ELSE COALESCE(tp.price_economy, 99999999) -- 默認經濟艙
                        END as sort_price,
                        -- 時間排序
                        EXTRACT(EPOCH FROM f.scheduled_departure) as sort_departure_time,
                        f.duration as sort_duration,
                        -- 分區排序，取最新價格
                        ROW_NUMBER() OVER (
                            PARTITION BY f.flight_number, f.scheduled_departure::date 
                            ORDER BY tp.last_updated DESC NULLS LAST
                        ) as rn
                    FROM flights f
                    JOIN airports a_dep ON f.departure_airport_id = a_dep.airport_id
                    JOIN airports a_arr ON f.arrival_airport_id = a_arr.airport_id
                    JOIN airlines al ON f.airline_id = al.airline_id
                    LEFT JOIN ticket_prices tp ON f.flight_id = tp.flight_id
                    WHERE a_dep.airport_id = ANY($2::text[]) -- $2 是 TAIWAN_AIRPORTS
                      AND a_arr.airport_id = $3 -- $3 是 arrival_iata
                      AND f.scheduled_departure >= $4 -- $4 是 start_of_day
                      AND f.scheduled_departure <= $5 -- $5 是 end_of_day
                      {airline_filter}
                      {price_filter}
                )
                SELECT * 
                FROM RankedFlights 
                WHERE rn = 1
                {sort_order}
                LIMIT $6; -- $6 是 max_results_total
                """

                params = [class_type, TAIWAN_AIRPORTS, arrival_iata, start_of_day, end_of_day]
                param_index = 5 # LIMIT 是第6個參數 ($6)

                # 航空公司過濾
                airline_filter_sql = ""
                if airlines:
                    airline_placeholders = ', '.join(f'${i}' for i in range(param_index + 1, param_index + 1 + len(airlines)))
                    airline_filter_sql = f" AND al.airline_id IN ({airline_placeholders})"
                    params.extend(airlines)
                    param_index += len(airlines)

                # 價格過濾 (根據 class_type)
                price_filter_sql = ""
                price_col_for_filter = "tp.price_economy" # 默認
                if class_type == "商務":
                    price_col_for_filter = "tp.price_business"
                elif class_type == "頭等":
                    price_col_for_filter = "tp.price_first"
                
                if price_min is not None:
                    price_filter_sql += f" AND {price_col_for_filter} >= ${param_index + 1}"
                    params.append(price_min)
                    param_index += 1
                if price_max is not None:
                    price_filter_sql += f" AND {price_col_for_filter} <= ${param_index + 1}"
                    params.append(price_max)
                    param_index += 1
                    
                # 排序條件
                sort_order_sql = ""
                if sort_by == "price":
                    sort_order_sql = " ORDER BY sort_price ASC, sort_departure_time ASC"
                elif sort_by == "duration":
                    sort_order_sql = " ORDER BY sort_duration ASC, sort_price ASC"
                elif sort_by == "departure_time":
                    sort_order_sql = " ORDER BY sort_departure_time ASC, sort_price ASC"
                else:
                    sort_order_sql = " ORDER BY sort_price ASC, sort_departure_time ASC" # 默認價格

                # 添加總結果數限制參數
                params.append(max_results_total)

                # 格式化最終 SQL
                final_sql = sql.format(
                    airline_filter=airline_filter_sql,
                    price_filter=price_filter_sql,
                    sort_order=sort_order_sql
                )
                
                logger.debug(f"Executing search from Taiwan SQL: {final_sql} with params: {params}")
                
                rows = await conn.fetch(final_sql, *params)
                logger.info(f"從台灣機場查詢到 {len(rows)} 條飛往 {arrival_iata} 的航班記錄")
                
                # 格式化結果
                formatted_flights = await SearchService._format_flights([dict(row) for row in rows], class_type)
                return formatted_flights

            except Exception as e:
                logger.error(f"從台灣搜索航班時出錯: {e}\nSQL: {final_sql}\nParams: {params}", exc_info=True)
                return []
                
    @staticmethod
    async def get_popular_flights(
        max_results: int = 20,
        cabin_class: str = "經濟" # 假設需要指定艙等以格式化價格
    ) -> List[Dict[str, Any]]:
        """
        獲取預定義的熱門航線的航班信息 (使用 asyncpg)

        Args:
            max_results: 每個熱門航線顯示的最大航班數
            cabin_class: 用於格式化價格的艙位

        Returns:
            List[Dict[str, Any]]: 熱門航班列表，包含航線信息和航班詳情
        """
        pool = None
        all_popular_flights_details = []
        # 使用常量中的航線元組
        popular_routes = FRONTEND_POPULAR_ROUTES_TUPLES 
        
        today_str = datetime.now().strftime("%Y-%m-%d")

        pool = await init_asyncpg_pool()
        async with pool.acquire() as conn:
            try:
                for dep_iata, arr_iata in popular_routes:
                    logger.info(f"正在查詢熱門航線: {dep_iata} -> {arr_iata} (日期: {today_str})")
                    # 調用 _query_flights 獲取當天該航線的航班數據
                    # 注意: _query_flights 需要 conn
                    route_flights_raw = await SearchService._query_flights(
                        conn,
                        dep_iata, 
                        arr_iata, 
                        today_str, 
                        max_results=max_results, # 限制每個航線的結果數
                        sort_by="price" # 按價格排序
                        # 其他過濾條件可以按需添加
                    )
                    
                    # 格式化查詢到的航班
                    formatted_route_flights = await SearchService._format_flights(route_flights_raw, cabin_class)
                    
                    if formatted_route_flights:
                         # 添加航線信息到結果中
                        all_popular_flights_details.append({
                            "departure_iata": dep_iata,
                            "arrival_iata": arr_iata,
                            "flights": formatted_route_flights 
                        })
                        logger.info(f"找到 {len(formatted_route_flights)} 個 {dep_iata} -> {arr_iata} 的航班")
                    else:
                         logger.info(f"未找到 {dep_iata} -> {arr_iata} 的今日航班")

                logger.info(f"共獲取到 {len(all_popular_flights_details)} 個熱門航線的航班數據")
                return all_popular_flights_details

            except Exception as e:
                logger.error(f"獲取熱門航班時出錯: {e}", exc_info=True)
                return [] # 返回空列表表示錯誤

    @staticmethod
    async def get_flights_from_taiwan(
        arrival_iata: str,
        date_str: str,
        max_results: int = 50,
        cabin_class: str = "經濟" # 假設需要指定艙等以格式化價格
    ) -> List[Dict[str, Any]]:
        """
        (此方法與 search_flights_from_taiwan 功能重疊，但保留以防直接調用)
        從所有台灣機場獲取飛往特定目的地的航班 (使用 asyncpg)

        Args:
            arrival_iata: 目的地機場IATA代碼
            date_str: 日期 (YYYY-MM-DD)
            max_results: 最大結果數
            cabin_class: 艙位

        Returns:
            List[Dict[str, Any]]: 格式化後的航班列表
        """
        logger.warning("調用了 get_flights_from_taiwan，建議使用 search_flights_from_taiwan 以獲得更多過濾選項。")
        # 直接調用更通用的搜索函數，傳遞必要參數
        return await SearchService.search_flights_from_taiwan(
            arrival_iata=arrival_iata,
            date_str=date_str,
            class_type=cabin_class,
            max_results_total=max_results,
            sort_by="price" # 默認按價格排序
        ) 