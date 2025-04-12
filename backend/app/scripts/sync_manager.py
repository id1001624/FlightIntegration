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
import time  # 添加此行，用於請求延遲

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('sync_manager')

# 導入 API 客戶端
try:
    from tdx_sync import TdxApiClient
    from flightstats_sync import FlightStatsApiClient
except ImportError:
    # 嘗試相對導入
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.append(current_dir)
    try:
        from tdx_sync import TdxApiClient
        from flightstats_sync import FlightStatsApiClient
    except ImportError as e:
        logger.error(f"無法導入 API 客戶端: {str(e)}")
        sys.exit(1)

class ApiSyncManager:
    """API 同步管理器，協調 TDX 和 FlightStats API 的數據同步"""
    
    # 台灣機場代碼列表（用於判斷是否為國內或國際航線）
    TAIWAN_AIRPORTS = ['TPE', 'TSA', 'RMQ', 'KHH', 'TNN', 'CYI', 'HUN', 'TTT', 'KNH', 'MZG', 'LZN', 'MFK', 'KYD', 'GNI', 'WOT']
    
    # 暫時清空此列表，讓所有機場優先嘗試TDX API
    TDX_PROBLEMATIC_AIRPORTS = [] 
    
    # 指定航空公司列表
    TARGET_AIRLINES = ['AE', 'B7', 'BR', 'CI', 'CX', 'DA', 'IT', 'JL', 'JX', 'OZ']
    
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
        return departure in self.TAIWAN_AIRPORTS and arrival in self.TAIWAN_AIRPORTS
    
    def is_taiwan_departure(self, departure: str) -> bool:
        """
        判斷是否為從台灣出發的航線
        
        Args:
            departure: 出發機場 IATA 代碼
            
        Returns:
            True 如果是從台灣出發，否則 False
        """
        return departure in self.TAIWAN_AIRPORTS
    
    def is_target_airline(self, airline_code: str) -> bool:
        """
        判斷是否為目標航空公司
        
        Args:
            airline_code: 航空公司 IATA 代碼
            
        Returns:
            True 如果是目標航空公司，否則 False
        """
        return airline_code in self.TARGET_AIRLINES
    
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
        missing_airports = [code for code in self.TAIWAN_AIRPORTS if code not in taiwan_iata_codes]
        
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
        if self.tdx_api and iata_code in self.TAIWAN_AIRPORTS and iata_code not in self.TDX_PROBLEMATIC_AIRPORTS:
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
                        if iata_code and iata_code in self.TARGET_AIRLINES and iata_code not in processed_iata_codes:
                             airlines_for_cache.append(airline)
                             processed_iata_codes.add(iata_code)
            except Exception as e:
                logger.error(f"從 TDX API 獲取航空公司資料失敗: {str(e)}")
        
        # 從 FlightStats 獲取目標航空公司資料 (僅獲取 TDX 未提供的)
        if self.flightstats_api:
            missing_airlines = [code for code in self.TARGET_AIRLINES if code not in processed_iata_codes]
            
            if missing_airlines:
                logger.info(f"嘗試從 FlightStats 獲取 {len(missing_airlines)} 個航空公司用於緩存: {missing_airlines}")
                for iata_code in missing_airlines:
                    try:
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
        if self.tdx_api and iata_code in self.TARGET_AIRLINES:
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
        if departure not in self.TAIWAN_AIRPORTS:
            logger.warning(f"出發機場 {departure} 不在台灣機場列表中，僅使用FlightStats API獲取數據")
            if self.flightstats_api:
                try:
                    fs_flights = self.flightstats_api.get_flights(
                        departure, arrival, date.strftime('%Y-%m-%d'), days
                    )
                    if fs_flights:
                        # 篩選目標航空公司
                        filtered_flights = [f for f in fs_flights if f.get('airline_code') in self.TARGET_AIRLINES]
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
        is_problematic = departure in self.TDX_PROBLEMATIC_AIRPORTS or arrival in self.TDX_PROBLEMATIC_AIRPORTS
        
        # 國內航線且非問題機場優先使用 TDX API
        if is_domestic and not is_problematic and self.tdx_api:
            try:
                tdx_flights = self.tdx_api.get_flights(departure, arrival, date.strftime('%Y-%m-%d'), days)
                if tdx_flights:
                    logger.info(f"已從 TDX 獲取 {len(tdx_flights)} 個航班")
                    self._add_unique_flights(flights, tdx_flights, flight_keys)
                else:
                    logger.warning(f"從 TDX 獲取 {departure}->{arrival} 航班返回空結果")
            except Exception as e:
                logger.error(f"從 TDX 獲取航班數據失敗: {str(e)}")

        # 同時使用 FlightStats 獲取國際航線或補充數據
        # 條件：非國內線 or 是問題機場 or TDX結果數量小於預期
        if (not is_domestic or is_problematic or len(flights) < self.MIN_EXPECTED_FLIGHTS) and self.flightstats_api:
            try:
                # 增加延遲避免過多請求
                time.sleep(self.request_delay)
                fs_flights = self.flightstats_api.get_flights(
                    departure, arrival, date.strftime('%Y-%m-%d'), days
                )
                if fs_flights:
                    # 篩選目標航空公司
                    filtered_flights = [f for f in fs_flights if f.get('airline_code') in self.TARGET_AIRLINES]
                    if filtered_flights:
                        logger.info(f"已從 FlightStats 獲取並篩選出 {len(filtered_flights)} 個目標航空公司航班")
                        self._add_unique_flights(flights, filtered_flights, flight_keys)
                    else:
                        logger.warning(f"從 FlightStats 獲取航班後未找到目標航空公司航班")
            except Exception as e:
                logger.error(f"從 FlightStats 獲取航班數據失敗: {str(e)}")

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
            departure_time = flight.get('departure_time', '')
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
        for departure in self.TAIWAN_AIRPORTS:
            all_flights = []
            flight_keys = set()  # 用於去重
            tdx_original_count = 0  # TDX原始獲取航班數
            tdx_filtered_count = 0  # TDX過濾後航班數
            
            # 判斷是否為問題機場
            is_problematic = departure in self.TDX_PROBLEMATIC_AIRPORTS
            
            # 非問題機場使用TDX API
            if self.tdx_api and not is_problematic:
                try:
                    logger.info(f"正在獲取從 {departure} 出發的所有航班 (TDX)")

                    # 使用TDX API的FIDS功能獲取航班信息
                    current_date = date
                    for day in range(days):
                        date_str = current_date.strftime('%Y-%m-%d')
                        try:
                            # 獲取當天的FIDS數據
                            fids_flights = self.tdx_api.get_fids_flights(departure, date_str)
                            if fids_flights:
                                logger.info(f"TDX API原始返回 {departure} 機場的 {len(fids_flights)} 個航班")
                                tdx_original_count += len(fids_flights)

                                # 記錄非目標航空公司的航班
                                non_target_flights = [f.get('AirlineID', '') for f in fids_flights
                                                    if f.get('AirlineID', '') not in self.TARGET_AIRLINES]
                                if non_target_flights:
                                    logger.info(f"發現非目標航空公司航班: {set(non_target_flights)}")

                                # 處理成標準航班格式
                                processed_flights = []
                                time_parse_failed = 0
                                for flight in fids_flights:
                                    try: # Inner try for processing a single flight record
                                        airline_code = flight.get('AirlineID', '')
                                        # 放寬航空公司過濾條件，如果非目標航空公司，記錄但不中斷處理
                                        if airline_code not in self.TARGET_AIRLINES:
                                            continue

                                        flight_number = flight.get('FlightNumber', '')
                                        arrival_airport = flight.get('ArrivalAirportID', '')

                                        # 詳細日誌：原始時間字符串
                                        sched_dep_time = flight.get('ScheduleDepartureTime')
                                        logger.debug(f"航班 {airline_code}{flight_number} 原始時間: {sched_dep_time}")

                                        # 解析時間 - 增加對多種格式的支持
                                        dep_time = None
                                        if sched_dep_time:
                                            # Inner try specifically for parsing time
                                            try:
                                                # 嘗試多種時間格式
                                                formats = [
                                                    '%Y-%m-%dT%H:%M',
                                                    '%Y-%m-%dT%H:%M:%S',
                                                    '%Y-%m-%d %H:%M:%S',
                                                    '%Y-%m-%d %H:%M'
                                                ]
                                                for fmt in formats:
                                                    try:
                                                        dep_time = datetime.strptime(sched_dep_time, fmt)
                                                        logger.debug(f"成功使用格式 {fmt} 解析時間")
                                                        break
                                                    except ValueError:
                                                        continue # Try next format

                                                if not dep_time:
                                                    # 如果依然無法解析，嘗試手動解析
                                                    parts = sched_dep_time.replace('T', ' ').split(' ')
                                                    if len(parts) >= 2:
                                                        date_part = parts[0]
                                                        time_part = parts[1].split('.')[0]  # 去除毫秒
                                                        try:
                                                            dep_time = datetime.strptime(
                                                                f"{date_part} {time_part}",
                                                                "%Y-%m-%d %H:%M" if len(time_part) <= 5 else "%Y-%m-%d %H:%M:%S"
                                                            )
                                                            logger.debug(f"成功使用手動解析處理時間")
                                                        except ValueError:
                                                            logger.warning(f"手動解析時間失敗: {date_part} {time_part}")

                                                    if not dep_time and '/' in sched_dep_time:
                                                        # 嘗試處理可能的日期格式 MM/DD/YYYY
                                                        try:
                                                            dep_time = datetime.strptime(sched_dep_time, '%m/%d/%Y %H:%M')
                                                            logger.debug(f"成功解析MM/DD/YYYY格式")
                                                        except ValueError:
                                                            pass # Failed MM/DD/YYYY format
                                            except Exception as e_time: # Catch errors during time parsing
                                                time_parse_failed += 1
                                                logger.warning(f"無法解析出發時間: {sched_dep_time}, 錯誤: {str(e_time)}")
                                                continue # Skip to next flight if time parsing fails
                                        else:
                                            time_parse_failed += 1
                                            logger.warning(f"航班 {airline_code}{flight_number} 缺少出發時間")
                                            continue # Skip to next flight if time is missing

                                        if not dep_time:
                                            time_parse_failed += 1
                                            logger.warning(f"所有格式都無法解析時間: {sched_dep_time}")
                                            continue # Skip to next flight if time parsing fails

                                        # --- Process flight data if time parsed successfully ---

                                        # 預估到達時間
                                        is_domestic = arrival_airport in self.TAIWAN_AIRPORTS
                                        flight_hours = 1 if is_domestic else 3
                                        arr_time = dep_time + timedelta(hours=flight_hours)

                                        flight_id = f"{airline_code}{flight_number}_{dep_time.strftime('%Y%m%d')}"
                                        full_flight_number = f"{airline_code}{flight_number}"

                                        # 檢查是否重複
                                        flight_key = f"{full_flight_number}_{dep_time.strftime('%Y-%m-%d')}"
                                        if flight_key in flight_keys:
                                            logger.debug(f"跳過重複航班: {flight_key}")
                                            continue

                                        flight_keys.add(flight_key)

                                        processed_flight = {
                                            'flight_id': flight_id,
                                            'flight_number': full_flight_number,
                                            'airline_code': airline_code,
                                            'departure_airport': departure,
                                            'arrival_airport': arrival_airport,
                                            'departure_time': dep_time.strftime('%Y-%m-%dT%H:%M:%S'),
                                            'arrival_time': arr_time.strftime('%Y-%m-%dT%H:%M:%S'),
                                            'status': self.tdx_api._map_flight_status(flight.get('DepartureRemark', '')),
                                            'data_source': 'TDX'
                                        }
                                        processed_flights.append(processed_flight)

                                    except Exception as e_process: # Catch errors during the processing of a single flight record
                                        logger.error(f"處理航班數據時出錯: {str(e_process)}")
                                        continue # Continue to the next flight in the loop

                                # 添加到結果中
                                tdx_filtered_count += len(processed_flights)
                                self._add_unique_flights(all_flights, processed_flights, flight_keys)
                                logger.info(f"從 {departure} 獲取了 {len(processed_flights)} 個 {date_str} 的航班")

                                # 記錄過濾情況
                                if time_parse_failed > 0:
                                    logger.warning(f"{departure} 有 {time_parse_failed} 個航班因時間解析問題被過濾")
                                elif not fids_flights: # Corrected the logic to check if fids_flights was empty
                                    logger.warning(f"TDX API 返回 {departure} 機場 {date_str} 空數據")
                        except Exception as day_fetch_e:
                            logger.error(f"獲取 {departure} 在 {date_str} 的TDX航班時出錯: {day_fetch_e}")
                        finally:
                            # 移至下一天
                            current_date += timedelta(days=1)
                except Exception as e_tdx_block: # Catch errors for the entire TDX block
                    logger.error(f"處理 {departure} 的TDX航班時發生頂層錯誤: {str(e_tdx_block)}")

            # 使用FlightStats API補充或替代
            # 修改判斷邏輯：問題機場、TDX數據為空或TDX數據少於預期時使用FlightStats
            use_flightstats = (is_problematic or
                              not all_flights or
                              len(all_flights) < self.MIN_EXPECTED_FLIGHTS or
                              (tdx_original_count > 0 and tdx_filtered_count == 0))

            if self.flightstats_api and use_flightstats:
                try:
                    reasons = []
                    if is_problematic:
                        reasons.append("問題機場")
                    if not all_flights:
                        reasons.append("TDX數據為空")
                    if len(all_flights) < self.MIN_EXPECTED_FLIGHTS:
                        reasons.append("航班數量少於預期")
                    if tdx_original_count > 0 and tdx_filtered_count == 0:
                        reasons.append("TDX數據全被過濾")

                    reason_text = ", ".join(reasons)
                    logger.info(f"{departure} 因為{reason_text}，使用FlightStats獲取數據 (將調用 get_airport_departures)")

                    # **修改備用邏輯：調用 get_airport_departures**
                    current_date_fs = date # 從請求的日期開始
                    for day in range(days):
                        try:
                            date_str_fs = current_date_fs.strftime('%Y-%m-%d')
                            logger.info(f"FlightStats: 正在獲取 {departure} 在 {date_str_fs} 的所有出發航班")
                            # 增加延遲
                            time.sleep(self.request_delay * 2)
                            fs_departures = self.flightstats_api.get_airport_departures(
                                departure, date_str_fs
                            )

                            if fs_departures:
                                logger.info(f"FlightStats 原始返回 {len(fs_departures)} 個 {departure} 的出發航班")
                                # 篩選目標航空公司並處理
                                filtered_flights = []
                                for flight in fs_departures:
                                    try:
                                        if flight.get('carrierFsCode', '') in self.TARGET_AIRLINES:
                                            # 需要知道到達機場才能處理，從原始數據中獲取
                                            arrival_airport = flight.get('arrivalAirportFsCode', '')
                                            if arrival_airport:
                                                processed = self.flightstats_api._process_flight_data(flight, departure, arrival_airport)
                                                if processed:
                                                    filtered_flights.append(processed)
                                            else:
                                                logger.warning(f"FlightStats返回的航班缺少到達機場: {flight.get('carrierFsCode')}{flight.get('flightNumber')}")
                                    except Exception as inner_e:
                                        logger.error(f"處理FlightStats航班時出錯: {inner_e}")

                                if filtered_flights:
                                    logger.info(f"從 FlightStats 獲取並處理了 {len(filtered_flights)} 個目標航空公司航班")
                                    self._add_unique_flights(all_flights, filtered_flights, flight_keys)
                                else:
                                    logger.info(f"FlightStats 返回的 {departure} 出發航班中沒有目標航空公司")
                            else:
                                logger.info(f"FlightStats 未返回 {departure} 在 {date_str_fs} 的出發航班數據")
                        except Exception as day_e:
                             logger.error(f"FlightStats: 獲取 {departure} 在 {date_str_fs} 的出發航班時出錯: {day_e}")
                        finally:
                           current_date_fs += timedelta(days=1) # 移至下一天

                except Exception as e_fs_block:
                    logger.error(f"使用FlightStats備用邏輯獲取 {departure} 航班時出錯: {str(e_fs_block)}")

            # 保存結果
            results[departure] = all_flights
            logger.info(f"{departure} 機場總計獲取 {len(all_flights)} 個航班")
            
            # 詳細總結
            summary = {
                "機場": departure,
                "TDX原始航班數": tdx_original_count,
                "TDX過濾後航班數": tdx_filtered_count,
                "最終航班數": len(all_flights),
                "數據來源": "FlightStats" if is_problematic else ("混合" if len(all_flights) > tdx_filtered_count else "TDX")
            }
            logger.info(f"航班同步摘要: {summary}")
        
        return results


def main():
    """主函數，處理命令行參數並執行相應操作"""
    parser = argparse.ArgumentParser(description='航班資料同步工具')
    subparsers = parser.add_subparsers(dest='command', help='指令')
    
    # 機場同步指令
    airports_parser = subparsers.add_parser('airports', help='同步機場資料')
    
    # 航空公司同步指令
    airlines_parser = subparsers.add_parser('airlines', help='同步航空公司資料')
    
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