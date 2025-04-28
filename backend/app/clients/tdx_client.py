"""
TDX API客戶端 - 專門處理台灣運輸資料服務平台API的交互
"""
import os
import json
import logging
from typing import Dict, List, Optional, Any
import time
from datetime import datetime, timedelta

from .base_client import BaseAPIClient
from ..utils.date_utils import parse_datetime, format_datetime
from ..utils.cache_utils import cached

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
    
    @cached(ttl=1800, key_prefix="tdx_daily_schedule_all") # 快取前綴可能也需要更新，反映是按航空公司而非機場
    def get_domestic_flight_schedules(self, airline_iata: str) -> List[Dict]: # 修改參數名稱 airport_iata -> airline_iata
        """
        獲取特定航空公司未來所有可用的國內航班預定時刻表 (例如 AE, B7, DA)。
        從 /v2/Air/DailyFlightSchedule/Domestic/{AirlineIATA} 獲取所有數據，並篩選掉過去的航班。
        注意：此端點不包含航廈資訊和即時狀態。

        Args:
            airline_iata: 航空公司 IATA 代碼 (例如: 'AE', 'B7', 'DA')

        Returns:
            未來航班信息列表 (不含狀態和航廈)
        """
        # 支持的航空公司列表現在可能不需要在此處硬編碼，因為參數就是航空公司
        # supported_airlines = {'AE', 'B7', 'DA'} 

        self.logger.info(f"正在從 TDX DailyFlightSchedule 獲取 {airline_iata} 航空公司的所有未來預定航班")

        # 端點變更: 使用 airline_iata
        url = f"{self.base_url}/v2/Air/DailyFlightSchedule/Domestic/{airline_iata}"

        params = {
            '$format': 'JSON',
            '$top': 5000 # 增加獲取數量
        }

        self.logger.debug(f"請求 TDX DailyFlightSchedule URL: {url} with params: {params}")

        response = self.make_request(
            url=url,
            headers=self._build_headers(),
            params=params
        )

        if not response or not isinstance(response, list):
            self.logger.warning(f"從 TDX DailyFlightSchedule ({airline_iata}) 獲取航班數據失敗或返回空/非列表數據")
            return []
        
        if len(response) == 5000:
            self.logger.warning(f"TDX DailyFlightSchedule 返回了 5000 筆記錄，可能還有更多數據未獲取。 airline: {airline_iata}")

        today = datetime.now().date()
        self.logger.info(f"成功從 TDX DailyFlightSchedule ({airline_iata}) 獲取 {len(response)} 筆原始航班記錄，準備篩選未來日期") # 移除航空公司過濾描述

        parsed_and_filtered_flights = []
        for item in response:
            try:
                # 再次確認獲取的 AirlineID 是否與請求的一致 (通常應該一致)
                fetched_airline_id = item.get('AirlineID', '')
                if fetched_airline_id != airline_iata:
                    self.logger.warning(f"記錄中的航空公司 ({fetched_airline_id}) 與請求的 ({airline_iata}) 不符，跳過: {item}")
                    continue

                flight_date_str = item.get('FlightDate', '')
                departure_airport_id = item.get('DepartureAirport', {}).get('AirportID', '') # 保留以獲取機場信息
                
                try:
                    flight_date = datetime.strptime(flight_date_str, '%Y-%m-%d').date()
                except (ValueError, TypeError):
                    self.logger.warning(f"無法解析航班日期: {flight_date_str}, 跳過記錄: {item}")
                    continue

                # 只根據日期過濾
                if flight_date < today:
                    continue # 跳過過去的航班

                flight_number_only = item.get('FlightNumber', '')
                departure_time_str = item.get('DepartureTime')
                arrival_time_str = item.get('ArrivalTime')
                
                departure_dt_str = f"{flight_date_str}T{departure_time_str}:00" if departure_time_str else None
                arrival_dt_str = f"{flight_date_str}T{arrival_time_str}:00" if arrival_time_str else None
                
                scheduled_departure = parse_datetime(departure_dt_str) 
                scheduled_arrival = parse_datetime(arrival_dt_str)     

                if scheduled_departure and scheduled_arrival and scheduled_arrival < scheduled_departure:
                    scheduled_arrival += timedelta(days=1)
                
                flight = {
                    'flight_number': fetched_airline_id + flight_number_only, # 使用確認過的 airline_id
                    'airline_id': fetched_airline_id,
                    'departure_airport_id': departure_airport_id,
                    'arrival_airport_id': item.get('ArrivalAirport', {}).get('AirportID', ''),
                    'scheduled_departure': format_datetime(scheduled_departure) if scheduled_departure else None,
                    'scheduled_arrival': format_datetime(scheduled_arrival) if scheduled_arrival else None,
                    'aircraft': item.get('AircraftType'), 
                    'source': 'TDX'
                }
                parsed_and_filtered_flights.append(flight)

            except Exception as e:
                self.logger.error(f"處理 TDX DailyFlightSchedule ({airline_iata}) 記錄時出錯: {item}, Error: {e}", exc_info=True)
                continue # 跳過錯誤記錄

        self.logger.info(f"TDX DailyFlightSchedule ({airline_iata}): 篩選後得到 {len(parsed_and_filtered_flights)} 筆未來航班記錄")
        return parsed_and_filtered_flights

    # ... (保留 get_international_flight_schedules 和其他方法) ...