#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
航班詳情服務模組 - 處理航班詳細信息的業務邏輯
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

import asyncpg
from ..database.db import init_asyncpg_pool
from .db_utils import execute_db_operation, execute_query

logger = logging.getLogger(__name__)

class FlightDetailsService:
    """航班詳情服務 - 處理航班詳細信息相關操作"""
    
    @staticmethod
    async def get_flight_details_by_id(flight_id: str) -> Optional[Dict[str, Any]]:
        """
        通過 flight_id 獲取詳細航班信息
        
        Args:
            flight_id: 航班ID
            
        Returns:
            Optional[Dict[str, Any]]: 航班詳細信息，如果不存在則返回None
        """
        async def fetch_flight_details(conn):
            # SQL 查詢獲取航班詳細信息，包括機場、航空公司數據
            sql = """
            SELECT 
                f.flight_id, 
                f.flight_number,
                f.scheduled_departure, 
                f.scheduled_arrival,
                f.aircraft,
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
                al.name_en as airline_name_en,
                al.logo_path,
                EXTRACT(EPOCH FROM (f.scheduled_arrival - f.scheduled_departure)) / 60 AS duration_minutes,
                tp.available_seats,
                tp.economy_price,
                tp.business_price,
                tp.first_price
            FROM flights f
            JOIN airports a1 ON f.departure_airport_id = a1.airport_id
            JOIN airports a2 ON f.arrival_airport_id = a2.airport_id
            JOIN airlines al ON f.airline_id = al.airline_id
            LEFT JOIN ticket_prices tp ON f.flight_id = tp.flight_id
            WHERE f.flight_id = $1;
            """
            
            row = await conn.fetchrow(sql, flight_id)
            if not row:
                logger.warning(f"航班ID {flight_id} 未找到")
                return None
                
            logger.info(f"成功獲取航班ID {flight_id} 的詳細信息")
            # 轉換為字典並返回
            flight_details = dict(row)
            
            # 添加價格信息，格式化為前端期望的結構
            economy_price = flight_details.pop('economy_price', None)
            business_price = flight_details.pop('business_price', None)
            first_price = flight_details.pop('first_price', None)
            
            flight_details['prices'] = {
                'economy': economy_price,
                'business': business_price,
                'first': first_price
            }
            
            # 添加可用座位信息
            available_seats = flight_details.pop('available_seats', None)
            flight_details['available_seats'] = {
                'economy': available_seats,
                'business': available_seats,
                'first': available_seats
            }
            
            return flight_details
            
        # 使用通用資料庫操作模式
        pool = await init_asyncpg_pool()
        conn = await pool.acquire()
        try:
            return await fetch_flight_details(conn)
        except Exception as e:
            logger.error(f"獲取航班ID {flight_id} 的詳細信息時出錯: {e}", exc_info=True)
            return None
        finally:
            if conn:
                await pool.release(conn)

    @staticmethod
    async def get_flights_by_route(
        dep_airport: str, 
        arr_airport: str, 
        from_date: str = None, 
        to_date: str = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
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
        
        async def fetch_flights(conn):
            params = [dep_airport, arr_airport]
            date_condition = ""
            param_index = 3
            
            if from_date:
                try:
                    from_date_obj = datetime.strptime(from_date, "%Y-%m-%d").date()
                    date_condition += f" AND f.scheduled_departure >= ${param_index}"
                    params.append(from_date_obj)
                    param_index += 1
                except ValueError:
                    logger.error(f"無效的起始日期格式: {from_date}")
                    return []
            
            if to_date:
                try:
                    # 確保結束日期包含當天
                    to_date_obj = datetime.strptime(to_date, "%Y-%m-%d").date()
                    to_date_end_of_day = datetime.combine(to_date_obj, datetime.max.time())
                    date_condition += f" AND f.scheduled_departure <= ${param_index}"
                    params.append(to_date_end_of_day)
                except ValueError:
                    logger.error(f"無效的結束日期格式: {to_date}")
                    return []
            
            sql = f"""
            SELECT 
                f.flight_id,
                f.flight_number,
                al.airline_id,
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
            LIMIT $3
            """
            
            # 添加 limit 參數
            params.append(limit)
            
            rows = await conn.fetch(sql, *params)
            flights = [dict(row) for row in rows]
            
            logger.info(f"成功獲取從機場ID {dep_airport} 到機場ID {arr_airport} 的航班，共 {len(flights)} 個航班")
            return flights
                
        # 使用通用資料庫操作模式
        pool = await init_asyncpg_pool()
        conn = await pool.acquire()
        try:
            return await fetch_flights(conn)
        except Exception as e:
            logger.error(f"獲取從機場ID {dep_airport} 到機場ID {arr_airport} 的航班時出錯: {e}", exc_info=True)
            return []
        finally:
            if conn:
                await pool.release(conn)

    @staticmethod
    async def get_flight_status(flight_number: str, date: str = None) -> Optional[Dict[str, Any]]:
        """
        查詢航班狀態
        
        Args:
            flight_number (str): 航班編號
            date (str, optional): 日期 (YYYY-MM-DD)，不提供則使用當天
            
        Returns:
            Optional[Dict[str, Any]]: 航班狀態信息，如果不存在則返回None
        """
        async def fetch_status(conn):
            # 如果未提供日期，使用當前日期
            if not date:
                current_date = datetime.now().date()
            else:
                try:
                    current_date = datetime.strptime(date, "%Y-%m-%d").date()
                except ValueError:
                    logger.error(f"無效的日期格式: {date}")
                    return None
            
            # 查詢當日該航班編號的航班
            sql = """
            SELECT 
                f.flight_id,
                f.flight_number,
                f.scheduled_departure,
                f.scheduled_arrival,
                f.actual_departure,
                f.actual_arrival,
                f.status,
                f.gate,
                f.terminal,
                a_dep.airport_id AS departure_airport,
                a_dep.name_zh AS departure_airport_name,
                a_arr.airport_id AS arrival_airport,
                a_arr.name_zh AS arrival_airport_name,
                al.airline_id,
                al.name_zh AS airline_name
            FROM flights f
            JOIN airports a_dep ON f.departure_airport_id = a_dep.airport_id
            JOIN airports a_arr ON f.arrival_airport_id = a_arr.airport_id
            JOIN airlines al ON f.airline_id = al.airline_id
            WHERE f.flight_number = $1
            AND DATE(f.scheduled_departure) = $2
            """
            
            row = await conn.fetchrow(sql, flight_number, current_date)
            if not row:
                return None
                
            flight_status = dict(row)
            
            # 計算延誤時間（如果有）
            if flight_status.get('actual_departure') and flight_status.get('scheduled_departure'):
                scheduled = flight_status['scheduled_departure']
                actual = flight_status['actual_departure']
                delay_minutes = int((actual - scheduled).total_seconds() / 60)
                flight_status['departure_delay_minutes'] = delay_minutes
            
            if flight_status.get('actual_arrival') and flight_status.get('scheduled_arrival'):
                scheduled = flight_status['scheduled_arrival']
                actual = flight_status['actual_arrival']
                delay_minutes = int((actual - scheduled).total_seconds() / 60)
                flight_status['arrival_delay_minutes'] = delay_minutes
                
            return flight_status
            
        # 使用通用資料庫操作模式
        pool = await init_asyncpg_pool()
        conn = await pool.acquire()
        try:
            return await fetch_status(conn)
        except Exception as e:
            logger.error(f"獲取航班 {flight_number} 的狀態時出錯: {e}", exc_info=True)
            return None
        finally:
            if conn:
                await pool.release(conn) 