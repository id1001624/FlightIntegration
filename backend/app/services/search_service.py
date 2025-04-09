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
            "outbound": outbound_results.get(cabin_class.lower().replace("艙", ""), outbound_results["economy"]),
            "all_cabins": {
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
        
        if inbound_results:
            result["inbound"] = inbound_results.get(cabin_class.lower().replace("艙", ""), inbound_results["economy"])
            result["all_cabins"]["return"] = {
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
            
        return result
    
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
            f.status,
            al.is_domestic,
            a_dep.airport_id as departure_id, 
            a_dep.name_zh as departure_name,
            a_dep.city as departure_city,
            a_arr.airport_id as arrival_id, 
            a_arr.name_zh as arrival_name,
            a_arr.city as arrival_city,
            al.airline_id, 
            al.name_zh as airline_name
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
        格式化航班列表為API響應格式，並生成模擬票價數據
        
        Args:
            flights: 航班列表
            cabin_class: 艙位類型
            
        Returns:
            List[Dict[str, Any]]: 格式化後的航班列表
        """
        import random
        formatted_flights = []
        
        # 定義可能的航班狀態
        possible_statuses = [
            'on_time',    # 準時
            'scheduled',  # 已排程
            'delayed',    # 延誤
            'in_air',     # 已起飛
            'arrived',    # 已抵達
            'cancelled'   # 取消
        ]
        # 加權分配，多數航班準時
        status_weights = [0.65, 0.15, 0.08, 0.05, 0.05, 0.02]
        
        for flight in flights:
            # 生成模擬票價數據
            base_price = None
            if cabin_class == "經濟":
                base_price = random.randint(8000, 15000)
            elif cabin_class == "商務":
                base_price = random.randint(20000, 30000)
            elif cabin_class == "頭等":
                base_price = random.randint(40000, 60000)
            else:
                base_price = random.randint(8000, 15000)
                
            # 計算飛行時間（分鐘）
            try:
                dep_time = flight["scheduled_departure"]
                arr_time = flight["scheduled_arrival"]
                duration_minutes = int((arr_time - dep_time).total_seconds() / 60)
            except:
                duration_minutes = random.randint(120, 360)  # 模擬2-6小時飛行時間
            
            # 如果沒有狀態或狀態為unknown，則生成隨機狀態
            status = flight.get("status", "unknown")
            if status is None or status.lower() == "unknown" or status == "":
                status = random.choices(possible_statuses, weights=status_weights, k=1)[0]
            
            # 格式化航班數據
            formatted_flight = {
                "flight_id": flight["flight_id"],
                "airline": {
                    "airline_id": flight["airline_id"],
                    "name": flight["airline_name"],
                    "logo_url": f"https://example.com/airlines/{flight['airline_id']}.png"
                },
                "flight_number": flight["flight_number"],
                "departure": {
                    "airport_id": flight["departure_id"],
                    "name": flight["departure_name"],
                    "city": flight["departure_city"],
                    "terminal": random.choice(["1", "2", "3"]),
                    "gate": f"{random.choice('ABCDE')}{random.randint(1, 20)}",
                    "time": flight["scheduled_departure"].isoformat()
                },
                "arrival": {
                    "airport_id": flight["arrival_id"],
                    "name": flight["arrival_name"],
                    "city": flight["arrival_city"],
                    "terminal": random.choice(["1", "2", "3"]),
                    "gate": f"{random.choice('ABCDE')}{random.randint(1, 20)}",
                    "time": flight["scheduled_arrival"].isoformat()
                },
                "duration_minutes": duration_minutes,
                "status": status,
                "price": {
                    "amount": base_price,
                    "currency": "TWD",
                    "cabin_class": cabin_class,
                    "available_seats": random.randint(5, 50)
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
            query = """
            SELECT 
                airline_id, 
                airline_id as iata_code, 
                name_zh, 
                name_en, 
                is_domestic
            FROM 
                airlines
            ORDER BY 
                name_zh
            """
            
            airlines = await db.fetch(query)
            result = []
            
            for airline in airlines:
                # 使用固定模板生成logo_url
                logo_url = f"https://example.com/airlines/{airline['airline_id']}.png"
                
                result.append({
                    'airline_id': airline['airline_id'],
                    'iata_code': airline['iata_code'],
                    'name': airline['name_zh'],
                    'name_en': airline['name_en'],
                    'logo_url': logo_url,
                    'country': '台灣' if airline.get('is_domestic') else '國際'
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
    async def get_available_destinations(departure_iata, date_str=None):
        """
        獲取從指定出發地可以到達的所有目的地
        
        Args:
            departure_iata: 出發地機場IATA代碼
            date_str: 可選，指定日期字符串 (YYYY-MM-DD)，如提供將只返回該日期有航班的目的地
            
        Returns:
            List[Dict[str, Any]]: 目的地列表
        """
        db = await get_db()
        try:
            params = [departure_iata]
            date_filter = ""
            
            if date_str:
                try:
                    flight_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                    date_filter = "AND DATE(f.scheduled_departure) = $2"
                    params.append(flight_date)
                except ValueError:
                    logger.error(f"日期格式錯誤: {date_str}")
            
            query = f"""
            SELECT DISTINCT 
                a.airport_id, 
                a.airport_id as iata_code, 
                a.name_zh, 
                a.name_en, 
                a.city, 
                a.country,
                COUNT(f.flight_id) as flight_count
            FROM 
                airports a
            JOIN 
                flights f ON a.airport_id = f.arrival_airport_id
            JOIN 
                airports dep ON f.departure_airport_id = dep.airport_id
            WHERE 
                dep.airport_id = $1
                AND f.scheduled_departure >= CURRENT_DATE
                {date_filter}
            GROUP BY
                a.airport_id, a.name_zh, a.name_en, a.city, a.country
            ORDER BY 
                a.country, a.city, a.name_zh
            """
            
            destinations = await db.fetch(query, *params)
            result = []
            
            for dest in destinations:
                result.append({
                    'airport_id': dest['airport_id'],
                    'iata_code': dest['iata_code'],
                    'name': dest['name_zh'],
                    'name_en': dest['name_en'],
                    'city': dest['city'],
                    'country': dest['country'],
                    'flight_count': dest['flight_count']
                })
            
            return result
        finally:
            await release_db(db) 