#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
飛行搜索服務模組 - 處理航班搜尋的業務邏輯
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple, Union
from sqlalchemy.sql import text, func

# 移除 SQLAlchemy 相關導入
from app.database.db import get_db, release_db
# 這些模型現在僅用於類型提示
from app.models.airline import Airline
from app.models.airport import Airport
from app.models.flight import Flight
from app.models.ticket_price import TicketPrice

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
        db = None # 初始化 db
        try:
            # 獲取數據庫連接
            db = await get_db()
            
            # 查詢航班
            outbound_flights = await SearchService._query_flights(
                db, departure_code, arrival_code, date_str, 
                airline_code, price_min, price_max, 
                cabin_class, max_results, sort_by
            )
            
            # 生成三種艙等的航班數據
            cabin_classes = ["經濟", "商務", "頭等"]
            outbound_results = {
                "economy": await SearchService._format_flights(outbound_flights, "經濟"),
                "business": await SearchService._format_flights(outbound_flights, "商務"),
                "first": await SearchService._format_flights(outbound_flights, "頭等")
            }
            
            # 如果提供了回程日期，也查詢回程航班
            inbound_results = None
            if return_date_str:
                inbound_flights = await SearchService._query_flights(
                    db, arrival_code, departure_code, return_date_str, 
                    airline_code, price_min, price_max, 
                    cabin_class, max_results, sort_by
                )
                inbound_results = {
                    "economy": await SearchService._format_flights(inbound_flights, "經濟"),
                    "business": await SearchService._format_flights(inbound_flights, "商務"),
                    "first": await SearchService._format_flights(inbound_flights, "頭等")
                }
                
            # 準備結果
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

        finally:
            # 確保數據庫連接被釋放
            if db:
                await release_db(db)
    
    @staticmethod
    async def _query_flights(
        db,
        departure_code: str,
        arrival_code: str,
        date_str: str,
        airline_code: Optional[Union[str, List[str]]] = None,
        price_min: Optional[int] = None,
        price_max: Optional[int] = None,
        cabin_class: str = "經濟",
        max_results: int = 20,  # 預設限制為20個結果
        sort_by: str = "price"
    ) -> List[Dict[str, Any]]:
        """
        查詢航班
        
        Args:
            db: 數據庫連接
            departure_code: 出發地機場IATA代碼
            arrival_code: 目的地機場IATA代碼
            date_str: 日期字符串 (YYYY-MM-DD)
            airline_code: 航空公司IATA代碼或代碼列表，可選
            price_min: 最低價格，可選
            price_max: 最高價格，可選
            cabin_class: 艙位類型
            max_results: 最大結果數
            sort_by: 排序方式
        
        Returns:
            List[Dict[str, Any]]: 航班列表
        """
        # 解析日期
        try:
            flight_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            logger.info(f"解析日期成功: {flight_date}")
        except ValueError:
            logger.error(f"日期格式錯誤: {date_str}")
            return []
        
        # 構建 SQL 查詢 - 使用IATA代碼
        sql = """
        SELECT 
            f.flight_id, 
            f.flight_number, 
            f.scheduled_departure, 
            f.scheduled_arrival, 
            a_dep.airport_id as departure_id, 
            a_dep.name_zh as departure_name,
            a_dep.city as departure_city,
            a_arr.airport_id as arrival_id, 
            a_arr.name_zh as arrival_name,
            a_arr.city as arrival_city,
            al.airline_id, 
            al.name_zh as airline_name_zh,
            al.name_en as airline_name_en,
            al.is_domestic as airline_is_domestic,
            al.logo_path as airline_logo_path
        FROM 
            flights f
        JOIN 
            airports a_dep ON f.departure_airport_id = a_dep.airport_id
        JOIN 
            airports a_arr ON f.arrival_airport_id = a_arr.airport_id
        JOIN 
            airlines al ON f.airline_id = al.airline_id
        WHERE 
            a_dep.airport_id = $1
            AND a_arr.airport_id = $2
            AND DATE(f.scheduled_departure) = $3
        """
        
        params = [departure_code, arrival_code, flight_date]
        param_index = 4
        
        # 添加航空公司過濾 - 處理字符串或列表
        if airline_code:
            if isinstance(airline_code, list):
                # 如果是列表，使用 IN 操作符
                placeholders = []
                for code in airline_code:
                    placeholders.append(f"${param_index}")
                    params.append(code)
                    param_index += 1
                sql += f" AND al.airline_id IN ({', '.join(placeholders)})"
            else:
                # 如果是字符串，使用等號
                sql += f" AND al.airline_id = ${param_index}"
                params.append(airline_code)
                param_index += 1
        
        # 添加排序 - 移除價格排序，改用出發時間
        sql += " ORDER BY f.scheduled_departure"
            
        # 添加結果限制
        sql += f" LIMIT {max_results}"
        
        logger.info(f"執行SQL查詢: {sql} 參數: {params}")
        
        # 執行查詢
        try:
            flights = await db.fetch(sql, *params)
            logger.info(f"找到 {len(flights)} 個航班 ({departure_code}->{arrival_code} on {date_str})")
            return flights
        except Exception as e:
            logger.error(f"查詢航班時出錯: {str(e)}")
            return []
    
    @staticmethod
    async def _format_flights(flights: List[Dict[str, Any]], cabin_class: str) -> List[Dict[str, Any]]:
        """
        格式化航班列表為API響應格式，並從數據庫獲取票價數據
        
        Args:
            flights: 航班列表 (包含 flight_id)
            cabin_class: 艙位類型
            
        Returns:
            List[Dict[str, Any]]: 格式化後的航班列表
        """
        import random # 保留 random 用於 status 和 terminal/gate
        formatted_flights = []
        db = None
        
        if not flights:
            return []
            
        # --- 獲取所有相關航班的票價 --- 
        flight_ids = [flight["flight_id"] for flight in flights]
        prices_map = {}
        try:
            db = await get_db()
            price_query = """
            SELECT flight_id, base_price, available_seats
            FROM ticket_prices
            WHERE flight_id = ANY($1::uuid[]) AND class_type = $2
            """
            price_records = await db.fetch(price_query, flight_ids, cabin_class)
            for record in price_records:
                prices_map[record['flight_id']] = {
                    'amount': float(record['base_price']) if record['base_price'] is not None else None,
                    'available_seats': record['available_seats']
                }
            logger.info(f"為 {len(flights)} 個航班獲取了 {len(prices_map)} 條 '{cabin_class}' 艙位票價記錄")
        except Exception as e:
            logger.error(f"查詢票價時出錯: {e}", exc_info=True)
            # 即使票價查詢失敗，也繼續格式化航班，只是價格信息會缺失
        finally:
            if db:
                await release_db(db)
        # --- 結束票價獲取 ---

        # 定義可能的航班狀態
        possible_statuses = [
            'on_time', 'scheduled', 'delayed', 'in_air', 'arrived', 'cancelled'
        ]
        status_weights = [0.65, 0.15, 0.08, 0.05, 0.05, 0.02]
        
        for flight in flights:
            # --- 從 map 中獲取票價信息 --- 
            price_info = prices_map.get(flight["flight_id"])
            flight_price_amount = price_info['amount'] if price_info else None
            flight_available_seats = price_info['available_seats'] if price_info else None
            # --- 結束票價獲取 ---

            # 計算飛行時間（分鐘）
            try:
                dep_time = flight["scheduled_departure"]
                arr_time = flight["scheduled_arrival"]
                duration_minutes = int((arr_time - dep_time).total_seconds() / 60)
            except:
                duration_minutes = random.randint(120, 360) # 保留備用邏輯
            
            # 如果沒有狀態或狀態為unknown，則生成隨機狀態
            status = flight.get("status", "unknown")
            if status is None or status.lower() == "unknown" or status == "":
                status = random.choices(possible_statuses, weights=status_weights, k=1)[0]
            
            # 格式化航班數據 - 匹配 AirlineBasicSchema
            formatted_flight = {
                "flight_id": flight["flight_id"],
                "airline": {
                    "code": flight["airline_id"],
                    "name_zh": flight.get("airline_name_zh"),
                    "name_en": flight.get("airline_name_en"),
                    "logo_path": flight.get("airline_logo_path"),
                    "is_domestic": flight.get("airline_is_domestic")
                },
                "flight_number": flight["flight_number"],
                "departure": {
                    "airport_id": flight["departure_id"],
                    "name": flight["departure_name"],
                    "city": flight["departure_city"],
                    "terminal": random.choice(["1", "2", "3"]), # 保留隨機生成
                    "gate": f"{random.choice('ABCDE')}{random.randint(1, 20)}", # 保留隨機生成
                    "time": flight["scheduled_departure"].isoformat()
                },
                "arrival": {
                    "airport_id": flight["arrival_id"],
                    "name": flight["arrival_name"],
                    "city": flight["arrival_city"],
                    "terminal": random.choice(["1", "2", "3"]), # 保留隨機生成
                    "gate": f"{random.choice('ABCDE')}{random.randint(1, 20)}", # 保留隨機生成
                    "time": flight["scheduled_arrival"].isoformat()
                },
                "duration_minutes": duration_minutes,
                "status": status,
                "price": { # 使用從數據庫獲取的數據
                    "amount": flight_price_amount,
                    "currency": "TWD",
                    "cabin_class": cabin_class,
                    "available_seats": flight_available_seats
                }
            }
            
            formatted_flights.append(formatted_flight)
        
        return formatted_flights
    
    @staticmethod
    async def get_low_fare_calendar(
        departure_code: str,
        arrival_code: str,
        start_date: str,
        end_date: str,
        cabin_class: str = "經濟"
    ) -> Dict[str, Any]:
        """
        獲取低價日曆
        
        Args:
            departure_code: 出發地IATA代碼
            arrival_code: 目的地IATA代碼
            start_date: 開始日期 (YYYY-MM-DD)
            end_date: 結束日期 (YYYY-MM-DD)
            cabin_class: 艙位類型
            
        Returns:
            Dict[str, Any]: 各日期的最低價格
        """
        # 獲取數據庫連接
        db = await get_db()
        
        # 解析日期
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            logger.error(f"日期格式錯誤: {start_date} or {end_date}")
            return {"error": "日期格式錯誤"}
        
        # 構建查詢
        try:
            # 這個查詢使用原生SQL以獲得更好的性能
            result = db.execute(
                text("""
                SELECT 
                    DATE(f.scheduled_departure) as flight_date,
                    MIN(tp.base_price) as min_price
                FROM 
                    flights f
                JOIN 
                    ticket_prices tp ON f.flight_id = tp.flight_id
                WHERE 
                    f.departure_airport_id = :departure_code
                    AND f.arrival_airport_id = :arrival_code
                    AND DATE(f.scheduled_departure) BETWEEN :start_date AND :end_date
                    AND tp.class_type = :cabin_class
                GROUP BY 
                    DATE(f.scheduled_departure)
                ORDER BY 
                    flight_date
                """),
                {
                    "departure_code": departure_code,
                    "arrival_code": arrival_code,
                    "start_date": start,
                    "end_date": end,
                    "cabin_class": cabin_class
                }
            )
            
            # 將結果轉換為字典
            price_calendar = {}
            for row in result:
                flight_date = row.flight_date.strftime("%Y-%m-%d")
                price_calendar[flight_date] = row.min_price
            
            return {
                "route": f"{departure_code}-{arrival_code}",
                "cabin_class": cabin_class,
                "date_range": [start_date, end_date],
                "prices": price_calendar
            }
            
        except Exception as e:
            logger.error(f"獲取低價日曆時出錯: {str(e)}")
            return {"error": f"查詢執行錯誤: {str(e)}"}
            
    @staticmethod
    async def get_fare_trends(
        departure_code: str,
        arrival_code: str,
        start_date: str,
        cabin_class: str = "經濟",
        days_before: int = 30
    ) -> Dict[str, Any]:
        """
        獲取機票價格趨勢
        
        Args:
            departure_code: 出發地IATA代碼
            arrival_code: 目的地IATA代碼
            start_date: 出發日期 (YYYY-MM-DD)
            cabin_class: 艙位類型
            days_before: 查詢過去多少天的價格變化
            
        Returns:
            Dict[str, Any]: 價格趨勢數據
        """
        # 獲取數據庫連接
        db = await get_db()
        
        # 解析日期
        try:
            flight_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        except ValueError:
            logger.error(f"日期格式錯誤: {start_date}")
            return {"error": "日期格式錯誤"}
        
        # 構建查詢
        try:
            # 查詢航班ID
            flights = db.query(Flight.flight_id).filter(
                Flight.departure_airport_id == departure_code,
                Flight.arrival_airport_id == arrival_code,
                func.date(Flight.scheduled_departure) == flight_date
            ).all()
            
            if not flights:
                return {
                    "route": f"{departure_code}-{arrival_code}",
                    "date": start_date,
                    "cabin_class": cabin_class,
                    "trends": {}
                }
            
            flight_ids = [f.flight_id for f in flights]
            
            # 查詢價格歷史
            history = db.query(
                TicketPrice.flight_id,
                TicketPrice.price_updated_at,
                TicketPrice.base_price
            ).filter(
                TicketPrice.flight_id.in_(flight_ids),
                TicketPrice.class_type == cabin_class,
                TicketPrice.price_updated_at >= datetime.now() - timedelta(days=days_before)
            ).order_by(
                TicketPrice.flight_id,
                TicketPrice.price_updated_at
            ).all()
            
            # 處理結果
            trends = {}
            for flight_id, updated_at, price in history:
                date_key = updated_at.strftime("%Y-%m-%d")
                if date_key not in trends:
                    trends[date_key] = []
                
                trends[date_key].append({
                    "flight_id": flight_id,
                    "price": price
                })
            
            # 計算每天的平均價格
            avg_trends = {}
            for date, prices in trends.items():
                avg_price = sum(p["price"] for p in prices) / len(prices)
                avg_trends[date] = round(avg_price, 2)
            
            return {
                "route": f"{departure_code}-{arrival_code}",
                "date": start_date,
                "cabin_class": cabin_class,
                "trends": avg_trends
            }
            
        except Exception as e:
            logger.error(f"獲取價格趨勢時出錯: {str(e)}")
            return {"error": f"查詢執行錯誤: {str(e)}"}
    
    @staticmethod
    async def get_route_stats(departure_code: str, arrival_code: str) -> Dict[str, Any]:
        """
        獲取航線統計信息
        
        Args:
            departure_code: 出發地IATA代碼
            arrival_code: 目的地IATA代碼
            
        Returns:
            Dict[str, Any]: 航線統計信息
        """
        # 獲取數據庫連接
        db = await get_db()
        
        try:
            # 查詢航線的航班數量
            flight_count = db.query(func.count(Flight.flight_id)).filter(
                Flight.departure_airport_id == departure_code,
                Flight.arrival_airport_id == arrival_code
            ).scalar()
            
            # 查詢航空公司分布
            airlines = db.query(
                Airline.airline_id,
                Airline.name,
                func.count(Flight.flight_id).label('flight_count')
            ).join(
                Flight, Flight.airline_id == Airline.airline_id
            ).filter(
                Flight.departure_airport_id == departure_code,
                Flight.arrival_airport_id == arrival_code
            ).group_by(
                Airline.airline_id, Airline.name
            ).all()
            
            airline_stats = [
                {
                    "airline_id": a.airline_id,
                    "name": a.name,
                    "flight_count": a.flight_count,
                    "percentage": round((a.flight_count / flight_count) * 100, 2) if flight_count else 0
                }
                for a in airlines
            ]
            
            # 查詢價格統計
            price_stats = db.query(
                func.min(TicketPrice.base_price).label('min_price'),
                func.max(TicketPrice.base_price).label('max_price'),
                func.avg(TicketPrice.base_price).label('avg_price')
            ).join(
                Flight, Flight.flight_id == TicketPrice.flight_id
            ).filter(
                Flight.departure_airport_id == departure_code,
                Flight.arrival_airport_id == arrival_code
            ).first()
            
            # 查詢飛行時間統計
            duration_stats = db.query(
                func.min(Flight.duration_minutes).label('min_duration'),
                func.max(Flight.duration_minutes).label('max_duration'),
                func.avg(Flight.duration_minutes).label('avg_duration')
            ).filter(
                Flight.departure_airport_id == departure_code,
                Flight.arrival_airport_id == arrival_code
            ).first()
            
            return {
                "route": f"{departure_code}-{arrival_code}",
                "flight_count": flight_count,
                "airlines": airline_stats,
                "price_stats": {
                    "min": price_stats.min_price if price_stats else None,
                    "max": price_stats.max_price if price_stats else None,
                    "avg": round(price_stats.avg_price, 2) if price_stats and price_stats.avg_price else None
                },
                "duration_stats": {
                    "min": duration_stats.min_duration if duration_stats else None,
                    "max": duration_stats.max_duration if duration_stats else None,
                    "avg": round(duration_stats.avg_duration, 2) if duration_stats and duration_stats.avg_duration else None
                }
            }
            
        except Exception as e:
            logger.error(f"獲取航線統計時出錯: {str(e)}")
            return {"error": f"查詢執行錯誤: {str(e)}"}
    
    @staticmethod
    async def get_available_airlines():
        """
        獲取所有可用的航空公司列表
        
        Returns:
            List[Dict[str, Any]]: 航空公司列表
        """
        db = await get_db()
        try:
            # 在查詢中包含 logo_path
            query = """
            SELECT 
                airline_id, 
                airline_id as iata_code, 
                name_zh, 
                name_en, 
                is_domestic,
                logo_path  -- 新增 logo_path
            FROM 
                airlines
            ORDER BY 
                name_zh
            """
            
            airlines = await db.fetch(query)
            result = []
            
            for airline in airlines:
                # 不再生成假的 logo_url，使用從數據庫讀取的 logo_path
                # logo_url = f"https://example.com/airlines/{airline['airline_id']}.png"
                
                result.append({
                    'airline_id': airline['airline_id'],
                    'iata_code': airline['iata_code'],
                    'name': airline['name_zh'], # 前端可能期望 'name'
                    'name_zh': airline['name_zh'], # 同時保留 name_zh
                    'name_en': airline['name_en'],
                    # 'logo_url': logo_url, # 移除舊的 logo_url
                    'logo_path': airline['logo_path'], # 添加 logo_path
                    'is_domestic': airline.get('is_domestic'), # 保留 is_domestic
                    'country': '台灣' if airline.get('is_domestic') else '國際' # 可以選擇性保留 country
                })
            
            return result
        finally:
            await release_db(db)
    
    @staticmethod
    async def get_taiwan_airports():
        """
        獲取台灣所有有航班的機場列表
        
        Returns:
            List[Dict[str, Any]]: 機場列表，只包含有航班的機場
        """
        db = await get_db()
        try:
            query = """
            SELECT DISTINCT
                a.airport_id, 
                a.airport_id as iata_code, 
                a.name_zh, 
                a.name_en, 
                a.city, 
                a.country
            FROM 
                airports a
            JOIN 
                flights f ON a.airport_id = f.departure_airport_id
            WHERE 
                a.country = 'Taiwan'
                AND f.scheduled_departure >= CURRENT_DATE
            ORDER BY 
                a.name_zh
            """
            
            airports = await db.fetch(query)
            result = []
            
            for airport in airports:
                result.append({
                    'airport_id': airport['airport_id'],
                    'iata_code': airport['iata_code'],
                    'name': airport['name_zh'],
                    'name_en': airport['name_en'],
                    'city': airport['city'],
                    'country': airport['country']
                })
            
            return result
        finally:
            await release_db(db)
    
    @staticmethod
    async def get_available_destinations(departure_iata, date_str=None): # 保留 date_str 參數以兼容 API，但不再使用
        """
        獲取從指定出發地可以到達的所有目的地機場 (查詢所有日期的航班記錄)
        
        Args:
            departure_iata (str): 出發地機場的IATA代碼
            date_str (str, optional): YYYY-MM-DD格式的日期。此參數被保留但不再使用。
            
        Returns:
            List[Dict[str, Any]]: 目的地機場列表，每個機場包含 id, code, name, city 字段
        """
        db = None
        try:
            db = await get_db()
            
            # **注意這裡的SQL語句**
            sql = """
            SELECT DISTINCT 
                a.airport_id, 
                a.name_zh, 
                a.name_en, 
                a.city, 
                a.country 
                -- 確保只選擇存在的列，移除任何對 iata_code 的潛在引用
            FROM 
                airports a
            JOIN 
                flights f ON a.airport_id = f.arrival_airport_id 
            WHERE 
                f.departure_airport_id = $1
            """
            params = [departure_iata]
            
            # **原本用於過濾日期的部分已被移除或註釋掉**
            
            logger.info(f"執行目的地查詢 (所有日期): {departure_iata}")
            
            results = await db.fetch(sql, *params)
            
            # 將 asyncpg Row 轉換為字典列表
            destinations = [dict(row) for row in results]
            
            logger.info(f"找到 {len(destinations)} 個從 {departure_iata} 出發的目的地")
            return destinations
            
        except Exception as e:
            logger.error(f"獲取可用目的地時出錯: {e}", exc_info=True)
            return [] # 返回空列表表示失敗
        finally:
            if db:
                await release_db(db)
    
    @staticmethod
    async def get_flight_details_by_id(flight_id: str) -> Optional[Dict[str, Any]]:
        """根據 Flight ID 獲取詳細的航班信息"""
        db = await get_db()
        try:
            logger.info(f"正在獲取航班 ID: {flight_id} 的詳細信息")

            # 查詢航班基本信息及關聯機場、航空公司，包含 logo_path
            query = """
            SELECT
                f.flight_id,
                f.flight_number,
                f.scheduled_departure,
                f.scheduled_arrival,
                al.is_domestic as airline_is_domestic,
                f.aircraft,
                f.departure_terminal as terminal,
                f.arrival_terminal as arrival_terminal,
                a_dep.airport_id as departure_id,
                a_dep.name_zh as departure_name,
                a_dep.city as departure_city,
                a_dep.country as departure_country,
                a_arr.airport_id as arrival_id,
                a_arr.name_zh as arrival_name,
                a_arr.city as arrival_city,
                a_arr.country as arrival_country,
                al.airline_id,
                al.name_zh as airline_name_zh,
                al.name_en as airline_name_en,
                al.logo_path as airline_logo_path
            FROM
                flights f
            JOIN
                airports a_dep ON f.departure_airport_id = a_dep.airport_id
            JOIN
                airports a_arr ON f.arrival_airport_id = a_arr.airport_id
            JOIN
                airlines al ON f.airline_id = al.airline_id
            WHERE
                f.flight_id = $1
            """

            flight_record = await db.fetchrow(query, flight_id)

            if not flight_record:
                logger.warning(f"未找到航班 ID: {flight_id}")
                return None

            # 查詢票價信息
            price_query = """
            SELECT
                class_type,
                base_price,
                available_seats,
                price_updated_at
            FROM
                ticket_prices
            WHERE
                flight_id = $1
            ORDER BY
                CASE class_type
                    WHEN '經濟' THEN 1
                    WHEN '商務' THEN 2
                    WHEN '頭等' THEN 3
                    ELSE 4
                END,
                base_price -- Added price sorting as secondary criteria
            """
            prices_records = await db.fetch(price_query, flight_id)

            prices = []
            for price in prices_records:
                prices.append({
                    'class_type': price['class_type'],
                    'price': float(price['base_price']) if price['base_price'] is not None else None,
                    'currency': 'TWD', # 假設貨幣單位
                    'available_seats': price['available_seats'],
                    'updated_at': price['price_updated_at'].isoformat() if price['price_updated_at'] else None
                })

            # 計算飛行時間
            duration_minutes = None
            try:
                dep_time = flight_record['scheduled_departure']
                arr_time = flight_record['scheduled_arrival']
                if dep_time and arr_time:
                    duration_minutes = int((arr_time - dep_time).total_seconds() / 60)
            except Exception as dur_e:
                logger.warning(f"計算航班 {flight_id} 飛行時間時出錯: {dur_e}")

            # 格式化結果 - 修正欄位使用並移除不存在的欄位對應
            result = {
                'flight_id': flight_record['flight_id'],
                'flight_number': flight_record['flight_number'],
                'airline': {
                    'id': flight_record['airline_id'],
                    'code': flight_record['airline_id'],
                    'name': flight_record['airline_name_zh'],
                    'logo_path': flight_record.get('airline_logo_path')
                },
                'departure': {
                    'airport_id': flight_record['departure_id'],
                    'code': flight_record['departure_id'],
                    'name': flight_record['departure_name'],
                    'city': flight_record['departure_city'],
                    'country': flight_record['departure_country'],
                    'scheduled_time': flight_record['scheduled_departure'].isoformat() if flight_record['scheduled_departure'] else None,
                    'actual_time': None, # 設為 None
                    'terminal': flight_record['terminal'],
                    'gate': None # 設為 None
                },
                'arrival': {
                    'airport_id': flight_record['arrival_id'],
                    'code': flight_record['arrival_id'],
                    'name': flight_record['arrival_name'],
                    'city': flight_record['arrival_city'],
                    'country': flight_record['arrival_country'],
                    'scheduled_time': flight_record['scheduled_arrival'].isoformat() if flight_record['scheduled_arrival'] else None,
                    'actual_time': None, # 設為 None
                    'terminal': flight_record['arrival_terminal'],
                    'gate': None # 設為 None
                },
                'status': None,
                'duration_minutes': duration_minutes,
                'aircraft': flight_record['aircraft'],
                'is_domestic': flight_record['airline_is_domestic'],
                'prices': prices
            }

            logger.info(f"成功獲取並格式化航班 {flight_id} 的詳細信息")
            return result

        except Exception as e:
            logger.error(f"獲取航班 {flight_id} 詳細信息時發生錯誤: {e}", exc_info=True)
            return None # 服務層錯誤，控制器應處理此 None 返回
        finally:
            await release_db(db)

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
        """搜索從台灣主要機場飛往指定目的地的航班"""
        db = await get_db()
        try:
            logger.info(f"搜索從台灣主要機場到 {arrival_iata} 在 {date_str} 的航班")
            # 解析日期
            try:
                flight_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                logger.error(f"日期格式錯誤: {date_str}")
                return []

            # 定義相關的台灣出發機場
            # 可以考慮從 constants 導入或配置
            relevant_taiwan_airports = ['TPE', 'TSA', 'KHH', 'RMQ', 'TNN']

            # 構建基礎查詢
            sql = """
            SELECT
                f.flight_id,
                f.flight_number,
                f.scheduled_departure,
                f.scheduled_arrival,
                al.is_domestic,
                a_dep.airport_id as departure_id,
                a_dep.name_zh as departure_name,
                a_dep.city as departure_city,
                a_arr.airport_id as arrival_id,
                a_arr.name_zh as arrival_name,
                a_arr.city as arrival_city,
                al.airline_id,
                al.name_zh as airline_name_zh,
                al.name_en as airline_name_en,
                al.logo_path as airline_logo_path
            FROM
                flights f
            JOIN
                airports a_dep ON f.departure_airport_id = a_dep.airport_id
            JOIN
                airports a_arr ON f.arrival_airport_id = a_arr.airport_id
            JOIN
                airlines al ON f.airline_id = al.airline_id
            WHERE
                a_arr.airport_id = $1
                AND a_dep.airport_id = ANY($2::text[]) -- Use ANY for array matching
                AND DATE(f.scheduled_departure) = $3
            """
            params = [arrival_iata, relevant_taiwan_airports, flight_date]
            param_index = 4

            # 添加航空公司過濾
            if airlines:
                placeholders = []
                for code in airlines:
                    placeholders.append(f"${param_index}")
                    params.append(code)
                    param_index += 1
                sql += f" AND al.airline_id IN ({', '.join(placeholders)})"

            # 注意：價格過濾需要在獲取票價後進行，或者修改查詢連接票價表
            # 暫時不在此主查詢中過濾價格

            # 排序 (暫時按計劃出發時間排序，價格排序在格式化後處理)
            sql += " ORDER BY f.scheduled_departure"

            # 執行查詢獲取航班基礎信息
            flight_records = await db.fetch(sql, *params)
            logger.info(f"從數據庫找到 {len(flight_records)} 個從台灣主要機場到 {arrival_iata} 的基礎航班記錄")

            if not flight_records:
                return []

            # 格式化航班並添加模擬價格 (或未來查詢真實價格)
            formatted_flights = await SearchService._format_flights(flight_records, class_type)

            # 應用價格過濾 (如果需要)
            if price_min is not None or price_max is not None:
                filtered_by_price = []
                for flight in formatted_flights:
                    price = flight.get('price', {}).get('amount')
                    if price is not None:
                        if (price_min is None or price >= price_min) and \
                           (price_max is None or price <= price_max):
                            filtered_by_price.append(flight)
                formatted_flights = filtered_by_price
                logger.info(f"價格過濾後剩餘 {len(formatted_flights)} 個航班")

            # 排序結果
            try:
                if sort_by == 'price':
                    formatted_flights.sort(key=lambda x: (x.get('price', {}).get('amount', float('inf')), x.get('departure', {}).get('time', '')))
                else: # 預設按時間排序 (因為 SQL 已排序，這裡可以省略，除非格式化改變了順序)
                    # formatted_flights.sort(key=lambda x: x.get('departure', {}).get('time', ''))
                    pass # Already sorted by departure time in SQL
            except Exception as sort_e:
                logger.error(f"排序台灣出發航班結果時出錯: {sort_e}")
                # 排序失敗，返回SQL排序的結果

            # 限制最終結果數量
            final_flights = formatted_flights[:max_results_total]

            logger.info(f"最終返回 {len(final_flights)} 個從台灣到 {arrival_iata} 的航班")
            return final_flights

        except Exception as e:
            logger.error(f"搜索從台灣出發航班時發生錯誤: {e}", exc_info=True)
            return [] # 返回空列表表示錯誤
        finally:
            await release_db(db) 