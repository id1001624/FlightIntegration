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
    
    @cached(ttl=1800, key_prefix="tdx_fids_flight") # 使用 FIDS Flight 的快取
    def get_domestic_flight_schedules(self, airport_iata: str, date_str: str) -> List[Dict]:
        """
        獲取特定機場在指定日期的國內航班時刻表與狀態 (AE、B7、DA 航空公司)
        從 /v2/Air/FIDS/Flight 獲取所有數據，然後在程式碼中篩選

        Args:
            airport_iata: 機場 IATA 代碼 (例如: 'TSA', 'KHH', 'RMQ')
            date_str: 指定日期字符串 (格式: YYYY-MM-DD)

        Returns:
            航班信息列表 (包含狀態)
        """
        supported_airlines = {'AE', 'B7', 'DA'} # 使用集合以便快速查找
        # current_date_str = datetime.now().strftime('%Y-%m-%d') # 不再使用當前日期
        self.logger.info(f"正在從 TDX FIDS Flight 獲取 {airport_iata} 機場在 {date_str} 的航班狀態")

        url = f"{self.base_url}/v2/Air/FIDS/Flight"

        params = {
            '$format': 'JSON',
            # 不再使用日期過濾
            '$orderby': 'ScheduleDepartureTime', 
            '$top': 3000 # 獲取足夠多的數據以供篩選
        }

        self.logger.debug(f"請求 TDX FIDS Flight URL: {url} with params: {params}")

        response = self.make_request(
            url=url,
            headers=self._build_headers(),
            params=params
        )

        if not response or not isinstance(response, list):
            self.logger.warning(f"從 TDX FIDS Flight 獲取航班數據失敗或返回空/非列表數據")
            return []

        self.logger.info(f"成功從 TDX FIDS Flight 獲取 {len(response)} 筆原始航班記錄，準備篩選指定日期 ({date_str}) 和機場 ({airport_iata})")

        parsed_and_filtered_flights = []
        for item in response:
            try:
                airline_id = item.get('AirlineID', '')
                departure_airport = item.get('DepartureAirportID', '')
                flight_date = item.get('FlightDate', '') # 獲取航班日期

                # 在這裡進行篩選 (機場 + 日期 + 航空公司)
                if (departure_airport != airport_iata or 
                    flight_date != date_str or 
                    airline_id not in supported_airlines):
                    continue # 跳過不符合條件的航班

                flight_number_only = item.get('FlightNumber', '')

                # 解析時間，處理可能的錯誤和 None 值
                scheduled_departure = parse_datetime(item.get('ScheduleDepartureTime'))
                scheduled_arrival = parse_datetime(item.get('ScheduleArrivalTime'))
                actual_departure = parse_datetime(item.get('ActualDepartureTime')) # 可能為 None
                actual_arrival = parse_datetime(item.get('ActualArrivalTime'))     # 可能為 None

                # 決定狀態
                departure_remark = item.get('DepartureRemark', '')
                arrival_remark = item.get('ArrivalRemark', '')
                status = departure_remark if departure_remark else arrival_remark
                if not status:
                    if actual_arrival:
                        status = "已抵達"
                    elif actual_departure:
                        status = "已起飛"
                    else:
                        status = "準時"

                flight = {
                    'flight_number': airline_id + flight_number_only,
                    'airline_id': airline_id,
                    'flight_date': flight_date,
                    'departure_airport_id': departure_airport,
                    'arrival_airport_id': item.get('ArrivalAirportID', ''),
                    'scheduled_departure': format_datetime(scheduled_departure) if scheduled_departure else None,
                    'scheduled_arrival': format_datetime(scheduled_arrival) if scheduled_arrival else None,
                    'actual_departure': format_datetime(actual_departure) if actual_departure else None,
                    'actual_arrival': format_datetime(actual_arrival) if actual_arrival else None,
                    'status': status,
                    'source': 'TDX',
                    'departure_terminal': item.get('DepartureTerminal') or None,
                    'arrival_terminal': item.get('ArrivalTerminal') or None
                }
                parsed_and_filtered_flights.append(flight)
            except Exception as e:
                self.logger.error(f"解析或篩選單筆 FIDS 航班數據時出錯: {item} - {str(e)}")
                continue

        if parsed_and_filtered_flights:
             # 按航空公司統計數量
            airline_counts = {}
            for flight in parsed_and_filtered_flights:
                airline = flight.get('airline_id', 'Unknown')
                airline_counts[airline] = airline_counts.get(airline, 0) + 1
            self.logger.info(f"篩選並解析後，找到 {len(parsed_and_filtered_flights)} 筆從 {airport_iata} 出發的航班:")
            for airline, count in airline_counts.items():
                 airline_name = {"AE": "華信航空", "B7": "立榮航空", "DA": "德安航空"}.get(airline, "未知航空")
                 self.logger.info(f"  航空公司 {airline} ({airline_name}): {count} 個航班")
        else:
            self.logger.warning(f"從 TDX FIDS ({airport_iata}) 的數據中，未能篩選出符合條件 (機場: {airport_iata}, 航空公司: {supported_airlines}) 的航班")

        return parsed_and_filtered_flights