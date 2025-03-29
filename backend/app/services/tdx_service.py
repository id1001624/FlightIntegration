"""
TDX API服務模組 - 處理TDX平台API的調用
"""
import logging
from flask import current_app
import json

from app.utils.api_client import APIClient
from app.services.auth_service import AuthService
from app.utils.mock_data_generator import MockDataGenerator

# 設置日誌
logger = logging.getLogger(__name__)

class TDXService:
    """
    TDX API服務類 - 負責與交通部TDX平台進行通信
    """
    
    def __init__(self, test_mode=False, auth_service=None):
        """
        初始化TDX服務
        
        Args:
            test_mode (bool): 是否為測試模式
            auth_service (AuthService, optional): 認證服務實例
        """
        self.test_mode = test_mode
        self.auth_service = auth_service or AuthService(test_mode=test_mode)
        self.api_client = APIClient(base_url="https://tdx.transportdata.tw/api/basic/v2/Air")
    
    def _get_auth_header(self):
        """
        獲取認證頭
        
        Returns:
            dict: 包含認證信息的頭
        """
        # 獲取TDX令牌
        success, result = self.auth_service.get_tdx_token()
        
        if not success:
            logger.error(f"獲取TDX令牌失敗: {result}")
            return None
        
        return {
            'authorization': f'Bearer {result}',
            'Accept-Encoding': 'gzip'
        }
    
    def get_airport_flights(self, airport_code="TPE", direction="Departure", date=None, limit=None):
        """
        獲取機場航班資訊
        
        Args:
            airport_code (str): 機場代碼 (IATA)
            direction (str): "Departure" 或 "Arrival"
            date (str, optional): 日期，格式為YYYY-MM-DD
            limit (int, optional): 限制返回數量
            
        Returns:
            dict: 操作結果
        """
        if self.test_mode:
            # 測試模式下返回模擬數據
            mock_data = MockDataGenerator.generate_flight_data(
                airport_code=airport_code,
                direction=direction,
                date=date,
                count=limit or 10
            )
            return {'success': True, 'data': mock_data}
        
        # 獲取認證頭
        headers = self._get_auth_header()
        if not headers:
            return {'success': False, 'message': '無法獲取TDX授權'}
        
        # 設定API URL
        endpoint = f"/FIDS/Airport/{direction}/{airport_code}"
        
        # 設定查詢參數
        params = {'$format': 'JSON'}
        if date:
            params['$filter'] = f"contains({direction}Time,'{date}')"
        if limit:
            params['$top'] = str(limit)
        
        # 發送請求
        success, response = self.api_client.get(endpoint, params=params, headers=headers)
        
        if not success:
            return {'success': False, 'message': f'獲取航班資訊失敗: {response.get("error", "未知錯誤")}'}
        
        return {'success': True, 'data': response}
    
    def get_airport_info(self, airport_code=None):
        """
        獲取機場基本資訊
        
        Args:
            airport_code (str, optional): 機場代碼，若不提供則獲取所有機場
            
        Returns:
            dict: 操作結果
        """
        if self.test_mode:
            # 測試模式下返回模擬數據
            mock_data = MockDataGenerator.generate_airport_data(airport_code)
            if mock_data:
                return {'success': True, 'data': mock_data if isinstance(mock_data, list) else [mock_data]}
            else:
                return {'success': False, 'message': f'找不到機場: {airport_code}'}
        
        # 獲取認證頭
        headers = self._get_auth_header()
        if not headers:
            return {'success': False, 'message': '無法獲取TDX授權'}
        
        # 設定API URL
        endpoint = "/Airport"
        if airport_code:
            endpoint = f"{endpoint}/{airport_code}"
        
        # 設定查詢參數
        params = {'$format': 'JSON'}
        
        # 發送請求
        success, response = self.api_client.get(endpoint, params=params, headers=headers)
        
        if not success:
            return {'success': False, 'message': f'獲取機場資訊失敗: {response.get("error", "未知錯誤")}'}
        
        return {'success': True, 'data': response}
    
    def get_airline_info(self, airline_code=None):
        """
        獲取航空公司基本資訊
        
        Args:
            airline_code (str, optional): 航空公司代碼，若不提供則獲取所有航空公司
            
        Returns:
            dict: 操作結果
        """
        if self.test_mode:
            # 測試模式下返回模擬數據
            mock_data = MockDataGenerator.generate_airline_data(airline_code)
            if mock_data:
                return {'success': True, 'data': mock_data if isinstance(mock_data, list) else [mock_data]}
            else:
                return {'success': False, 'message': f'找不到航空公司: {airline_code}'}
        
        # 獲取認證頭
        headers = self._get_auth_header()
        if not headers:
            return {'success': False, 'message': '無法獲取TDX授權'}
        
        # 設定API URL
        endpoint = "/Airline"
        if airline_code:
            endpoint = f"{endpoint}/{airline_code}"
        
        # 設定查詢參數
        params = {'$format': 'JSON'}
        
        # 發送請求
        success, response = self.api_client.get(endpoint, params=params, headers=headers)
        
        if not success:
            return {'success': False, 'message': f'獲取航空公司資訊失敗: {response.get("error", "未知錯誤")}'}
        
        return {'success': True, 'data': response}
    
    def get_flight_info(self, airline_code, flight_number, date):
        """
        獲取特定航班資訊
        
        Args:
            airline_code (str): 航空公司代碼
            flight_number (str): 航班號
            date (str): 日期，格式為YYYY-MM-DD
            
        Returns:
            dict: 操作結果
        """
        if self.test_mode:
            # 測試模式下生成模擬數據
            mock_data = MockDataGenerator.generate_flight_data(
                airport_code="TPE",  # 使用默認機場
                direction="Departure",
                date=date,
                count=1
            )
            
            # 修改模擬數據以匹配所請求的航班
            if mock_data:
                mock_data[0]['AirlineID'] = airline_code
                mock_data[0]['FlightNumber'] = flight_number
                return {'success': True, 'data': mock_data[0]}
            else:
                return {'success': False, 'message': '無法生成模擬航班數據'}
        
        # 獲取認證頭
        headers = self._get_auth_header()
        if not headers:
            return {'success': False, 'message': '無法獲取TDX授權'}
        
        # 設定API URL
        endpoint = f"/FIDS/Flight/{airline_code}/{flight_number}"
        
        # 設定查詢參數
        params = {
            '$format': 'JSON',
            '$filter': f"contains(ScheduleDepartureTime,'{date}')"
        }
        
        # 發送請求
        success, response = self.api_client.get(endpoint, params=params, headers=headers)
        
        if not success:
            return {'success': False, 'message': f'獲取航班資訊失敗: {response.get("error", "未知錯誤")}'}
        
        if not response:
            return {'success': False, 'message': f'找不到航班: {airline_code}{flight_number} 於 {date}'}
        
        return {'success': True, 'data': response[0] if isinstance(response, list) and response else response}
    
    def get_city_weather(self, city, date=None):
        """
        獲取城市天氣資訊
        
        Args:
            city (str): 城市名稱
            date (str, optional): 日期，格式為YYYY-MM-DD
            
        Returns:
            dict: 操作結果
        """
        # 在實際應用中，應從天氣API獲取數據
        # 這裡使用模擬數據
        mock_data = MockDataGenerator.generate_weather_data(city, date)
        return {'success': True, 'data': mock_data}
    
    def get_weather_forecast(self, city, date=None):
        """
        獲取天氣預報資訊
        
        Args:
            city (str): 城市名稱
            date (str, optional): 日期，格式為YYYY-MM-DD
            
        Returns:
            dict: 操作結果
        """
        # 在實際應用中，應從天氣API獲取數據
        # 這裡使用模擬數據
        mock_data = MockDataGenerator.generate_weather_data(city, date)
        return {'success': True, 'data': mock_data}