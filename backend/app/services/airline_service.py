#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
航空公司服務模組 - 處理航空公司信息相關的業務邏輯
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

import asyncpg
from ..database.db import init_asyncpg_pool
from .db_utils import execute_db_operation

logger = logging.getLogger(__name__)

class AirlineService:
    """航空公司服務 - 處理航空公司數據相關操作"""
    
    @staticmethod
    async def get_available_airlines() -> List[Dict[str, Any]]:
        """
        獲取資料庫中所有可用航空公司的基本信息
        
        Returns:
            List[Dict[str, Any]]: 航空公司列表
        """
        async def fetch_airlines(conn):
            sql = """
            SELECT 
                airline_id, 
                name_zh, 
                name_en, 
                logo_path,
                is_domestic
            FROM airlines 
            ORDER BY name_zh
            """
            rows = await conn.fetch(sql)
            logger.info(f"獲取到 {len(rows)} 家航空公司")
            # 直接返回字典列表
            return [dict(row) for row in rows]
            
        # 使用通用資料庫操作模式
        pool = await init_asyncpg_pool()
        conn = await pool.acquire()
        try:
            return await fetch_airlines(conn)
        except Exception as e:
            logger.error(f"獲取航空公司列表時出錯: {e}", exc_info=True)
            return []
        finally:
            if conn:
                await pool.release(conn)
                
    @staticmethod
    async def get_airline_by_id(airline_id: str) -> Optional[Dict[str, Any]]:
        """
        根據航空公司ID獲取詳細信息
        
        Args:
            airline_id (str): 航空公司ID
            
        Returns:
            Optional[Dict[str, Any]]: 航空公司詳情，如果不存在則返回None
        """
        async def fetch_airline(conn):
            sql = """
            SELECT 
                airline_id,
                name_zh,
                name_en,
                logo_path,
                is_domestic,
                alliance,
                country
            FROM airlines
            WHERE airline_id = $1
            """
            
            row = await conn.fetchrow(sql, airline_id)
            if row:
                return dict(row)
            return None
            
        # 使用通用資料庫操作模式
        pool = await init_asyncpg_pool()
        conn = await pool.acquire()
        try:
            return await fetch_airline(conn)
        except Exception as e:
            logger.error(f"獲取航空公司ID {airline_id} 的詳細信息時出錯: {e}", exc_info=True)
            return None
        finally:
            if conn:
                await pool.release(conn)
                
    @staticmethod
    async def search_airlines(
        keyword: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        搜索航空公司 (支持中文名稱、英文名稱)
        
        Args:
            keyword (str): 搜索關鍵詞
            limit (int, optional): 返回結果的最大數量，預設為 10
            
        Returns:
            List[Dict[str, Any]]: 航空公司列表
        """
        async def perform_search(conn):
            # 構建模糊搜索條件
            search_term = f"%{keyword}%"
            
            sql = """
            SELECT 
                airline_id,
                name_zh,
                name_en,
                logo_path,
                is_domestic
            FROM airlines
            WHERE 
                airline_id ILIKE $1 OR
                name_zh ILIKE $1 OR
                name_en ILIKE $1
            ORDER BY 
                CASE 
                    WHEN airline_id = $2 THEN 1
                    WHEN name_zh = $2 THEN 2
                    WHEN name_en = $2 THEN 3
                    ELSE 4
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
            logger.error(f"搜索航空公司時出錯: {e}", exc_info=True)
            return []
        finally:
            if conn:
                await pool.release(conn)
                
    @staticmethod
    async def get_airlines_by_route(
        departure_airport: str,
        arrival_airport: str,
        date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        獲取特定航線上的航空公司
        
        Args:
            departure_airport (str): 出發機場ID
            arrival_airport (str): 到達機場ID
            date (Optional[str], optional): 指定日期 (YYYY-MM-DD)
            
        Returns:
            List[Dict[str, Any]]: 航空公司列表，包含運營該航線的航班數量
        """
        async def fetch_airlines(conn):
            params: List[Any] = [departure_airport, arrival_airport]
            date_condition = ""
            
            if date:
                try:
                    date_obj = datetime.strptime(date, '%Y-%m-%d').date()
                    date_condition = "AND DATE(f.scheduled_departure) = $3"
                    params.append(date_obj)
                except ValueError:
                    logger.error(f"無效的日期格式: {date}")
                    return []
            
            sql = f"""
            SELECT 
                al.airline_id,
                al.name_zh,
                al.name_en,
                al.logo_path,
                al.is_domestic,
                COUNT(f.flight_id) AS flight_count,
                MIN(tp.economy_price) AS min_price
            FROM 
                flights f
            JOIN 
                airlines al ON f.airline_id = al.airline_id
            LEFT JOIN 
                ticket_prices tp ON f.flight_id = tp.flight_id
            WHERE 
                f.departure_airport_id = $1
                AND f.arrival_airport_id = $2
                {date_condition}
            GROUP BY 
                al.airline_id, al.name_zh, al.name_en, al.logo_path, al.is_domestic
            ORDER BY 
                flight_count DESC
            """
            
            rows = await conn.fetch(sql, *params)
            return [dict(row) for row in rows]
        
        # 使用通用資料庫操作模式
        pool = await init_asyncpg_pool()
        conn = await pool.acquire()
        try:
            return await fetch_airlines(conn)
        except Exception as e:
            logger.error(f"獲取航線 {departure_airport} -> {arrival_airport} 的航空公司時出錯: {e}", exc_info=True)
            return []
        finally:
            if conn:
                await pool.release(conn)

    @staticmethod
    async def get_airline_by_code(iata_code: str) -> Optional[Dict[str, Any]]:
        """
        根據 IATA code 獲取航空公司信息
        
        Args:
            iata_code (str): 航空公司的 IATA code
            
        Returns:
            Optional[Dict[str, Any]]: 航空公司詳情，如果不存在則返回None
        """
        async def fetch_airline(conn):
            # airline_id 在我們的 schema 中就是 IATA code
            sql = "SELECT * FROM airlines WHERE airline_id = $1"
            row = await conn.fetchrow(sql, iata_code)
            return dict(row) if row else None

        pool = await init_asyncpg_pool()
        conn = await pool.acquire()
        try:
            return await fetch_airline(conn)
        except Exception as e:
            logger.error(f"根據 IATA code {iata_code} 獲取航空公司時出錯: {e}", exc_info=True)
            return None
        finally:
            if conn:
                await pool.release(conn)

    @staticmethod
    async def bulk_save_airlines(airlines_data: List[Dict[str, Any]]) -> int:
        """
        批量儲存或更新航空公司數據
        
        Args:
            airlines_data (List[Dict[str, Any]]): 從 Amadeus 適配器傳來的航空公司數據列表
            
        Returns:
            int: 成功儲存或更新的記錄數量
        """
        if not airlines_data:
            return 0

        async def upsert_airlines(conn):
            # 準備數據以符合 copy_records_to_table 的格式
            records_to_insert = []
            for airline in airlines_data:
                records_to_insert.append(
                    (
                        airline.get("iataCode"),
                        airline.get("commonName", airline.get("businessName")),
                        airline.get("businessName"),
                        f"static/images/logos/{airline.get('iataCode', 'default')}.png"
                    )
                )

            # 定義表名和列名
            table_name = 'airlines'
            columns = ['airline_id', 'name_zh', 'name_en', 'logo_path']
            
            try:
                # 使用事務確保操作的原子性
                async with conn.transaction():
                    # 創建一個臨時表來存放待處理的數據
                    temp_table_name = f"temp_airlines_{uuid.uuid4().hex}"
                    await conn.execute(f"""
                        CREATE TEMP TABLE {temp_table_name} (
                            airline_id VARCHAR(3) PRIMARY KEY,
                            name_zh VARCHAR(255),
                            name_en VARCHAR(255),
                            logo_path VARCHAR(255)
                        ) ON COMMIT DROP;
                    """)

                    # 將數據批量複製到臨時表
                    await conn.copy_records_to_table(
                        table_name=temp_table_name,
                        records=records_to_insert,
                        columns=columns
                    )

                    # 執行 "upsert" 操作：如果 airline_id 衝突，則更新；否則插入新記錄
                    upsert_sql = f"""
                    INSERT INTO {table_name} (airline_id, name_zh, name_en, logo_path)
                    SELECT airline_id, name_zh, name_en, logo_path FROM {temp_table_name}
                    ON CONFLICT (airline_id) DO UPDATE SET
                        name_zh = EXCLUDED.name_zh,
                        name_en = EXCLUDED.name_en,
                        logo_path = EXCLUDED.logo_path;
                    """
                    await conn.execute(upsert_sql)
                    
                    logger.info(f"成功批量處理 {len(records_to_insert)} 筆航空公司數據。")
                    return len(records_to_insert)

            except Exception as e:
                logger.error(f"批量儲存航空公司時發生數據庫錯誤: {e}", exc_info=True)
                raise

        # 獲取連接池並執行操作
        pool = await init_asyncpg_pool()
        conn = await pool.acquire()
        try:
            return await upsert_airlines(conn)
        except Exception:
            # 如果在 upsert_airlines 之外發生錯誤，確保返回 0
            return 0
        finally:
            if conn:
                await pool.release(conn)

    @staticmethod
    async def get_or_create_airline_from_amadeus(iata_code: str, dictionaries: Dict) -> Optional[Dict[str, Any]]:
        """
        根據 IATA code 查詢航空公司，如果不存在，則從 Amadeus dictionaries 中提取信息並創建。
        """
        # 1. 嘗試獲取航空公司
        existing_airline = await AirlineService.get_airline_by_id(iata_code)
        if existing_airline:
            return existing_airline

        # 2. 如果不存在，從 dictionaries 中查找並創建
        logger.info(f"本地數據庫中未找到航空公司 {iata_code}，嘗試從 Amadeus dictionaries 創建。")
        amadeus_airline_data = dictionaries.get('carriers', {}).get(iata_code)

        if not amadeus_airline_data:
            logger.warning(f"在 Amadeus dictionaries 中也找不到航空公司 {iata_code} 的詳細資訊。")
            # 返回一個包含iata_code的默認字典，以避免後續操作出錯
            return {"airline_id": iata_code, "name_zh": iata_code, "name_en": iata_code}

        # 3. 準備數據並創建
        new_airline_to_save = {
            "iataCode": iata_code,
            "businessName": amadeus_airline_data,
            "commonName": amadeus_airline_data
        }

        # 使用 bulk_save (傳入單一元素的列表) 來創建
        await AirlineService.bulk_save_airlines([new_airline_to_save])

        # 4. 再次查詢以返回創建的對象
        created_airline = await AirlineService.get_airline_by_id(iata_code)
        if created_airline:
            logger.info(f"成功創建並獲取了新航空公司: {iata_code}")
        else:
            logger.error(f"創建航空公司 {iata_code} 後無法從數據庫中將其取回。")
            # 如果還是找不到，返回默認字典
            return {"airline_id": iata_code, "name_zh": iata_code, "name_en": amadeus_airline_data}

        return created_airline

# 創建服務實例以供其他模塊導入
airline_service = AirlineService() 