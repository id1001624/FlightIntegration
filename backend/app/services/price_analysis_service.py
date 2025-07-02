#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
價格服務模組 - 處理機票價格相關的業務邏輯
整合基本價格操作與高級價格分析功能
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

import asyncpg
from sqlalchemy import func, desc, exc as sqlalchemy_exc
from ..database.db import init_asyncpg_pool
from ..models import TicketPrice, Flight, Airline, PriceHistory
from ..models.base import db
from .db_utils import execute_db_operation, execute_query, get_price_field_by_cabin_class, normalize_cabin_class, get_display_name_by_cabin_field

logger = logging.getLogger(__name__)

class PriceAnalysisService:
    """價格服務 - 處理票價查詢、分析和統計的邏輯"""
    
    # 從 price_service.py 移植的基本票價功能
    @staticmethod
    async def get_price_by_flight(flight_id, cabin_preference=None):
        """
        獲取航班的票價信息 (使用 asyncpg)
        
        Args:
            flight_id: 航班ID
            cabin_preference: 艙等偏好（可選，如 'economy'）
            
        Returns:
            list: 票價列表
        """
        cabin_preference = normalize_cabin_class(cabin_preference) if cabin_preference else None
        
        pool = await init_asyncpg_pool() # 獲取連接池
        if pool is None:
            logger.error("無法獲取資料庫連接池")
            return []
            
        try:
            async with pool.acquire() as conn: # 從連接池獲取連接
                # 構建基礎查詢字符串
                base_query = """
                    SELECT economy_price, premium_economy_price, business_price, first_price, available_seats, price_updated_at
                    FROM ticket_prices
                    WHERE flight_id = $1
                """ # 修正: SQL 內容移到下一行並正確縮排
                
                # 執行查詢
                results = await conn.fetch(base_query, flight_id)
                
                # 處理結果
                prices = []
                for record in results:
                    # 如果指定了艙等偏好，只返回該艙等的價格
                    if cabin_preference:
                        price_field = get_price_field_by_cabin_class(cabin_preference)
                        price_value = record[price_field]
                        if price_value is not None:
                            display_name = get_display_name_by_cabin_field(price_field)
                            prices.append({
                                'cabin_class': display_name, 
                                'cabin_type': cabin_preference,
                                'price': float(price_value),
                                'available_seats': record['available_seats'],
                                'updated_at': record['price_updated_at'].isoformat() if record['price_updated_at'] else None
                            })
                    else:
                        # 如果沒有指定艙等，返回所有艙等的價格
                        cabin_types = ['economy', 'premium_economy', 'business', 'first']
                        for cabin_type in cabin_types:
                            price_field = get_price_field_by_cabin_class(cabin_type)
                            price_value = record[price_field]
                            if price_value is not None:
                                display_name = get_display_name_by_cabin_field(price_field)
                                prices.append({
                                    'cabin_class': display_name,
                                    'cabin_type': cabin_type,
                                    'price': float(price_value),
                                    'available_seats': record['available_seats'],
                                    'updated_at': record['price_updated_at'].isoformat() if record['price_updated_at'] else None
                                })
                
                return prices
        except asyncpg.PostgresError as pg_err: # 捕捉 asyncpg 錯誤
            logger.error(f"Error fetching price for flight {flight_id} using asyncpg: {pg_err}", exc_info=True)
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching price for flight {flight_id}: {e}", exc_info=True)
            return []
    
    @staticmethod
    async def get_prices_for_flights_batch(flight_ids: list[str]) -> dict[str, dict[str, dict]]:
        """
        批量獲取多個航班的所有艙位價格信息 (使用 asyncpg)。

        Args:
            flight_ids: 航班 ID 列表。

        Returns:
            一個字典，鍵是航班 ID (str)，值是另一個字典，
            其鍵是艙位類型 (str)，值是包含價格信息的字典。
            例如: {'flight_id1': {'economy': {'amount': 100.0, ...}, 'business': {...}}, ...}
        """
        if not flight_ids:
            return {}

        prices_map = {}
        pool = await init_asyncpg_pool() # 獲取連接池
        if pool is None:
            logger.error("無法獲取資料庫連接池")
            return {}
            
        try:
            async with pool.acquire() as conn: # 從連接池獲取連接
                # SQL 查詢字符串
                price_query_str = """
                SELECT flight_id, economy_price, premium_economy_price, business_price, first_price, available_seats, price_updated_at
                FROM ticket_prices
                WHERE flight_id = ANY($1::uuid[])
                """ # 修正: SQL 內容移到下一行並正確縮排
                
                # 直接傳遞 flight_ids 列表作為參數
                price_records = await conn.fetch(price_query_str, flight_ids)
                
                for record in price_records:
                    flight_id_str = str(record['flight_id']) # 確保轉換為字符串
                    if flight_id_str not in prices_map:
                        prices_map[flight_id_str] = {}
                    
                    # 處理各艙等價格
                    cabin_types = ['economy', 'premium_economy', 'business', 'first']
                    for cabin_type in cabin_types:
                        price_field = get_price_field_by_cabin_class(cabin_type)
                        price_value = record[price_field]
                        if price_value is not None:
                            display_name = get_display_name_by_cabin_field(price_field)
                            prices_map[flight_id_str][cabin_type] = {
                                'amount': float(price_value),
                                'available_seats': record['available_seats'],
                                'cabin_class': display_name,
                                'cabin_type': cabin_type,
                                'updated_at': record['price_updated_at'].isoformat() if record['price_updated_at'] else None
                            }
                
                logger.info(f"批量獲取了 {len(flight_ids)} 個航班的 {len(price_records)} 條票價記錄")

        except asyncpg.PostgresError as pg_err: # 捕捉 asyncpg 特定錯誤
            logger.error(f"批量查詢票價時出錯: {pg_err}", exc_info=True)
        except Exception as e:
            logger.error(f"批量查詢票價時發生未知錯誤: {e}", exc_info=True)
            # 即使出錯，也可能返回部分獲取的數據
        
        return prices_map
    
    @staticmethod
    async def get_lowest_prices(
        departure_code: str, 
        arrival_code: str, 
        start_date: str, 
        end_date: Optional[str] = None,
        cabin_preference: str = "economy"
    ) -> Dict[str, Any]:
        """
        獲取指定日期範圍內的最低票價 (異步版本)
        
        Args:
            departure_code: 出發機場代碼
            arrival_code: 到達機場代碼
            start_date: 開始日期 (YYYY-MM-DD)
            end_date: 結束日期 (YYYY-MM-DD)，可選，默認為開始日期後30天
            cabin_preference: 艙等偏好 (默認為 economy)
            
        Returns:
            Dict: 包含最低票價數據的字典
        """
        # 標準化艙等
        cabin_preference = normalize_cabin_class(cabin_preference)
        price_field = get_price_field_by_cabin_class(cabin_preference)
        
        async def fetch_lowest_prices(conn):
            # 處理日期
            try:
                start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
                if end_date:
                    end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
                else:
                    end_date_obj = start_date_obj + timedelta(days=30)
            except ValueError:
                logger.error(f"無效的日期格式: {start_date} 或 {end_date}")
                return {
                    "error": "無效的日期格式",
                    "departure": departure_code,
                    "arrival": arrival_code
                }
            
            # 查詢最低票價
            sql = f"""
            WITH DailyMinPrices AS (
                SELECT 
                    DATE(f.scheduled_departure) AS flight_date,
                    MIN(tp.{price_field}) AS min_price
                FROM flights f
                JOIN ticket_prices tp ON f.flight_id = tp.flight_id
                WHERE f.departure_airport_id = $1
                  AND f.arrival_airport_id = $2
                  AND DATE(f.scheduled_departure) >= $3
                  AND DATE(f.scheduled_departure) <= $4
                  AND tp.{price_field} IS NOT NULL
                GROUP BY DATE(f.scheduled_departure)
            )
            SELECT 
                TO_CHAR(flight_date, 'YYYY-MM-DD') AS date,
                min_price
            FROM DailyMinPrices
            ORDER BY flight_date;
            """
            
            # 執行查詢
            rows = await conn.fetch(
                sql, 
                departure_code, 
                arrival_code, 
                start_date_obj, 
                end_date_obj
            )
            
            # 格式化結果
            price_map = {}
            for row in rows:
                price_map[row["date"]] = float(row["min_price"])
            
            return price_map
            
        # 使用通用資料庫操作模式
        pool = await init_asyncpg_pool()
        if pool is None:
            logger.error("無法獲取資料庫連接池")
            return {
                "error": "資料庫連接失敗",
                "departure": departure_code,
                "arrival": arrival_code
            }
            
        try:
            async with pool.acquire() as conn:
                return await fetch_lowest_prices(conn)
        except Exception as e:
            logger.error(f"獲取最低票價時發生錯誤: {e}", exc_info=True)
            return {
                "error": f"獲取最低票價失敗: {str(e)}",
                "departure": departure_code,
                "arrival": arrival_code
            }
    
    @staticmethod
    async def get_price_history(
        flight_id: str, 
        cabin_class: str = "經濟", 
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        獲取航班的歷史票價 (異步版本)
        
        Args:
            flight_id: 航班ID
            cabin_class: 艙等類型
            days: 歷史天數
            
        Returns:
            List[Dict]: 歷史票價列表
        """
        # 標準化艙等
        cabin_class = normalize_cabin_class(cabin_class)
        price_field = get_price_field_by_cabin_class(cabin_class)
        
        async def fetch_price_history(conn):
            # 計算時間範圍
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # 查詢歷史票價
            sql = f"""
            SELECT 
                tp.flight_id,
                tp.{price_field} AS price,
                tp.available_seats,
                tp.created_at
            FROM price_history tp
            WHERE tp.flight_id = $1
              AND tp.created_at >= $2
              AND tp.created_at <= $3
              AND tp.{price_field} IS NOT NULL
            ORDER BY tp.created_at ASC;
            """
            
            # 執行查詢
            rows = await conn.fetch(sql, flight_id, start_date, end_date)
            
            # 格式化結果
            history = []
            for row in rows:
                history.append({
                    "date": row["created_at"].strftime("%Y-%m-%d"),
                    "time": row["created_at"].strftime("%H:%M:%S"),
                    "price": float(row["price"]),
                    "available_seats": row["available_seats"]
                })
            
            return history
            
        # 使用通用資料庫操作模式
        pool = await init_asyncpg_pool()
        if pool is None:
            logger.error("無法獲取資料庫連接池")
            return []
            
        try:
            async with pool.acquire() as conn:
                return await fetch_price_history(conn)
        except Exception as e:
            logger.error(f"獲取航班 {flight_id} 歷史票價時發生錯誤: {e}", exc_info=True)
            return []
    
    @staticmethod
    async def analyze_price_trend(
        flight_id: str, 
        cabin_class: str = "經濟"
    ) -> Dict[str, Any]:
        """
        分析航班票價趨勢並提供購買建議 (異步版本)
        
        Args:
            flight_id: 航班ID
            cabin_class: 艙等類型
            
        Returns:
            Dict[str, Any]: 包含價格趨勢分析和購買建議的字典
        """
        # 標準化艙等
        cabin_class = normalize_cabin_class(cabin_class)
        
        async def analyze_trend(conn):
            # 獲取航班信息
            flight_info_sql = """
            SELECT 
                f.flight_number,
                f.airline_id,
                f.departure_airport_id,
                f.arrival_airport_id,
                f.scheduled_departure,
                a_dep.name_zh AS departure_name,
                a_arr.name_zh AS arrival_name,
                al.name_zh AS airline_name
            FROM flights f
            JOIN airports a_dep ON f.departure_airport_id = a_dep.airport_id
            JOIN airports a_arr ON f.arrival_airport_id = a_arr.airport_id
            JOIN airlines al ON f.airline_id = al.airline_id
            WHERE f.flight_id = $1;
            """
            
            flight_info = await conn.fetchrow(flight_info_sql, flight_id)
            if not flight_info:
                return {
                    "error": f"找不到航班 ID: {flight_id}",
                    "flight_id": flight_id
                }
            
            # 獲取當前票價
            price_field = get_price_field_by_cabin_class(cabin_class)
            current_price_sql = f"""
            SELECT {price_field} AS price
            FROM ticket_prices
            WHERE flight_id = $1;
            """
            
            current_price_record = await conn.fetchrow(current_price_sql, flight_id)
            current_price = float(current_price_record["price"]) if current_price_record and current_price_record["price"] else None
            
            if not current_price:
                return {
                    "error": f"找不到航班 {flight_id} 的{cabin_class}艙票價",
                    "flight_id": flight_id,
                    "cabin_class": cabin_class
                }
            
            # 獲取歷史票價
            history = await PriceAnalysisService.get_price_history(flight_id, cabin_class, 30)
            
            # 如果沒有足夠的歷史數據進行分析
            if len(history) < 2:
                return {
                    "flight_id": flight_id,
                    "flight_number": flight_info["flight_number"],
                    "departure": flight_info["departure_airport_id"],
                    "departure_name": flight_info["departure_name"],
                    "arrival": flight_info["arrival_airport_id"],
                    "arrival_name": flight_info["arrival_name"],
                    "airline": flight_info["airline_id"],
                    "airline_name": flight_info["airline_name"],
                    "scheduled_departure": flight_info["scheduled_departure"].isoformat(),
                    "cabin_class": cabin_class,
                    "current_price": current_price,
                    "price_trend": "unknown",
                    "recommendation": "無法提供建議 (歷史數據不足)",
                    "confidence": 0,
                    "history": history
                }
            
            # 分析票價趨勢
            first_price = history[0]["price"]
            last_price = history[-1]["price"]
            price_change = last_price - first_price
            price_change_percent = (price_change / first_price) * 100 if first_price > 0 else 0
            
            # 確定趨勢和建議
            if price_change_percent > 10:
                trend = "rising"
                recommendation = "建議儘快購買，票價上漲趨勢明顯"
                confidence = 0.8
            elif price_change_percent > 5:
                trend = "slightly_rising"
                recommendation = "票價有小幅上升趨勢，近期購買較合適"
                confidence = 0.7
            elif price_change_percent < -10:
                trend = "falling"
                recommendation = "票價下降趨勢明顯，可考慮等待進一步下降"
                confidence = 0.8
            elif price_change_percent < -5:
                trend = "slightly_falling"
                recommendation = "票價有小幅下降趨勢，等待可能獲得更好價格"
                confidence = 0.7
            else:
                trend = "stable"
                recommendation = "票價相對穩定，預期不會有大幅變動"
                confidence = 0.6
            
            # 檢查距離出發日期
            days_to_departure = (flight_info["scheduled_departure"].date() - datetime.now().date()).days
            if days_to_departure < 7:
                recommendation = "距離出發日期較近，建議儘快購買，避免票價進一步上漲"
                confidence = max(confidence, 0.85)
            elif days_to_departure < 14 and trend in ["rising", "slightly_rising", "stable"]:
                recommendation = "距離出發日期兩週左右，且價格趨勢不佳，建議現在購買"
                confidence = max(confidence, 0.75)
            
            # 返回分析結果
            return {
                "flight_id": flight_id,
                "flight_number": flight_info["flight_number"],
                "departure": flight_info["departure_airport_id"],
                "departure_name": flight_info["departure_name"],
                "arrival": flight_info["arrival_airport_id"],
                "arrival_name": flight_info["arrival_name"],
                "airline": flight_info["airline_id"],
                "airline_name": flight_info["airline_name"],
                "scheduled_departure": flight_info["scheduled_departure"].isoformat(),
                "cabin_class": cabin_class,
                "current_price": current_price,
                "price_trend": trend,
                "price_change": round(price_change, 2),
                "price_change_percent": round(price_change_percent, 2),
                "recommendation": recommendation,
                "confidence": confidence,
                "history": history
            }
        
        # 使用通用資料庫操作模式
        pool = await init_asyncpg_pool()
        if pool is None:
            logger.error("無法獲取資料庫連接池")
            return {
                "error": "資料庫連接失敗",
                "flight_id": flight_id,
                "cabin_class": cabin_class
            }
            
        try:
            async with pool.acquire() as conn:
                return await analyze_trend(conn)
        except Exception as e:
            logger.error(f"分析航班 {flight_id} 票價趨勢時發生錯誤: {e}", exc_info=True)
            return {
                "error": f"分析票價趨勢失敗: {str(e)}",
                "flight_id": flight_id,
                "cabin_class": cabin_class
            }
    
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
        async def fetch_calendar_data(conn):
            # 嘗試解析日期
            try:
                start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
                end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
                
                # 確保日期範圍合理
                if (end_date_obj - start_date_obj).days > 90:  # 限制最多90天
                    end_date_obj = start_date_obj + timedelta(days=90)
                    logger.warning(f"日期範圍過大，已限制為90天: {start_date} 到 {end_date_obj.strftime('%Y-%m-%d')}")
            except ValueError:
                logger.error(f"無效的日期格式: {start_date} 或 {end_date}")
                return {
                    "error": "無效的日期格式",
                    "departure": departure_code,
                    "arrival": arrival_code
                }
            
            # 根據艙等選擇對應的價格欄位
            price_field = get_price_field_by_cabin_class(cabin_class)
            
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
        
        # 使用通用資料庫操作模式
        pool = await init_asyncpg_pool()
        if pool is None:
            logger.error("無法獲取資料庫連接池")
            return {
                "error": "資料庫連接失敗",
                "departure": departure_code,
                "arrival": arrival_code
            }
            
        try:
            async with pool.acquire() as conn:
                return await fetch_calendar_data(conn)
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
        async def fetch_trend_data(conn):
            # 解析日期
            try:
                start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
            except ValueError:
                logger.error(f"無效的日期格式: {start_date}")
                return {
                    "error": "無效的日期格式",
                    "departure": departure_code,
                    "arrival": arrival_code
                }
            
            # 計算查詢的開始日期
            history_start_date = start_date_obj - timedelta(days=days_before)
            
            # 根據艙等選擇價格欄位
            price_field = get_price_field_by_cabin_class(cabin_class)
            
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
        
        # 使用通用資料庫操作模式
        pool = await init_asyncpg_pool()
        if pool is None:
            logger.error("無法獲取資料庫連接池")
            return {
                "error": "資料庫連接失敗",
                "departure": departure_code,
                "arrival": arrival_code
            }
            
        try:
            async with pool.acquire() as conn:
                return await fetch_trend_data(conn)
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
        async def fetch_stats(conn):
            # 查詢航線基本統計信息
            sql = """
            WITH RouteFlights AS (
                SELECT 
                    f.flight_id,
                    f.airline_id,
                    DATE(f.scheduled_departure) AS departure_date,
                    f.scheduled_departure,
                    tp.economy_price, 
                    tp.business_price,
                    tp.first_price
                FROM flights f
                LEFT JOIN ticket_prices tp ON f.flight_id = tp.flight_id
                WHERE f.departure_airport_id = $1
                  AND f.arrival_airport_id = $2
                  AND f.scheduled_departure >= CURRENT_DATE
                  AND f.scheduled_departure < CURRENT_DATE + INTERVAL '30 days'
            ), 
            PriceStats AS (
                SELECT
                    MIN(economy_price) AS min_economy,
                    AVG(economy_price) AS avg_economy,
                    MAX(economy_price) AS max_economy,
                    MIN(business_price) AS min_business,
                    AVG(business_price) AS avg_business,
                    MAX(business_price) AS max_business,
                    MIN(first_price) AS min_first,
                    AVG(first_price) AS avg_first,
                    MAX(first_price) AS max_first
                FROM RouteFlights
                WHERE economy_price IS NOT NULL
                  OR business_price IS NOT NULL
                  OR first_price IS NOT NULL
            ),
            AirlineStats AS (
                SELECT
                    airline_id,
                    COUNT(*) AS flight_count
                FROM RouteFlights
                GROUP BY airline_id
                ORDER BY flight_count DESC
            ),
            DateStats AS (
                SELECT
                    departure_date,
                    COUNT(*) AS flight_count
                FROM RouteFlights
                GROUP BY departure_date
                ORDER BY departure_date
            ),
            TimeStats AS (
                SELECT
                    EXTRACT(HOUR FROM scheduled_departure) AS hour,
                    COUNT(*) AS flight_count
                FROM RouteFlights
                GROUP BY EXTRACT(HOUR FROM scheduled_departure)
                ORDER BY hour
            )
            SELECT 
                (SELECT COUNT(*) FROM RouteFlights) AS total_flights,
                (SELECT COUNT(DISTINCT departure_date) FROM RouteFlights) AS days_with_flights,
                (SELECT COUNT(DISTINCT airline_id) FROM RouteFlights) AS airline_count,
                (SELECT json_agg(row_to_json(ps)) FROM PriceStats ps) AS price_stats,
                (SELECT json_agg(row_to_json(ast)) FROM AirlineStats ast) AS airline_stats,
                (SELECT json_agg(row_to_json(dst)) FROM DateStats dst) AS date_stats,
                (SELECT json_agg(row_to_json(tst)) FROM TimeStats tst) AS time_stats;
            """
            
            # 執行查詢
            result = await conn.fetchrow(sql, departure_code, arrival_code)
            
            # 處理結果
            if not result or result["total_flights"] == 0:
                return {
                    "error": "找不到該航線的航班",
                    "departure": departure_code,
                    "arrival": arrival_code
                }
            
            # 格式化價格統計
            price_stats = {}
            if result["price_stats"]:
                ps = result["price_stats"][0]  # 只有一個行
                for cabin in ["economy", "business", "first"]:
                    if ps[f"min_{cabin}"] is not None:
                        price_stats[cabin] = {
                            "min": float(ps[f"min_{cabin}"]),
                            "avg": round(float(ps[f"avg_{cabin}"]), 2),
                            "max": float(ps[f"max_{cabin}"])
                        }
            
            # 格式化每日航班數量
            date_distribution = {}
            if result["date_stats"]:
                for d in result["date_stats"]:
                    date_distribution[d["departure_date"].strftime("%Y-%m-%d")] = d["flight_count"]
            
            # 格式化時段分布
            hour_distribution = {}
            if result["time_stats"]:
                for t in result["time_stats"]:
                    hour_distribution[int(t["hour"])] = t["flight_count"]
            
            # 格式化航空公司分布
            airline_distribution = {}
            if result["airline_stats"]:
                for a in result["airline_stats"]:
                    airline_distribution[a["airline_id"]] = a["flight_count"]
            
            return {
                "departure": departure_code,
                "arrival": arrival_code,
                "total_flights": result["total_flights"],
                "days_with_flights": result["days_with_flights"],
                "airline_count": result["airline_count"],
                "price_stats": price_stats,
                "date_distribution": date_distribution,
                "hour_distribution": hour_distribution,
                "airline_distribution": airline_distribution
            }
        
        # 使用通用資料庫操作模式
        pool = await init_asyncpg_pool()
        if pool is None:
            logger.error("無法獲取資料庫連接池")
            return {
                "error": "資料庫連接失敗",
                "departure": departure_code,
                "arrival": arrival_code
            }
            
        try:
            async with pool.acquire() as conn:
                return await fetch_stats(conn)
        except Exception as e:
            logger.error(f"獲取航線統計數據時發生錯誤: {e}", exc_info=True)
            return {
                "error": f"獲取航線統計數據失敗: {str(e)}",
                "departure": departure_code,
                "arrival": arrival_code
            }
                
    # 為了兼容性，提供同名方法作為別名
    @staticmethod
    def get_lowest_prices_sync(
        departure_code: str, 
        arrival_code: str, 
        start_date: str, 
        end_date: Optional[str] = None,
        cabin_preference: str = "經濟"
    ):
        """
        同步方法，用於兼容舊的代碼。建議遷移至異步版本的 PriceAnalysisService.get_lowest_prices
        """
        logger.warning(
            "使用了同步版本的 get_lowest_prices_sync，建議遷移至異步版本的 PriceAnalysisService.get_lowest_prices"
        )
        import asyncio
        
        return asyncio.run(PriceAnalysisService.get_lowest_prices(
            departure_code=departure_code,
            arrival_code=arrival_code,
            start_date=start_date,
            end_date=end_date,
            cabin_preference=cabin_preference
        )) 