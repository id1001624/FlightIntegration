"""
FlightStats API客戶端 - 專門處理FlightStats API的交互
"""
import os
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import uuid

from app.clients.base_client import BaseAPIClient
from app.utils.date_utils import parse_datetime, format_datetime, get_date_range
from app.utils.cache_utils import cached

# --- Define module-level logger ---
logger = logging.getLogger(__name__)
# --- End logger definition ---

# --- 新增導入 constants --- 
try:
    from app.scripts.constants import TARGET_AIRLINES
except ImportError:
    # Fallback if constants cannot be imported from the primary location
    logger.warning("無法從 app.scripts.constants 導入 TARGET_AIRLINES，使用預設列表")
    # 定義一個預設值，以防導入失敗，但最好確保導入成功
    TARGET_AIRLINES = ['BR', 'CI', 'CX', 'IT', 'JL', 'JX', 'OZ']
# --- 結束導入 ---

class FlightStatsApiClient(BaseAPIClient):
    """FlightStats API客戶端，處理與FlightStats API的交互"""
    
    def __init__(self):
        """初始化FlightStats API客戶端"""
        super().__init__()
        self.logger = logging.getLogger('FlightStatsApiClient')
        
        # API配置
        self.base_url = 'https://api.flightstats.com/flex'
        
        # 認證配置
        self.app_id = os.environ.get('FLIGHTSTATS_APP_ID')
        self.app_key = os.environ.get('FLIGHTSTATS_APP_KEY')
        
        if not self.app_id or not self.app_key:
            self.logger.warning("FlightStats認證信息未設置，部分功能可能不可用")
        
        # 修正：使用從 constants 導入的 TARGET_AIRLINES
        self.target_airlines = TARGET_AIRLINES
        
        # 確保target_airlines是字串列表
        if not isinstance(self.target_airlines, list):
            self.logger.warning(f"TARGET_AIRLINES不是列表類型，正在轉換: {type(self.target_airlines)}")
            # 嘗試轉換為列表
            try:
                self.target_airlines = list(self.target_airlines)
            except Exception:
                self.logger.error(f"無法將TARGET_AIRLINES轉換為列表，使用預設值")
                self.target_airlines = ['BR', 'CI', 'CX','IT', 'JL', 'JX', 'OZ']
        
        # 確保所有元素都是字串
        cleaned_airlines = []
        for airline in self.target_airlines:
            if isinstance(airline, str):
                cleaned_airlines.append(airline)
            else:
                self.logger.warning(f"忽略非字串航空公司代碼: {airline}")
        
        if not cleaned_airlines:
            self.logger.warning("清理後的航空公司列表為空，使用預設值")
            cleaned_airlines = ['AE', 'B7', 'BR', 'CI', 'CX', 'DA', 'IT', 'JL', 'JX', 'OZ']
        
        self.target_airlines = cleaned_airlines
        self.logger.info(f"FlightStats客戶端將處理的目標航空公司: {self.target_airlines}")
        
        # 請求間隔設置
        self.request_interval = 1.0  # 增加間隔以避免達到速率限制
    
    def _build_params(self, extra_params: Optional[Dict] = None) -> Dict:
        """
        構建包含認證信息的請求參數
        
        Args:
            extra_params: 額外的請求參數
            
        Returns:
            完整的請求參數字典
        """
        params = {
            'appId': self.app_id,
            'appKey': self.app_key,
            'codeType': 'IATA',  # 添加默認的 codeType 參數
        }
        
        if extra_params:
            params.update(extra_params)
            
        return params
    
    @cached(ttl=7200, key_prefix="flightstats_flights")
    def get_flights(self, dep_airport: str, arr_airport: str, date: str) -> List[Dict]:
        """
        獲取特定出發地、目的地和日期的航班信息，只使用 schedules 端點
        
        Args:
            dep_airport: 出發機場IATA代碼
            arr_airport: 到達機場IATA代碼
            date: 日期字符串，格式為YYYY-MM-DD
            
        Returns:
            航班信息列表
        """
        if not dep_airport or not arr_airport or not date:
            self.logger.error("獲取航班信息的參數不完整")
            return []
            
        dep_airport = dep_airport.strip().upper()
        arr_airport = arr_airport.strip().upper()
        
        # 解析日期
        try:
            dt = datetime.strptime(date, '%Y-%m-%d')
            year, month, day = dt.year, dt.month, dt.day
        except ValueError:
            self.logger.error(f"日期格式無效: {date}")
            return []
            
        self.logger.info(f"獲取航班: {dep_airport} → {arr_airport}, 日期: {date}")
        
        # 使用 schedules 端點獲取航班信息
        url = f"{self.base_url}/schedules/rest/v1/json/from/{dep_airport}/to/{arr_airport}/departing/{year}/{month}/{day}"
        
        response = self.make_request(
            url=url,
            method='GET',
            params=self._build_params({
                'extendedOptions': 'includeNewFields'
            })
        )
        
        flights = []
            
            if response and 'scheduledFlights' in response:
                self.logger.info(f"接收到 scheduledFlights 回應，包含 {len(response['scheduledFlights'])} 個航班")
                try:
                    for item in response['scheduledFlights']:
                        # 篩選目標航空公司
                        airline_code = item.get('carrierFsCode', '')
                        if airline_code not in self.target_airlines and len(self.target_airlines) > 0:
                            continue
                        # 解析日期時間
                        dep_time = None
                        arr_time = None
                        try:
                            dep_time_str = item.get('departureTime', '')
                            if dep_time_str:
                                dep_time = parse_datetime(dep_time_str)
                            arr_time_str = item.get('arrivalTime', '')
                            if arr_time_str:
                                arr_time = parse_datetime(arr_time_str)
                        except Exception as e:
                            self.logger.warning(f"解析日期時間出錯: {str(e)}")
                    # 創建航班信息字典，只包含資料庫中存在的欄位
                    # 並移除 UUID 的生成
                        flight = {
                            'flight_number': item.get('carrierFsCode', '') + item.get('flightNumber', ''),
                        'airline_id': item.get('carrierFsCode', ''),
                        'departure_airport_id': dep_airport,
                        'arrival_airport_id': arr_airport,
                                    'scheduled_departure': format_datetime(dep_time) if dep_time else None,
                                    'scheduled_arrival': format_datetime(arr_time) if arr_time else None,
                            'aircraft': item.get('flightEquipmentIataCode', ''),
                        # 確保提取航廈資訊，如果為 None 或空字串則設為 None
                        'departure_terminal': item.get('departureTerminal') or None,
                        'arrival_terminal': item.get('arrivalTerminal') or None,
                        }
                        flights.append(flight)
                self.logger.info(f"成功從schedules接口獲取並處理 {len(flights)} 個航班信息") 
                except Exception as e:
                    self.logger.error(f"解析schedules數據時出錯: {str(e)}")

        if not flights:
            self.logger.warning(f"最終未獲取到航班信息: {dep_airport} → {arr_airport}, 日期: {date}")

        return flights
    
    def get_airports(self) -> List[Dict]:
        """獲取所有機場信息"""