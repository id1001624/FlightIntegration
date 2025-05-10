#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
航空公司服務模組 - 處理航空公司信息相關的業務邏輯
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

import asyncpg
from ..database.db import init_asyncpg_pool
from .db_utils import execute_db_operation, execute_query

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
            params = [departure_airport, arrival_airport]
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