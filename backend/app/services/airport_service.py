# -*- coding: utf-8 -*-
"""
機場服務模組
提供機場相關的業務邏輯處理
"""
import logging
import uuid
from typing import List, Dict, Any, Optional
from flask import current_app
from datetime import datetime, timedelta

from ..database.db import init_asyncpg_pool
from app.models.airport import Airport, AirportDestination
from ..models.base import db

logger = logging.getLogger(__name__)

class AirportService:
    """機場服務類，提供機場相關的業務邏輯處理"""
    
    @staticmethod
    async def _get_taiwan_airport_activity_scores_async(conn, days_ahead: int = 7) -> Dict[str, int]:
        """
        異步獲取台灣機場活躍度分數（基於未來航班數量）
        
        Args:
            conn: 資料庫連接
            days_ahead (int): 查詢未來幾天的航班，預設為 7 天
            
        Returns:
            Dict[str, int]: 機場代碼到活躍度分數的映射
        """
        today = datetime.utcnow().date()
        future_start_date = today 
        future_end_date = today + timedelta(days=days_ahead)

        logger.info(f"[_get_taiwan_airport_activity_scores_async] Calculating activity for dates: {future_start_date} (inclusive) to {future_end_date} (exclusive)")

        try:
            sql = """
            SELECT
                f.departure_airport_id,
                    COUNT(f.flight_id) as flight_count
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
            
            rows = await conn.fetch(sql, future_start_date, future_end_date)
            activity_scores = {}
            
            if rows:
                max_flights = max(row['flight_count'] for row in rows)
                for row in rows:
                    airport_id = row['departure_airport_id']
                    flight_count = row['flight_count']
                    score = int((flight_count / max_flights) * 100) if max_flights > 0 else 0
                    activity_scores[airport_id] = score
                    
            logger.info(f"計算了 {len(activity_scores)} 個台灣機場的活躍度分數")
            return activity_scores
            
        except Exception as e:
            logger.error(f"獲取台灣機場活躍度分數時出錯: {e}", exc_info=True)
            return {}

    @staticmethod
    async def get_all_airports_with_activity(days_ahead: int = 7) -> List[Dict[str, Any]]:
        """
        獲取所有機場列表，並為台灣機場附加近期活躍度分數
        """
        pool = await init_asyncpg_pool()
        if not pool:
            logger.error("無法初始化資料庫連接池")
            return []
            
        conn = None
        try:
            conn = await pool.acquire()
            
            # 1. 獲取所有機場的基本信息
            all_airports_sql = """
            SELECT 
                airport_id,
                name_zh,
                name_en,
                city,
                country,
                timezone
            FROM airports
            ORDER BY country, city, name_zh
            """
            
            all_airports_rows = await conn.fetch(all_airports_sql)
            all_airports_list = [dict(row) for row in all_airports_rows]
            
            if not all_airports_list:
                logger.warning("未獲取到任何機場數據")
                return []

            # 2. 獲取台灣機場的活躍度分數
            taiwan_activity_scores = await AirportService._get_taiwan_airport_activity_scores_async(conn, days_ahead)

            # 3. 將活躍度分數合併到台灣機場數據中
            for airport_data in all_airports_list:
                if airport_data.get('country') == 'Taiwan':
                    airport_data['activity_score'] = taiwan_activity_scores.get(airport_data['airport_id'], 0)
                else:
                    airport_data['activity_score'] = 0 
            
            logger.info(f"成功獲取所有機場列表，並已附加台灣機場活躍度。共 {len(all_airports_list)} 個機場")
            return all_airports_list
            
        except Exception as e:
            logger.error(f"獲取所有機場並附加活躍度時出錯: {e}", exc_info=True)
            return []
        finally:
            if conn and pool:
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
            ORDER BY 
                CASE airport_id
                    WHEN 'TPE' THEN 1
                    WHEN 'TSA' THEN 2
                    WHEN 'KHH' THEN 3
                    WHEN 'RMQ' THEN 4
                    WHEN 'TXG' THEN 5
                    WHEN 'TNN' THEN 6
                    WHEN 'CYI' THEN 7
                    WHEN 'HUN' THEN 8
                    WHEN 'TTT' THEN 9
                    WHEN 'KNH' THEN 10
                    WHEN 'MZG' THEN 11
                    WHEN 'LZN' THEN 12
                    WHEN 'GNI' THEN 13
                    WHEN 'WOT' THEN 14
                    WHEN 'PIF' THEN 15
                    WHEN 'MFK' THEN 16
                    WHEN 'CMJ' THEN 17
                    WHEN 'TEN' THEN 18
                    WHEN 'KYD' THEN 19
                    WHEN 'NKM' THEN 20
                    WHEN 'FUN' THEN 21
                    WHEN 'TCN' THEN 22
                    WHEN 'YMI' THEN 23
                    WHEN 'LGK' THEN 24
                    WHEN 'WON' THEN 25
                    WHEN 'SWO' THEN 26
                    WHEN 'QPN' THEN 27
                    WHEN 'LYU' THEN 28
                    WHEN 'NNK' THEN 29
                    WHEN 'VRE' THEN 30
                    ELSE 999
                END
            """
            
            rows = await conn.fetch(sql)
            airports = [dict(row) for row in rows]
            logger.info(f"成功獲取台灣機場列表, 共 {len(airports)} 個機場")
            return airports
            
        # 使用通用資料庫操作模式
        pool = await init_asyncpg_pool()
        if not pool:
            logger.error("無法初始化資料庫連接池")
            return []
            
        conn = None
        try:
            conn = await pool.acquire()
            return await fetch_airports(conn)
        except Exception as e:
            logger.error(f"獲取台灣機場列表時出錯: {e}", exc_info=True)
            return []
        finally:
            if conn and pool:
                await pool.release(conn)

    @staticmethod
    async def get_available_destinations(
        departure_airport_param: str,
        date: Optional[str] = None, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        獲取從指定台灣機場出發可到達的目的地機場列表
        
        Args:
            departure_airport_param (str): 出發機場的 ID (IATA 代碼)
            date (Optional[str]): 過濾日期 (YYYY-MM-DD 格式)，若提供則返回該日期附近有航班的目的地
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
                # 如果提供了日期參數，查詢該日期前後3天的航班（更寬鬆的查詢）
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
                    AND f.scheduled_departure::date BETWEEN ($3::date - INTERVAL '3 days') AND ($3::date + INTERVAL '3 days')
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
                # 不過濾日期，返回所有目的地（只查詢未來航班）
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
                    AND f.scheduled_departure >= CURRENT_TIMESTAMP
                GROUP BY 
                    arr.airport_id, arr.name_zh, arr.city, arr.country
                ORDER BY 
                    arr.city
                LIMIT $2
                """
            
            # 執行查詢
            rows = await conn.fetch(sql, *params)
            destinations = [dict(row) for row in rows]
            
            logger.info(f"從機場ID {dep_code_upper} 查詢到的目的地數量: {len(destinations)} {' (日期範圍: ' + date + ' ±3天)' if date else ' (所有未來航班)'}")
            return destinations
        
        # 使用通用資料庫操作模式
        pool = await init_asyncpg_pool()
        if not pool:
            return []
        async with pool.acquire() as conn:
            return await fetch_destinations(conn, departure_airport_param)
    
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
        if not pool:
            logger.error("無法初始化資料庫連接池")
            return None
            
        conn = None
        try:
            conn = await pool.acquire()
            return await fetch_airport(conn)
        except Exception as e:
            logger.error(f"獲取機場ID {airport_id} 的詳細信息時出錯: {e}", exc_info=True)
            return None
        finally:
            if conn and pool:
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
                name_zh ILIKE $1 OR
                name_en ILIKE $1 OR
                city ILIKE $1 OR
                country ILIKE $1 OR
                airport_id ILIKE $1
            ORDER BY 
                CASE 
                    WHEN name_zh ILIKE $1 THEN 1
                    WHEN name_en ILIKE $1 THEN 2
                    WHEN airport_id ILIKE $1 THEN 3
                    ELSE 4
                END,
                name_zh
            LIMIT $2
            """
            
            rows = await conn.fetch(sql, search_term, limit)
            return [dict(row) for row in rows]
            
        # 使用通用資料庫操作模式
        pool = await init_asyncpg_pool()
        if not pool:
            logger.error("無法初始化資料庫連接池")
            return []
            
        conn = None
        try:
            conn = await pool.acquire()
            return await perform_search(conn)
        except Exception as e:
            logger.error(f"搜索機場時出錯: {e}", exc_info=True)
            return []
        finally:
            if conn and pool:
                await pool.release(conn)

    @staticmethod
    async def get_available_departure_airports(limit: int = 200) -> List[Dict[str, Any]]:
        """
        獲取所有有有效未來出發航班的機場列表
        結果按機場的航班數量降序排序，然後按城市、機場名稱排序

        Args:
            limit (int, optional): 返回結果的最大數量。預設為 200

        Returns:
            List[Dict[str, Any]]: 機場列表，每個機場包含代碼、名稱、城市、國家和未來航班數量
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
                logger.info(f"查詢到 {len(rows)} 個有未來出發航班的機場")
                return [dict(row) for row in rows]
            except Exception as e_query:
                logger.error(f"查詢有未來出發航班的機場時出錯: {e_query}", exc_info=True)
                return []

        pool = await init_asyncpg_pool()
        if not pool:
            logger.error("無法初始化資料庫連接池")
            return []
            
        conn = None
        try:
            conn = await pool.acquire()
            return await fetch_airports_with_future_flights(conn)
        except Exception as e_service:
            logger.error(f"在 get_available_departure_airports 服務中發生錯誤: {e_service}", exc_info=True)
            return []
        finally:
            if conn and pool:
                await pool.release(conn)

    @staticmethod
    async def bulk_save_airports(airports_data: List[Dict[str, Any]]) -> int:
        """
        批量儲存或更新機場數據
        
        Args:
            airports_data (List[Dict[str, Any]]): 機場數據列表
            
        Returns:
            int: 成功儲存或更新的記錄數量
        """
        if not airports_data:
            return 0

        async def upsert_airports(conn):
            records_to_insert = [
                (
                    d.get("iata_code", ''),
                    d.get("name_zh", ''),
                    d.get("name_en", ''),
                    d.get("city", ''),
                    d.get("country", '')
                ) for d in airports_data
            ]
            
            table_name = 'airports'
            columns = ['airport_id', 'name_zh', 'name_en', 'city', 'country']

            try:
                async with conn.transaction():
                    # 創建臨時表
                    temp_table_name = f"temp_airports_{uuid.uuid4().hex}"
                    await conn.execute(f"""
                        CREATE TEMP TABLE {temp_table_name} (
                            airport_id VARCHAR(3) PRIMARY KEY,
                            name_zh VARCHAR(255),
                            name_en VARCHAR(255),
                            city VARCHAR(255),
                            country VARCHAR(255)
                        ) ON COMMIT DROP;
                    """)

                    # 複製數據到臨時表
                    await conn.copy_records_to_table(
                        table_name=temp_table_name,
                        records=records_to_insert,
                        columns=columns
                    )

                    # Upsert
                    upsert_sql = f"""
                    INSERT INTO {table_name} (airport_id, name_zh, name_en, city, country)
                    SELECT airport_id, name_zh, name_en, city, country FROM {temp_table_name}
                    ON CONFLICT (airport_id) DO UPDATE SET
                        name_zh = EXCLUDED.name_zh,
                        name_en = EXCLUDED.name_en,
                        city = EXCLUDED.city,
                        country = EXCLUDED.country;
                    """
                    await conn.execute(upsert_sql)
                    
                    return len(records_to_insert)

            except Exception as e:
                logger.error(f"批量儲存機場時發生數據庫錯誤: {e}", exc_info=True)
                raise

        pool = await init_asyncpg_pool()
        if not pool:
            logger.error("無法初始化資料庫連接池")
            return 0
            
        conn = None
        try:
            conn = await pool.acquire()
            return await upsert_airports(conn)
        except Exception:
            return 0
        finally:
            if conn and pool:
                await pool.release(conn)

    @staticmethod
    async def get_airport_by_iata(iata_code: str) -> Optional[Dict[str, Any]]:
        """
        根據 IATA code 獲取機場信息
        
        Args:
            iata_code (str): 機場的 IATA code
            
        Returns:
            Optional[Dict[str, Any]]: 機場詳情，如果不存在則返回None
        """
        async def fetch_airport(conn):
            # airport_id 在我們的 schema 中就是 IATA code
            sql = "SELECT * FROM airports WHERE airport_id = $1"
            row = await conn.fetchrow(sql, iata_code)
            return dict(row) if row else None

        pool = await init_asyncpg_pool()
        if not pool:
            logger.error("無法初始化資料庫連接池")
            return None
            
        conn = None
        try:
            conn = await pool.acquire()
            return await fetch_airport(conn)
        except Exception as e:
            logger.error(f"根據 IATA code {iata_code} 獲取機場時出錯: {e}", exc_info=True)
            return None
        finally:
            if conn and pool:
                await pool.release(conn)

    @staticmethod
    async def get_airports_by_codes(airport_codes: List[str]) -> List[Dict[str, Any]]:
        """
        批量獲取機場資訊，用於前端中文名稱轉換
        
        Args:
            airport_codes (List[str]): 機場代碼列表
            
        Returns:
            List[Dict[str, Any]]: 機場資訊列表
        """
        if not airport_codes:
            return []
            
        async def fetch_airports_batch(conn):
            # 構建 IN 條件的佔位符
            placeholders = ','.join(f'${i+1}' for i in range(len(airport_codes)))
            
            sql = f"""
            SELECT 
                airport_id as code,
                name_zh,
                name_en,
                city,
                country,
                timezone
            FROM airports
            WHERE airport_id IN ({placeholders})
            """
            
            rows = await conn.fetch(sql, *airport_codes)
            return [dict(row) for row in rows]
            
        # 使用通用資料庫操作模式
        pool = await init_asyncpg_pool()
        if not pool:
            logger.error("無法初始化資料庫連接池")
            return []
            
        conn = None
        try:
            conn = await pool.acquire()
            return await fetch_airports_batch(conn)
        except Exception as e:
            logger.error(f"批量獲取機場資訊時出錯: {e}", exc_info=True)
            return []
        finally:
            if conn and pool:
                await pool.release(conn) 

    async def get_destinations_cached(self, departure_airport_id: str, fallback_to_amadeus: bool = True) -> List[Dict[str, Any]]:
        """
        從本地緩存獲取機場目的地，如果緩存為空且允許回退，則調用 Amadeus API
        
        Args:
            departure_airport_id: 出發機場 IATA 代碼
            fallback_to_amadeus: 是否在本地無數據時回退到 Amadeus API
            
        Returns:
            List[Dict]: 目的地機場列表
        """
        try:
            # 首先嘗試從本地緩存獲取
            cached_destinations = AirportDestination.get_destinations_for_departure(
                departure_airport_id, active_only=True
            )
            
            if cached_destinations:
                # 構建返回格式，包含目的地機場的詳細信息
                result = []
                for route in cached_destinations:
                    dest_airport = route.destination_airport
                    result.append({
                        'airport_id': dest_airport.airport_id,
                        'name': dest_airport.name_en,
                        'name_zh': dest_airport.name_zh,
                        'city': dest_airport.city,
                        'country': dest_airport.country,
                        'flight_count_30days': route.flight_count_30days,
                        'last_synced_at': route.last_synced_at.isoformat() if route.last_synced_at else None
                    })
                
                logger.info(f"Retrieved {len(result)} cached destinations for {departure_airport_id}")
                return result
            
            # 如果本地沒有數據且允許回退到 Amadeus
            if fallback_to_amadeus:
                logger.info(f"No cached destinations found for {departure_airport_id}, falling back to Amadeus API")
                # 使用 AmadeusService 直接獲取
                from ..services.amadeus_service import AmadeusService
                amadeus_service = AmadeusService()
                amadeus_response = await amadeus_service.get_airport_destinations(departure_airport_id)
                await amadeus_service.close_session()
                
                if amadeus_response and 'data' in amadeus_response:
                    return amadeus_response['data']
                else:
                    return []
            else:
                logger.info(f"No cached destinations found for {departure_airport_id}, not using Amadeus fallback")
                return []
                
        except Exception as e:
            logger.error(f"Error getting cached destinations for {departure_airport_id}: {str(e)}")
            
            # 如果出錯且允許回退，嘗試使用 Amadeus
            if fallback_to_amadeus:
                try:
                    from ..services.amadeus_service import AmadeusService
                    amadeus_service = AmadeusService()
                    amadeus_response = await amadeus_service.get_airport_destinations(departure_airport_id)
                    await amadeus_service.close_session()
                    
                    if amadeus_response and 'data' in amadeus_response:
                        return amadeus_response['data']
                    else:
                        return []
                except Exception as amadeus_e:
                    logger.error(f"Amadeus fallback also failed: {str(amadeus_e)}")
            
            return []
    
    def get_popular_destinations_cached(self, departure_airport_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        從本地緩存獲取熱門目的地（按航班數量排序）
        
        Args:
            departure_airport_id: 出發機場 IATA 代碼
            limit: 返回數量限制
            
        Returns:
            List[Dict]: 熱門目的地列表
        """
        try:
            popular_routes = AirportDestination.get_popular_destinations(departure_airport_id, limit)
            
            result = []
            for route in popular_routes:
                dest_airport = route.destination_airport
                result.append({
                    'airport_id': dest_airport.airport_id,
                    'name': dest_airport.name_en,
                    'name_zh': dest_airport.name_zh,
                    'city': dest_airport.city,
                    'country': dest_airport.country,
                    'flight_count_30days': route.flight_count_30days,
                    'flight_count_7days': route.flight_count_7days,
                    'popularity_rank': len(result) + 1
                })
            
            logger.info(f"Retrieved {len(result)} popular destinations for {departure_airport_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error getting popular cached destinations for {departure_airport_id}: {str(e)}")
            return []

    @staticmethod
    async def sync_destination_cache_for_airport(departure_airport_id: str) -> bool:
        """
        為指定機場同步目的地緩存
        
        Args:
            departure_airport_id: 出發機場 IATA 代碼
            
        Returns:
            bool: 同步是否成功
        """
        from flask import current_app
        
        try:
            # 調用 AmadeusService 獲取最新目的地
            from ..services.amadeus_service import AmadeusService
            amadeus_service = AmadeusService()
            
            destinations_response = await amadeus_service.get_airport_destinations(departure_airport_id)
            
            if not destinations_response or 'data' not in destinations_response:
                logger.warning(f"No destinations returned for {departure_airport_id}")
                return False
            
            destinations = destinations_response['data']
            synced_count = 0
            
            # 在 Flask app context 中操作資料庫
            with current_app.app_context():
                for dest_data in destinations:
                    try:
                        destination_airport_id = dest_data.get('iataCode')
                        if not destination_airport_id:
                            continue
                        
                        # 確保目的地機場存在
                        dest_airport = Airport.query.filter_by(airport_id=destination_airport_id).first()
                        if not dest_airport:
                            # 可以選擇創建基本記錄或跳過
                            continue
                        
                        # 創建或更新 AirportDestination 記錄
                        route = AirportDestination.query.filter_by(
                            departure_airport_id=departure_airport_id,
                            destination_airport_id=destination_airport_id
                        ).first()
                        
                        if route:
                            route.updated_at = datetime.utcnow()
                            route.last_synced_at = datetime.utcnow()
                            route.is_active = True
                        else:
                            route = AirportDestination(
                                departure_airport_id=departure_airport_id,
                                destination_airport_id=destination_airport_id,
                                is_active=True,
                                last_synced_at=datetime.utcnow()
                            )
                            db.session.add(route)
                        
                        synced_count += 1
                        
                    except Exception as e:
                        logger.error(f"Error processing destination {dest_data}: {str(e)}")
                        continue
                
                db.session.commit()
                logger.info(f"Successfully synced {synced_count} destinations for {departure_airport_id}")
            
            # 關閉 Amadeus session
            await amadeus_service.close_session()
            
            return True
            
        except Exception as e:
            logger.error(f"Error syncing destination cache for {departure_airport_id}: {str(e)}")
            try:
                db.session.rollback()
            except:
                pass
            return False

# 創建服務實例以供其他模塊導入
airport_service = AirportService()