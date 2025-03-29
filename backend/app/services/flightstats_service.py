import requests
import logging
from datetime import datetime
from flask import current_app
from app.utils.api_client import ApiClient
from app.utils.token_manager import TokenManager

logger = logging.getLogger(__name__)

class FlightStatsService:
    """FlightStats API服務類，提供航班狀態和歷史價格查詢功能"""
    
    def __init__(self, test_mode=False, token_manager=None):
        """初始化FlightStats服務
        
        Args:
            test_mode (bool): 是否為測試模式，測試模式下返回模擬數據
            token_manager (TokenManager, optional): 令牌管理器實例
        """
        self.test_mode = test_mode
        self.api_client = ApiClient()
        self.base_url = "https://api.flightstats.com/flex"
        self.token_manager = token_manager or TokenManager()
    
    def _get_auth_params(self):
        """獲取認證參數
        
        Returns:
            dict: 包含appId和appKey的字典
        """
        app_id = current_app.config.get('FLIGHTSTATS_APP_ID')
        app_key = current_app.config.get('FLIGHTSTATS_APP_KEY')
        
        # 使用TokenManager獲取/刷新令牌
        success, credentials = self.token_manager.get_or_refresh_token(
            'flightstats', 
            app_id=app_id, 
            app_key=app_key
        )
        
        if success:
            return credentials
        else:
            logger.error(f"獲取FlightStats認證失敗: {credentials}")
            return {'appId': app_id, 'appKey': app_key}
    
    def get_flight_status(self, carrier, flight_number, year, month, day):
        """獲取航班狀態
        
        Args:
            carrier (str): 航空公司代碼
            flight_number (str): 航班號
            year (int): 年份
            month (int): 月份
            day (int): 日期
            
        Returns:
            dict: 航班狀態信息
        """
        if self.test_mode:
            return self._get_mock_flight_status(carrier, flight_number)
        
        try:
            auth_params = self._get_auth_params()
            
            url = f"{self.base_url}/flightstatus/rest/v2/json/flight/status/{carrier}/{flight_number}/dep/{year}/{month}/{day}"
            params = {
                "appId": auth_params.get('appId'),
                "appKey": auth_params.get('appKey'),
                "utc": "false"
            }
            
            response = self.api_client.get(url, params=params)
            
            if response and "flightStatuses" in response:
                return {
                    'success': True,
                    'data': response
                }
            else:
                logger.warning(f"未找到航班狀態數據: {carrier}{flight_number}")
                return {
                    'success': False,
                    'message': "未找到航班數據"
                }
        
        except Exception as e:
            logger.error(f"獲取航班狀態時發生錯誤: {str(e)}")
            return {
                'success': False,
                'message': f"獲取航班狀態時發生錯誤: {str(e)}"
            }
    
    def get_flight_routes(self, departure_airport, arrival_airport):
        """獲取兩個機場間的航線信息
        
        Args:
            departure_airport (str): 出發機場代碼
            arrival_airport (str): 到達機場代碼
            
        Returns:
            dict: 航線信息
        """
        if self.test_mode:
            return {
                'success': True,
                'data': self._get_mock_flight_routes(departure_airport, arrival_airport)
            }
        
        try:
            auth_params = self._get_auth_params()
            
            url = f"{self.base_url}/schedules/rest/v1/json/from/{departure_airport}/to/{arrival_airport}/departing/{datetime.now().strftime('%Y/%m/%d')}"
            params = {
                "appId": auth_params.get('appId'),
                "appKey": auth_params.get('appKey')
            }
            
            response = self.api_client.get(url, params=params)
            
            if response and "scheduledFlights" in response:
                return {
                    'success': True,
                    'data': response
                }
            else:
                logger.warning(f"未找到航線數據: {departure_airport} 到 {arrival_airport}")
                return {
                    'success': False,
                    'message': "未找到航線數據"
                }
        
        except Exception as e:
            logger.error(f"獲取航線數據時發生錯誤: {str(e)}")
            return {
                'success': False,
                'message': f"獲取航線數據時發生錯誤: {str(e)}"
            }
    
    def get_historical_delays(self, carrier, flight_number, year, month):
        """獲取航班的歷史延誤數據
        
        Args:
            carrier (str): 航空公司代碼
            flight_number (str): 航班號
            year (int): 年份
            month (int): 月份
            
        Returns:
            dict: 歷史延誤數據
        """
        if self.test_mode:
            return {
                'success': True,
                'data': self._get_mock_historical_delays(carrier, flight_number)
            }
        
        try:
            auth_params = self._get_auth_params()
            
            url = f"{self.base_url}/flightstats/rest/v1/json/historical/flight/{carrier}/{flight_number}/delays"
            params = {
                "appId": auth_params.get('appId'),
                "appKey": auth_params.get('appKey'),
                "year": year,
                "month": month
            }
            
            response = self.api_client.get(url, params=params)
            
            if response and "flightDelays" in response:
                return {
                    'success': True,
                    'data': response
                }
            else:
                logger.warning(f"未找到歷史延誤數據: {carrier}{flight_number}")
                return {
                    'success': False,
                    'message': "未找到歷史延誤數據"
                }
        
        except Exception as e:
            logger.error(f"獲取歷史延誤數據時發生錯誤: {str(e)}")
            return {
                'success': False,
                'message': f"獲取歷史延誤數據時發生錯誤: {str(e)}"
            }
    
    def _get_mock_flight_status(self, carrier, flight_number):
        """生成模擬的航班狀態數據
        
        Args:
            carrier (str): 航空公司代碼
            flight_number (str): 航班號
            
        Returns:
            dict: 模擬的航班狀態數據
        """
        return {
            'success': True,
            'data': {
                "flightStatuses": [
                    {
                        "flightId": 1234567,
                        "carrierFsCode": carrier,
                        "flightNumber": flight_number,
                        "departureAirportFsCode": "TPE",
                        "arrivalAirportFsCode": "KHH",
                        "departureDate": {
                            "dateLocal": "2023-06-01T08:00:00.000",
                            "dateUtc": "2023-06-01T00:00:00.000Z"
                        },
                        "arrivalDate": {
                            "dateLocal": "2023-06-01T09:15:00.000",
                            "dateUtc": "2023-06-01T01:15:00.000Z"
                        },
                        "status": "S",
                        "schedule": {
                            "flightType": "J",
                            "serviceClasses": "YFCJ",
                            "restrictions": ""
                        },
                        "operationalTimes": {
                            "publishedDeparture": {
                                "dateLocal": "2023-06-01T08:00:00.000",
                                "dateUtc": "2023-06-01T00:00:00.000Z"
                            },
                            "publishedArrival": {
                                "dateLocal": "2023-06-01T09:15:00.000",
                                "dateUtc": "2023-06-01T01:15:00.000Z"
                            }
                        },
                        "flightDurations": {
                            "scheduledBlockMinutes": 75
                        }
                    }
                ]
            }
        }
    
    def _get_mock_flight_routes(self, departure_airport, arrival_airport):
        """生成模擬的航線數據
        
        Args:
            departure_airport (str): 出發機場代碼
            arrival_airport (str): 到達機場代碼
            
        Returns:
            dict: 模擬的航線數據
        """
        return {
            "scheduledFlights": [
                {
                    "carrierFsCode": "BR",
                    "flightNumber": "123",
                    "departureAirportFsCode": departure_airport,
                    "arrivalAirportFsCode": arrival_airport,
                    "departureTime": "2023-06-01T08:00:00.000",
                    "arrivalTime": "2023-06-01T09:15:00.000",
                    "stops": 0,
                    "flightEquipmentIataCode": "738"
                },
                {
                    "carrierFsCode": "CI",
                    "flightNumber": "456",
                    "departureAirportFsCode": departure_airport,
                    "arrivalAirportFsCode": arrival_airport,
                    "departureTime": "2023-06-01T10:30:00.000",
                    "arrivalTime": "2023-06-01T11:45:00.000",
                    "stops": 0,
                    "flightEquipmentIataCode": "333"
                }
            ],
            "appendix": {
                "airlines": [
                    {
                        "fs": "BR",
                        "name": "EVA Air"
                    },
                    {
                        "fs": "CI",
                        "name": "China Airlines"
                    }
                ],
                "airports": [
                    {
                        "fs": departure_airport,
                        "name": "Taiwan Taoyuan International Airport",
                        "city": "Taipei",
                        "countryCode": "TW"
                    },
                    {
                        "fs": arrival_airport,
                        "name": "Kaohsiung International Airport",
                        "city": "Kaohsiung",
                        "countryCode": "TW"
                    }
                ],
                "equipment": [
                    {
                        "iata": "738",
                        "name": "Boeing 737-800"
                    },
                    {
                        "iata": "333",
                        "name": "Airbus A330-300"
                    }
                ]
            }
        }
    
    def _get_mock_historical_delays(self, carrier, flight_number):
        """生成模擬的歷史延誤數據
        
        Args:
            carrier (str): 航空公司代碼
            flight_number (str): 航班號
            
        Returns:
            dict: 模擬的歷史延誤數據
        """
        return {
            "flightDelays": {
                "carrierFsCode": carrier,
                "flightNumber": flight_number,
                "departureAirport": "TPE",
                "arrivalAirport": "KHH",
                "year": 2023,
                "month": 6,
                "observations": 30,
                "onTimePercent": 82,
                "delayedPercent": 18,
                "canceledPercent": 2,
                "averageDelayMinutes": 15,
                "maximumDelayMinutes": 120
            }
        } 