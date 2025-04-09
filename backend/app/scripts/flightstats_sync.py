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
        "MFK", "KYD", "GNI", "WOT", "CMJ"
    ]
    
    # 指定的航空公司
    TARGET_AIRLINES = [
        "AE", "B7", "BR", "CI", "CX", 
        "DA", "IT", "JL", "JX", "OZ"
    ]

    def __init__(self):
        """初始化客戶端，設定 API 金鑰和基礎 URL"""
        self.app_id = os.environ.get('FLIGHTSTATS_APP_ID')
        self.app_key = os.environ.get('FLIGHTSTATS_APP_KEY')
        
        if not self.app_id or not self.app_key:
            raise ValueError("請設置 FLIGHTSTATS_APP_ID 和 FLIGHTSTATS_APP_KEY 環境變數")
        
        self.base_url = "https://api.flightstats.com/flex"
        self.airports_cache = None
        self.airlines_cache = None
        self.language_param = "languageCode:en"  # 設定為英文
        self.retry_delay = 2  # 重試延遲（秒）
        self.max_retries = 3  # 最大重試次數

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
        
        # 重試邏輯
        for attempt in range(self.max_retries):
            try:
                logger.info(f"正在請求: {url}")
                response = requests.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:  # 速率限制
                    sleep_time = self.retry_delay * (attempt + 1)
                    logger.warning(f"API 速率限制，等待 {sleep_time} 秒後重試...")
                    time.sleep(sleep_time)
                    continue
                else:
                    logger.error(f"API 請求失敗: {response.status_code}, 回應: {response.text}")
                    response.raise_for_status()
            except requests.RequestException as e:
                logger.error(f"請求出錯: {str(e)}")
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
        if self.airports_cache:
            return self.airports_cache
        
        try:
            # 使用測試驗證過的 API 路徑
            response = self._make_request("airports/rest/v1/json/active")
            
            if 'airports' in response and isinstance(response['airports'], list):
                logger.info(f"成功獲取 {len(response['airports'])} 個機場")
                self.airports_cache = response['airports']
                return self.airports_cache
            else:
                logger.error(f"機場數據格式錯誤: {response}")
                # 如果 API 不返回完整信息，使用預定義的主要機場列表
                return self._get_predefined_airports()
        except Exception as e:
            logger.error(f"獲取機場列表出錯: {str(e)}")
            return self._get_predefined_airports()

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
            {"fs": "CMJ", "iata": "CMJ", "icao": "RCMO", "name": "七美機場", "city": "七美", "countryCode": "TW"},
            
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
        logger.info(f"使用預定義的機場列表，共 {len(airports)} 個機場")
        self.airports_cache = airports
        return airports

    def get_airport(self, iata_code: str) -> Optional[Dict]:
        """
        獲取特定機場資料
        
        Args:
            iata_code: 機場 IATA 代碼
            
        Returns:
            機場資料字典，未找到時返回 None
        """
        try:
            # 使用測試驗證過的 API 路徑
            endpoint = f"airports/rest/v1/json/{iata_code}/today"
            params = {'codeType': 'IATA'}
            
            response = self._make_request(endpoint, params)
            if 'airport' in response:
                logger.info(f"成功獲取機場 {iata_code} 資料")
                return response['airport']
            else:
                logger.error(f"找不到機場 {iata_code}")
                return None
        except Exception as e:
            logger.error(f"獲取機場 {iata_code} 失敗: {str(e)}")
            
            # 嘗試從緩存中獲取
            if self.airports_cache:
                for airport in self.airports_cache:
                    if airport.get('iata') == iata_code:
                        return airport
            
            # 從預定義列表中查找
            airports = self._get_predefined_airports()
            for airport in airports:
                if airport.get('iata') == iata_code:
                    return airport
            
            return None

    def get_airlines(self) -> List[Dict]:
        """
        獲取航空公司列表
        
        Returns:
            航空公司資料列表
        """
        if self.airlines_cache:
            return self.airlines_cache
        
        try:
            # 使用測試驗證過的 API 路徑
            response = self._make_request("airlines/rest/v1/json/active")
            
            if 'airlines' in response and isinstance(response['airlines'], list):
                logger.info(f"成功獲取 {len(response['airlines'])} 個航空公司")
                # 過濾出我們需要的航空公司
                filtered_airlines = [airline for airline in response['airlines'] 
                                    if airline.get('iata', '') in self.TARGET_AIRLINES]
                logger.info(f"過濾後剩餘 {len(filtered_airlines)} 個目標航空公司")
                self.airlines_cache = filtered_airlines
                return self.airlines_cache
            else:
                logger.error(f"航空公司數據格式錯誤: {response}")
                # 使用預定義列表
                return self._get_predefined_airlines()
        except Exception as e:
            logger.error(f"獲取航空公司列表出錯: {str(e)}")
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
        logger.info(f"使用預定義的航空公司列表，共 {len(airlines)} 個航空公司")
        self.airlines_cache = airlines
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
            logger.warning(f"航空公司 {iata_code} 不在目標列表中")
            return self._get_default_airline(iata_code)
            
        # 先嘗試從緩存中獲取
        if self.airlines_cache:
            for airline in self.airlines_cache:
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
            
            # 降低超時時間
            response = requests.get(f"{self.base_url}/{endpoint}", 
                                   params={**params, 'appId': self.app_id, 'appKey': self.app_key, 
                                          'extendedOptions': self.language_param},
                                   timeout=5)  # 降低超時時間到5秒
            
            if response.status_code == 200:
                data = response.json()
                if 'airline' in data:
                    logger.info(f"成功獲取航空公司 {iata_code} 資料")
                    return data['airline']
                
        except Exception as e:
            logger.error(f"獲取航空公司 {iata_code} 失敗，使用預設值: {str(e)}")
            
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
                logger.info(f"正在獲取機場 {airport} 的航班資料")
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
                        logger.info(f"成功獲取機場 {airport} 的 {len(filtered_flights)} 個航班")
                    else:
                        logger.info(f"機場 {airport} 沒有目標航空公司的航班")
                else:
                    logger.info(f"機場 {airport} 沒有航班資料")
            except Exception as e:
                logger.error(f"獲取機場 {airport} 航班出錯: {str(e)}")
                
        return results

    def get_airport_departures(self, airport_code: str, date: Union[datetime, str]) -> List[Dict]:
        """
        獲取指定機場在指定日期的出發航班
        
        Args:
            airport_code: 機場 IATA 代碼
            date: 查詢日期，可以是 datetime 對象或 "YYYY-MM-DD" 格式的字符串
            
        Returns:
            航班列表
        """
        if isinstance(date, str):
            date = datetime.strptime(date, "%Y-%m-%d")
        
        try:
            # 轉換為 API 所需的日期格式
            year = date.year
            month = date.month
            day = date.day
            hour = 0  # 從午夜開始
            
            # 使用測試驗證過的 API 路徑
            endpoint = f"schedules/rest/v1/json/from/{airport_code}/departing/{year}/{month}/{day}/{hour}"
            params = {
                'codeType': 'IATA',
                'numHours': 24  # 獲取整天的航班
            }
            
            response = self._make_request(endpoint, params)
            
            if 'scheduledFlights' in response and isinstance(response['scheduledFlights'], list):
                flights = response['scheduledFlights']
                logger.info(f"成功獲取 {airport_code} 機場的 {len(flights)} 個航班")
                return flights
            else:
                logger.warning(f"未獲取到 {airport_code} 機場的航班或數據格式錯誤")
                return []
        except Exception as e:
            logger.error(f"獲取 {airport_code} 機場航班出錯: {str(e)}")
            return []

    def get_flights(self, departure_airport: str, arrival_airport: str, 
                     date: Union[datetime, str], days: int = 1) -> List[Dict]:
        """
        獲取指定日期從出發機場到目的機場的航班清單
        
        Args:
            departure_airport: 出發機場 IATA 代碼
            arrival_airport: 目的機場 IATA 代碼
            date: 起始日期，可以是 datetime 對象或 "YYYY-MM-DD" 格式的字符串
            days: 查詢天數
            
        Returns:
            航班資料列表
        """
        if isinstance(date, str):
            date = datetime.strptime(date, "%Y-%m-%d")
        
        processed_flights = []
        
        try:
            # 使用測試驗證過的 API 路徑
            year = date.year
            month = date.month
            day = date.day
            
            endpoint = f"schedules/rest/v1/json/from/{departure_airport}/to/{arrival_airport}/departing/{year}/{month}/{day}"
            params = {
                'codeType': 'IATA',
            }
            
            response = self._make_request(endpoint, params)
            
            if 'scheduledFlights' in response and isinstance(response['scheduledFlights'], list):
                flights = response['scheduledFlights']
                logger.info(f"成功獲取 {len(flights)} 個 {departure_airport}->{arrival_airport} 航班")
                
                # 處理每個航班資料
                for flight in flights:
                    try:
                        # 檢查航空公司是否在目標列表中
                        carrier = flight.get('carrierFsCode', '')
                        if carrier in self.TARGET_AIRLINES:
                            processed_flight = self._process_flight_data(flight, departure_airport, arrival_airport)
                            if processed_flight:
                                processed_flights.append(processed_flight)
                        else:
                            logger.debug(f"跳過非目標航空公司的航班: {carrier}{flight.get('flightNumber', '')}")
                    except Exception as e:
                        logger.error(f"處理航班數據時出錯: {str(e)}")
                
                return processed_flights
            else:
                logger.warning(f"未獲取到航班或數據格式錯誤: {response}")
                return []
        except Exception as e:
            logger.error(f"獲取 {departure_airport}->{arrival_airport} 航班出錯: {str(e)}")
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
                logger.error(f"航班數據不是字典類型: {type(flight)}")
                return None
            
            carrier = flight.get('carrierFsCode', '')
            flight_number = flight.get('flightNumber', '')
            full_flight_number = f"{carrier}{flight_number}"  # 合併為完整航班號
            
            # 解析日期時間
            departure_time_str = flight.get('departureTime', '')
            arrival_time_str = flight.get('arrivalTime', '')
            
            # 改進日期時間解析，考慮不同格式
            try:
                if '.' in departure_time_str:  # 處理帶毫秒的格式
                    departure_time = datetime.strptime(departure_time_str, "%Y-%m-%dT%H:%M:%S.%f")
                else:  # 處理不帶毫秒的格式
                    departure_time = datetime.strptime(departure_time_str, "%Y-%m-%dT%H:%M:%S.000")
            except (ValueError, TypeError):
                logger.warning(f"無法解析出發時間: {departure_time_str}，使用替代方法")
                try:
                    # 嘗試使用更簡單的格式
                    departure_time = datetime.strptime(departure_time_str.split('.')[0], "%Y-%m-%dT%H:%M:%S")
                except (ValueError, TypeError, IndexError):
                    logger.error(f"無法以任何方式解析出發時間: {departure_time_str}")
                    departure_time = None
            
            try:
                if '.' in arrival_time_str:  # 處理帶毫秒的格式
                    arrival_time = datetime.strptime(arrival_time_str, "%Y-%m-%dT%H:%M:%S.%f")
                else:  # 處理不帶毫秒的格式
                    arrival_time = datetime.strptime(arrival_time_str, "%Y-%m-%dT%H:%M:%S.000")
            except (ValueError, TypeError):
                logger.warning(f"無法解析到達時間: {arrival_time_str}，使用替代方法")
                try:
                    # 嘗試使用更簡單的格式
                    arrival_time = datetime.strptime(arrival_time_str.split('.')[0], "%Y-%m-%dT%H:%M:%S")
                except (ValueError, TypeError, IndexError):
                    logger.error(f"無法以任何方式解析到達時間: {arrival_time_str}")
                    arrival_time = None
            
            # 計算飛行時間（分鐘）
            duration_minutes = 0
            if departure_time and arrival_time:
                duration = arrival_time - departure_time
                duration_minutes = int(duration.total_seconds() / 60)
            
            # 根據服務類型模擬票價
            service_classes = flight.get('serviceClasses', [])
            has_first = 'F' in service_classes or 'P' in service_classes
            has_business = 'J' in service_classes or 'C' in service_classes
            has_economy = 'Y' in service_classes
            
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
            
            # 獲取航班的航空公司資訊
            airline_info = self.get_airline(carrier) or {}
            
            # 獲取機場資訊
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
                "status": "準時",  # 預設狀態改為中文
                "is_delayed": False,  # 預設未延誤
                "terminal": flight.get('departureTerminal', ''),
                "gate": flight.get('departureGate', ''),
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
            logger.error(f"處理航班數據時出錯: {str(e)}")
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
            logger.warning(f"航空公司 {carrier} 不在目標列表中")
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
                logger.info(f"成功獲取航班 {carrier}{flight_number} 狀態")
                return response['flightStatuses'][0]
            else:
                logger.error(f"找不到航班 {carrier}{flight_number} 狀態")
                return None
        except Exception as e:
            logger.error(f"獲取航班 {carrier}{flight_number} 狀態失敗: {str(e)}")
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
            logger.info(f"處理 {airport} 機場的 {len(flights)} 個航班")
            
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
                    logger.error(f"處理航班時出錯: {str(e)}")
                    continue
        
        logger.info(f"成功處理 {total_flights} 個台灣出發的航班")
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
    flights = api.get_flights("TPE", "NRT", datetime.now())
    print(f"獲取到 {len(flights)} 個 TPE->NRT 航班") 