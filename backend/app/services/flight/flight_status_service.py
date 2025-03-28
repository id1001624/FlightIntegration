"""
航班狀態服務 - 負責處理航班狀態更新和查詢
"""
import logging
from datetime import datetime, timedelta
from sqlalchemy import and_
from app.models.base import db
from app.models.flight import Flight
from flask import current_app

logger = logging.getLogger(__name__)

class FlightStatusService:
    """航班狀態服務類，提供航班狀態更新和查詢功能"""
    
    def __init__(self, test_mode=False, flightstats_service=None):
        """初始化航班狀態服務
        
        Args:
            test_mode (bool): 是否為測試模式，測試模式下返回模擬數據
            flightstats_service: FlightStats服務實例
        """
        self.test_mode = test_mode
        self.flightstats_service = flightstats_service
    
    def update_flight_status(self):
        """更新所有航班狀態
        
        Returns:
            dict: 更新結果
        """
        try:
            # 獲取需要更新的航班（當日和未來24小時內的航班）
            now = datetime.utcnow()
            end_time = now + timedelta(hours=24)
            
            if self.test_mode:
                # 測試模式下，生成模擬數據
                from app.utils.mock_data_generator import MockDataGenerator
                mock_generator = MockDataGenerator()
                flights = mock_generator.generate_flight_list(count=10)
                updated_count = len(flights)
                
                logger.info(f"測試模式：已模擬更新 {updated_count} 個航班狀態")
                return {
                    'success': True,
                    'message': f"測試模式：已模擬更新 {updated_count} 個航班狀態",
                    'data': {
                        'updated_count': updated_count
                    }
                }
            
            # 從數據庫獲取需要更新的航班
            flights_to_update = Flight.query.filter(
                and_(
                    Flight.scheduled_departure_time >= now,
                    Flight.scheduled_departure_time <= end_time
                )
            ).all()
            
            if not flights_to_update:
                logger.info("沒有需要更新狀態的航班")
                return {
                    'success': True,
                    'message': "沒有需要更新狀態的航班",
                    'data': {
                        'updated_count': 0
                    }
                }
            
            updated_count = 0
            
            # 更新每個航班的狀態
            for flight in flights_to_update:
                try:
                    # 從外部API獲取最新狀態
                    flight_status = self.flightstats_service.get_flight_status(
                        flight.airline.iata_code,
                        flight.flight_number.replace(flight.airline.iata_code, ''),
                        flight.scheduled_departure_time.year,
                        flight.scheduled_departure_time.month,
                        flight.scheduled_departure_time.day
                    )
                    
                    if flight_status.get('success') and flight_status.get('data', {}).get('flightStatuses'):
                        # 獲取第一個匹配的航班狀態
                        status_data = flight_status.get('data', {}).get('flightStatuses')[0]
                        
                        # 更新航班資訊
                        flight.status = status_data.get('status', 'S')
                        flight.actual_departure_time = self._parse_datetime(status_data.get('operationalTimes', {}).get('actualGateDeparture', {}).get('dateLocal'))
                        flight.estimated_arrival_time = self._parse_datetime(status_data.get('operationalTimes', {}).get('estimatedGateArrival', {}).get('dateLocal'))
                        flight.actual_arrival_time = self._parse_datetime(status_data.get('operationalTimes', {}).get('actualGateArrival', {}).get('dateLocal'))
                        flight.departure_terminal = status_data.get('airportResources', {}).get('departureTerminal')
                        flight.departure_gate = status_data.get('airportResources', {}).get('departureGate')
                        flight.arrival_terminal = status_data.get('airportResources', {}).get('arrivalTerminal')
                        flight.arrival_gate = status_data.get('airportResources', {}).get('arrivalGate')
                        flight.delay_minutes = status_data.get('delays', {}).get('departureGateDelayMinutes', 0)
                        flight.last_updated = datetime.utcnow()
                        
                        # 保存更新
                        db.session.add(flight)
                        updated_count += 1
                        
                except Exception as e:
                    logger.error(f"更新航班 {flight.airline.iata_code}{flight.flight_number} 狀態時發生錯誤: {str(e)}")
                    continue
            
            # 提交所有更新
            try:
                db.session.commit()
                logger.info(f"已成功更新 {updated_count} 個航班狀態")
            except Exception as e:
                db.session.rollback()
                logger.error(f"提交航班狀態更新時發生錯誤: {str(e)}")
                return {
                    'success': False,
                    'message': f"提交航班狀態更新時發生錯誤: {str(e)}"
                }
            
            return {
                'success': True,
                'message': f"已成功更新 {updated_count} 個航班狀態",
                'data': {
                    'updated_count': updated_count
                }
            }
            
        except Exception as e:
            logger.error(f"更新航班狀態時發生錯誤: {str(e)}")
            return {
                'success': False,
                'message': f"更新航班狀態時發生錯誤: {str(e)}"
            }
    
    def get_flight_status(self, airline_code, flight_number, departure_date):
        """獲取特定航班的狀態
        
        Args:
            airline_code (str): 航空公司代碼
            flight_number (str): 航班號
            departure_date (str): 出發日期，格式為 YYYY-MM-DD
            
        Returns:
            dict: 航班狀態
        """
        try:
            # 驗證日期格式
            try:
                dep_date = datetime.strptime(departure_date, '%Y-%m-%d')
            except ValueError:
                logger.error("日期格式錯誤")
                return {
                    'success': False,
                    'message': "日期格式錯誤，應為 YYYY-MM-DD"
                }
            
            if self.test_mode:
                # 測試模式下，生成模擬數據
                from app.utils.mock_data_generator import MockDataGenerator
                mock_generator = MockDataGenerator()
                flight_data = mock_generator.generate_flight_data(
                    airline_code=airline_code,
                    flight_number=flight_number,
                    departure_date=departure_date
                )
                
                return {
                    'success': True,
                    'data': flight_data
                }
            
            # 從外部API獲取航班狀態
            flight_status = self.flightstats_service.get_flight_status(
                airline_code, flight_number,
                dep_date.year, dep_date.month, dep_date.day
            )
            
            if not flight_status.get('success'):
                logger.warning(f"無法獲取航班 {airline_code}{flight_number} 的狀態")
                return flight_status
            
            return flight_status
            
        except Exception as e:
            logger.error(f"獲取航班狀態時發生錯誤: {str(e)}")
            return {
                'success': False,
                'message': f"獲取航班狀態時發生錯誤: {str(e)}"
            }
    
    def _parse_datetime(self, datetime_str):
        """解析API返回的日期時間字符串
        
        Args:
            datetime_str (str): 日期時間字符串，格式為 YYYY-MM-DDTHH:MM:SS
            
        Returns:
            datetime|None: 解析後的datetime對象，若解析失敗則返回None
        """
        if not datetime_str:
            return None
            
        try:
            return datetime.strptime(datetime_str.split('T')[0], '%Y-%m-%d')
        except (ValueError, TypeError, IndexError):
            logger.error(f"無法解析日期時間: {datetime_str}")
            return None
