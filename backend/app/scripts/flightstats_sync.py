#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
FlightStats API 客戶端，用於同步國際航班資料
"""
import os
import json
import logging
import random
import requests
import time
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Optional, Any, Tuple, Union

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('flightstats_api')

class FlightStatsApiClient:
    """FlightStats API 客戶端，用於獲取國際航班資料"""

    # 台灣機場清單
    TAIWAN_AIRPORTS = [
        "TPE", "TSA", "RMQ", "KHH", "TNN", "CYI", 
        "HUN", "TTT", "KNH", "MZG", "LZN", 
        "MFK", "KYD", "GNI", "WOT"  # 移除 CMJ (七美機場)
    ]
    
    # 指定的航空公司
    TARGET_AIRLINES = [
        'BR', 'JL', 'JX', 'IT', 'CX', 'DA', 'CI', 'OZ', 'AE', 'B7'
    ]

    def __init__(self):
        """初始化 FlightStats API 客戶端"""
        # 設置 logger
        self.logger = logging.getLogger('flightstats_api')
        
        # 設置 session
        self.session = requests.Session()
        
        self.app_id = os.environ.get('FLIGHTSTATS_APP_ID')
        self.app_key = os.environ.get('FLIGHTSTATS_APP_KEY')
        
        if not self.app_id or not self.app_key:
            raise ValueError("請設置 FLIGHTSTATS_APP_ID 和 FLIGHTSTATS_APP_KEY 環境變數")
        
        self.base_url = "https://api.flightstats.com/flex"
        self.airports_cache = {}  # 改為字典以便按IATA代碼快速查找
        self.airlines_cache = {}  # 改為字典以便按IATA代碼快速查找
        self.language_param = "languageCode:en"  # 設定為英文
        self.retry_delay = 2  # 重試延遲（秒）
        self.max_retries = 3  # 最大重試次數
        self.request_interval = 0.5  # 請求間隔時間（秒），避免頻繁請求
        self.last_request_time = 0  # 上次請求時間

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """
        向 FlightStats API 發送請求
        
        Args:
            endpoint: API 端點 URL
            params: 額外的查詢參數
            
        Returns:
            解析後的 JSON 回應
        """
        if params is None:
            params = {}
        
        # 添加基本的身份驗證參數
        params.update({
            'appId': self.app_id,
            'appKey': self.app_key,
            'extendedOptions': self.language_param
        })
        
        url = f"{self.base_url}/{endpoint}"
        
        # 控制請求頻率
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.request_interval:
            sleep_time = self.request_interval - time_since_last_request
            time.sleep(sleep_time)
        
        # 重試邏輯
        for attempt in range(self.max_retries):
            try:
                self.logger.info(f"正在請求: {url}")
                # 使用 self.session 而不是直接使用 requests
                response = self.session.get(url, params=params, timeout=10)
                self.last_request_time = time.time()  # 更新最後請求時間
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:  # 速率限制
                    sleep_time = self.retry_delay * (attempt + 1)
                    self.logger.warning(f"API 速率限制，等待 {sleep_time} 秒後重試...")
                    time.sleep(sleep_time)
                    continue
                else:
                    self.logger.error(f"API 請求失敗: {response.status_code}, 回應: {response.text}")
                    response.raise_for_status()
            except requests.RequestException as e:
                self.logger.error(f"請求出錯: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                raise
                
        # 如果所有重試都失敗
        raise Exception(f"在 {self.max_retries} 次嘗試後仍無法連接到 API")

    def get_airports(self) -> List[Dict]:
        """
        獲取機場清單
        
        Returns:
            機場資料列表
        """
        # 如果緩存不為空，返回緩存列表
        if self.airports_cache:
            return list(self.airports_cache.values())
        
        try:
            # 使用測試驗證過的 API 路徑
            response = self._make_request("airports/rest/v1/json/active")
            
            if 'airports' in response and isinstance(response['airports'], list):
                airports = response['airports']
                self.logger.info(f"成功獲取 {len(airports)} 個機場")
                
                # 將機場信息存入緩存
                for airport in airports:
                    iata = airport.get('iata')
                    if iata:
                        self.airports_cache[iata] = airport
                
                return list(self.airports_cache.values())
            else:
                self.logger.error(f"機場數據格式錯誤: {response}")
                # 如果 API 不返回完整信息，使用預定義的主要機場列表
                predefined_airports = self._get_predefined_airports()
                return predefined_airports
        except Exception as e:
            self.logger.error(f"獲取機場列表出錯: {str(e)}")
            predefined_airports = self._get_predefined_airports()
            return predefined_airports

    def _get_predefined_airports(self) -> List[Dict]:
        """返回預定義的主要國際機場列表，確保包含台灣所有機場"""
        airports = [
            # 台灣機場
            {"fs": "TPE", "iata": "TPE", "icao": "RCTP", "name": "臺灣桃園國際機場", "city": "臺北", "countryCode": "TW"},
            {"fs": "TSA", "iata": "TSA", "icao": "RCSS", "name": "臺北松山機場", "city": "臺北", "countryCode": "TW"},
            {"fs": "KHH", "iata": "KHH", "icao": "RCKH", "name": "高雄國際機場", "city": "高雄", "countryCode": "TW"},
            {"fs": "RMQ", "iata": "RMQ", "icao": "RCMQ", "name": "臺中機場", "city": "臺中", "countryCode": "TW"},
            {"fs": "TNN", "iata": "TNN", "icao": "RCNN", "name": "臺南機場", "city": "臺南", "countryCode": "TW"},
            {"fs": "CYI", "iata": "CYI", "icao": "RCKU", "name": "嘉義機場", "city": "嘉義", "countryCode": "TW"},
            {"fs": "HUN", "iata": "HUN", "icao": "RCBS", "name": "花蓮機場", "city": "花蓮", "countryCode": "TW"},
            {"fs": "TTT", "iata": "TTT", "icao": "RCQS", "name": "臺東機場", "city": "臺東", "countryCode": "TW"},
            {"fs": "KNH", "iata": "KNH", "icao": "RCPO", "name": "金門機場", "city": "金門", "countryCode": "TW"},
            {"fs": "MZG", "iata": "MZG", "icao": "RCQC", "name": "馬公機場", "city": "澎湖", "countryCode": "TW"},
            {"fs": "LZN", "iata": "LZN", "icao": "RCLY", "name": "蘭嶼機場", "city": "蘭嶼", "countryCode": "TW"},
            {"fs": "MFK", "iata": "MFK", "icao": "RCMT", "name": "馬祖北竿機場", "city": "馬祖", "countryCode": "TW"},
            {"fs": "KYD", "iata": "KYD", "icao": "RCNO", "name": "蘭嶼綠島機場", "city": "綠島", "countryCode": "TW"},
            {"fs": "GNI", "iata": "GNI", "icao": "RCGI", "name": "綠島機場", "city": "綠島", "countryCode": "TW"},
            {"fs": "WOT", "iata": "WOT", "icao": "RCFN", "name": "望安機場", "city": "望安", "countryCode": "TW"},
            
            # 國際熱門機場
            {"fs": "NRT", "iata": "NRT", "icao": "RJAA", "name": "東京成田國際機場", "city": "東京", "countryCode": "JP"},
            {"fs": "HND", "iata": "HND", "icao": "RJTT", "name": "東京羽田機場", "city": "東京", "countryCode": "JP"},
            {"fs": "HKG", "iata": "HKG", "icao": "VHHH", "name": "香港國際機場", "city": "香港", "countryCode": "HK"},
            {"fs": "ICN", "iata": "ICN", "icao": "RKSI", "name": "首爾仁川國際機場", "city": "首爾", "countryCode": "KR"},
            {"fs": "BKK", "iata": "BKK", "icao": "VTBS", "name": "曼谷素萬那普機場", "city": "曼谷", "countryCode": "TH"},
            {"fs": "SIN", "iata": "SIN", "icao": "WSSS", "name": "新加坡樟宜機場", "city": "新加坡", "countryCode": "SG"},
            {"fs": "PVG", "iata": "PVG", "icao": "ZSPD", "name": "上海浦東國際機場", "city": "上海", "countryCode": "CN"},
            {"fs": "PEK", "iata": "PEK", "icao": "ZBAA", "name": "北京首都國際機場", "city": "北京", "countryCode": "CN"},
            {"fs": "LAX", "iata": "LAX", "icao": "KLAX", "name": "洛杉磯國際機場", "city": "洛杉磯", "countryCode": "US"},
            {"fs": "JFK", "iata": "JFK", "icao": "KJFK", "name": "紐約甘迺迪國際機場", "city": "紐約", "countryCode": "US"},
            {"fs": "SFO", "iata": "SFO", "icao": "KSFO", "name": "舊金山國際機場", "city": "舊金山", "countryCode": "US"}
        ]
        self.logger.info(f"使用預定義的機場列表，共 {len(airports)} 個機場")
        
        # 將預定義機場存入緩存
        for airport in airports:
            iata = airport.get('iata')
            if iata:
                self.airports_cache[iata] = airport
                
        return airports

    def get_airport(self, iata_code: str) -> Optional[Dict]:
        """
        獲取特定機場資料
        
        Args:
            iata_code: 機場 IATA 代碼
            
        Returns:
            機場資料字典，未找到時返回 None
        """
        # 先檢查緩存
        if iata_code in self.airports_cache:
            return self.airports_cache[iata_code]
            
        try:
            # 使用測試驗證過的 API 路徑
            endpoint = f"airports/rest/v1/json/{iata_code}/today"
            params = {'codeType': 'IATA'}
            
            response = self._make_request(endpoint, params)
            if 'airport' in response:
                airport = response['airport']
                self.logger.info(f"成功獲取機場 {iata_code} 資料")
                # 添加到緩存
                self.airports_cache[iata_code] = airport
                return airport
            else:
                self.logger.error(f"找不到機場 {iata_code}")
                
                # 嘗試從預定義列表中查找
                airport = next((a for a in self._get_predefined_airports() if a.get('iata') == iata_code), None)
                if airport:
                    return airport
                
                return None
        except Exception as e:
            self.logger.error(f"獲取機場 {iata_code} 失敗: {str(e)}")
            
            # 嘗試從預定義列表中查找
            airport = next((a for a in self._get_predefined_airports() if a.get('iata') == iata_code), None)
            if airport:
                return airport
            
            return None

    def get_airlines(self) -> List[Dict]:
        """
        獲取航空公司列表
        
        Returns:
            航空公司資料列表
        """
        # 如果緩存不為空，返回緩存列表
        if self.airlines_cache:
            return list(self.airlines_cache.values())
        
        try:
            # 使用測試驗證過的 API 路徑
            response = self._make_request("airlines/rest/v1/json/active")
            
            if 'airlines' in response and isinstance(response['airlines'], list):
                self.logger.info(f"成功獲取 {len(response['airlines'])} 個航空公司")
                # 過濾出我們需要的航空公司
                filtered_airlines = [airline for airline in response['airlines'] 
                                    if airline.get('iata', '') in self.TARGET_AIRLINES]
                self.logger.info(f"過濾後剩餘 {len(filtered_airlines)} 個目標航空公司")
                
                # 將航空公司信息存入緩存
                for airline in filtered_airlines:
                    iata = airline.get('iata')
                    if iata:
                        self.airlines_cache[iata] = airline
                
                return filtered_airlines
            else:
                self.logger.error(f"航空公司數據格式錯誤: {response}")
                # 使用預定義列表
                return self._get_predefined_airlines()
        except Exception as e:
            self.logger.error(f"獲取航空公司列表出錯: {str(e)}")
            return self._get_predefined_airlines()

    def _get_predefined_airlines(self) -> List[Dict]:
        """返回預定義的目標航空公司列表"""
        airlines = [
            {"fs": "AE", "iata": "AE", "icao": "MDA", "name": "華信航空", "countryCode": "TW"},
            {"fs": "B7", "iata": "B7", "icao": "UIA", "name": "立榮航空", "countryCode": "TW"},
            {"fs": "BR", "iata": "BR", "icao": "EVA", "name": "長榮航空", "countryCode": "TW"},
            {"fs": "CI", "iata": "CI", "icao": "CAL", "name": "中華航空", "countryCode": "TW"},
            {"fs": "CX", "iata": "CX", "icao": "CPA", "name": "國泰航空", "countryCode": "HK"},
            {"fs": "DA", "iata": "DA", "icao": "GMG", "name": "遠東航空", "countryCode": "TW"},
            {"fs": "IT", "iata": "IT", "icao": "TTW", "name": "台灣虎航", "countryCode": "TW"},
            {"fs": "JL", "iata": "JL", "icao": "JAL", "name": "日本航空", "countryCode": "JP"},
            {"fs": "JX", "iata": "JX", "icao": "STD", "name": "星宇航空", "countryCode": "TW"},
            {"fs": "OZ", "iata": "OZ", "icao": "AAR", "name": "韓亞航空", "countryCode": "KR"}
        ]
        self.logger.info(f"使用預定義的航空公司列表，共 {len(airlines)} 個航空公司")
        return airlines

    def get_airline(self, iata_code: str) -> Optional[Dict]:
        """
        獲取特定航空公司資料
        
        Args:
            iata_code: 航空公司 IATA 代碼
            
        Returns:
            航空公司資料字典，未找到時返回預設值
        """
        # 如果不在目標航空公司列表中，直接返回預設值
        if iata_code not in self.TARGET_AIRLINES:
            self.logger.warning(f"航空公司 {iata_code} 不在目標列表中")
            return self._get_default_airline(iata_code)
            
        # 先嘗試從緩存中獲取
        if self.airlines_cache:
            for airline in self.airlines_cache.values():
                if airline.get('iata') == iata_code:
                    return airline
                    
        # 從預定義列表中查找
        airline_defaults = self._get_predefined_airlines()
        for airline in airline_defaults:
            if airline.get('iata') == iata_code:
                return airline
                
        # 最後嘗試 API，但只嘗試一次
        try:
            # 使用測試驗證過的 API 路徑
            endpoint = f"airlines/rest/v1/json/{iata_code}/today"
            params = {'codeType': 'IATA'}
            
            # 使用 _make_request 方法而不是直接發送請求
            response = self._make_request(endpoint, params)
            
            if 'airline' in response:
                self.logger.info(f"成功獲取航空公司 {iata_code} 資料")
                return response['airline']
                
        except Exception as e:
            self.logger.error(f"獲取航空公司 {iata_code} 失敗，使用預設值: {str(e)}")
            
        # 如果 API 呼叫失敗，使用默認值
        return self._get_default_airline(iata_code)
    
    def _get_default_airline(self, iata_code: str) -> Dict:
        """
        獲取航空公司的預設資料
        
        Args:
            iata_code: 航空公司 IATA 代碼
            
        Returns:
            預設的航空公司資料
        """
        airline_name_map = {
            "CI": "中華航空",
            "BR": "長榮航空",
            "AE": "華信航空",
            "B7": "立榮航空",
            "CX": "國泰航空",
            "DA": "大韓航空",
            "IT": "台灣虎航",
            "JL": "日本航空",
            "JX": "星宇航空",
            "OZ": "韓亞航空"
        }
        
        name = airline_name_map.get(iata_code, f"{iata_code} 航空公司")
        
        return {
            "iata": iata_code,
            "fs": iata_code,
            "name": name,
            "name_zh": name,
            "active": True
        }

    def get_taiwanese_airports_flights(self, date=None) -> Dict[str, List[Dict]]:
        """
        獲取所有台灣機場的出發航班（當天日期）
        
        Args:
            date: 查詢日期（可選，默認為今天）
            
        Returns:
            機場IATA代碼到航班列表的映射
        """
        if date is None:
            date = datetime.now()
            
        results = {}
        
        for airport in self.TAIWAN_AIRPORTS:
            try:
                self.logger.info(f"正在獲取機場 {airport} 的航班資料")
                airport_flights = self.get_airport_departures(airport, date)
                
                if airport_flights:
                    # 過濾目標航空公司的航班
                    filtered_flights = []
                    for flight in airport_flights:
                        carrier = flight.get('carrierFsCode', '')
                        if carrier in self.TARGET_AIRLINES:
                            filtered_flights.append(flight)
                    
                    if filtered_flights:
                        results[airport] = filtered_flights
                        self.logger.info(f"成功獲取機場 {airport} 的 {len(filtered_flights)} 個航班")
                    else:
                        self.logger.info(f"機場 {airport} 沒有目標航空公司的航班")
                else:
                    self.logger.info(f"機場 {airport} 沒有航班資料")
            except Exception as e:
                self.logger.error(f"獲取機場 {airport} 航班出錯: {str(e)}")
                
        return results

    def get_airport_departures(self, airport_code, date, requested_fields=None, **params):
        """
        取得指定機場的出發航班資訊
        
        Args:
            airport_code (str): 機場代碼 (IATA格式)
            date (str or datetime): 查詢日期，支援字串格式'YYYY-MM-DD'或datetime物件
            requested_fields (str or list): 要包含在回應中的欄位，可以是逗號分隔的字串或欄位名稱列表
            **params: 其他API參數，可包含：
                - sortFields: 排序欄位
                - includeAirlines/excludeAirlines: 包含/排除的航空公司
                - includeCodeshares: 是否包含代碼共享航班
                - timeFormat: 時間格式(12/24小時制)
                - maxFlights: 最大航班數
                - timeWindowBegin/timeWindowEnd: 指定時間窗口(分鐘)
        
        Returns:
            list: 航班資訊列表
        """
        return self._make_fids_request(airport_code, "departures", date, requested_fields, **params)

    def get_airport_arrivals(self, airport_code, date, requested_fields=None, **params):
        """
        取得指定機場的到達航班資訊
        
        Args:
            airport_code (str): 機場代碼 (IATA格式)
            date (str or datetime): 查詢日期，支援字串格式'YYYY-MM-DD'或datetime物件
            requested_fields (str or list): 要包含在回應中的欄位，可以是逗號分隔的字串或欄位名稱列表
            **params: 其他API參數，可包含：
                - sortFields: 排序欄位
                - includeAirlines/excludeAirlines: 包含/排除的航空公司
                - includeCodeshares: 是否包含代碼共享航班
                - timeFormat: 時間格式(12/24小時制)
                - maxFlights: 最大航班數
                - timeWindowBegin/timeWindowEnd: 指定時間窗口(分鐘)
        
        Returns:
            list: 航班資訊列表
        """
        return self._make_fids_request(airport_code, "arrivals", date, requested_fields, **params)

    def _make_fids_request(self, airport_code, endpoint_type, date, requested_fields=None, **params):
        """
        構建並發送FIDS API請求
        
        Args:
            airport_code (str): 機場代碼
            endpoint_type (str): 端點類型，'arrivals'或'departures'
            date (str or datetime): 查詢日期
            requested_fields (str or list): 要包含在回應中的欄位
            **params: 其他API參數
        
        Returns:
            list: 航班資訊列表
        """
        format_type = "json"
        url = f"{self.base_url}/fids/rest/v1/{format_type}/{airport_code}/{endpoint_type}"
        
        # 設置認證參數
        params["appId"] = self.app_id
        params["appKey"] = self.app_key
        
        # 處理日期參數
        if isinstance(date, datetime):
            # FIDS API 不直接接受日期參數，但我們可以使用日期來過濾和記錄
            date_str = date.strftime('%Y/%m/%d')
            self.logger.info(f"正在請求: {url} 日期: {date_str}")
        elif isinstance(date, str):
            # 假設日期格式為 YYYY-MM-DD
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            date_str = date_obj.strftime('%Y/%m/%d')
            self.logger.info(f"正在請求: {url} 日期: {date_str}")
        
        # 設置請求字段
        if requested_fields:
            if isinstance(requested_fields, list):
                params["requestedFields"] = ",".join(requested_fields)
            else:
                params["requestedFields"] = requested_fields
        else:
            # 預設字段 - 包含關鍵航班資訊
            params["requestedFields"] = "airlineCode,flightNumber,flight,scheduledTime,scheduledDate,estimatedTime,estimatedDate,actualTime,actualDate,currentTime,currentDate,statusCode,isCodeshare,operatingAirlineCode,originAirportCode,destinationAirportCode,gate,terminal,baggage,remarks"
        
        # 設置預設參數 (如果未提供)
        if "timeFormat" not in params:
            params["timeFormat"] = 24  # 使用24小時制
        
        if "includeCodeshares" not in params:
            params["includeCodeshares"] = "true"  # 默認包含代碼共享
        
        # 設置時間窗口 (如果未提供)
        if "timeWindowBegin" not in params and "timeWindowEnd" not in params:
            params["timeWindowBegin"] = 60  # 過去1小時
            params["timeWindowEnd"] = 1440  # 未來24小時
        
        # 嘗試發送請求，實現指數退避重試
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                self.logger.info(f"正在請求: {url}")
                response = self.session.get(url, params=params, timeout=30)
                
                # 檢查狀態碼
                if response.status_code != 200:
                    self.logger.error(f"API錯誤: {response.status_code} - {response.text}")
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (2 ** attempt)
                        self.logger.info(f"將在 {wait_time} 秒後重試...")
                        time.sleep(wait_time)
                        continue
                    return None
                
                # 解析回應
                data = response.json()
                
                # 檢查API錯誤
                if "error" in data and data["error"]:
                    error_message = data["error"].get("errorMessage", "未知錯誤")
                    self.logger.error(f"API錯誤: {error_message}")
                    return None
                
                # 獲取航班數據
                flights = data.get("fidsData", [])
                self.logger.info(f"成功獲取 {airport_code} 機場的 {len(flights)} 個航班")
                
                # 僅返回目標航空公司的航班 (如果已設置)
                if hasattr(self, 'target_airlines') and self.target_airlines:
                    flights = [f for f in flights if f.get('airlineCode') in self.target_airlines]
                    self.logger.info(f"過濾後剩餘 {len(flights)} 個目標航空公司航班")
                
                return flights
                
            except requests.exceptions.RequestException as e:
                self.logger.error(f"請求異常: {str(e)}")
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    self.logger.info(f"將在 {wait_time} 秒後重試...")
                    time.sleep(wait_time)
                else:
                    self.logger.error("達到最大重試次數，放棄請求")
                    return None

    def get_flights(self, departure: str, arrival: str, date_str: str, days: int = 1) -> List[Dict]:
        """
        獲取指定出發和到達機場之間的航班
        
        Args:
            departure: 出發機場 IATA 代碼
            arrival: 目的機場 IATA 代碼
            date_str: 日期字符串，格式為 YYYY-MM-DD
            days: 查詢的天數，默認為 1
            
        Returns:
            航班列表
        """
        try:
            # 解析日期
            start_date = datetime.strptime(date_str, "%Y-%m-%d")
            
            flights = []
            
            # 檢查機場是否有效
            if not self.get_airport(departure) or not self.get_airport(arrival):
                self.logger.warning(f"無效的機場代碼: {departure} 或 {arrival}")
                return flights
            
            for day in range(days):
                # 計算當前查詢日期
                current_date = start_date + timedelta(days=day)
                year = current_date.year
                month = current_date.month
                day = current_date.day
                
                # 構建 API 端點
                endpoint = f"schedules/rest/v1/json/from/{departure}/to/{arrival}/departing/{year}/{month}/{day}"
                
                # 添加查詢參數
                params = {
                    'codeType': 'IATA',
                    'maxFlights': 100,  # 限制最大返回結果數量
                }
                
                # 增加延遲，避免過快請求導致 API 限制
                time.sleep(self.request_interval)
                
                try:
                    self.logger.info(f"查詢 {departure}->{arrival} 在 {year}-{month}-{day} 的航班")
                    response = self._make_request(endpoint, params)
                    
                    if 'scheduledFlights' in response and isinstance(response['scheduledFlights'], list):
                        scheduled_flights = response['scheduledFlights']
                        self.logger.info(f"成功獲取 {len(scheduled_flights)} 個 {departure}->{arrival} 航班")
                        
                        # 處理每個航班數據
                        day_flights = []
                        for flight in scheduled_flights:
                            processed_flight = self._process_flight_data(flight, departure, arrival)
                            if processed_flight:
                                day_flights.append(processed_flight)
                        
                        self.logger.info(f"成功處理 {len(day_flights)} 個 {departure}->{arrival} 航班")
                        flights.extend(day_flights)
                    else:
                        self.logger.warning(f"未找到 {departure}->{arrival} 在 {year}-{month}-{day} 的航班")
                except Exception as e:
                    self.logger.error(f"獲取 {departure}->{arrival} 在 {year}-{month}-{day} 的航班時出錯: {str(e)}")
                    # 出錯時不應該立即放棄，繼續處理下一天
                    continue
            
            return flights
            
        except Exception as e:
            self.logger.error(f"獲取 {departure}->{arrival} 航班時出錯: {str(e)}")
            return []

    def _process_flight_data(self, flight: Dict, departure_airport: str, arrival_airport: str) -> Optional[Dict]:
        """
        處理航班數據，統一格式
        
        Args:
            flight: 原始航班數據
            departure_airport: 出發機場 IATA 代碼
            arrival_airport: 目的機場 IATA 代碼
            
        Returns:
            處理後的航班數據
        """
        try:
            # 處理數據前進行類型檢查
            if not isinstance(flight, dict):
                self.logger.error(f"航班數據不是字典類型: {type(flight)}")
                return None
            
            # 嘗試從多種可能的字段獲取航空公司代碼
            carrier = flight.get('carrierFsCode', '') or flight.get('airlineCode', '') or flight.get('operatingAirlineCode', '')
            if not carrier:
                self.logger.warning(f"無法獲取航空公司代碼: {flight}")
                # 使用一個預設值而不是直接返回None
                carrier = 'UNK'  # Unknown
                
            flight_number = flight.get('flightNumber', '')
            if not flight_number:
                # 嘗試從其他可能的字段獲取航班號
                flight_str = flight.get('flight', '')
                if flight_str and len(flight_str) > 2:
                    # 假設航班號格式為 "XX123"，提取數字部分
                    flight_number = ''.join([c for c in flight_str if c.isdigit()])
                    
            full_flight_number = f"{carrier}{flight_number}"  # 合併為完整航班號
            
            # 解析日期時間 - 優先從FIDS特有字段獲取
            departure_time = None
            arrival_time = None
            
            # FIDS API通常返回這些字段
            scheduled_date = flight.get('scheduledDate', '')
            scheduled_time = flight.get('scheduledTime', '')
            
            if scheduled_date and scheduled_time:
                try:
                    # 組合日期和時間
                    departure_time_str = f"{scheduled_date} {scheduled_time}"
                    departure_time = self._parse_datetime(departure_time_str)
                except Exception as e:
                    self.logger.warning(f"無法解析FIDS日期時間: {e}")
            
            # 如果FIDS特有字段解析失敗，嘗試標準字段
            if not departure_time:
                departure_time_str = flight.get('departureTime', '')
                departure_time = self._parse_datetime(departure_time_str)
                
            # 同樣對到達時間處理
            estimated_date = flight.get('estimatedDate', '')
            estimated_time = flight.get('estimatedTime', '')
            
            if estimated_date and estimated_time:
                try:
                    arrival_time_str = f"{estimated_date} {estimated_time}"
                    arrival_time = self._parse_datetime(arrival_time_str)
                except Exception as e:
                    self.logger.warning(f"無法解析到達日期時間: {e}")
                    
            if not arrival_time:
                arrival_time_str = flight.get('arrivalTime', '')
                arrival_time = self._parse_datetime(arrival_time_str)
            
            # 即使時間解析失敗，仍繼續處理其他數據
            if not departure_time and not arrival_time:
                self.logger.warning(f"航班 {full_flight_number} 無法解析出發和到達時間，使用當前時間作為替代")
                current_time = datetime.now()
                # 為了確保有基本時間數據，使用當前時間作為出發時間
                departure_time = current_time
                # 估算到達時間（當前時間+2小時）
                arrival_time = current_time + timedelta(hours=2)
            elif not departure_time and arrival_time:
                # 如果只有到達時間，估算出發時間（到達時間-2小時）
                self.logger.warning(f"航班 {full_flight_number} 缺少出發時間，根據到達時間估算")
                departure_time = arrival_time - timedelta(hours=2)
            elif departure_time and not arrival_time:
                # 如果只有出發時間，估算到達時間（出發時間+2小時）
                self.logger.warning(f"航班 {full_flight_number} 缺少到達時間，根據出發時間估算")
                arrival_time = departure_time + timedelta(hours=2)
            
            # 計算飛行時間（分鐘）
            duration_minutes = 0
            if departure_time and arrival_time:
                duration = arrival_time - departure_time
                duration_minutes = max(0, int(duration.total_seconds() / 60))
            
            # 根據服務類型模擬票價
            service_classes = flight.get('serviceClasses', [])
            has_first = 'F' in service_classes or 'P' in service_classes
            has_business = 'J' in service_classes or 'C' in service_classes
            has_economy = 'Y' in service_classes or len(service_classes) == 0  # 如果沒有指定，假設有經濟艙
            
            # 基礎價格根據航班時長調整
            base_price = max(3000, min(15000, duration_minutes * 10))
            economy_price = base_price if has_economy else None
            business_price = base_price * 2.5 if has_business else None
            first_price = base_price * 4 if has_first else None
            
            # 模擬座位可用性
            economy_seats = random.randint(30, 200) if has_economy else 0
            business_seats = random.randint(10, 40) if has_business else 0
            first_seats = random.randint(5, 15) if has_first else 0
            available_seats = economy_seats + business_seats + first_seats
            
            # 獲取航班的航空公司資訊 (使用緩存)
            airline_info = self.get_airline(carrier) or {}
            
            # 獲取機場資訊 (使用緩存)
            departure_airport_info = self.get_airport(departure_airport) or {}
            arrival_airport_info = self.get_airport(arrival_airport) or {}
            
            # 構建標準化的航班數據
            processed_data = {
                "flight_id": f"{full_flight_number}_{departure_time.strftime('%Y%m%d') if departure_time else 'unknown'}",
                "flight_number": full_flight_number,  # 使用完整航班號
                "airline_code": carrier,
                "airline_name": airline_info.get('name', '未知航空公司'),  # 英文名稱，中文名稱將在資料庫同步時添加
                "departure_airport": departure_airport,
                "departure_airport_name": departure_airport_info.get('name', '未知機場'),  # 英文名稱，中文名稱將在資料庫同步時添加
                "departure_city": departure_airport_info.get('city', '未知城市'),  # 英文名稱，中文名稱將在資料庫同步時添加
                "arrival_airport": arrival_airport,
                "arrival_airport_name": arrival_airport_info.get('name', '未知機場'),  # 英文名稱，中文名稱將在資料庫同步時添加
                "arrival_city": arrival_airport_info.get('city', '未知城市'),  # 英文名稱，中文名稱將在資料庫同步時添加
                "departure_time": departure_time.isoformat() if departure_time else None,
                "arrival_time": arrival_time.isoformat() if arrival_time else None,
                "status": flight.get('statusCode', '準時'),  # 從API獲取狀態，預設為準時
                "is_delayed": flight.get('statusCode', '').lower() == 'delayed',  # 檢查狀態是否為延誤
                "terminal": flight.get('departureTerminal', ''),
                "gate": flight.get('departureGate', '') or flight.get('gate', ''),
                "economy_price": economy_price,
                "business_price": business_price,
                "first_price": first_price,
                "economy_seats": economy_seats,
                "business_seats": business_seats, 
                "first_seats": first_seats,
                "available_seats": available_seats,
                "duration_minutes": duration_minutes,
                "aircraft_type": flight.get('flightEquipmentIataCode', 'Unknown'),
                "service_classes": service_classes,
                "data_source": "FlightStats",
                # 將原始數據也保存，以備後續處理
                "raw_data": {
                    key: value for key, value in flight.items()
                    if key not in ['raw', 'legs', 'codeshares', 'flightDuration']  # 排除大型或冗餘字段
                }
            }
            
            # 將票價資料格式化為列表，方便後續資料庫同步
            processed_data['prices'] = []
            if economy_price:
                processed_data['prices'].append({
                    'class_type': '經濟',
                    'price': economy_price,
                    'available_seats': economy_seats
                })
            if business_price:
                processed_data['prices'].append({
                    'class_type': '商務',
                    'price': business_price,
                    'available_seats': business_seats
                })
            if first_price:
                processed_data['prices'].append({
                    'class_type': '頭等',
                    'price': first_price,
                    'available_seats': first_seats
                })
            
            return processed_data
        except Exception as e:
            self.logger.error(f"處理航班數據時出錯: {str(e)}")
            return None

    def _parse_datetime(self, datetime_str: str) -> Optional[datetime]:
        """
        解析多種格式的日期時間字符串
        
        Args:
            datetime_str: 日期時間字符串
            
        Returns:
            解析後的datetime對象，解析失敗時返回None
        """
        if not datetime_str:
            return None
            
        # 嘗試多種常見格式
        formats = [
            '%Y-%m-%dT%H:%M:%S.%f',  # 2025-04-11T00:05:00.000
            '%Y-%m-%dT%H:%M:%S',     # 2025-04-11T00:05:00
            '%Y-%m-%dT%H:%M',        # 2025-04-11T00:05
            '%Y-%m-%d %H:%M:%S',     # 2025-04-11 00:05:00
            '%Y-%m-%d %H:%M',        # 2025-04-11 00:05
            '%m/%d/%Y %H:%M',        # 04/14/2025 11:30 (FlightStats API 格式)
            '%m/%d/%Y %H:%M:%S'      # 04/14/2025 11:30:00 (帶秒的 FlightStats API 格式)
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(datetime_str, fmt)
            except (ValueError, TypeError):
                continue
                
        # 如果所有格式都失敗，嘗試手動解析
        try:
            # 處理可能的T分隔符和可能的毫秒
            clean_str = datetime_str.replace('T', ' ')
            if '.' in clean_str:
                clean_str = clean_str.split('.')[0]  # 移除毫秒部分
                
            # 分離日期和時間部分
            parts = clean_str.strip().split(' ')
            if len(parts) >= 2:
                date_part = parts[0]
                time_part = parts[1]
                
                # 檢查日期部分是否包含斜線（如 MM/DD/YYYY）
                if '/' in date_part:
                    # 處理 MM/DD/YYYY 格式
                    month, day, year = date_part.split('/')
                    date_part = f"{year}-{month}-{day}"
                
                # 根據時間部分的長度選擇格式
                if len(time_part) <= 5:  # HH:MM
                    return datetime.strptime(f"{date_part} {time_part}", "%Y-%m-%d %H:%M")
                else:  # HH:MM:SS
                    return datetime.strptime(f"{date_part} {time_part}", "%Y-%m-%d %H:%M:%S")
        except Exception as e:
            self.logger.error(f"手動解析日期時間失敗: {str(e)} 原始值: {datetime_str}")
            self.logger.info(f"嘗試更靈活的日期時間格式解析")
            
            # 再嘗試一種更靈活的方式解析
            try:
                # 使用 dateutil 庫嘗試解析（如果可用）
                from dateutil import parser
                return parser.parse(datetime_str)
            except:
                try:
                    # 嘗試檢測 MM/DD/YYYY 格式
                    if '/' in datetime_str and ' ' in datetime_str:
                        date_part, time_part = datetime_str.split(' ', 1)
                        if date_part.count('/') == 2:
                            month, day, year = date_part.split('/')
                            new_date_part = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                            new_datetime_str = f"{new_date_part} {time_part}"
                            return datetime.strptime(new_datetime_str, "%Y-%m-%d %H:%M")
                except Exception as inner_e:
                    self.logger.error(f"靈活解析日期時間也失敗: {str(inner_e)}")
            
        return None

    def get_flight_status(self, carrier: str, flight_number: str, date: Union[datetime, str]) -> Optional[Dict]:
        """
        獲取特定航班狀態
        
        Args:
            carrier: 航空公司代碼
            flight_number: 航班號
            date: 航班日期，可以是 datetime 對象或 "YYYY-MM-DD" 格式的字符串
            
        Returns:
            航班狀態資料字典，未找到時返回 None
        """
        # 如果不在目標航空公司列表中，直接返回 None
        if carrier not in self.TARGET_AIRLINES:
            self.logger.warning(f"航空公司 {carrier} 不在目標列表中")
            return None
            
        if isinstance(date, str):
            date = datetime.strptime(date, "%Y-%m-%d")
        
        try:
            # 使用測試驗證過的 API 路徑
            year = date.year
            month = date.month
            day = date.day
            
            endpoint = f"flightstatus/rest/v2/json/flight/status/{carrier}/{flight_number}/dep/{year}/{month}/{day}"
            params = {'codeType': 'IATA'}
            
            response = self._make_request(endpoint, params)
            
            if 'flightStatuses' in response and response['flightStatuses']:
                self.logger.info(f"成功獲取航班 {carrier}{flight_number} 狀態")
                return response['flightStatuses'][0]
            else:
                self.logger.error(f"找不到航班 {carrier}{flight_number} 狀態")
                return None
        except Exception as e:
            self.logger.error(f"獲取航班 {carrier}{flight_number} 狀態失敗: {str(e)}")
            return None

    def sync_all_taiwan_flights(self, date=None, callback=None):
        """
        同步所有台灣機場出發的航班資料
        
        Args:
            date: 查詢日期（可選，默認為今天）
            callback: 每個航班處理完後的回調函數
            
        Returns:
            同步結果摘要
        """
        if date is None:
            date = datetime.now()
            
        total_flights = 0
        processed_flights = []
        
        # 獲取所有台灣機場的航班
        airports_flights = self.get_taiwanese_airports_flights(date)
        
        for airport, flights in airports_flights.items():
            self.logger.info(f"處理 {airport} 機場的 {len(flights)} 個航班")
            
            for flight in flights:
                try:
                    departure_airport = flight.get('departureAirportFsCode', '')
                    arrival_airport = flight.get('arrivalAirportFsCode', '')
                    
                    # 處理航班資料
                    processed_flight = self._process_flight_data(flight, departure_airport, arrival_airport)
                    
                    if processed_flight:
                        processed_flights.append(processed_flight)
                        total_flights += 1
                        
                        # 如果提供了回調函數，則調用它
                        if callback and callable(callback):
                            callback(processed_flight)
                except Exception as e:
                    self.logger.error(f"處理航班時出錯: {str(e)}")
                    continue
        
        self.logger.info(f"成功處理 {total_flights} 個台灣出發的航班")
        return {
            "status": "success",
            "message": f"成功同步 {total_flights} 個台灣出發的航班",
            "total_flights": total_flights,
            "flights": processed_flights
        }


if __name__ == "__main__":
    # 測試代碼
    api = FlightStatsApiClient()
    
    # 測試獲取機場資訊
    airports = api.get_airports()
    print(f"獲取到 {len(airports)} 個機場")
    
    # 測試獲取特定機場
    tpe = api.get_airport("TPE")
    print(f"TPE 機場: {tpe}")
    
    # 測試獲取航空公司
    airlines = api.get_airlines()
    print(f"獲取到 {len(airlines)} 個航空公司")
    
    # 測試獲取航班
    flights = api.get_flights("TPE", "NRT", datetime.now().strftime('%Y-%m-%d'))
    print(f"獲取到 {len(flights)} 個 TPE->NRT 航班") 