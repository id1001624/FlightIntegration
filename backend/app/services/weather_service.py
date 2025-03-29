"""
天氣服務模組 - 處理天氣數據獲取和預測
"""
import logging
from datetime import datetime, timedelta
from flask import current_app
from sqlalchemy import func
import random

from app.models import db, Airport, Weather
from app.services.tdx_service import TDXService
from app.utils.mock_data_generator import MockDataGenerator

# 設置日誌
logger = logging.getLogger(__name__)

class WeatherService:
    """
    天氣服務類 - 處理天氣相關功能
    """
    
    def __init__(self, test_mode=False, tdx_service=None):
        """
        初始化天氣服務
        
        Args:
            test_mode (bool): 是否為測試模式
            tdx_service (TDXService, optional): TDX服務實例
        """
        self.test_mode = test_mode
        self.tdx_service = tdx_service or TDXService(test_mode=test_mode)
    
    def get_airport_weather(self, airport_code, date=None):
        """
        獲取機場天氣數據
        
        Args:
            airport_code (str): 機場IATA代碼
            date (str, optional): 日期，格式為YYYY-MM-DD，若不提供則獲取今天的數據
            
        Returns:
            dict: 天氣數據
        """
        try:
            # 查詢機場資訊
            airport = Airport.query.filter_by(iata_code=airport_code).first()
            if not airport:
                return {
                    'success': False,
                    'message': f'找不到機場: {airport_code}'
                }
            
            # 處理日期
            if date:
                target_date = datetime.strptime(date, '%Y-%m-%d').date()
            else:
                target_date = datetime.now().date()
            
            # 查詢資料庫中是否已有天氣數據
            weather = Weather.query.filter_by(
                airport_id=airport.id,
                forecast_date=target_date,
                is_test_data=self.test_mode
            ).first()
            
            if weather:
                return {
                    'success': True,
                    'data': weather.to_dict()
                }
            
            # 從TDX API獲取數據
            if self.test_mode:
                # 測試模式下生成模擬數據
                weather_data = self._generate_mock_weather(airport, target_date)
            else:
                # 真實模式下從API獲取
                result = self.tdx_service.get_city_weather(airport.city)
                if not result['success']:
                    return result
                
                # 處理API回應
                weather_data = self._process_weather_data(result['data'], airport, target_date)
            
            # 保存到資料庫
            new_weather = Weather(
                airport_id=airport.id,
                city=weather_data.get('city'),
                forecast_date=target_date,
                weather_description=weather_data.get('weather_description'),
                temperature=weather_data.get('temperature'),
                humidity=weather_data.get('humidity'),
                wind_speed=weather_data.get('wind_speed'),
                wind_direction=weather_data.get('wind_direction'),
                precipitation=weather_data.get('precipitation'),
                visibility=weather_data.get('visibility'),
                pressure=weather_data.get('pressure'),
                data_source=weather_data.get('data_source', 'TDX'),
                raw_data=weather_data.get('raw_data'),
                is_test_data=self.test_mode
            )
            db.session.add(new_weather)
            db.session.commit()
            
            return {
                'success': True,
                'data': new_weather.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"獲取機場天氣時發生錯誤: {e}")
            return {
                'success': False,
                'message': f'獲取機場天氣時發生錯誤: {str(e)}'
            }
    
    def get_forecast(self, airport_code, days=7):
        """
        獲取未來天氣預報
        
        Args:
            airport_code (str): 機場IATA代碼
            days (int, optional): 獲取未來幾天的預報
            
        Returns:
            dict: 天氣預報數據
        """
        try:
            # 查詢機場資訊
            airport = Airport.query.filter_by(iata_code=airport_code).first()
            if not airport:
                return {
                    'success': False,
                    'message': f'找不到機場: {airport_code}'
                }
            
            # 計算日期範圍
            today = datetime.now().date()
            forecast_days = [today + timedelta(days=i) for i in range(days)]
            
            forecast_data = []
            for forecast_date in forecast_days:
                # 查詢資料庫中是否已有天氣數據
                weather = Weather.query.filter_by(
                    airport_id=airport.id,
                    forecast_date=forecast_date,
                    is_test_data=self.test_mode
                ).first()
                
                if weather:
                    forecast_data.append(weather.to_dict())
                else:
                    # 生成新的預報數據
                    if self.test_mode:
                        weather_data = self._generate_mock_weather(airport, forecast_date)
                    else:
                        # 實際情況下應從API獲取
                        result = self.tdx_service.get_weather_forecast(airport.city, forecast_date.strftime('%Y-%m-%d'))
                        if not result['success']:
                            # 如果API失敗，使用模擬數據代替
                            weather_data = self._generate_mock_weather(airport, forecast_date)
                        else:
                            weather_data = self._process_weather_data(result['data'], airport, forecast_date)
                    
                    # 保存到資料庫
                    new_weather = Weather(
                        airport_id=airport.id,
                        city=weather_data.get('city'),
                        forecast_date=forecast_date,
                        weather_description=weather_data.get('weather_description'),
                        temperature=weather_data.get('temperature'),
                        humidity=weather_data.get('humidity'),
                        wind_speed=weather_data.get('wind_speed'),
                        wind_direction=weather_data.get('wind_direction'),
                        precipitation=weather_data.get('precipitation'),
                        visibility=weather_data.get('visibility'),
                        pressure=weather_data.get('pressure'),
                        data_source=weather_data.get('data_source', 'TDX'),
                        raw_data=weather_data.get('raw_data'),
                        is_test_data=self.test_mode
                    )
                    db.session.add(new_weather)
                    forecast_data.append(new_weather.to_dict())
            
            db.session.commit()
            
            return {
                'success': True,
                'data': forecast_data
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"獲取天氣預報時發生錯誤: {e}")
            return {
                'success': False,
                'message': f'獲取天氣預報時發生錯誤: {str(e)}'
            }
    
    def sync_weather_data(self, days=3):
        """
        同步未來幾天的天氣數據到資料庫
        
        Args:
            days (int): 同步未來幾天的數據
            
        Returns:
            dict: 同步結果
        """
        try:
            # 獲取所有機場
            airports = Airport.query.all()
            if not airports:
                return {
                    'success': False,
                    'message': '未找到任何機場'
                }
            
            # 計算日期範圍
            today = datetime.now().date()
            forecast_days = [today + timedelta(days=i) for i in range(days)]
            
            sync_count = 0
            for airport in airports:
                for forecast_date in forecast_days:
                    # 檢查是否已有數據
                    existing_weather = Weather.query.filter_by(
                        airport_id=airport.id,
                        forecast_date=forecast_date,
                        is_test_data=self.test_mode
                    ).first()
                    
                    if existing_weather:
                        continue
                    
                    # 生成/獲取天氣數據
                    if self.test_mode:
                        weather_data = self._generate_mock_weather(airport, forecast_date)
                    else:
                        # 從API獲取數據
                        result = self.tdx_service.get_weather_forecast(airport.city, forecast_date.strftime('%Y-%m-%d'))
                        if not result['success']:
                            continue
                        
                        weather_data = self._process_weather_data(result['data'], airport, forecast_date)
                    
                    # 保存到資料庫
                    new_weather = Weather(
                        airport_id=airport.id,
                        city=weather_data.get('city'),
                        forecast_date=forecast_date,
                        weather_description=weather_data.get('weather_description'),
                        temperature=weather_data.get('temperature'),
                        humidity=weather_data.get('humidity'),
                        wind_speed=weather_data.get('wind_speed'),
                        wind_direction=weather_data.get('wind_direction'),
                        precipitation=weather_data.get('precipitation'),
                        visibility=weather_data.get('visibility'),
                        pressure=weather_data.get('pressure'),
                        data_source=weather_data.get('data_source', 'TDX'),
                        raw_data=weather_data.get('raw_data'),
                        is_test_data=self.test_mode
                    )
                    db.session.add(new_weather)
                    sync_count += 1
            
            db.session.commit()
            
            return {
                'success': True,
                'message': f'已同步 {sync_count} 筆天氣數據'
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"同步天氣數據時發生錯誤: {e}")
            return {
                'success': False,
                'message': f'同步天氣數據時發生錯誤: {str(e)}'
            }
    
    def _generate_mock_weather(self, airport, date):
        """
        生成模擬天氣數據
        
        Args:
            airport (Airport): 機場對象
            date (date): 日期
            
        Returns:
            dict: 天氣數據
        """
        # 使用模擬數據生成器生成數據
        mock_data = MockDataGenerator.generate_weather_data(airport.iata_code, date.strftime('%Y-%m-%d'))
        
        return {
            'city': airport.city,
            'weather_description': mock_data['weather_condition'],
            'temperature': mock_data['temperature'],
            'humidity': mock_data['humidity'],
            'wind_speed': mock_data['wind_speed'],
            'wind_direction': random.choice(['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']),
            'precipitation': mock_data['precipitation'],
            'visibility': random.randint(5, 20),
            'pressure': random.randint(990, 1030),
            'data_source': 'Mock',
            'raw_data': str(mock_data)
        }
    
    def _process_weather_data(self, api_data, airport, date):
        """
        處理API返回的天氣數據
        
        Args:
            api_data (dict): API返回的數據
            airport (Airport): 機場對象
            date (date): 日期
            
        Returns:
            dict: 處理後的天氣數據
        """
        # 如果API數據不符合預期格式，則生成模擬數據代替
        if not api_data:
            return self._generate_mock_weather(airport, date)
        
        try:
            # 處理API數據
            # 實際實現取決於TDX API返回的格式
            weather_desc = api_data.get('WeatherDescription', '未知')
            temperature = api_data.get('Temperature', {}).get('Value', 25)
            humidity = api_data.get('RelativeHumidity', 80)
            wind_speed = api_data.get('WindSpeed', 5)
            wind_direction = api_data.get('WindDirection', 'N')
            precipitation = api_data.get('Precipitation', 0)
            
            return {
                'city': airport.city,
                'weather_description': weather_desc,
                'temperature': temperature,
                'humidity': humidity,
                'wind_speed': wind_speed,
                'wind_direction': wind_direction,
                'precipitation': precipitation,
                'visibility': api_data.get('Visibility', 10),
                'pressure': api_data.get('AirPressure', 1013),
                'data_source': 'TDX',
                'raw_data': str(api_data)
            }
        except Exception as e:
            logger.error(f"處理天氣數據時發生錯誤: {e}")
            return self._generate_mock_weather(airport, date)