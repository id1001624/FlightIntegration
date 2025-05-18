#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
機場服務模組 - 處理機場信息相關的業務邏輯
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

import asyncpg
from ..database.db import init_asyncpg_pool
from .db_utils import execute_db_operation, execute_query

logger = logging.getLogger(__name__)

class AirportService:
    """機場服務 - 處理機場數據相關操作"""
    
    @staticmethod
    async def _get_taiwan_airport_activity_scores_async(conn, days_ahead: int = 7) -> Dict[str, int]:
        """
        (私有) 計算台灣各機場未來指定天數內的出發航班活躍度分數。
        排除 is_test_data = True 的航班。
        """
        today = datetime.utcnow().date()
        # 確保 future_start_date 和 future_end_date 的計算與 SQL 查詢邏輯一致
        # SQL 是 >= $1 AND < $2，所以 end_date 不需要 +1
        future_start_date = today 
        future_end_date = today + timedelta(days=days_ahead) # 結束日期是不包含的上限

        logger.info(f"[_get_taiwan_airport_activity_scores_async] Calculating activity for dates: {future_start_date} (inclusive) to {future_end_date} (exclusive)")

        sql = """
        SELECT
            f.departure_airport_id,
            COUNT(f.flight_id) AS flight_count
        FROM
            flights f
        JOIN
            airports a ON f.departure_airport_id = a.airport_id
        WHERE
            a.country = 'Taiwan'
            AND f.scheduled_departure >= $1
            AND f.scheduled_departure < $2 
            -- AND f.is_test_data = FALSE  -- 確保這行仍然是註解狀態
        GROUP BY
            f.departure_airport_id;
        """
        try:
            logger.debug(f"[_get_taiwan_airport_activity_scores_async] Executing SQL with params: $1={future_start_date}, $2={future_end_date}")
            
            rows = await conn.fetch(sql, future_start_date, future_end_date)
            
            logger.info(f"[_get_taiwan_airport_activity_scores_async] Raw rows from DB: {rows}")
            
            activity_scores = {row['departure_airport_id']: row['flight_count'] for row in rows}
            
            logger.info(f"[_get_taiwan_airport_activity_scores_async] Calculated activity_scores: {activity_scores}")
            
            return activity_scores
        except Exception as e:
            logger.error(f"Error calculating Taiwan airport activity scores: {e}", exc_info=True)
            return {}

    @staticmethod
    async def get_all_airports_with_activity(days_ahead: int = 7) -> List[Dict[str, Any]]:
        """
        獲取所有機場列表，並為台灣機場附加近期活躍度分數。
        """
        pool = await init_asyncpg_pool()
        conn = await pool.acquire()
        try:
            # 1. 獲取所有機場的基本信息
            all_airports_sql = """
            SELECT 
                airport_id,
                name_zh,
                name_en,
                city,
                city_en,
                country,
                timezone,
                contact_info,
                website_url
            FROM airports
            ORDER BY country, city, name_zh;
            """
            airport_rows = await conn.fetch(all_airports_sql)
            all_airports_list = [dict(row) for row in airport_rows]
            
            if not all_airports_list:
                logger.warning("未獲取到任何機場數據。")
                return []

            # 2. 獲取台灣機場的活躍度分數
            taiwan_activity_scores = await AirportService._get_taiwan_airport_activity_scores_async(conn, days_ahead)

            # 3. 將活躍度分數合併到台灣機場數據中
            for airport_data in all_airports_list:
                if airport_data.get('country') == 'Taiwan':
                    airport_data['activity_score'] = taiwan_activity_scores.get(airport_data['airport_id'], 0)
                else:
                    # 非台灣機場可以選擇不加此欄位或設為None/0
                    airport_data['activity_score'] = 0 
            
            logger.info(f"成功獲取所有機場列表，並已附加台灣機場活躍度。共 {len(all_airports_list)} 個機場。")
            return all_airports_list
            
        except Exception as e:
            logger.error(f"獲取所有機場並附加活躍度時出錯: {e}", exc_info=True)
            return []
        finally:
            if conn:
                await pool.release(conn)

    @staticmethod
    async def get_taiwan_airports() -> List[Dict[str, Any]]:
        """
        獲取台灣所有機場列表
        
        Returns:
            List[Dict[str, Any]]: 台灣機場列表
        """
        async def fetch_airports(conn):
            sql = """
            SELECT 
                airport_id,
                name_zh,
                city,
                country
            FROM airports
            WHERE country = 'Taiwan'
            ORDER BY city, name_zh;
            """
            
            rows = await conn.fetch(sql)
            logger.debug(f"[AirportService.get_taiwan_airports] 原始查詢結果 (rows): {rows}")
            airports = [dict(row) for row in rows]
            logger.info(f"成功獲取台灣機場列表, 共 {len(airports)} 個機場.")
            return airports
            
        # 使用通用資料庫操作模式
        pool = await init_asyncpg_pool()
        conn = await pool.acquire()
        try:
            return await fetch_airports(conn)
        except Exception as e:
            logger.error(f"獲取台灣機場列表時出錯: {e}", exc_info=True)
            return []
        finally:
            if conn:
                await pool.release(conn)

    @staticmethod
    async def get_available_destinations(
        departure_airport_param: str,
        date: str = None, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        獲取從指定台灣機場出發可到達的目的地機場列表
        
        Args:
            departure_airport_param (str): 出發機場的 ID (IATA 代碼)
            date (str, optional): 過濾日期 (YYYY-MM-DD 格式)，若提供則只返回該日期有航班的目的地
            limit (int, optional): 返回結果的最大數量，預設為 100
            
        Returns:
            List[Dict[str, Any]]: 目的地機場資訊列表，包含代碼、名稱、城市、國家、航班數量和最低價格
        """
        
        async def fetch_destinations(conn, dep_airport_code_internal: str):
            # 轉換參數
            dep_code_upper = dep_airport_code_internal.upper()
            
            # 構建 SQL 查詢，根據是否有日期參數調整
            params = [dep_code_upper, limit]
            
            if date:
                # 如果提供了日期參數，只返回該日期有航班的目的地
                sql = """
                SELECT DISTINCT 
                    arr.airport_id,
                    arr.name_zh,
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
                    AND DATE(f.scheduled_departure) = $3
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
                    logger.error(f"無效的日期格式: {date}")
                    return []
            else:
                # 不過濾日期，返回所有目的地
                sql = """
                SELECT DISTINCT
                    arr.airport_id,
                    arr.name_zh,
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
            
            logger.info(f"從機場ID {dep_code_upper} 查詢到的目的地數量: {len(destinations)} {' (過濾日期: ' + date + ')' if date else ''}")
            return destinations
        
        # 使用通用資料庫操作模式
        pool = await init_asyncpg_pool()
        conn = await pool.acquire()
        try:
            return await fetch_destinations(conn, departure_airport_param)
        except Exception as e:
            logger.error(f"獲取從機場ID {departure_airport_param} 出發的目的地時出錯: {e}", exc_info=True)
            return []
        finally:
            if conn:
                await pool.release(conn)
    
    @staticmethod
    async def get_airport_by_id(airport_id: str) -> Optional[Dict[str, Any]]:
        """
        根據機場ID獲取機場詳情
        
        Args:
            airport_id (str): 機場ID
            
        Returns:
            Optional[Dict[str, Any]]: 機場詳情，如果不存在則返回None
        """
        async def fetch_airport(conn):
            sql = """
            SELECT 
                airport_id,
                name_zh,
                name_en,
                city,
                country,
                timezone
            FROM airports
            WHERE airport_id = $1
            """
            
            row = await conn.fetchrow(sql, airport_id)
            if row:
                return dict(row)
            return None
            
        # 使用通用資料庫操作模式
        pool = await init_asyncpg_pool()
        conn = await pool.acquire()
        try:
            return await fetch_airport(conn)
        except Exception as e:
            logger.error(f"獲取機場ID {airport_id} 的詳細信息時出錯: {e}", exc_info=True)
            return None
        finally:
            if conn:
                await pool.release(conn)
                
    @staticmethod
    async def search_airports(
        keyword: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        搜索機場 (支持中文名稱、英文名稱、城市、國家)
        
        Args:
            keyword (str): 搜索關鍵詞
            limit (int, optional): 返回結果的最大數量，預設為 10
            
        Returns:
            List[Dict[str, Any]]: 機場列表
        """
        async def perform_search(conn):
            # 構建模糊搜索條件
            search_term = f"%{keyword}%"
            
            sql = """
            SELECT 
                airport_id,
                name_zh,
                name_en,
                city,
                country
            FROM airports
            WHERE 
                airport_id ILIKE $1 OR
                name_zh ILIKE $1 OR
                name_en ILIKE $1 OR
                city ILIKE $1 OR
                country ILIKE $1
            ORDER BY 
                CASE 
                    WHEN airport_id = $2 THEN 1
                    WHEN name_zh = $2 THEN 2
                    WHEN name_en = $2 THEN 3
                    WHEN city = $2 THEN 4
                    ELSE 5
                END
            LIMIT $3
            """
            
            rows = await conn.fetch(sql, search_term, keyword, limit)
            return [dict(row) for row in rows]
            
        # 使用通用資料庫操作模式
        pool = await init_asyncpg_pool()
        conn = await pool.acquire()
        try:
            return await perform_search(conn)
        except Exception as e:
            logger.error(f"搜索機場時出錯: {e}", exc_info=True)
            return []
        finally:
            if conn:
                await pool.release(conn)

    @staticmethod
    async def get_available_departure_airports(limit: int = 200) -> List[Dict[str, Any]]:
        """
        獲取所有有有效未來出發航班的機場列表。
        結果按機場的航班數量降序排序，然後按城市、機場名稱排序。

        Args:
            limit (int, optional): 返回結果的最大數量。預設為 200。

        Returns:
            List[Dict[str, Any]]: 機場列表，每個機場包含代碼、名稱、城市、國家和未來航班數量。
        """
        async def fetch_airports_with_future_flights(conn):
            sql = """
            SELECT
                a.airport_id,
                a.name_zh,
                a.city,
                a.country,
                COUNT(f.flight_id) as future_flight_count
            FROM
                airports a
            JOIN
                flights f ON a.airport_id = f.departure_airport_id
            WHERE
                f.scheduled_departure >= CURRENT_DATE -- 只考慮今天及未來的航班
            GROUP BY
                a.airport_id, a.name_zh, a.city, a.country
            HAVING
                COUNT(f.flight_id) > 0 -- 確保至少有一個未來航班
            ORDER BY
                future_flight_count DESC, a.city ASC, a.name_zh ASC
            LIMIT $1;
            """
            try:
                rows = await conn.fetch(sql, limit)
                logger.info(f"查詢到 {len(rows)} 個有未來出發航班的機場。")
                return [dict(row) for row in rows]
            except Exception as e_query:
                logger.error(f"查詢有未來出發航班的機場時出錯: {e_query}", exc_info=True)
                return []

        pool = await init_asyncpg_pool()
        conn = await pool.acquire()
        try:
            return await fetch_airports_with_future_flights(conn)
        except Exception as e_service:
            logger.error(f"在 get_available_departure_airports 服務中發生錯誤: {e_service}", exc_info=True)
            return []
        finally:
            if conn:
                await pool.release(conn) 