"""
航班緩存服務 - 負責處理航班數據的緩存功能
"""
import logging
from datetime import datetime, timedelta
from app.models.base import db
from app.models.flight import Flight
from flask import current_app

logger = logging.getLogger(__name__)

class FlightCacheService:
    """航班緩存服務類，提供航班數據緩存功能"""
    
    def __init__(self, test_mode=False):
        """初始化航班緩存服務
        
        Args:
            test_mode (bool): 是否為測試模式
        """
        self.test_mode = test_mode
        
    def check_cached_flights(self, departure_airport, arrival_airport, date, airline=None):
        """檢查緩存中是否有符合條件的航班數據
        
        Args:
            departure_airport (str): 出發機場代碼
            arrival_airport (str): 到達機場代碼
            date (str): 日期，格式為 YYYY-MM-DD
            airline (str, optional): 航空公司代碼
            
        Returns:
            list|None: 航班列表，若無緩存則返回None
        """
        try:
            # 將日期字符串轉為datetime對象
            flight_date = datetime.strptime(date, '%Y-%m-%d').date()
            
            # 設定緩存有效期（默認為12小時）
            cache_ttl = current_app.config.get('CACHE_TTL', 12)
            cache_cutoff_time = datetime.utcnow() - timedelta(hours=cache_ttl)
            
            # 基礎查詢條件
            query = Flight.query.filter(
                Flight.departure_airport.has(iata_code=departure_airport),
                Flight.arrival_airport.has(iata_code=arrival_airport),
                Flight.scheduled_departure_time >= datetime.combine(flight_date, datetime.min.time()),
                Flight.scheduled_departure_time < datetime.combine(flight_date + timedelta(days=1), datetime.min.time()),
                Flight.last_updated >= cache_cutoff_time
            )
            
            # 如果指定了航空公司，添加過濾條件
            if airline:
                query = query.filter(Flight.airline.has(iata_code=airline))
            
            # 獲取符合條件的航班
            cached_flights = query.all()
            
            if not cached_flights:
                logger.info(f"未找到符合條件的緩存航班: {departure_airport} -> {arrival_airport}, 日期: {date}")
                return None
            
            logger.info(f"從緩存中找到 {len(cached_flights)} 個航班: {departure_airport} -> {arrival_airport}, 日期: {date}")
            
            # 轉換為API格式
            return [flight.to_dict() for flight in cached_flights]
            
        except Exception as e:
            logger.error(f"檢查航班緩存時發生錯誤: {str(e)}")
            return None
    
    def save_flights_to_cache(self, flights_data, departure_airport, arrival_airport, date, airline=None):
        """將航班數據保存到緩存（數據庫）
        
        Args:
            flights_data (list): 航班數據列表
            departure_airport (str): 出發機場代碼
            arrival_airport (str): 到達機場代碼
            date (str): 日期，格式為 YYYY-MM-DD
            airline (str, optional): 航空公司代碼
            
        Returns:
            bool: 是否成功保存
        """
        if not flights_data:
            logger.warning("沒有航班數據需要保存到緩存")
            return False
        
        try:
            # 獲取機場和航空公司信息
            from app.models.airport import Airport
            from app.models.airline import Airline
            
            # 將日期字符串轉為datetime對象
            flight_date = datetime.strptime(date, '%Y-%m-%d').date()
            
            # 獲取或創建機場和航空公司對象
            departure_airport_obj = Airport.get_by_iata(departure_airport)
            arrival_airport_obj = Airport.get_by_iata(arrival_airport)
            
            if not departure_airport_obj or not arrival_airport_obj:
                logger.error(f"無法找到機場信息: 出發 {departure_airport}, 到達 {arrival_airport}")
                return False
            
            # 遍歷航班數據並保存
            for flight_data in flights_data:
                try:
                    # 獲取航空公司
                    airline_code = flight_data.get('AirlineID') or airline
                    if not airline_code:
                        logger.warning("缺少航空公司代碼，無法保存航班數據")
                        continue
                    
                    airline_obj = Airline.get_by_iata(airline_code)
                    if not airline_obj:
                        logger.warning(f"無法找到航空公司: {airline_code}")
                        continue
                    
                    # 獲取或創建航班對象
                    flight_number = flight_data.get('FlightNumber')
                    scheduled_departure_time = datetime.strptime(
                        flight_data.get('ScheduleDepartureTime').split('T')[0], 
                        '%Y-%m-%d'
                    )
                    
                    existing_flight = Flight.query.filter(
                        Flight.airline_id == airline_obj.airline_id,
                        Flight.flight_number == flight_number,
                        Flight.scheduled_departure_time == scheduled_departure_time
                    ).first()
                    
                    if existing_flight:
                        # 更新現有航班
                        flight = existing_flight
                    else:
                        # 創建新航班
                        flight = Flight(
                            airline_id=airline_obj.airline_id,
                            flight_number=flight_number,
                            departure_airport_id=departure_airport_obj.airport_id,
                            arrival_airport_id=arrival_airport_obj.airport_id
                        )
                    
                    # 更新航班信息
                    flight.scheduled_departure_time = datetime.strptime(
                        flight_data.get('ScheduleDepartureTime'), 
                        '%Y-%m-%dT%H:%M:%S'
                    ) if 'ScheduleDepartureTime' in flight_data else None
                    
                    flight.scheduled_arrival_time = datetime.strptime(
                        flight_data.get('ScheduleArrivalTime'), 
                        '%Y-%m-%dT%H:%M:%S'
                    ) if 'ScheduleArrivalTime' in flight_data else None
                    
                    flight.status = flight_data.get('FlightStatus', 'S')
                    flight.aircraft_type = flight_data.get('AircraftTypeName')
                    flight.departure_terminal = flight_data.get('DepartureTerminal')
                    flight.departure_gate = flight_data.get('DepartureGate')
                    flight.arrival_terminal = flight_data.get('ArrivalTerminal')
                    flight.arrival_gate = flight_data.get('ArrivalGate')
                    flight.last_updated = datetime.utcnow()
                    
                    # 保存到數據庫
                    db.session.add(flight)
                    
                except Exception as e:
                    logger.error(f"保存航班數據到緩存時發生錯誤: {str(e)}")
                    continue
            
            # 提交事務
            try:
                db.session.commit()
                logger.info(f"已成功將 {len(flights_data)} 個航班數據保存到緩存")
                return True
            except Exception as e:
                db.session.rollback()
                logger.error(f"提交航班數據到緩存時發生錯誤: {str(e)}")
                return False
                
        except Exception as e:
            logger.error(f"保存航班數據到緩存時發生錯誤: {str(e)}")
            return False
    
    def clear_cache(self, older_than_hours=None):
        """清除緩存
        
        Args:
            older_than_hours (int, optional): 刪除多少小時前的緩存，默認為所有
            
        Returns:
            dict: 清除結果
        """
        try:
            if older_than_hours:
                # 清除指定時間之前的緩存
                cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)
                flights = Flight.query.filter(Flight.last_updated < cutoff_time).all()
                
                for flight in flights:
                    flight.last_updated = None
                    db.session.add(flight)
                
                db.session.commit()
                return {
                    'success': True,
                    'message': f"已清除 {len(flights)} 個{older_than_hours}小時前的航班緩存"
                }
            else:
                # 清除所有緩存
                flights = Flight.query.all()
                
                for flight in flights:
                    flight.last_updated = None
                    db.session.add(flight)
                
                db.session.commit()
                return {
                    'success': True,
                    'message': f"已清除所有航班緩存 ({len(flights)} 個)"
                }
                
        except Exception as e:
            db.session.rollback()
            logger.error(f"清除緩存時發生錯誤: {str(e)}")
            return {
                'success': False,
                'message': f"清除緩存時發生錯誤: {str(e)}"
            }
