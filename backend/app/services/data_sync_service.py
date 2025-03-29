"""
數據同步服務模組 - 負責同步外部數據到本地資料庫
"""
import logging
from datetime import datetime, timedelta
from flask import current_app
from sqlalchemy.exc import SQLAlchemyError

from app.models import db, Airport, Airline, Flight, Weather
from app.services.tdx_service import TDXService
from app.services.flightstats_service import FlightStatsService
from app.services.auth_service import AuthService

# 設置日誌
logger = logging.getLogger(__name__)

class DataSyncService:
    """
    數據同步服務類 - 負責從TDX API同步數據到系統資料庫
    """
    
    def __init__(self, test_mode=False):
        """
        初始化數據同步服務
        
        Args:
            test_mode (bool): 是否為測試模式
        """
        self.test_mode = test_mode
        self.tdx_service = TDXService(test_mode=test_mode)
        self.flightstats_service = FlightStatsService(test_mode=test_mode)
        self.auth_service = AuthService(test_mode=test_mode)
    
    def sync_all_data(self):
        """
        同步所有數據（機場、航空公司、航班）
        
        Returns:
            dict: 同步結果
        """
        try:
            # 同步機場數據
            airports_result = self.sync_airports()
            if not airports_result['success']:
                return airports_result
            
            # 同步航空公司數據
            airlines_result = self.sync_airlines()
            if not airlines_result['success']:
                return airlines_result
            
            # 同步航班數據
            flights_result = self.sync_flights()
            
            # 同步航班歷史延誤數據
            delays_result = self.sync_flight_delays()
            
            # 返回整體結果
            return {
                'success': flights_result['success'],
                'message': '資料同步完成',
                'details': {
                    'airports': airports_result['message'],
                    'airlines': airlines_result['message'],
                    'flights': flights_result['message'],
                    'delays': delays_result['message'] if 'message' in delays_result else 'N/A'
                }
            }
            
        except Exception as e:
            logger.error(f"同步所有數據時發生錯誤: {e}")
            return {
                'success': False,
                'message': f'同步所有數據時發生錯誤: {str(e)}'
            }
    
    def sync_airports(self):
        """
        同步機場數據
        
        Returns:
            dict: 同步結果
        """
        try:
            # 從TDX獲取機場數據
            airports_data = self.tdx_service.get_airport_info()
            
            if not airports_data['success']:
                return airports_data
            
            # 更新或新增機場數據
            sync_count = 0
            for airport_data in airports_data['data']:
                airport_id = airport_data.get('AirportID')
                
                # 檢查機場是否已存在
                airport = Airport.query.filter_by(iata_code=airport_id).first()
                
                if not airport:
                    # 新增機場
                    airport = Airport(
                        iata_code=airport_id,
                        icao_code=airport_data.get('AirportCode'),
                        name_zh=airport_data.get('AirportName', {}).get('Zh_tw'),
                        name_en=airport_data.get('AirportName', {}).get('En'),
                        city=airport_data.get('CityName', {}).get('Zh_tw'),
                        city_en=airport_data.get('CityName', {}).get('En'),
                        country=airport_data.get('CountryName', {}).get('Zh_tw'),
                        country_code=airport_data.get('CountryCode'),
                        timezone=None,  # TDX API沒提供時區
                        latitude=airport_data.get('PositionLat'),
                        longitude=airport_data.get('PositionLon'),
                        is_test_data=self.test_mode
                    )
                    db.session.add(airport)
                    sync_count += 1
                else:
                    # 更新機場
                    airport.icao_code = airport_data.get('AirportCode')
                    airport.name_zh = airport_data.get('AirportName', {}).get('Zh_tw')
                    airport.name_en = airport_data.get('AirportName', {}).get('En')
                    airport.city = airport_data.get('CityName', {}).get('Zh_tw')
                    airport.city_en = airport_data.get('CityName', {}).get('En')
                    airport.country = airport_data.get('CountryName', {}).get('Zh_tw')
                    airport.country_code = airport_data.get('CountryCode')
                    airport.latitude = airport_data.get('PositionLat')
                    airport.longitude = airport_data.get('PositionLon')
                    airport.is_test_data = self.test_mode
                    sync_count += 1
            
            # 提交變更
            db.session.commit()
            
            return {
                'success': True,
                'message': f'成功同步 {sync_count} 筆機場資料'
            }
            
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"同步機場數據時發生資料庫錯誤: {e}")
            return {
                'success': False,
                'message': f'同步機場數據時發生資料庫錯誤: {str(e)}'
            }
        except Exception as e:
            logger.error(f"同步機場數據時發生錯誤: {e}")
            return {
                'success': False,
                'message': f'同步機場數據時發生錯誤: {str(e)}'
            }
    
    def sync_airlines(self):
        """
        同步航空公司數據
        
        Returns:
            dict: 同步結果
        """
        try:
            # 從TDX獲取航空公司數據
            airlines_data = self.tdx_service.get_airline_info()
            
            if not airlines_data['success']:
                return airlines_data
            
            # 更新或新增航空公司數據
            sync_count = 0
            for airline_data in airlines_data['data']:
                airline_id = airline_data.get('AirlineID')
                
                # 檢查航空公司是否已存在
                airline = Airline.query.filter_by(iata_code=airline_id).first()
                
                if not airline:
                    # 新增航空公司
                    airline = Airline(
                        iata_code=airline_id,
                        icao_code=None,  # TDX API沒提供ICAO代碼
                        name_zh=airline_data.get('AirlineName', {}).get('Zh_tw'),
                        name_en=airline_data.get('AirlineName', {}).get('En'),
                        country=None,
                        website=None,
                        is_test_data=self.test_mode
                    )
                    db.session.add(airline)
                    sync_count += 1
                else:
                    # 更新航空公司
                    airline.name_zh = airline_data.get('AirlineName', {}).get('Zh_tw')
                    airline.name_en = airline_data.get('AirlineName', {}).get('En')
                    airline.is_test_data = self.test_mode
                    sync_count += 1
            
            # 提交變更
            db.session.commit()
            
            return {
                'success': True,
                'message': f'成功同步 {sync_count} 筆航空公司資料'
            }
            
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"同步航空公司數據時發生資料庫錯誤: {e}")
            return {
                'success': False,
                'message': f'同步航空公司數據時發生資料庫錯誤: {str(e)}'
            }
        except Exception as e:
            logger.error(f"同步航空公司數據時發生錯誤: {e}")
            return {
                'success': False,
                'message': f'同步航空公司數據時發生錯誤: {str(e)}'
            }
    
    def sync_flights(self):
        """
        同步航班數據
        
        Returns:
            dict: 同步結果
        """
        try:
            # 取得今天的日期
            today = datetime.now().date()
            
            # 同步TPE(桃園機場)出發的航班
            tpe_flights = self.tdx_service.get_airport_flights("TPE", "Departure")
            
            # 同步TSA(松山機場)出發的航班
            tsa_flights = self.tdx_service.get_airport_flights("TSA", "Departure")
            
            # 同步KHH(高雄機場)出發的航班
            khh_flights = self.tdx_service.get_airport_flights("KHH", "Departure")
            
            # 合併所有航班資料
            all_flights = []
            
            if tpe_flights['success']:
                all_flights.extend(tpe_flights['data'])
            if tsa_flights['success']:
                all_flights.extend(tsa_flights['data'])
            if khh_flights['success']:
                all_flights.extend(khh_flights['data'])
            
            # 如果沒有取得任何航班資料
            if not all_flights:
                return {
                    'success': False,
                    'message': '無法取得航班資料'
                }
            
            # 處理航班資料
            sync_count = 0
            for flight_data in all_flights:
                # 提取必要資訊
                flight_id = flight_data.get('FlightID')
                airline_id = flight_data.get('AirlineID')
                flight_number = flight_data.get('FlightNumber')
                dep_airport_id = flight_data.get('DepartureAirportID')
                arr_airport_id = flight_data.get('ArrivalAirportID')
                
                # 檢查必要資訊是否存在
                if not all([flight_id, airline_id, flight_number, dep_airport_id, arr_airport_id]):
                    continue
                
                # 取得關聯資料
                airline = Airline.query.filter_by(iata_code=airline_id).first()
                dep_airport = Airport.query.filter_by(iata_code=dep_airport_id).first()
                arr_airport = Airport.query.filter_by(iata_code=arr_airport_id).first()
                
                if not all([airline, dep_airport, arr_airport]):
                    continue
                
                # 處理日期時間
                dep_time_str = flight_data.get('ScheduleDepartureTime')
                arr_time_str = flight_data.get('ScheduleArrivalTime')
                
                if not dep_time_str or not arr_time_str:
                    continue
                
                dep_time = datetime.strptime(dep_time_str, '%Y-%m-%dT%H:%M:%S')
                arr_time = datetime.strptime(arr_time_str, '%Y-%m-%dT%H:%M:%S')
                
                # 處理實際出發/抵達時間
                actual_dep_time = None
                if flight_data.get('ActualDepartureTime'):
                    actual_dep_time = datetime.strptime(flight_data.get('ActualDepartureTime'), '%Y-%m-%dT%H:%M:%S')
                
                actual_arr_time = None
                if flight_data.get('ActualArrivalTime'):
                    actual_arr_time = datetime.strptime(flight_data.get('ActualArrivalTime'), '%Y-%m-%dT%H:%M:%S')
                
                # 處理航班狀態
                status = flight_data.get('FlightStatusCode', 'A')  # 預設為A(正常)
                status_desc = flight_data.get('FlightStatus', '正常')
                
                # 處理航廈和登機門
                terminal = flight_data.get('Terminal')
                gate = flight_data.get('Gate')
                
                # 檢查航班是否已存在
                flight = Flight.query.filter_by(flight_id=flight_id).first()
                
                if not flight:
                    # 創建新航班
                    flight = Flight(
                        flight_id=flight_id,
                        airline_id=airline.id,
                        flight_number=flight_number,
                        departure_airport_id=dep_airport.id,
                        arrival_airport_id=arr_airport.id,
                        scheduled_departure_time=dep_time,
                        scheduled_arrival_time=arr_time,
                        actual_departure_time=actual_dep_time,
                        actual_arrival_time=actual_arr_time,
                        status=status,
                        status_description=status_desc,
                        terminal=terminal,
                        gate=gate,
                        is_direct_flight=True,  # 假設直飛
                        aircraft_type=None,
                        is_test_data=self.test_mode
                    )
                    db.session.add(flight)
                    sync_count += 1
                else:
                    # 更新現有航班
                    flight.airline_id = airline.id
                    flight.flight_number = flight_number
                    flight.departure_airport_id = dep_airport.id
                    flight.arrival_airport_id = arr_airport.id
                    flight.scheduled_departure_time = dep_time
                    flight.scheduled_arrival_time = arr_time
                    flight.actual_departure_time = actual_dep_time
                    flight.actual_arrival_time = actual_arr_time
                    flight.status = status
                    flight.status_description = status_desc
                    flight.terminal = terminal
                    flight.gate = gate
                    flight.is_test_data = self.test_mode
                    sync_count += 1
            
            # 提交變更
            db.session.commit()
            
            return {
                'success': True,
                'message': f'成功同步 {sync_count} 筆航班資料'
            }
            
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"同步航班數據時發生資料庫錯誤: {e}")
            return {
                'success': False,
                'message': f'同步航班數據時發生資料庫錯誤: {str(e)}'
            }
        except Exception as e:
            logger.error(f"同步航班數據時發生錯誤: {e}")
            return {
                'success': False,
                'message': f'同步航班數據時發生錯誤: {str(e)}'
            }
    
    def sync_flight_delays(self):
        """
        同步航班歷史延誤數據（使用FlightStats API）
        
        Returns:
            dict: 同步結果
        """
        if self.test_mode:
            return {
                'success': True,
                'message': '測試模式下使用模擬數據，不進行實際同步'
            }
        
        try:
            # 獲取主要航空公司列表
            airlines = Airline.query.all()
            
            # 獲取當前年月
            current_date = datetime.now()
            year = current_date.year
            month = current_date.month
            
            sync_count = 0
            
            # 為每個航空公司的主要航線獲取延誤數據
            for airline in airlines:
                # 獲取該航空公司的航班
                flights = Flight.query.filter_by(
                    airline_id=airline.id
                ).limit(10).all()  # 限制每家航空公司處理10個航班
                
                for flight in flights:
                    # 獲取歷史延誤數據
                    delay_result = self.flightstats_service.get_historical_delays(
                        airline.iata_code, 
                        flight.flight_number, 
                        year, 
                        month
                    )
                    
                    if delay_result['success']:
                        # 更新航班歷史延誤信息
                        delay_data = delay_result['data'].get('flightDelays', {})
                        
                        # 這裡可以根據你的數據模型進行適當的更新
                        # 例如，如果你有一個專門存儲延誤統計的表，可以在這裡更新
                        # 或者直接更新Flight表中的相關字段
                        
                        # 假設Flight模型有延誤統計欄位
                        flight.average_delay = delay_data.get('averageDelayMinutes')
                        flight.on_time_percent = delay_data.get('onTimePercent')
                        flight.canceled_percent = delay_data.get('canceledPercent')
                        
                        sync_count += 1
            
            # 提交變更
            db.session.commit()
            
            return {
                'success': True,
                'message': f'成功同步 {sync_count} 筆航班延誤資料'
            }
            
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"同步航班延誤數據時發生資料庫錯誤: {e}")
            return {
                'success': False,
                'message': f'同步航班延誤數據時發生資料庫錯誤: {str(e)}'
            }
        except Exception as e:
            logger.error(f"同步航班延誤數據時發生錯誤: {e}")
            return {
                'success': False,
                'message': f'同步航班延誤數據時發生錯誤: {str(e)}'
            }
    
    def test_tdx_connection(self):
        """
        測試TDX API連線
        
        Returns:
            dict: 測試結果
        """
        try:
            # 使用TDX服務測試連線
            result = self.tdx_service.get_airport_flights(limit=1)
            
            if result['success']:
                return {
                    'success': True,
                    'message': 'TDX API連線正常',
                    'data': result['data'][:1] if result['data'] else []  # 只返回第一筆資料作為範例
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"測試TDX連線時發生錯誤: {e}")
            return {
                'success': False,
                'message': f'測試TDX連線時發生錯誤: {str(e)}'
            }
    
    def test_flightstats_connection(self):
        """
        測試FlightStats API連線
        
        Returns:
            dict: 測試結果
        """
        try:
            # 使用FlightStats服務測試連線
            current_date = datetime.now()
            result = self.flightstats_service.get_flight_status(
                "CI", "123", 
                current_date.year, 
                current_date.month, 
                current_date.day
            )
            
            if result['success']:
                return {
                    'success': True,
                    'message': 'FlightStats API連線正常',
                    'data': result['data'] if 'data' in result else {}
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"測試FlightStats連線時發生錯誤: {e}")
            return {
                'success': False,
                'message': f'測試FlightStats連線時發生錯誤: {str(e)}'
            }