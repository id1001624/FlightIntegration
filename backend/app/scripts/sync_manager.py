#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
API 同步管理器，集成 TDX 和 FlightStats API 數據同步功能
"""
import os
import sys
import uuid
import io
import gzip
import json
import logging
import datetime
import base64
import argparse
from datetime import datetime as dt_datetime
from datetime import timedelta as dt_timedelta
from ..utils.date_utils import parse_datetime, format_datetime
from typing import Dict, List, Optional, Any, Union, Tuple
import time
import pytz
import asyncio
import re

# *** 將 logger 配置移到頂部 ***
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('sync_manager') # 在模塊級別定義 logger

# *** 新增導入 asyncpg 相關函數 ***
try:
    from app.database.db import get_db, release_db
except ImportError:
    # 如果直接導入失敗，嘗試從父目錄添加路徑
    current_dir = os.path.dirname(os.path.abspath(__file__))
    app_dir = os.path.dirname(current_dir)
    backend_dir = os.path.dirname(app_dir)
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
    try:
        from app.database.db import get_db, release_db
    except ImportError:
        logger.error("無法導入資料庫輔助函數 get_db, release_db")
        # 定義空的替代函數避免後續 NameError，但功能會失效
        async def get_db(): return None
        async def release_db(conn): pass

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
from ..utils.date_utils import parse_datetime, format_datetime
from typing import Dict, List, Optional, Any, Union, Tuple
import time

# 導入常量和客戶端
try:
    # 優先嘗試新的客戶端導入路徑
    from app.clients.tdx_client import TdxApiClient
    from app.clients.flightstats_client import FlightStatsApiClient
    from app.scripts.constants import (
        TAIWAN_AIRPORTS,
        TAIPEI_AIRPORTS,
        TARGET_AIRLINES,
        POPULAR_DOMESTIC_ROUTES_TUPLES,
        POPULAR_INTERNATIONAL_ROUTES_TUPLES,
    )
    # 不再依賴這裡導入模型，get_airline 將直接查詢
    # from app.models.airline import Airline
    # from app.models.airport import Airport
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
        # from scripts.constants import TAIWAN_AIRPORTS, TARGET_AIRLINES
        # 改為導入所有需要的常量
        from scripts.constants import (
            TAIWAN_AIRPORTS,
            TARGET_AIRLINES,
            POPULAR_DOMESTIC_ROUTES_TUPLES,
            POPULAR_INTERNATIONAL_ROUTES_TUPLES
        )
        # *** 在備用導入中也加入模型導入 ***
        # from app.models.airline import Airline
        # from app.models.airport import Airport
    except ImportError:
        try:
            # 如果常量導入失敗，使用內部定義的常量
            from backend.app.deprecated.tdx_sync import TdxApiClient
            from backend.app.deprecated.flightstats_sync import FlightStatsApiClient
            TAIWAN_AIRPORTS = ['TPE', 'TSA', 'RMQ', 'KHH', 'TNN', 'CYI', 'HUN', 'TTT', 'KNH', 'MZG', 'LZN', 'MFK', 'KYD', 'GNI', 'CMJ', 'WOT']
            TARGET_AIRLINES = ['AE', 'B7', 'BR', 'CI', 'CX', 'DA', 'IT', 'JL', 'JX', 'OZ']
            # *** 如果連 app.models 都導入失敗，這裡需要處理 Airline 和 Airport 的定義 ***
            # 這裡可以定義一個簡單的模擬類或設置為 None，並在後續代碼中處理
            class MockModel:
                @staticmethod
                def get_by_iata(code):
                    return None
            Airline = MockModel
            Airport = MockModel
            logger.warning("無法導入資料庫模型，部分功能 (如獲取中文名) 將受限")
        except ImportError as e: # Inner try needs an except
            logger.error(f"無法導入任何版本的 API 客戶端: {str(e)}")
            # 這裡應該退出或拋出異常，因為缺少核心依賴
            sys.exit(1)
        except Exception as e: # Outer try/except for other potential errors during import
            logger.error(f"初始化導入過程中發生意外錯誤: {str(e)}")
        sys.exit(1)

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
        
        # --- 移除 UUID 生成 ---
        # flight_uuid = uuid.uuid4() 

        # 只保留資料庫表中存在的欄位
        return {
            # --- 移除 flight_id ---
            # 'flight_id': flight_uuid, 
            'flight_number': airline_id + flight_number,
            'airline_id': airline_id,
            'departure_airport_id': raw_flight.get('DepartureAirportID', ''),
            'arrival_airport_id': raw_flight.get('ArrivalAirportID', ''),
            'scheduled_departure': format_datetime(parse_datetime(scheduled_dep)) if scheduled_dep else None,
            'scheduled_arrival': format_datetime(parse_datetime(scheduled_arr)) if scheduled_arr else None,
            'actual_departure': format_datetime(parse_datetime(actual_dep)) if actual_dep else None, # 保留，可能有用
            'actual_arrival': format_datetime(parse_datetime(actual_arr)) if actual_arr else None, # 保留，可能有用
            # 確保 aircraft 字段存在，即使為空
            'aircraft': raw_flight.get('AircraftType', '') # 嘗試從 TDX 獲取，如果沒有則為空字符串
            # 移除了資料庫表格中不存在的欄位
            # 'status', 'departure_terminal', 'departure_gate', 'arrival_terminal', 'arrival_gate', 'source'
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
        # self.logger = logging.getLogger('sync_manager') # 可以移除，直接用全局 logger
        
        try:
            self.tdx_api = TdxApiClient()
            logger.info("已初始化 TDX API 客戶端") # 使用模塊級 logger
        except Exception as e:
            self.tdx_api = None
            logger.error(f"初始化 TDX API 客戶端出錯: {str(e)}") # 使用模塊級 logger
        
        try:
            self.flightstats_api = FlightStatsApiClient()
            logger.info("已初始化 FlightStats API 客戶端") # 使用模塊級 logger
        except Exception as e:
            self.flightstats_api = None
            logger.error(f"初始化 FlightStats API 客戶端出錯: {str(e)}") # 使用模塊級 logger
        
        # 檢查至少一個 API 客戶端可用
        if not self.tdx_api and not self.flightstats_api:
            logger.error("無法初始化任何 API 客戶端，同步功能將無法使用") # 使用模塊級 logger
        
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
        logger.info("開始同步機場數據...")
        added_count = 0
        updated_count = 0

        # 這裡的邏輯需要重新考慮。
        # 如果完全依賴資料庫，這個同步方法可能不再需要，
        # 或者需要從其他來源（如文件、管理界面）獲取數據。
        # 暫時將其留空或只記錄一條信息。
        logger.info("機場同步功能當前依賴資料庫數據，未執行外部API同步。")

        # 原有的合併和更新邏輯基於API數據，現已移除
        # all_airports_data = self._merge_airport_data(tdx_airports, flightstats_airports)
        # ... (原有的 database update/add logic)

        logger.info(f"機場同步完成。新增: {added_count}, 更新: {updated_count}")
        # 確保方法有返回值，即使是空的
        return []
    
    def get_airport(self, iata_code: str) -> Optional[Dict]:
        """嘗試從不同來源獲取機場資訊，優先使用資料庫"""
        if not iata_code:
            return None

        iata_code = iata_code.strip().upper()
        logger.debug(f"正在獲取機場資訊: {iata_code}")

        # 1. 優先從資料庫查詢
        try:
            airport_db = Airport.get_by_iata(iata_code)
            if airport_db:
                logger.debug(f"從資料庫找到機場 {iata_code}")
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
            logger.error(f"從資料庫查詢機場 {iata_code} 時出錯: {e}")
            return None
        
        logger.warning(f"在資料庫中未找到機場資訊: {iata_code}")
        return None
    
    def sync_airlines(self) -> List[Dict]:
        """同步航空公司數據 - 當前版本依賴資料庫數據，不執行外部同步"""
        logger.info("開始同步航空公司數據...")
        
        
        logger.info("航空公司同步功能當前依賴資料庫數據，未執行外部API同步。")
        
        # 始終返回空列表，因為此方法不再產生需要處理的外部數據
        return []
    
    async def get_airline(self, iata_code: str) -> Optional[Dict]:
        """直接從資料庫獲取航空公司資料 (使用 asyncpg)"""
        if not iata_code:
            return None
            
        iata_code = iata_code.strip().upper()
        logger.debug(f"正在從資料庫獲取航空公司資訊: {iata_code}") # 使用模塊 logger

        conn = None
        try:
            conn = await get_db() # 獲取 asyncpg 連接
            if conn is None:
                logger.error("無法獲取資料庫連接")
                return None

            # 執行 SQL 查詢
            # 假設 airlines 表有 airline_id (主鍵), name_zh, name_en 等欄位
            query = "SELECT airline_id, name_zh, name_en, website, contact_phone, is_domestic FROM airlines WHERE airline_id = $1"
            row = await conn.fetchrow(query, iata_code)

            if row:
                logger.debug(f"從資料庫找到航空公司 {iata_code}")
                # 將查詢結果轉換為字典
                return {
                    'airline_id': row['airline_id'],
                    'name_zh': row['name_zh'],
                    'name_en': row['name_en'],
                    'website': row['website'],
                    'contact_phone': row['contact_phone'],
                    'is_domestic': row['is_domestic'],
                    'source': 'database'
                }
            else:
                logger.warning(f"在資料庫中未找到航空公司: {iata_code}")
                return None
        except Exception as e:
            logger.error(f"從資料庫查詢航空公司 {iata_code} 時出錯: {e}")
            return None
        finally:
            if conn:
                await release_db(conn) # 釋放連接
    
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
            try:
                date = dt_datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                logger.error(f"提供的日期字串格式錯誤: {date}")
                return [] # 返回空列表如果日期無效
        
        flights = []
        flight_keys = set()  # 用於去重的集合，存儲flight_number+departure_date
        tdx_processed_flights = [] # 用於存儲從 TDX 獲取並格式化後的航班
        
        # 檢查起飛機場是否為台灣機場 (如果不是台灣出發，只用 FlightStats)
        if departure not in TAIWAN_AIRPORTS:
            logger.warning(f"出發機場 {departure} 不在台灣機場列表中，僅使用FlightStats API獲取數據")
            if self.flightstats_api:
                try:
                    fs_flights = self.flightstats_api.get_flights(
                        departure, arrival, date.strftime('%Y-%m-%d')
                    )
                    if fs_flights:
                        # 篩選目標航空公司
                        filtered_flights = [f for f in fs_flights if f.get('airline_id') in TARGET_AIRLINES]
                        if filtered_flights:
                            logger.info(f"已從 FlightStats 獲取並篩選出 {len(filtered_flights)} 個目標航空公司航班")
                            # 假設 FlightStats 返回的是內部格式或兼容格式
                            self._add_unique_flights(flights, filtered_flights, flight_keys)
                        else:
                            logger.warning(f"從 FlightStats 獲取航班後未找到目標航空公司航班")
                except Exception as e:
                    logger.error(f"從 FlightStats 獲取非台灣出發航班數據失敗: {str(e)}")
            return flights
        
        # --- 以下為台灣出發的處理邏輯 ---
        is_domestic = self.is_domestic_route(departure, arrival)
        use_tdx = self.should_use_tdx_for_airport(departure, date)
        date_str = date.strftime('%Y-%m-%d')
        
        # --- TDX API 邏輯 --- 
        if self.tdx_api and use_tdx:
            tdx_raw_flights_filtered = [] # 存放篩選後的原始TDX航班
            try:
                logger.info(f"嘗試從 TDX FIDS 獲取 {departure} 在 {date_str} 的所有航班")
                # 統一調用 FIDS 接口
                raw_data = self.tdx_api.get_domestic_flight_schedules(departure, date_str)
                
                if isinstance(raw_data, list):
                    logger.info(f"TDX FIDS 返回 {len(raw_data)} 筆 {departure} 的原始記錄，開始篩選...")
                    # 根據國內/國際進行篩選
                    if is_domestic:
                        tdx_raw_flights_filtered = [
                            f for f in raw_data
                            if f.get('DepartureAirportID') == departure and
                               f.get('ArrivalAirportID') == arrival and # 國內也需匹配到達機場
                               self.is_tdx_target_airline(f.get('AirlineID')) # 只篩選 AE, B7, DA
                        ]
                        logger.info(f"篩選國內航線 {departure}->{arrival} (AE, B7, DA) 結果: {len(tdx_raw_flights_filtered)} 個航班")
                    else: # 國際航線
                        tdx_raw_flights_filtered = [
                            f for f in raw_data
                            if f.get('DepartureAirportID') == departure and
                               f.get('ArrivalAirportID') == arrival and # 國際需匹配到達機場
                               f.get('AirlineID') in TARGET_AIRLINES # 篩選目標國際航空公司
                        ]
                        logger.info(f"篩選國際航線 {departure}->{arrival} (TARGET_AIRLINES) 結果: {len(tdx_raw_flights_filtered)} 個航班")
                else:
                    logger.warning(f"TDX FIDS 未返回列表: {type(raw_data)}")
                
                # 格式化篩選後的 TDX 航班
                for raw_flight in tdx_raw_flights_filtered:
                    formatted = format_tdx_flight(raw_flight)
                    if formatted:
                        tdx_processed_flights.append(formatted)
                        
                if tdx_processed_flights:
                    logger.info(f"已格式化 {len(tdx_processed_flights)} 個來自 TDX 的航班")
                    # 將格式化後的 TDX 航班添加到主列表 (去重)
                    self._add_unique_flights(flights, tdx_processed_flights, flight_keys)
                else:
                    logger.warning(f"從 TDX API 獲取 {departure}->{arrival} 的航班篩選/格式化後為空")

            except Exception as e:
                logger.error(f"處理 TDX 獲取 {departure}->{arrival} 航班數據失敗: {str(e)}")
        # --- 結束 TDX API 邏輯 ---
        
        # --- FlightStats API 邏輯 (補充或作為主要來源) ---
        if self.flightstats_api:
            try:
                time.sleep(self.request_delay)
                logger.info(f"嘗試從 FlightStats 獲取 {departure}->{arrival} 的航班 (日期: {date_str})")
                fs_flights_raw = self.flightstats_api.get_flights(departure, arrival, date_str)
                
                fs_processed_flights = [] # 存放格式化後的 FlightStats 航班
                if fs_flights_raw:
                    logger.info(f"FlightStats 返回 {len(fs_flights_raw)} 筆原始記錄，開始篩選...")
                    # 篩選目標航空公司，並排除已從 TDX 獲取的航班 (基於 flight_key)
                    for flight in fs_flights_raw:
                        airline_id = flight.get('airline_id')
                        if airline_id in TARGET_AIRLINES:
                            # 生成 flight_key 以檢查是否已從 TDX 添加
                            flight_number = flight.get('flight_number', '')
                            dep_dt_str = flight.get('scheduled_departure') # FlightStats 應返回內部格式
                            dep_date = dep_dt_str[:10] if isinstance(dep_dt_str, str) and len(dep_dt_str) >= 10 else ''
                            
                            flight_key = f"{flight_number}_{dep_date}" if flight_number and dep_date else None
                            
                            if flight_key and flight_key in flight_keys:
                                # logger.debug(f"FlightStats 航班 {flight_key} 已從 TDX 添加，跳過")
                                continue # 如果 TDX 已經添加過，則跳過
                            else:
                                # 假設 fs_flights_raw 已经是内部格式或兼容格式
                                fs_processed_flights.append(flight)
                                
                    if fs_processed_flights:
                        logger.info(f"從 FlightStats 篩選出 {len(fs_processed_flights)} 個新的目標航班")
                        # 將格式化後的 FlightStats 航班添加到主列表 (去重)
                        self._add_unique_flights(flights, fs_processed_flights, flight_keys)
                    else:
                        logger.info(f"從 FlightStats 未篩選出需要補充的新航班")
                else:
                    logger.warning(f"從 FlightStats 獲取 {departure}->{arrival} 航班返回空結果")
            except Exception as e:
                logger.error(f"從 FlightStats 獲取 {departure}->{arrival} 航班數據失敗: {str(e)}")
        # --- 結束 FlightStats API 邏輯 ---
        
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
            
            # 確保 flight_id 是 UUID 物件而非字串
            if 'flight_id' in flight and not isinstance(flight['flight_id'], uuid.UUID):
                try:
                    if isinstance(flight['flight_id'], str):
                        flight['flight_id'] = uuid.UUID(flight['flight_id'])
                    else:
                        flight['flight_id'] = uuid.uuid4()
                except ValueError:
                    # 如果無法轉換為 UUID，生成新的 UUID
                    flight['flight_id'] = uuid.uuid4()
                
            # 移除可能不存在於資料庫中的欄位 (不再移除航廈和登機門)
            keys_to_remove = [
                'status', 
                'departure_gate', 'arrival_gate', 'source' # 保留 departure_terminal, arrival_terminal
            ]
            for key in keys_to_remove:
                if key in flight:
                    flight.pop(key)
            
            # 如果航班不重複，添加到目標列表
            if flight_key not in flight_keys:
                flight_keys.add(flight_key)
                target_list.append(flight)
                added_count += 1
            # else:
            #     logger.debug(f"跳過重複航班: {flight_key}")
        # logger.info(f"添加了 {added_count} 個唯一航班") # 可以取消註釋以調試
        logger.info(f"在 _add_unique_flights 中添加了 {added_count} 個唯一航班到目標列表")
    
    def sync_popular_routes(self, date: Union[dt_datetime, str] = None, days: int = 1) -> Dict[Tuple[str, str], List[Dict]]:
        """
        同步熱門航線的航班數據（例如：TPE-NRT, TSA-HND 等）
        
        Args:
            date: 起始日期，默認為今天
            days: 從起始日期開始，連續查詢的天數
            
        Returns:
            一個字典，鍵是 (departure, arrival) 的元組，值是該航線的航班列表
        """
        if date is None:
            date = dt_datetime.now().date()
        elif isinstance(date, str):
            try:
                date = dt_datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                logger.error(f"提供的日期字串格式錯誤: {date}")
                return {}

        all_flights = {}
        popular_routes = POPULAR_DOMESTIC_ROUTES_TUPLES + POPULAR_INTERNATIONAL_ROUTES_TUPLES

        logger.info(f"開始同步 {len(popular_routes)} 條熱門航線，從 {date} 開始，共 {days} 天")

        for dep, arr in popular_routes:
            logger.info(f"正在處理熱門航線: {dep} -> {arr}")
            route_flights = []
            for i in range(days):
                current_date = date + dt_timedelta(days=i)
                try:
                    logger.debug(f"同步航班數據 {dep}->{arr} 日期: {current_date.strftime('%Y-%m-%d')}")
                    flights_for_day = self.sync_flights(dep, arr, current_date)
                    if flights_for_day:
                        logger.info(f"為 {dep}->{arr} 在 {current_date.strftime('%Y-%m-%d')} 找到 {len(flights_for_day)} 個航班")
                        route_flights.extend(flights_for_day)
                    else:
                        logger.warning(f"為 {dep}->{arr} 在 {current_date.strftime('%Y-%m-%d')} 未找到航班")
                    # 避免過於頻繁的請求
                    time.sleep(self.request_delay)
                except Exception as e:
                    logger.error(f"同步航線 {dep}->{arr} 日期 {current_date.strftime('%Y-%m-%d')} 時發生錯誤: {e}")
                    # 即使某一天出錯，也繼續處理下一天或下一航線
                    continue

            if route_flights:
                logger.info(f"航線 {dep}->{arr} 共找到 {len(route_flights)} 個航班 (共 {days} 天)")
                all_flights[(dep, arr)] = route_flights
            else:
                 logger.warning(f"航線 {dep}->{arr} 在指定的 {days} 天內未找到任何航班")

        logger.info(f"熱門航線同步完成，共處理 {len(all_flights)} 條有效航線")
        return all_flights


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
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 