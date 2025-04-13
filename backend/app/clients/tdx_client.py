"""
TDX API客戶端 - 專門處理台灣運輸資料服務平台API的交互
"""
import os
import json
import logging
from typing import Dict, List, Optional, Any
import time
from datetime import datetime, timedelta

from app.clients.base_client import BaseAPIClient
from app.utils.date_utils import parse_datetime, format_datetime
from app.utils.cache_utils import cached

class TdxApiClient(BaseAPIClient):
    """TDX API客戶端，處理與台灣運輸資料服務平台的API交互"""
    
    def __init__(self):
        """初始化TDX API客戶端"""
        super().__init__()
        self.logger = logging.getLogger('TdxApiClient')
        
        # API配置
        self.base_url = 'https://tdx.transportdata.tw/api/basic'
        self.auth_url = 'https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token'
        
        # 認證配置
        self.client_id = os.environ.get('TDX_CLIENT_ID')
        self.client_secret = os.environ.get('TDX_CLIENT_SECRET')
        if not self.client_id or not self.client_secret:
            self.logger.warning("TDX認證信息未設置，部分功能可能不可用")
            
        # 其他設置
        self.access_token = None
        self.token_expires_at = 0
        self.taiwanese_airports = self._get_taiwanese_airports()
        
    def get_access_token(self) -> Optional[str]:
        """
        獲取或刷新TDX API的訪問令牌
        
        Returns:
            訪問令牌字符串，失敗時返回None
        """
        current_time = time.time()
        
        # 檢查令牌是否有效，提前30秒刷新以避免邊界情況
        if self.access_token and current_time < self.token_expires_at - 30:
            return self.access_token
            
        # 獲取新令牌
        self.logger.info("獲取新的TDX訪問令牌")
        
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        response = self.make_request(
            url=self.auth_url,
            method='POST',
            headers=headers,
            data=data
        )
        
        if response and 'access_token' in response:
            self.access_token = response['access_token']
            # 設置過期時間，默認為1小時（3600秒）
            expires_in = response.get('expires_in', 3600)
            self.token_expires_at = current_time + expires_in
            self.logger.info(f"TDX訪問令牌獲取成功，有效期: {expires_in}秒")
            return self.access_token
        else:
            self.logger.error("獲取TDX訪問令牌失敗")
            return None
    
    def _handle_auth_error(self) -> bool:
        """
        處理認證錯誤
        
        Returns:
            是否成功處理
        """
        # 強制刷新令牌
        self.access_token = None
        self.token_expires_at = 0
        new_token = self.get_access_token()
        return new_token is not None
    
    def _build_headers(self) -> Dict[str, str]:
        """
        構建帶有授權信息的請求頭
        
        Returns:
            請求頭字典
        """
        token = self.get_access_token()
        if not token:
            self.logger.warning("無法獲取訪問令牌，將使用空令牌")
            
        return {
            'Authorization': f'Bearer {token or ""}',
            'Content-Type': 'application/json'
        }
    
    def _get_taiwanese_airports(self) -> List[str]:
        """
        獲取台灣機場IATA代碼列表
        
        Returns:
            IATA代碼列表
        """
        # 台灣主要機場IATA代碼，包含CMJ(七美)和WOT(望安)
        return ['TPE', 'TSA', 'KHH', 'RMQ', 'TNN', 'HUN', 'TTT', 'KNH', 'MZG', 'PIF', 'GNI', 'KYD', 'TXG', 'CYI', 'MFK', 'LZN', 'CMJ', 'WOT']
    
    @cached(ttl=86400, key_prefix="tdx_airports")
    def get_airports(self) -> List[Dict]:
        """
        獲取機場列表
        
        Returns:
            機場信息列表
        """
        self.logger.info("獲取TDX機場列表")
        
        url = f"{self.base_url}/v2/Air/Airport"
        params = {
            '$format': 'JSON'
        }
        
        response = self.make_request(
            url=url,
            method='GET',
            headers=self._build_headers(),
            params=params
        )
        
        if not response:
            self.logger.warning("獲取機場列表失敗，返回空列表")
            return []
            
        try:
            airports = []
            for item in response:
                # 提取機場信息
                airport = {
                    'iata_code': item.get('AirportIATA', ''),
                    'name': item.get('AirportName', {}).get('Zh_tw', ''),
                    'name_en': item.get('AirportName', {}).get('En', ''),
                    'city': item.get('CityName', {}).get('Zh_tw', ''),
                    'city_en': item.get('CityName', {}).get('En', ''),
                    'country': item.get('CountryName', {}).get('Zh_tw', ''),
                    'country_en': item.get('CountryName', {}).get('En', ''),
                    'position': {
                        'lat': item.get('AirportPosition', {}).get('PositionLat', 0),
                        'lon': item.get('AirportPosition', {}).get('PositionLon', 0)
                    }
                }
                airports.append(airport)
                
            self.logger.info(f"成功獲取{len(airports)}個機場信息")
            return airports
        except Exception as e:
            self.logger.error(f"解析機場數據時出錯: {str(e)}")
            return []
    
    @cached(ttl=86400, key_prefix="tdx_airport")
    def get_airport(self, iata_code: str) -> Optional[Dict]:
        """
        獲取特定機場信息
        
        Args:
            iata_code: 機場IATA代碼
            
        Returns:
            機場信息字典，未找到時返回None
        """
        if not iata_code:
            self.logger.error("IATA代碼為空")
            return None
            
        iata_code = iata_code.strip().upper()
        self.logger.info(f"獲取機場信息: {iata_code}")
        
        # 先嘗試從臺灣機場列表API獲取
        url = f"{self.base_url}/v2/Air/Airport/IATA/{iata_code}"
        params = {
            '$format': 'JSON'
        }
        
        response = self.make_request(
            url=url,
            headers=self._build_headers(),
            params=params
        )
        
        if response:
            try:
                # TDX API返回的是單個機場信息
                item = response
                airport = {
                    'iata_code': item.get('AirportIATA', ''),
                    'name': item.get('AirportName', {}).get('Zh_tw', ''),
                    'name_en': item.get('AirportName', {}).get('En', ''),
                    'city': item.get('CityName', {}).get('Zh_tw', ''),
                    'city_en': item.get('CityName', {}).get('En', ''),
                    'country': item.get('CountryName', {}).get('Zh_tw', ''),
                    'country_en': item.get('CountryName', {}).get('En', ''),
                    'position': {
                        'lat': item.get('AirportPosition', {}).get('PositionLat', 0),
                        'lon': item.get('AirportPosition', {}).get('PositionLon', 0)
                    }
                }
                return airport
            except Exception as e:
                self.logger.error(f"解析機場數據時出錯: {str(e)}")
        
        # 如果從單一機場API找不到，嘗試從所有機場列表查找
        airports = self.get_airports()
        for airport in airports:
            if airport.get('iata_code') == iata_code:
                return airport
                
        self.logger.warning(f"未找到機場: {iata_code}")
        return None
    
    @cached(ttl=3600, key_prefix="tdx_flight_schedules")
    def get_flight_schedules(self, date: Optional[str] = None) -> List[Dict]:
        """
        獲取指定日期的航班時刻表
        
        Args:
            date: 日期字符串，格式為YYYY-MM-DD，默認為今天
            
        Returns:
            航班時刻表列表
        """
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
            
        self.logger.info(f"獲取航班時刻表，日期: {date}")
        
        url = f"{self.base_url}/v2/Air/FIDS/Airport/Daily"
        params = {
            '$format': 'JSON',
            'date': date
        }
        
        response = self.make_request(
            url=url,
            headers=self._build_headers(),
            params=params
        )
        
        if not response:
            self.logger.warning(f"獲取航班時刻表失敗，日期: {date}")
            return []
            
        try:
            schedules = []
            for item in response:
                # 只處理台灣出發或到達的航班
                dep_airport = item.get('DepartureAirportID', '')
                arr_airport = item.get('ArrivalAirportID', '')
                
                if not (dep_airport in self.taiwanese_airports or arr_airport in self.taiwanese_airports):
                    continue
                    
                # 解析日期時間
                scheduled_dep_time = None
                actual_dep_time = None
                scheduled_arr_time = None
                actual_arr_time = None
                
                try:
                    scheduled_dep_time_str = item.get('ScheduleDepartureTime', '')
                    if scheduled_dep_time_str:
                        scheduled_dep_time = parse_datetime(scheduled_dep_time_str)
                        
                    actual_dep_time_str = item.get('ActualDepartureTime', '')
                    if actual_dep_time_str:
                        actual_dep_time = parse_datetime(actual_dep_time_str)
                        
                    scheduled_arr_time_str = item.get('ScheduleArrivalTime', '')
                    if scheduled_arr_time_str:
                        scheduled_arr_time = parse_datetime(scheduled_arr_time_str)
                        
                    actual_arr_time_str = item.get('ActualArrivalTime', '')
                    if actual_arr_time_str:
                        actual_arr_time = parse_datetime(actual_arr_time_str)
                except Exception as e:
                    self.logger.warning(f"解析日期時間出錯: {str(e)}")
                
                # 創建航班信息字典
                flight = {
                    'flight_number': item.get('AirlineID', '') + item.get('FlightNumber', ''),
                    'airline_code': item.get('AirlineID', ''),
                    'flight_id': item.get('FlightID', ''),
                    'departure_airport': dep_airport,
                    'arrival_airport': arr_airport,
                    'scheduled_departure': format_datetime(scheduled_dep_time) if scheduled_dep_time else None,
                    'scheduled_arrival': format_datetime(scheduled_arr_time) if scheduled_arr_time else None,
                    'scheduled_departure_time': format_datetime(scheduled_dep_time) if scheduled_dep_time else None,
                    'actual_departure_time': format_datetime(actual_dep_time) if actual_dep_time else None,
                    'scheduled_arrival_time': format_datetime(scheduled_arr_time) if scheduled_arr_time else None,
                    'actual_arrival_time': format_datetime(actual_arr_time) if actual_arr_time else None,
                    'status': item.get('FlightStatus', {}).get('Zh_tw', ''),
                    'status_en': item.get('FlightStatus', {}).get('En', ''),
                    'terminal': item.get('Terminal', ''),
                    'gate': item.get('Gate', ''),
                    'remark': item.get('Remark', {}).get('Zh_tw', ''),
                    'is_cargo': 'CARGO' in item.get('AirlineID', '') + item.get('FlightNumber', '').upper(),
                    'source': 'TDX'
                }
                
                schedules.append(flight)
                
            self.logger.info(f"成功獲取{len(schedules)}個航班時刻")
            return schedules
        except Exception as e:
            self.logger.error(f"解析航班時刻表數據時出錯: {str(e)}")
            return []
    
    @cached(ttl=3600, key_prefix="tdx_domestic_flights")
    def get_domestic_flight_schedules(self, airport_iata: str, date: str = None) -> List[Dict]:
        """
        獲取特定機場的國內航班時刻表，主要針對 AE、B7、DA 航空公司
        
        Args:
            airport_iata: 機場 IATA 代碼 (例如: 'TSA', 'KHH', 'RMQ')
            date: 日期 (格式: YYYY-MM-DD)，默認為今天
            
        Returns:
            航班信息列表
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        # 支持的航空公司列表 (華信航空、立榮航空、德安航空)
        supported_airlines = ['AE', 'B7', 'DA']
        
        self.logger.info(f"正在從 TDX 獲取 {airport_iata} 機場 {date} 的國內航班時刻表 (AE、B7、DA 航空公司)")
        
        try:
            # 獲取指定日期航班時刻表
            flight_schedules = self.get_flight_schedules(date)
            if not flight_schedules:
                self.logger.warning(f"無法從 TDX 獲取 {date} 的航班時刻表")
                return []
            
            # 篩選出指定機場和航空公司的航班
            domestic_flights = []
            for flight in flight_schedules:
                airline_code = flight.get('airline_code')
                departure_airport = flight.get('departure_airport')
                
                # 只篩選出特定機場出發且為支持的航空公司的航班
                if departure_airport == airport_iata and airline_code in supported_airlines:
                    domestic_flights.append(flight)
            
            # 如果找到航班，記錄並返回
            if domestic_flights:
                self.logger.info(f"從 TDX 獲取到 {len(domestic_flights)} 個 {airport_iata} 機場的國內航班")
                
                # 按航空公司統計航班數量
                airline_counts = {}
                for flight in domestic_flights:
                    airline = flight.get('airline_code', 'Unknown')
                    airline_counts[airline] = airline_counts.get(airline, 0) + 1
                
                # 更詳細的航空公司航班統計
                for airline, count in airline_counts.items():
                    airline_name = ""
                    if airline == "AE":
                        airline_name = "華信航空"
                    elif airline == "B7":
                        airline_name = "立榮航空"
                    elif airline == "DA":
                        airline_name = "德安航空"
                    
                    self.logger.info(f"航空公司 {airline} ({airline_name}): {count} 個航班")
                
                return domestic_flights
            else:
                self.logger.warning(f"未找到 {airport_iata} 機場的國內航班 (AE、B7、DA)")
                return []
            
        except Exception as e:
            self.logger.error(f"獲取 {airport_iata} 機場國內航班時出錯: {str(e)}")
            return []