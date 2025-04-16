#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
API 同步管理器，集成 TDX 和 FlightStats API 數據同步功能
"""
import os
import sys

# 獲取當前腳本所在的目錄
script_dir = os.path.dirname(os.path.abspath(__file__))
# 獲取 backend 目錄的路徑 (scripts 的上一級)
backend_dir = os.path.dirname(script_dir)

# 將 backend 目錄添加到 sys.path
# 這樣 Python 就能找到 app 包了
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import json
import logging
import argparse
from datetime import datetime as dt_datetime
from datetime import timedelta as dt_timedelta
from ..utils.date_utils import parse_datetime, format_datetime
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
    from app.scripts.constants import (
        TAIWAN_AIRPORTS,
        TARGET_AIRLINES,
        POPULAR_DOMESTIC_ROUTES_TUPLES,
        POPULAR_INTERNATIONAL_ROUTES_TUPLES
    )
    # 添加模型導入
    from app.models.airline import Airline 
    from app.models.airport import Airport
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
        except ImportError as e: # Inner try needs an except
            logger.error(f"無法導入任何版本的 API 客戶端: {str(e)}")
        sys.exit(1)

from ..models.flight import FlightStatus # 確保導入 FlightStatus Enum

# --- 狀態映射輔助函數 ---
def map_tdx_status(dep_remark: str, arr_remark: str) -> str:
    """根據 TDX 的備註推斷航班狀態"""
    # 優先判斷取消
    if "取消" in dep_remark or "取消" in arr_remark:
        return FlightStatus.CANCELLED.value # 返回 Enum 成員的值
    # 再判斷到達
    if "抵達" in arr_remark:
         return FlightStatus.ARRIVED.value # 返回 Enum 成員的值
    # 再判斷起飛
    if "已飛" in dep_remark:
        return FlightStatus.DEPARTED.value # 返回 Enum 成員的值
    # 再判斷延誤
    if "延誤" in dep_remark or "延誤" in arr_remark:
         return FlightStatus.DELAYED.value # 返回 Enum 成員的值
    # 其他情況（如 "準時", "登機"）視為準時
    return FlightStatus.ON_TIME.value # 返回 Enum 成員的值
# --- 結束狀態映射 ---

# --- TDX 數據格式化輔助函數 ---
def format_tdx_flight(raw_flight: Dict) -> Optional[Dict]:
    """將 TDX 原始航班數據轉換為內部格式"""
    try:
        airline_id = raw_flight.get('AirlineID')
        flight_number = raw_flight.get('FlightNumber')
        flight_date = raw_flight.get('FlightDate')
        
        # 確保關鍵字段存在
        if not airline_id or not flight_number or not flight_date:
             logger.warning(f"TDX 原始數據缺少關鍵字段: {raw_flight}")
             return None
             
        scheduled_dep = raw_flight.get('ScheduleDepartureTime')
        scheduled_arr = raw_flight.get('ScheduleArrivalTime')
        actual_dep = raw_flight.get('ActualDepartureTime') # 可能為 None
        actual_arr = raw_flight.get('ActualArrivalTime') # 可能為 None
        
        # 狀態映射 (從 Remark 推斷)
        dep_remark = raw_flight.get('DepartureRemark', '')
        arr_remark = raw_flight.get('ArrivalRemark', '')
        status = map_tdx_status(dep_remark, arr_remark)

        return {
            'flight_number': airline_id + flight_number,
            'airline_id': airline_id,
            'flight_id': f"TDX_{airline_id}{flight_number}_{flight_date}", # 創建唯一ID
            'departure_airport_id': raw_flight.get('DepartureAirportID', ''),
            'arrival_airport_id': raw_flight.get('ArrivalAirportID', ''),
            'scheduled_departure': format_datetime(parse_datetime(scheduled_dep)) if scheduled_dep else None,
            'scheduled_arrival': format_datetime(parse_datetime(scheduled_arr)) if scheduled_arr else None,
            'actual_departure': format_datetime(parse_datetime(actual_dep)) if actual_dep else None,
            'actual_arrival': format_datetime(parse_datetime(actual_arr)) if actual_arr else None,
            'status': status,
            'departure_terminal': raw_flight.get('DepartureTerminal', ''),
            'departure_gate': raw_flight.get('DepartureGate', ''),
            'arrival_terminal': raw_flight.get('ArrivalTerminal', ''),
            'arrival_gate': raw_flight.get('ArrivalGate', ''),
            # 'aircraft': '', # TDX FIDS 不提供飛機型號
            'source': 'TDX'
        }
    except Exception as e:
        logger.error(f"格式化 TDX 航班數據時出錯: {raw_flight}, 錯誤: {e}")
        return None
# --- 結束格式化 ---

class ApiSyncManager:
    """API 同步管理器，協調 TDX 和 FlightStats API 的數據同步"""
    
    # 暫時清空此列表，讓所有機場優先嘗試TDX API
    TDX_PROBLEMATIC_AIRPORTS = [] 
    
    # TDX API 專用航空公司代碼 (台灣國內航空公司)
    TDX_TARGET_AIRLINES = ['AE', 'B7', 'DA']  # 華信航空、立榮航空、德安航空
    
    # 最小期望航班數量（低於此數量將使用FlightStats補充）
    MIN_EXPECTED_FLIGHTS = 1
    
    def __init__(self):
        """初始化同步管理器"""
        # 初始化 logger 屬性
        self.logger = logging.getLogger('sync_manager')
        
        try:
            self.tdx_api = TdxApiClient()
            self.logger.info("已初始化 TDX API 客戶端")
        except Exception as e:
            self.tdx_api = None
            self.logger.error(f"初始化 TDX API 客戶端出錯: {str(e)}")
        
        try:
            self.flightstats_api = FlightStatsApiClient()
            self.logger.info("已初始化 FlightStats API 客戶端")
        except Exception as e:
            self.flightstats_api = None
            self.logger.error(f"初始化 FlightStats API 客戶端出錯: {str(e)}")
        
        # 檢查至少一個 API 客戶端可用
        if not self.tdx_api and not self.flightstats_api:
            self.logger.error("無法初始化任何 API 客戶端，同步功能將無法使用")
        
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
    
    def should_use_tdx_for_airport(self, airport_code: str, date: dt_datetime = None) -> bool:
        """
        判斷指定機場在特定日期是否應該使用TDX API
        
        Args:
            airport_code: 機場IATA代碼
            date: 日期，默認為今天
        
        Returns:
            是否應該使用TDX API
        """
        if not date:
            date = dt_datetime.now()
        
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
    
    def sync_airports(self):
        """同步機場數據"""
        self.logger.info("開始同步機場數據...")
        added_count = 0
        updated_count = 0

        # 這裡的邏輯需要重新考慮。
        # 如果完全依賴資料庫，這個同步方法可能不再需要，
        # 或者需要從其他來源（如文件、管理界面）獲取數據。
        # 暫時將其留空或只記錄一條信息。
        self.logger.info("機場同步功能當前依賴資料庫數據，未執行外部API同步。")

        # 原有的合併和更新邏輯基於API數據，現已移除
        # all_airports_data = self._merge_airport_data(tdx_airports, flightstats_airports)
        # ... (原有的 database update/add logic)

        self.logger.info(f"機場同步完成。新增: {added_count}, 更新: {updated_count}")
        # 確保方法有返回值，即使是空的
        return []
    
    def get_airport(self, iata_code: str) -> Optional[Dict]:
        """嘗試從不同來源獲取機場資訊，優先使用資料庫"""
        if not iata_code:
            return None

        iata_code = iata_code.strip().upper()
        self.logger.debug(f"正在獲取機場資訊: {iata_code}")

        # 1. 優先從資料庫查詢
        try:
            airport_db = Airport.get_by_iata(iata_code)
            if airport_db:
                self.logger.debug(f"從資料庫找到機場 {iata_code}")
                # 將模型對象轉換為字典以保持一致性
                return {
                    'airport_id': airport_db.airport_id,
                    'name_zh': airport_db.name_zh,
                    'name_en': airport_db.name_en,
                    'city': airport_db.city,
                    'city_en': airport_db.city_en,
                    'country': airport_db.country,
                    'timezone': airport_db.timezone,
                    'contact_info': airport_db.contact_info,
                    'website_url': airport_db.website_url,
                    'source': 'database'
                }
        except Exception as e:
            self.logger.error(f"從資料庫查詢機場 {iata_code} 時出錯: {e}")
            return None
        
        self.logger.warning(f"在資料庫中未找到機場資訊: {iata_code}")
        return None
    
    def sync_airlines(self) -> List[Dict]:
        """同步航空公司數據 - 當前版本依賴資料庫數據，不執行外部同步"""
        self.logger.info("開始同步航空公司數據...")
        
        
        self.logger.info("航空公司同步功能當前依賴資料庫數據，未執行外部API同步。")
        
        # 始終返回空列表，因為此方法不再產生需要處理的外部數據
        return []
    
    def get_airline(self, iata_code: str) -> Optional[Dict]:
        """直接從資料庫獲取航空公司資料"""
        if not iata_code:
            return None
            
        iata_code = iata_code.strip().upper()
        self.logger.debug(f"正在從資料庫獲取航空公司資訊: {iata_code}")
        
        # 直接查詢資料庫
        try:
            airline_db = Airline.get_by_iata(iata_code)
            if airline_db:
                self.logger.debug(f"從資料庫找到航空公司 {iata_code}")
                # 將模型對象轉換為字典
                return {
                    'airline_id': airline_db.airline_id,
                    'name_zh': airline_db.name_zh,
                    'name_en': airline_db.name_en,
                    'website': airline_db.website,
                    'contact_phone': airline_db.contact_phone,
                    'is_domestic': airline_db.is_domestic,
                    'source': 'database'
                }
            else:
                # 如果資料庫沒有找到，明確記錄並返回 None
                self.logger.warning(f"在資料庫中未找到航空公司: {iata_code}")
                return None
        except Exception as e:
            self.logger.error(f"從資料庫查詢航空公司 {iata_code} 時出錯: {e}")
            return None
    
    def sync_flights(self, departure: str, arrival: str, date: Union[dt_datetime, str], days: int = 1) -> List[Dict]:
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
            date = dt_datetime.strptime(date, "%Y-%m-%d")
        
        flights = []
        flight_keys = set()  # 用於去重的集合，存儲flight_number+departure_date
        
        # 檢查起飛機場是否為台灣機場
        if departure not in TAIWAN_AIRPORTS:
            logger.warning(f"出發機場 {departure} 不在台灣機場列表中，僅使用FlightStats API獲取數據")
            if self.flightstats_api:
                try:
                    fs_flights = self.flightstats_api.get_flights(
                        departure, arrival, date.strftime('%Y-%m-%d')
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
                tdx_raw_flights = self.tdx_api.get_domestic_flight_schedules(departure)
                if isinstance(tdx_raw_flights, list):
                    # --- 篩選邏輯在此 ---
                    tdx_domestic_flights = [
                        f for f in tdx_raw_flights 
                        if f.get('DepartureAirportID') == departure and  # <-- 使用 DepartureAirportID
                           self.is_tdx_target_airline(f.get('AirlineID')) # <-- 使用 AirlineID
                    ]
                    # --- 結束篩選 ---
                    logger.info(f"TDX API 為 {departure} on {date_str} 返回 {len(tdx_raw_flights)} 原始記錄, 篩選後得到 {len(tdx_domestic_flights)} 個 AE/B7/DA 航班")
                    if tdx_domestic_flights:
                        self._add_unique_flights(flights, tdx_domestic_flights, flight_keys)
                        tdx_flights_fetched = True
                
                if not tdx_flights_fetched:
                    logger.warning(f"從 TDX API 獲取 {departure}->{arrival} 的 AE、B7、DA 航班返回空結果")
            except Exception as e: # Correctly indented except block for TDX
                logger.error(f"從 TDX 獲取 {departure}->{arrival} 的 AE、B7、DA 航班數據失敗: {str(e)}")
            
        # 使用 FlightStats API 獲取其他航空公司的航班
        if self.flightstats_api: # Correct indentation for this block
            try: # Try block for flightstats starts here
                time.sleep(self.request_delay)
                logger.info(f"從 FlightStats 獲取 {departure}->{arrival} 的非 AE、B7、DA 航班")

                # Correct indentation for the API call
                fs_flights = self.flightstats_api.get_flights(
                    departure, arrival, date.strftime('%Y-%m-%d')
                )

                # Correct indentation for the conditional block
                if fs_flights:
                    # Correct indentation for list comprehensions
                    all_target_flights = [f for f in fs_flights if f.get('airline_code') in TARGET_AIRLINES]

                    other_airlines_flights = [
                        f for f in all_target_flights if f.get('airline_code') not in self.TDX_TARGET_AIRLINES
                    ]

                    if other_airlines_flights:
                        logger.info(f"從 FlightStats 獲取 {len(other_airlines_flights)} 個非 AE、B7、DA 的目標航空公司航班")
                        self._add_unique_flights(flights, other_airlines_flights, flight_keys)
                else: # Correct indentation for the else block
                    # Correct indentation for the logger warning
                    logger.warning(f"從 FlightStats 獲取 {departure}->{arrival} 航班返回空結果")
            except Exception as e: # Correctly indented except block for FlightStats
                logger.error(f"從 FlightStats 獲取 {departure}->{arrival} 航班數據失敗: {str(e)}")
        
        return flights
    
    def _add_unique_flights(self, target_list: List[Dict], source_flights: List[Dict], flight_keys: set):
        """
        將新航班添加到目標列表中，避免重複。假設 source_flights 中的數據已格式化。
        
        Args:
            target_list: 目標航班列表
            source_flights: 來源航班列表 (應為內部格式)
            flight_keys: 已存在航班鍵的集合
        """
        added_count = 0
        for flight in source_flights:
            # 確保 flight 是字典並且非空
            if not isinstance(flight, dict) or not flight:
                logger.warning(f"跳過無效的航班數據: {flight}")
                continue
                
            # 使用內部格式的鍵生成去重鍵
            flight_number = flight.get('flight_number', '')
            # 優先使用 scheduled_departure
            departure_dt_str = flight.get('scheduled_departure') or flight.get('departure_time') # 兼容舊鍵
            if isinstance(departure_dt_str, dt_datetime):
                # 如果是 datetime 物件，格式化為 YYYY-MM-DD
                departure_date = departure_dt_str.strftime('%Y-%m-%d')
            elif isinstance(departure_dt_str, str) and len(departure_dt_str) >= 10:
                # 如果是足夠長的字串，取前10個字符
                departure_date = departure_dt_str[:10]
            else:
                # 其他情況（None 或格式不符）設為空字串
                departure_date = ''
            
            # 確保 flight_number 和 departure_date 都存在
            if not flight_number or not departure_date:
                 logger.warning(f"無法為航班生成唯一鍵，缺少 flight_number 或 departure_date: {flight}")
                 continue
                 
            flight_key = f"{flight_number}_{departure_date}"
            
            # 如果航班不重複，添加到目標列表
            if flight_key not in flight_keys:
                flight_keys.add(flight_key)
                target_list.append(flight)
                added_count += 1
            # else:
            #     logger.debug(f"跳過重複航班: {flight_key}")
        # logger.info(f"添加了 {added_count} 個唯一航班") # 可以取消註釋以調試
    
    def sync_popular_routes(self, date: Union[dt_datetime, str] = None, days: int = 1) -> Dict[Tuple[str, str], List[Dict]]:
        """
        同步熱門航線數據
        
        Args:
            date: 起始日期，可以是 datetime 對象或 "YYYY-MM-DD" 格式的字符串，默認為今天
            days: 查詢天數
            
        Returns:
            以航線為鍵，航班列表為值的字典
        """
        if date is None:
            date = dt_datetime.now()
        elif isinstance(date, str):
            date = dt_datetime.strptime(date, "%Y-%m-%d")
        
        results = {}
        
        # 遍歷所有熱門航線
        all_popular_routes = POPULAR_DOMESTIC_ROUTES_TUPLES + POPULAR_INTERNATIONAL_ROUTES_TUPLES
        
        for departure, arrival in all_popular_routes:
            route_key = (departure, arrival)
            logger.info(f"處理熱門航線: {departure} -> {arrival}")
            
            # 檢查是否為台灣出發的航線
            if departure in TAIWAN_AIRPORTS:
                # 對於台灣出發的航線，假設數據由 sync_taiwan_departures 獲取
                # 不再此處重複調用 sync_flights 以避免冗餘 API 請求
                logger.info(f"台灣出發航線 {departure} -> {arrival} 的數據應由 sync_taiwan_departures 處理，跳過 API 調用。")
                # 可以在此處添加邏輯以從緩存或共享數據中獲取數據，目前暫存空列表
                results[route_key] = [] 
            else:
                # 對於非台灣出發的航線，仍然調用 sync_flights
                logger.info(f"非台灣出發航線 {departure} -> {arrival}，調用 sync_flights 獲取數據。")
                try:
                    flights = self.sync_flights(departure, arrival, date, days)
                    results[route_key] = flights
                    logger.info(f"完成 {departure}->{arrival} 同步，獲取 {len(flights)} 個航班")
                except Exception as e:
                    logger.error(f"同步非台灣出發熱門航線 {departure}->{arrival} 時出錯: {e}")
                    results[route_key] = [] # 出錯時也存儲空列表   
        return results
    
    def sync_taiwan_departures(self, date: Union[dt_datetime, str] = None, days: int = 1) -> Dict[str, List[Dict]]:
        """
        同步所有從台灣出發的航班
        
        Args:
            date: 起始日期，可以是 datetime 對象或 "YYYY-MM-DD" 格式的字符串，默認為今天
            days: 查詢天數
            
        Returns:
            以機場代碼為鍵，航班列表為值的字典
        """
        if date is None:
            date = dt_datetime.now()
        elif isinstance(date, str):
            date = dt_datetime.strptime(date, "%Y-%m-%d")
        
        results = {}
        
        for departure in TAIWAN_AIRPORTS:
            logger.info(f"正在同步從 {departure} 出發的航班")

            all_flights = []
            flight_keys = set()
            tdx_domestic_flights_formatted = [] # 存儲格式化後的 TDX 航班

            use_tdx = self.should_use_tdx_for_airport(departure, date)
            if self.tdx_api and use_tdx:
                try: 
                    current_date_obj = date # 從傳入的 date 開始
                    for day in range(days):
                        date_str = current_date_obj.strftime('%Y-%m-%d')
                        logger.info(f"從 TDX 獲取 {departure} 在 {date_str} 的 AE、B7、DA 航空公司航班")
                        
                        # 調用修改後的 get_domestic_flight_schedules
                        # 傳遞機場和日期字符串
                        tdx_domestic_flights = self.tdx_api.get_domestic_flight_schedules(departure, date_str)
                        
                        # get_domestic_flight_schedules 現在直接返回格式化後的數據
                        if isinstance(tdx_domestic_flights, list):
                            logger.info(f"TDX API 為 {departure} on {date_str} 返回 {len(tdx_domestic_flights)} 個已篩選和格式化的 AE/B7/DA 航班")
                            # 直接將返回的格式化數據添加到列表中
                            tdx_domestic_flights_formatted.extend(tdx_domestic_flights)
                        else:
                             logger.warning(f"TDX API get_domestic_flight_schedules 未返回列表: {type(tdx_domestic_flights)}")
                        
                        current_date_obj += dt_timedelta(days=1) # 迭代日期
                        
                    # 在日期循環外，一次性添加所有從TDX獲取的航班
                    if tdx_domestic_flights_formatted:
                        logger.info(f"準備將 {len(tdx_domestic_flights_formatted)} 個從 TDX 獲取的航班添加到結果列表")
                        self._add_unique_flights(all_flights, tdx_domestic_flights_formatted, flight_keys)
                        
                except Exception as e:
                    logger.error(f"從 TDX 獲取 {departure} 機場的 AE、B7、DA 航班失敗: {str(e)}", exc_info=True)
            
            # 從 FlightStats 獲取所有目標航空公司的航班
            if self.flightstats_api:
                try: 
                    logger.info(f"從 FlightStats 獲取 {departure} 的所有目標航空公司航班")
                    current_date_obj = date # 重置日期以遍歷
                    all_fs_departures_formatted = [] # 存儲從 FS 獲取的已格式化航班
                    for day in range(days):
                        date_str = current_date_obj.strftime('%Y-%m-%d')
                        time.sleep(self.request_delay)
                        
                        # 使用 languageCode:en
                        departures = self.flightstats_api.get_departures(
                            departure, 
                            date_str,
                            extended_options='languageCode:en' # 確保這裡也使用選項
                        )
                        
                        if departures:
                            # get_departures 返回的已經是內部格式，可以直接添加
                             self._add_unique_flights(all_fs_departures_formatted, departures, flight_keys)
                        else:
                            logger.warning(f"FlightStats 未返回 {departure} 在 {date_str} 的離港航班")
                            
                        current_date_obj += dt_timedelta(days=1)
                    
                    # 在日期循環外，一次性添加所有從FlightStats獲取的航班
                    if all_fs_departures_formatted:
                         logger.info(f"嘗試從 FlightStats 添加 {len(all_fs_departures_formatted)} 個航班到 {departure} 的結果列表 (包含去重)")
                         self._add_unique_flights(all_flights, all_fs_departures_formatted, flight_keys)
                    
                except Exception as e:
                    logger.error(f"從 FlightStats 獲取 {departure} 航班失敗: {str(e)}", exc_info=True)
            
            results[departure] = all_flights
            logger.info(f"{departure} 機場總計獲取 {len(all_flights)} 個航班")
        
        # --- 開始: 添加總結日誌 ---
        total_flights_overall = 0
        airline_summary = {airline: 0 for airline in TARGET_AIRLINES} # 初始化目標航空公司計數
        airport_summary = {}

        for airport, flights in results.items():
            airport_flight_count = len(flights)
            airport_summary[airport] = airport_flight_count
            total_flights_overall += airport_flight_count
            for flight in flights:
                airline_code = flight.get('airline_id')
                if airline_code in airline_summary:
                    airline_summary[airline_code] += 1
                elif airline_code: # 如果不在 TARGET_AIRLINES 但有代碼，也記錄一下
                    airline_summary[airline_code] = airline_summary.get(airline_code, 0) + 1

        logger.info("=" * 30 + " 台灣出發航班同步總結 " + "=" * 30)
        logger.info(f"總計處理 {len(TAIWAN_AIRPORTS)} 個台灣機場，共獲取 {total_flights_overall} 條航班記錄。")
        
        logger.info("--- 各機場獲取航班數量 ---")
        # 按數量降序排序機場
        sorted_airports = sorted(airport_summary.items(), key=lambda item: item[1], reverse=True)
        for airport, count in sorted_airports:
            if count > 0: # 只顯示有航班的機場
                logger.info(f"  {airport}: {count} 個航班")
            
        logger.info("--- 各目標航空公司獲取航班數量 (跨所有台灣機場) ---")
        # 按數量降序排序航空公司
        sorted_airlines = sorted(airline_summary.items(), key=lambda item: item[1], reverse=True)
        found_target_airlines = 0
        for airline, count in sorted_airlines:
            if airline in TARGET_AIRLINES and count > 0: # 只顯示有航班的目標航空公司
                logger.info(f"  {airline}: {count} 個航班")
                found_target_airlines += 1
            elif count > 0: # 顯示非目標但有數據的航空公司
                 logger.info(f"  {airline} (非目標): {count} 個航班")

        if found_target_airlines == 0:
            logger.warning("未找到任何目標航空公司的航班數據。")
            
        logger.info("=" * 30 + " 總結結束 " + "=" * 30)
        # --- 結束: 添加總結日誌 ---
        
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
    flights_parser.add_argument('--date', default=dt_datetime.now().strftime('%Y-%m-%d'), help='查詢日期（YYYY-MM-DD 格式），預設為今天')
    flights_parser.add_argument('--days', type=int, default=1, help='查詢天數，預設為 1')
    
    # 熱門航線同步指令
    popular_parser = subparsers.add_parser('popular', help='同步熱門航線資料')
    popular_parser.add_argument('--date', default=dt_datetime.now().strftime('%Y-%m-%d'), help='查詢日期（YYYY-MM-DD 格式），預設為今天')
    popular_parser.add_argument('--days', type=int, default=1, help='查詢天數，預設為 1')
    
    # 台灣出發航班同步指令
    taiwan_parser = subparsers.add_parser('taiwan', help='同步從台灣出發的航班資料')
    taiwan_parser.add_argument('--date', default=dt_datetime.now().strftime('%Y-%m-%d'), help='查詢日期（YYYY-MM-DD 格式），預設為今天')
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