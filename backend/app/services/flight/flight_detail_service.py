"""
航班詳情服務 - 負責處理航班詳情查詢
"""
import logging
from datetime import datetime
from app.models.base import db
from app.models.flight import Flight
from flask import current_app

logger = logging.getLogger(__name__)

class FlightDetailService:
    """航班詳情服務類，提供航班詳情查詢功能"""
    
    def __init__(self, test_mode=False, flightstats_service=None, 
                 price_service=None, weather_service=None):
        """初始化航班詳情服務
        
        Args:
            test_mode (bool): 是否為測試模式，測試模式下返回模擬數據
            flightstats_service: FlightStats服務實例
            price_service: 價格服務實例
            weather_service: 天氣服務實例
        """
        self.test_mode = test_mode
        self.flightstats_service = flightstats_service
        self.price_service = price_service
        self.weather_service = weather_service
    
    def get_flight_details(self, flight_id=None, airline_code=None, flight_number=None, departure_date=None):
        """獲取航班詳情
        
        Args:
            flight_id (int, optional): 航班ID
            airline_code (str, optional): 航空公司代碼
            flight_number (str, optional): 航班號
            departure_date (str, optional): 出發日期，格式為 YYYY-MM-DD
            
        Returns:
            dict: 航班詳情
        """
        try:
            flight_data = None
            
            # 如果提供了航班ID，直接查詢
            if flight_id:
                if self.test_mode:
                    from app.utils.mock_data_generator import MockDataGenerator
                    mock_generator = MockDataGenerator()
                    flight_data = mock_generator.generate_flight_data(flight_id=flight_id)
                else:
                    # 從數據庫獲取航班信息
                    flight = Flight.query.get(flight_id)
                    if flight:
                        flight_data = flight.to_dict()
                    else:
                        logger.warning(f"未找到航班ID為 {flight_id} 的航班")
                        return {
                            'success': False,
                            'message': f"未找到航班ID為 {flight_id} 的航班"
                        }
            
            # 如果提供了航空公司代碼、航班號和日期，查詢特定航班
            elif airline_code and flight_number and departure_date:
                try:
                    dep_date = datetime.strptime(departure_date, '%Y-%m-%d')
                except ValueError:
                    logger.error("日期格式錯誤")
                    return {
                        'success': False,
                        'message': "日期格式錯誤，應為 YYYY-MM-DD"
                    }
                
                if self.test_mode:
                    from app.utils.mock_data_generator import MockDataGenerator
                    mock_generator = MockDataGenerator()
                    flight_data = mock_generator.generate_flight_data(
                        airline_code=airline_code, 
                        flight_number=flight_number,
                        departure_date=dep_date.strftime('%Y-%m-%d')
                    )
                else:
                    # 從外部API獲取航班數據
                    flight_status = self.flightstats_service.get_flight_status(
                        airline_code, flight_number, 
                        dep_date.year, dep_date.month, dep_date.day
                    )
                    
                    if flight_status.get('success'):
                        flight_data = flight_status.get('data', {}).get('flightStatuses', [])[0] if flight_status.get('data', {}).get('flightStatuses') else None
                    
                    if not flight_data:
                        logger.warning(f"未找到航班: {airline_code}{flight_number}, 日期: {departure_date}")
                        return {
                            'success': False,
                            'message': f"未找到航班: {airline_code}{flight_number}, 日期: {departure_date}"
                        }
            
            else:
                logger.error("獲取航班詳情時缺少必要參數")
                return {
                    'success': False,
                    'message': "缺少必要參數：需要提供航班ID或(航空公司代碼、航班號和出發日期)"
                }
            
            # 拓展航班數據
            if flight_data:
                # 獲取航班價格
                prices = self.price_service.fetch_ticket_prices(
                    flight_data.get('carrierFsCode', ''),
                    flight_data.get('flightNumber', ''),
                    flight_data.get('departureDate', {}).get('dateLocal', '').split('T')[0] if isinstance(flight_data.get('departureDate', {}), dict) else ''
                )
                
                if prices.get('success'):
                    flight_data['prices'] = prices.get('data', [])
                
                # 獲取出發地和目的地天氣
                if 'departureAirportFsCode' in flight_data and 'arrivalAirportFsCode' in flight_data:
                    # 出發地天氣
                    dep_weather = self.weather_service.get_airport_weather(
                        flight_data['departureAirportFsCode']
                    )
                    
                    # 目的地天氣
                    arr_weather = self.weather_service.get_airport_weather(
                        flight_data['arrivalAirportFsCode']
                    )
                    
                    flight_data['departure_weather'] = dep_weather.get('data') if dep_weather.get('success') else None
                    flight_data['arrival_weather'] = arr_weather.get('data') if arr_weather.get('success') else None
                
                # 獲取飛行狀態並生成描述
                flight_data['status_description'] = self._generate_flight_status(flight_data)
                
                return {
                    'success': True,
                    'data': flight_data
                }
            
            return {
                'success': False,
                'message': "無法獲取航班詳情"
            }
            
        except Exception as e:
            logger.error(f"獲取航班詳情時發生錯誤: {str(e)}")
            return {
                'success': False,
                'message': f"獲取航班詳情時發生錯誤: {str(e)}"
            }
    
    def _generate_flight_status(self, flight):
        """根據航班數據生成飛行狀態描述
        
        Args:
            flight (dict): 航班數據
            
        Returns:
            str: 飛行狀態描述
        """
        if not flight:
            return "未知"
        
        status = flight.get('status', '')
        
        # 狀態映射
        status_map = {
            'A': '在途中',
            'C': '已取消',
            'D': '已轉飛',
            'DN': '已降落',
            'L': '已降落',
            'NO': '未運營',
            'R': '已轉降',
            'S': '已排定',
            'U': '未知'
        }
        
        return status_map.get(status, "正常")
