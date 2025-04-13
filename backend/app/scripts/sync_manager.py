#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
API 同步管理器，集成 TDX 和 FlightStats API 數據同步功能
"""
import os
import sys
import json
import logging
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
import time

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('sync_manager')

# 導入常量和客戶端
try:
    # 優先嘗試新的客戶端導入路徑
    from app.clients.tdx_client import TdxApiClient
    from app.clients.flightstats_client import FlightStatsApiClient
    from app.scripts.constants import TAIWAN_AIRPORTS, TARGET_AIRLINES
except ImportError:
    # 嘗試相對導入舊的客戶端
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.append(current_dir)

    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.append(parent_dir)

    # This inner try/except handles the case where even deprecated imports fail.
    try:
        from clients.tdx_client import TdxApiClient
        from clients.flightstats_client import FlightStatsApiClient
        from scripts.constants import TAIWAN_AIRPORTS, TARGET_AIRLINES
    except ImportError:
        try:
            # 如果常量導入失敗，使用內部定義的常量
            from backend.app.deprecated.tdx_sync import TdxApiClient
            from backend.app.deprecated.flightstats_sync import FlightStatsApiClient
            TAIWAN_AIRPORTS = ['TPE', 'TSA', 'RMQ', 'KHH', 'TNN', 'CYI', 'HUN', 'TTT', 'KNH', 'MZG', 'LZN', 'MFK', 'KYD', 'GNI', 'CMJ', 'WOT']
            TARGET_AIRLINES = ['AE', 'B7', 'BR', 'CI', 'CX', 'DA', 'IT', 'JL', 'JX', 'OZ']
        except ImportError as e:
            logger.error(f"無法導入任何版本的 API 客戶端: {str(e)}")
            sys.exit(1)

class ApiSyncManager:
    """API 同步管理器，協調 TDX 和 FlightStats API 的數據同步"""
    
    # 暫時清空此列表，讓所有機場優先嘗試TDX API
    TDX_PROBLEMATIC_AIRPORTS = [] 
    
    # TDX API 專用航空公司代碼 (台灣國內航空公司)
    TDX_TARGET_AIRLINES = ['AE', 'B7', 'DA']  # 華信航空、立榮航空、德安航空
    
    # 最小期望航班數量（低於此數量將使用FlightStats補充）
    MIN_EXPECTED_FLIGHTS = 1
    
    # 熱門國際航線
    POPULAR_INTERNATIONAL_ROUTES = [
        # 台北桃園國際機場
        ('TPE', 'NRT'), ('TPE', 'HND'), ('TPE', 'ICN'), ('TPE', 'HKG'), 
        ('TPE', 'BKK'), ('TPE', 'SIN'), ('TPE', 'KUL'), ('TPE', 'PVG'),
        ('TPE', 'PEK'), ('TPE', 'LAX'), ('TPE', 'SFO'), ('TPE', 'JFK'),
        ('TPE', 'CDG'), ('TPE', 'LHR'), ('TPE', 'FRA'), ('TPE', 'SYD'),
        
        # 台北松山機場
        ('TSA', 'HND'), ('TSA', 'PVG'), ('TSA', 'HKG'), ('TSA', 'ICN'),
        
        # 高雄國際機場
        ('KHH', 'NRT'), ('KHH', 'ICN'), ('KHH', 'HKG'), ('KHH', 'SIN')
    ]
    
    # 熱門國內航線
    POPULAR_DOMESTIC_ROUTES = [
        ('TPE', 'KHH'), ('TSA', 'KHH'), ('TSA', 'RMQ'), ('TSA', 'TNN'),
        ('TSA', 'MZG'), ('TSA', 'HUN'), ('TSA', 'TTT'), ('TSA', 'KNH'),
        ('KHH', 'TSA'), ('RMQ', 'TSA'), ('TNN', 'TSA'), ('MZG', 'TSA')
    ]
    
    def __init__(self):
        """初始化同步管理器"""
        try:
            self.tdx_api = TdxApiClient()
            logger.info("已初始化 TDX API 客戶端")
        except Exception as e:
            self.tdx_api = None
            logger.error(f"初始化 TDX API 客戶端出錯: {str(e)}")
        
        try:
            self.flightstats_api = FlightStatsApiClient()
            logger.info("已初始化 FlightStats API 客戶端")
        except Exception as e:
            self.flightstats_api = None
            logger.error(f"初始化 FlightStats API 客戶端出錯: {str(e)}")
        
        # 檢查至少一個 API 客戶端可用
        if not self.tdx_api and not self.flightstats_api:
            logger.error("無法初始化任何 API 客戶端，同步功能將無法使用")
        
        # 機場和航空公司緩存
        self.airports_cache = {}
        self.airlines_cache = {}
        
        # 請求延遲時間 (秒)
        self.request_delay = 0.5
    
    def is_domestic_route(self, departure: str, arrival: str) -> bool:
        """
        判斷是否為國內航線
        
        Args:
            departure: 出發機場 IATA 代碼
            arrival: 目的機場 IATA 代碼
            
        Returns:
            True 如果是國內航線，否則 False
        """
        return departure in TAIWAN_AIRPORTS and arrival in TAIWAN_AIRPORTS
    
    def is_taiwan_departure(self, departure: str) -> bool:
        """
        判斷是否為從台灣出發的航線
        
        Args:
            departure: 出發機場 IATA 代碼
            
        Returns:
            True 如果是從台灣出發，否則 False
        """
        return departure in TAIWAN_AIRPORTS
    
    def is_target_airline(self, airline_code: str) -> bool:
        """
        判斷是否為目標航空公司
        
        Args:
            airline_code: 航空公司 IATA 代碼
            
        Returns:
            True 如果是目標航空公司，否則 False
        """
        return airline_code in TARGET_AIRLINES
    
    def should_use_tdx_for_airport(self, airport_code: str, date: datetime = None) -> bool:
        """
        判斷指定機場在特定日期是否應該使用TDX API
        
        Args:
            airport_code: 機場IATA代碼
            date: 日期，默認為今天
            
        Returns:
            是否應該使用TDX API
        """
        if not date:
            date = datetime.now()
        
        # MZG、CMJ 總是使用TDX
        if airport_code in ['MZG', 'CMJ']:
            return True
        
        # WOT只在週一(0)和週五(4)使用TDX
        if airport_code == 'WOT':
            weekday = date.weekday()
            return weekday == 0 or weekday == 4
        
        # 其他機場正常判斷
        return airport_code not in self.TDX_PROBLEMATIC_AIRPORTS
    
    def is_tdx_target_airline(self, airline_code: str) -> bool:
        """
        判斷是否為 TDX API 專用航空公司 (AE, B7, DA)
        
        Args:
            airline_code: 航空公司 IATA 代碼
            
        Returns:
            True 如果是 TDX 目標航空公司，否則 False
        """
        return airline_code in self.TDX_TARGET_AIRLINES
    
    def sync_airports(self) -> List[Dict]:
        """
        同步機場數據，優先使用台灣機場列表
        
        Returns:
            機場數據列表
        """
        airports = []
        
        # 先從 TDX API 獲取台灣機場資料
        if self.tdx_api:
            try:
                tdx_airports = self.tdx_api.get_airports()
                if tdx_airports:
                    logger.info(f"已從 TDX API 獲取 {len(tdx_airports)} 個台灣機場")
                    airports.extend(tdx_airports)
            except Exception as e:
                logger.error(f"從 TDX API 獲取機場資料失敗: {str(e)}")
        
        # 如果 TDX 沒有足夠資料，從 FlightStats 獲取
        taiwan_iata_codes = set(airport.get('iata_code') for airport in airports)
        missing_airports = [code for code in TAIWAN_AIRPORTS if code not in taiwan_iata_codes]
        
        if missing_airports and self.flightstats_api:
            logger.info(f"從 TDX API 缺少 {len(missing_airports)} 個台灣機場，嘗試從 FlightStats 獲取")
            for iata_code in missing_airports:
                try:
                    airport = self.flightstats_api.get_airport(iata_code)
                    if airport:
                        airport['data_source'] = 'FlightStats'
                        airports.append(airport)
                        logger.info(f"已從 FlightStats 獲取機場 {iata_code}")
                except Exception as e:
                    logger.error(f"從 FlightStats 獲取機場 {iata_code} 失敗: {str(e)}")
        
        # 更新緩存
        for airport in airports:
            if 'iata_code' in airport:
                self.airports_cache[airport['iata_code']] = airport
            elif 'iata' in airport:
                self.airports_cache[airport['iata']] = airport
        
        logger.info(f"總共獲取了 {len(airports)} 個機場")
        return airports
    
    def get_airport(self, iata_code: str) -> Optional[Dict]:
        """
        獲取機場資料
        
        Args:
            iata_code: 機場 IATA 代碼
            
        Returns:
            機場資料字典，未找到時返回 None
        """
        # 先檢查緩存
        if iata_code in self.airports_cache:
            return self.airports_cache[iata_code]
        
        # 如果緩存中沒有，嘗試從 API 獲取
        airport = None
        
        # 判斷使用哪個API
        if self.tdx_api and iata_code in TAIWAN_AIRPORTS and iata_code not in self.TDX_PROBLEMATIC_AIRPORTS:
            try:
                airport = self.tdx_api.get_airport(iata_code)
                if airport:
                    logger.info(f"已從 TDX API 獲取機場 {iata_code}")
                    self.airports_cache[iata_code] = airport
                    return airport
            except Exception as e:
                logger.error(f"從 TDX API 獲取機場 {iata_code} 失敗: {str(e)}")
        
        # 如果 TDX 獲取失敗或是問題機場，嘗試從 FlightStats 獲取
        if not airport and self.flightstats_api:
            try:
                airport = self.flightstats_api.get_airport(iata_code)
                if airport:
                    logger.info(f"已從 FlightStats API 獲取機場 {iata_code}")
                    self.airports_cache[iata_code] = airport
                    return airport
            except Exception as e:
                logger.error(f"從 FlightStats API 獲取機場 {iata_code} 失敗: {str(e)}")
        
        logger.warning(f"無法從任何 API 獲取機場 {iata_code}")
        return None
    
    def sync_airlines(self) -> List[Dict]:
        """
        同步航空公司數據，填充內部緩存，但返回空列表以防止資料庫更新。
        
        Returns:
            一個空列表。
        """
        # 此列表僅用於內部填充緩存，不會被返回
        airlines_for_cache = [] 
        processed_iata_codes = set() # 追蹤已處理的IATA代碼
        
        # 先從 TDX API 獲取目標航空公司資料
        if self.tdx_api:
            try:
                tdx_airlines = self.tdx_api.get_airlines()
                if tdx_airlines:
                    logger.info(f"已從 TDX API 獲取 {len(tdx_airlines)} 個航空公司用於緩存")
                    for airline in tdx_airlines:
                        # 確保鍵名統一
                        iata_code = airline.get('iata_code')
                        if iata_code and iata_code in TARGET_AIRLINES and iata_code not in processed_iata_codes:
                            airlines_for_cache.append(airline)
                            processed_iata_codes.add(iata_code)
            except Exception as e:
                logger.error(f"從 TDX API 獲取航空公司資料失敗: {str(e)}")
        
        # 從 FlightStats 獲取目標航空公司資料 (僅獲取 TDX 未提供的)
        if self.flightstats_api:
            missing_airlines = [code for code in TARGET_AIRLINES if code not in processed_iata_codes]
            
            if missing_airlines:
                logger.info(f"嘗試從 FlightStats 獲取 {len(missing_airlines)} 個航空公司用於緩存: {missing_airlines}")
                for iata_code in missing_airlines:
                    try:
                        time.sleep(self.request_delay)  # 添加延遲避免請求過於頻繁
                        airline = self.flightstats_api.get_airline(iata_code)
                        if airline:
                            # 確保鍵名統一
                            if 'iata' in airline and 'iata_code' not in airline:
                                airline['iata_code'] = airline.pop('iata')
                            
                            # 再次確認是目標航空公司且未處理過
                            fetched_code = airline.get('iata_code')
                            if fetched_code and fetched_code == iata_code and fetched_code not in processed_iata_codes:
                                airlines_for_cache.append(airline)
                                processed_iata_codes.add(fetched_code)
                                logger.info(f"已從 FlightStats 獲取航空公司 {iata_code} 用於緩存")
                    except Exception as e:
                        logger.error(f"從 FlightStats 獲取航空公司 {iata_code} 失敗: {str(e)}")
        
        # 更新緩存 (使用 airlines_for_cache)
        for airline in airlines_for_cache:
            iata_code = airline.get('iata_code')
            if iata_code:
                self.airlines_cache[iata_code] = airline
        
        logger.info(f"航空公司緩存已更新，包含 {len(self.airlines_cache)} 個航空公司。")
        # **始終返回空列表**
        return []
    
    def get_airline(self, iata_code: str) -> Optional[Dict]:
        """
        獲取航空公司資料
        
        Args:
            iata_code: 航空公司 IATA 代碼
            
        Returns:
            航空公司資料字典，未找到時返回 None
        """
        # 先檢查緩存
        if iata_code in self.airlines_cache:
            return self.airlines_cache[iata_code]
        
        # 如果緩存中沒有，嘗試從 API 獲取
        airline = None
        
        # 先從 TDX API 獲取
        if self.tdx_api and iata_code in TARGET_AIRLINES:
            try:
                airline = self.tdx_api.get_airline(iata_code)
                if airline:
                    logger.info(f"已從 TDX API 獲取航空公司 {iata_code}")
                    self.airlines_cache[iata_code] = airline
                    return airline
            except Exception as e:
                logger.error(f"從 TDX API 獲取航空公司 {iata_code} 失敗: {str(e)}")
        
        # 如果 TDX 獲取失敗，嘗試從 FlightStats 獲取
        if not airline and self.flightstats_api:
            try:
                airline = self.flightstats_api.get_airline(iata_code)
                if airline:
                    logger.info(f"已從 FlightStats API 獲取航空公司 {iata_code}")
                    self.airlines_cache[iata_code] = airline
                    return airline
            except Exception as e:
                logger.error(f"從 FlightStats API 獲取航空公司 {iata_code} 失敗: {str(e)}")
        
        logger.warning(f"無法從任何 API 獲取航空公司 {iata_code}")
        return None
    
    def sync_flights(self, departure: str, arrival: str, date: Union[datetime, str], days: int = 1) -> List[Dict]:
        """
        同步航班數據
        
        Args:
            departure: 出發機場 IATA 代碼
            arrival: 目的機場 IATA 代碼
            date: 起始日期，可以是 datetime 對象或 "YYYY-MM-DD" 格式的字符串
            days: 查詢天數
            
        Returns:
            航班數據列表
        """
        if isinstance(date, str):
            date = datetime.strptime(date, "%Y-%m-%d")
        
        flights = []
        flight_keys = set()  # 用於去重的集合，存儲flight_number+departure_date
        
        # 檢查起飛機場是否為台灣機場
        if departure not in TAIWAN_AIRPORTS:
            logger.warning(f"出發機場 {departure} 不在台灣機場列表中，僅使用FlightStats API獲取數據")
            if self.flightstats_api:
                try:
                    fs_flights = self.flightstats_api.get_flights(
                        departure, arrival, date.strftime('%Y-%m-%d'), days
                    )
                    if fs_flights:
                        # 篩選目標航空公司
                        filtered_flights = [f for f in fs_flights if f.get('airline_code') in TARGET_AIRLINES]
                        if filtered_flights:
                            logger.info(f"已從 FlightStats 獲取並篩選出 {len(filtered_flights)} 個目標航空公司航班")
                            self._add_unique_flights(flights, filtered_flights, flight_keys)
                        else:
                            logger.warning(f"從 FlightStats 獲取航班後未找到目標航空公司航班")
                except Exception as e:
                    logger.error(f"從 FlightStats 獲取航班數據失敗: {str(e)}")
            return flights
        
        # 判斷航線類型（國內或國際）和機場是否為問題機場
        is_domestic = self.is_domestic_route(departure, arrival)
        
        # 使用新的判斷邏輯決定是否使用TDX API
        use_tdx = self.should_use_tdx_for_airport(departure, date)
        
        # 標記是否已從 TDX 獲取過航班數據
        tdx_flights_fetched = False
        
        # 先嘗試使用 TDX API 獲取 AE、B7、DA 航空公司的航班
        if self.tdx_api and use_tdx:
            try:
                # 獲取日期字串
                date_str = date.strftime('%Y-%m-%d')
                logger.info(f"嘗試從 TDX 獲取 {departure}->{arrival} 的 AE、B7、DA 航班")
                
                # 先嘗試獲取國內航班時刻表
                tdx_domestic_flights = self.tdx_api.get_domestic_flight_schedules(departure, date_str)
                if tdx_domestic_flights:
                    # 篩選指定航線的航班和 AE、B7、DA 航空公司
                    filtered_domestic_flights = [
                        f for f in tdx_domestic_flights 
                        if f.get('arrival_airport') == arrival and 
                        f.get('airline_code') in self.TDX_TARGET_AIRLINES
                    ]
                    
                    if filtered_domestic_flights:
                        logger.info(f"已從 TDX 國內航班 API 獲取 {len(filtered_domestic_flights)} 個 {departure}->{arrival} 航班")
                        self._add_unique_flights(flights, filtered_domestic_flights, flight_keys)
                        tdx_flights_fetched = True
                
                # 如果國內航班 API 沒有獲取到航班，嘗試獲取常規航班時刻表
                if not tdx_flights_fetched:
                    # 獲取所有航班時刻表
                    tdx_flights = self.tdx_api.get_flight_schedules(date_str)
                    if tdx_flights:
                        # 篩選指定航線的航班和 AE、B7、DA 航空公司
                        filtered_flights = [
                            f for f in tdx_flights 
                            if f.get('departure_airport') == departure and 
                            f.get('arrival_airport') == arrival and 
                            f.get('airline_code') in self.TDX_TARGET_AIRLINES
                        ]
                        
                        if filtered_flights:
                            logger.info(f"已從 TDX 常規 API 獲取 {len(filtered_flights)} 個 {departure}->{arrival} 航班")
                            self._add_unique_flights(flights, filtered_flights, flight_keys)
                            tdx_flights_fetched = True
                
                if not tdx_flights_fetched:
                    logger.warning(f"從 TDX API 獲取 {departure}->{arrival} 的 AE、B7、DA 航班返回空結果")
            except Exception as e:
                logger.error(f"從 TDX 獲取 {departure}->{arrival} 的 AE、B7、DA 航班數據失敗: {str(e)}")
            
        # 使用 FlightStats API 獲取其他航空公司的航班
        if self.flightstats_api:
            try:
                # 增加延遲避免過多請求
                time.sleep(self.request_delay)
                logger.info(f"從 FlightStats 獲取 {departure}->{arrival} 的非 AE、B7、DA 航班")
                
                fs_flights = self.flightstats_api.get_flights(
                    departure, arrival, date.strftime('%Y-%m-%d'), days
                )
                
                if fs_flights:
                    # 獲取所有目標航空公司的航班
                    all_target_flights = [f for f in fs_flights if f.get('airline_code') in TARGET_AIRLINES]
                    
                    # 分成兩組：TDX_TARGET_AIRLINES 和其他航空公司
                    tdx_airlines_flights = [
                        f for f in all_target_flights if f.get('airline_code') in self.TDX_TARGET_AIRLINES
                    ]
                    
                    other_airlines_flights = [
                        f for f in all_target_flights if f.get('airline_code') not in self.TDX_TARGET_AIRLINES
                    ]
                    
                    # 如果 TDX API 沒有獲取到 AE、B7、DA 航班，使用 FlightStats 的數據作為備用
                    if not tdx_flights_fetched and tdx_airlines_flights:
                        logger.info(f"TDX API 未獲取到數據，使用 FlightStats 獲取的 {len(tdx_airlines_flights)} 個 AE、B7、DA 航班作為備用")
                        self._add_unique_flights(flights, tdx_airlines_flights, flight_keys)
                    
                    # 添加其他航空公司的航班
                    if other_airlines_flights:
                        logger.info(f"從 FlightStats 獲取 {len(other_airlines_flights)} 個非 AE、B7、DA 的目標航空公司航班")
                        self._add_unique_flights(flights, other_airlines_flights, flight_keys)
                else:
                    logger.warning(f"從 FlightStats 獲取 {departure}->{arrival} 航班返回空結果")
            except Exception as e:
                logger.error(f"從 FlightStats 獲取 {departure}->{arrival} 航班數據失敗: {str(e)}")
        
        return flights
    
    def _add_unique_flights(self, target_list: List[Dict], source_flights: List[Dict], flight_keys: set):
        """
        將新航班添加到目標列表中，避免重複
        
        Args:
            target_list: 目標航班列表
            source_flights: 來源航班列表
            flight_keys: 已存在航班鍵的集合
        """
        for flight in source_flights:
            # 生成用於去重的鍵
            flight_number = flight.get('flight_number', '')
            departure_time = flight.get('departure_time', '') or flight.get('scheduled_departure_time', '')
            departure_date = departure_time[:10] if departure_time else ''
            flight_key = f"{flight_number}_{departure_date}"
            
            # 如果航班不重複，添加到目標列表
            if flight_key not in flight_keys:
                flight_keys.add(flight_key)
                target_list.append(flight)
    
    def sync_popular_routes(self, date: Union[datetime, str] = None, days: int = 1) -> Dict[Tuple[str, str], List[Dict]]:
        """
        同步熱門航線數據
        
        Args:
            date: 起始日期，可以是 datetime 對象或 "YYYY-MM-DD" 格式的字符串，默認為今天
            days: 查詢天數
            
        Returns:
            以航線為鍵，航班列表為值的字典
        """
        if date is None:
            date = datetime.now()
        elif isinstance(date, str):
            date = datetime.strptime(date, "%Y-%m-%d")
        
        results = {}
        
        # 同步國內航線
        for departure, arrival in self.POPULAR_DOMESTIC_ROUTES:
            logger.info(f"正在同步國內熱門航線: {departure} -> {arrival}")
            flights = self.sync_flights(departure, arrival, date, days)
            results[(departure, arrival)] = flights
            logger.info(f"完成 {departure}->{arrival} 同步，獲取 {len(flights)} 個航班")
        
        # 同步國際航線
        for departure, arrival in self.POPULAR_INTERNATIONAL_ROUTES:
            logger.info(f"正在同步國際熱門航線: {departure} -> {arrival}")
            flights = self.sync_flights(departure, arrival, date, days)
            results[(departure, arrival)] = flights
            logger.info(f"完成 {departure}->{arrival} 同步，獲取 {len(flights)} 個航班")
        
        return results
    
    def sync_taiwan_departures(self, date: Union[datetime, str] = None, days: int = 1) -> Dict[str, List[Dict]]:
        """
        同步所有從台灣出發的航班
        
        Args:
            date: 起始日期，可以是 datetime 對象或 "YYYY-MM-DD" 格式的字符串，默認為今天
            days: 查詢天數
            
        Returns:
            以機場代碼為鍵，航班列表為值的字典
        """
        if date is None:
            date = datetime.now()
        elif isinstance(date, str):
            date = datetime.strptime(date, "%Y-%m-%d")
        
        results = {}
        
        # 對台灣每個機場獲取當天航班
        for departure in TAIWAN_AIRPORTS:
            logger.info(f"正在同步從 {departure} 出發的航班")
            
            all_flights = []
            flight_keys = set()  # 用於去重
            
            # 從 TDX API 獲取 AE、B7、DA 航空公司的航班
            tdx_flights_fetched = False
            # 使用更智能的方法來判斷是否應該使用 TDX API
            use_tdx = self.should_use_tdx_for_airport(departure, date)
            if self.tdx_api and use_tdx:
                try:
                    # 獲取日期範圍內的航班
                    current_date = date
                    for day in range(days):
                        date_str = current_date.strftime('%Y-%m-%d')
                        logger.info(f"從 TDX 獲取 {departure} 在 {date_str} 的 AE、B7、DA 航空公司航班")
                        
                        # 針對 AE、B7、DA 三家航空公司使用專用的國內航班 API
                        tdx_domestic_flights = self.tdx_api.get_domestic_flight_schedules(departure, date_str)
                        if tdx_domestic_flights:
                            # 篩選出 AE、B7、DA 航空公司航班
                            domestic_flights = [
                                f for f in tdx_domestic_flights 
                                if f.get('departure_airport') == departure and 
                                f.get('airline_code') in self.TDX_TARGET_AIRLINES
                            ]
                            
                            if domestic_flights:
                                logger.info(f"從 TDX 國內航班 API 獲取到 {len(domestic_flights)} 個從 {departure} 出發的 AE、B7、DA 航班")
                                self._add_unique_flights(all_flights, domestic_flights, flight_keys)
                                tdx_flights_fetched = True
                        
                        # 獲取常規航班時刻表，篩選 AE、B7、DA 航空公司
                        flights_tdx = self.tdx_api.get_flight_schedules(date_str)
                        if flights_tdx:
                            departure_flights = [
                                f for f in flights_tdx 
                                if f.get('departure_airport') == departure and 
                                f.get('airline_code') in self.TDX_TARGET_AIRLINES
                            ]
                            
                            if departure_flights:
                                logger.info(f"從 TDX 常規 API 獲取到 {len(departure_flights)} 個從 {departure} 出發的 AE、B7、DA 航班")
                                self._add_unique_flights(all_flights, departure_flights, flight_keys)
                                tdx_flights_fetched = True
                        
                        # 移至下一天
                        current_date += timedelta(days=1)
                        
                    if not tdx_flights_fetched:
                        logger.warning(f"從 TDX API 未獲取到 {departure} 機場的 AE、B7、DA 航班")
                except Exception as e:
                    logger.error(f"從 TDX 獲取 {departure} 機場的 AE、B7、DA 航班失敗: {str(e)}")
            
            # 從 FlightStats 獲取所有航空公司的航班
            if self.flightstats_api:
                try:
                    logger.info(f"從 FlightStats 獲取 {departure} 的所有目標航空公司航班")
                    
                    # 獲取日期範圍內的航班
                    current_date = date
                    for day in range(days):
                        date_str = current_date.strftime('%Y-%m-%d')
                        
                        # 增加延遲避免請求過於頻繁
                        time.sleep(self.request_delay * 2)
                        
                        # 從 FlightStats 獲取機場出發的航班
                        if hasattr(self.flightstats_api, 'get_airport_departures'):
                            # 如果有機場出發航班的方法
                            departures = self.flightstats_api.get_airport_departures(departure, date_str)
                            
                            if departures:
                                # 篩選非 AE、B7、DA 的目標航空公司
                                non_tdx_departures = [
                                    d for d in departures 
                                    if d.get('airline_code') in TARGET_AIRLINES and 
                                    d.get('airline_code') not in self.TDX_TARGET_AIRLINES
                                ]
                                
                                # 如果 TDX API 未獲取到 AE、B7、DA 航班，也從 FlightStats 獲取
                                tdx_departures = []
                                if not tdx_flights_fetched:
                                    tdx_departures = [
                                        d for d in departures 
                                        if d.get('airline_code') in self.TDX_TARGET_AIRLINES
                                    ]
                                    if tdx_departures:
                                        logger.info(f"TDX API 未獲取到數據，從 FlightStats 獲取 {len(tdx_departures)} 個 AE、B7、DA 航班作為備用")
                                        self._add_unique_flights(all_flights, tdx_departures, flight_keys)
                                
                                # 添加非 TDX 航空公司的航班
                                if non_tdx_departures:
                                    logger.info(f"從 FlightStats 獲取到 {len(non_tdx_departures)} 個從 {departure} 出發的非 AE、B7、DA 航班")
                                    self._add_unique_flights(all_flights, non_tdx_departures, flight_keys)
                        else:
                            # 如果沒有專門的方法，使用通用方法獲取一些熱門目的地的航班
                            for arrival in ['HKG', 'NRT', 'ICN', 'PVG', 'BKK', 'SIN']:
                                if arrival != departure:  # 避免相同機場
                                    try:
                                        time.sleep(self.request_delay)  # 增加延遲
                                        flights = self.flightstats_api.get_flights(departure, arrival, date_str)
                                        
                                        if flights:
                                            # 篩選所有目標航空公司
                                            all_target_flights = [
                                                f for f in flights if f.get('airline_code') in TARGET_AIRLINES
                                            ]
                                            
                                            # 分成兩組：TDX_TARGET_AIRLINES 和其他航空公司
                                            tdx_flights = [
                                                f for f in all_target_flights 
                                                if f.get('airline_code') in self.TDX_TARGET_AIRLINES
                                            ]
                                            
                                            non_tdx_flights = [
                                                f for f in all_target_flights 
                                                if f.get('airline_code') not in self.TDX_TARGET_AIRLINES
                                            ]
                                            
                                            # 如果 TDX API 未獲取到數據，使用 FlightStats 的 AE、B7、DA 航班
                                            if not tdx_flights_fetched and tdx_flights:
                                                logger.info(f"TDX API 未獲取到數據，從 FlightStats 獲取 {len(tdx_flights)} 個 {departure} 到 {arrival} 的 AE、B7、DA 航班作為備用")
                                                self._add_unique_flights(all_flights, tdx_flights, flight_keys)
                                            
                                            # 添加非 TDX 航空公司的航班
                                            if non_tdx_flights:
                                                logger.info(f"從 FlightStats 獲取到 {len(non_tdx_flights)} 個從 {departure} 到 {arrival} 的非 AE、B7、DA 航班")
                                                self._add_unique_flights(all_flights, non_tdx_flights, flight_keys)
                                    except Exception as inner_e:
                                        logger.error(f"從 FlightStats 獲取 {departure} 到 {arrival} 航班失敗: {str(inner_e)}")
                        
                        # 移至下一天
                        current_date += timedelta(days=1)
                except Exception as e:
                    logger.error(f"從 FlightStats 獲取 {departure} 航班失敗: {str(e)}")
            
            # 保存結果
            results[departure] = all_flights
            logger.info(f"{departure} 機場總計獲取 {len(all_flights)} 個航班")
        
        return results


def main():
    """主函數，處理命令行參數並執行相應操作"""
    parser = argparse.ArgumentParser(description='航班資料同步工具')
    subparsers = parser.add_subparsers(dest='command', help='指令')
    
    # 機場同步指令
    subparsers.add_parser('airports', help='同步機場資料')
    
    # 航空公司同步指令
    subparsers.add_parser('airlines', help='同步航空公司資料')
    
    # 航班同步指令
    flights_parser = subparsers.add_parser('flights', help='同步航班資料')
    flights_parser.add_argument('--departure', '-d', required=True, help='出發機場 IATA 代碼')
    flights_parser.add_argument('--arrival', '-a', required=True, help='目的機場 IATA 代碼')
    flights_parser.add_argument('--date', default=datetime.now().strftime('%Y-%m-%d'), help='查詢日期（YYYY-MM-DD 格式），預設為今天')
    flights_parser.add_argument('--days', type=int, default=1, help='查詢天數，預設為 1')
    
    # 熱門航線同步指令
    popular_parser = subparsers.add_parser('popular', help='同步熱門航線資料')
    popular_parser.add_argument('--date', default=datetime.now().strftime('%Y-%m-%d'), help='查詢日期（YYYY-MM-DD 格式），預設為今天')
    popular_parser.add_argument('--days', type=int, default=1, help='查詢天數，預設為 1')
    
    # 台灣出發航班同步指令
    taiwan_parser = subparsers.add_parser('taiwan', help='同步從台灣出發的航班資料')
    taiwan_parser.add_argument('--date', default=datetime.now().strftime('%Y-%m-%d'), help='查詢日期（YYYY-MM-DD 格式），預設為今天')
    taiwan_parser.add_argument('--days', type=int, default=1, help='查詢天數，預設為 1')
    
    args = parser.parse_args()
    
    # 初始化同步管理器
    sync_manager = ApiSyncManager()
    
    # 根據指令執行相應操作
    if args.command == 'airports':
        airports = sync_manager.sync_airports()
        print(json.dumps(airports, ensure_ascii=False, indent=2))
    
    elif args.command == 'airlines':
        airlines = sync_manager.sync_airlines()
        print(json.dumps(airlines, ensure_ascii=False, indent=2))
    
    elif args.command == 'flights':
        flights = sync_manager.sync_flights(args.departure, args.arrival, args.date, args.days)
        print(json.dumps(flights, ensure_ascii=False, indent=2))
    
    elif args.command == 'popular':
        popular_routes = sync_manager.sync_popular_routes(args.date, args.days)
        # 轉換結果為可序列化的格式
        result = {}
        for route, flights in popular_routes.items():
            result[f"{route[0]}-{route[1]}"] = flights
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif args.command == 'taiwan':
        taiwan_departures = sync_manager.sync_taiwan_departures(args.date, args.days)
        print(json.dumps(taiwan_departures, ensure_ascii=False, indent=2))
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 