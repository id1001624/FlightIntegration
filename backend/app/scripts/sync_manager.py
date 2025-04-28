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
from typing import Dict, List, Optional, Any, Union, Tuple
import time
import pytz
import re

# *** Logger 配置 ***
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('sync_manager')

# *** 統一使用相對導入 ***
try:
    from ..utils.api_client import ApiClient
    from ..clients.tdx_client import TdxApiClient
    from ..clients.flightstats_client import FlightStatsApiClient
    from .constants import (
        TAIWAN_AIRPORTS,
        TAIPEI_AIRPORTS,
        TARGET_AIRLINES,
        POPULAR_DOMESTIC_ROUTES_TUPLES,
        POPULAR_INTERNATIONAL_ROUTES_TUPLES,
    )
    from ..utils.date_utils import parse_datetime, format_datetime
    # 導入模型，用於 get_airport 方法中的類型檢查或查詢 (如果需要)
    # from ..models import Airport, Airline #<-- 移除，不由 SyncManager 處理

except ImportError as e:
    logger.error(f"無法導入必要的模組，請檢查路徑和依賴: {e}")
    sys.exit(1)

# --- TDX 數據格式化輔助函數 ---
def format_tdx_flight(raw_flight: Dict) -> Optional[Dict]:
    """將 TDX 原始航班數據轉換為內部格式"""
    try:
        # --- 使用正確的 snake_case 鍵名 ---
        airline_id = raw_flight.get('airline_id')
        # flight_number 來自 tdx_client 的組合 flight_number
        flight_number = raw_flight.get('flight_number')
        
        # 確保關鍵字段存在
        if not airline_id or not flight_number:
             logger.warning(f"TDX 原始數據缺少關鍵字段 (檢查 airline_id, flight_number): {raw_flight}")
             return None
             
        # --- 使用正確的 snake_case 鍵名 ---
        scheduled_dep = raw_flight.get('scheduled_departure') # 應為 ISO 8601 字符串或 None
        scheduled_arr = raw_flight.get('scheduled_arrival')   # 應為 ISO 8601 字符串或 None
        departure_airport_id = raw_flight.get('departure_airport_id')
        arrival_airport_id = raw_flight.get('arrival_airport_id')
        aircraft_type = raw_flight.get('aircraft') # 直接讀取 aircraft

        # --- 格式化返回的字典，確保鍵名與模型一致 --- 
        formatted_flight = {
            'flight_number': flight_number, # 使用從 tdx_client 處理過的 flight_number
            'airline_id': airline_id,
            'departure_airport_id': departure_airport_id,
            'arrival_airport_id': arrival_airport_id,
            'scheduled_departure': scheduled_dep, # 直接使用 tdx_client 返回的格式化時間或 None
            'scheduled_arrival': scheduled_arr,   # 直接使用 tdx_client 返回的格式化時間或 None
            'aircraft': aircraft_type if aircraft_type else '', # 使用 aircraft
            # 移除 status, actual_departure, actual_arrival
            # 由於 TDX 不再提供，設置為 None，依賴 FlightStats (如果可用)
            'departure_terminal': None, 
            'arrival_terminal': None, 
        }
        
        # --- 移除多餘的時間格式化檢查 --- 
        # tdx_client 應該已經返回了正確格式或 None
             
        return formatted_flight
        
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
        """同步機場數據 - 此方法應由數據管理層處理或從外部來源獲取"""
        logger.warning("ApiSyncManager.sync_airports 不再執行實際的 API 同步或數據庫操作。機場數據應由 DbManager 或管理腳本處理。")
        return []
    
    def get_airport(self, iata_code: str) -> Optional[Dict]:
        """獲取機場資訊 - ApiSyncManager 不應直接訪問數據庫"""
        logger.warning(f"ApiSyncManager.get_airport 被調用 ({iata_code})，但它不應直接訪問數據庫。請從 DbManager 獲取此信息。")
        return None
    
    def sync_airlines(self) -> List[Dict]:
        """同步航空公司數據 - 此方法應由數據管理層處理或從外部來源獲取"""
        logger.warning("ApiSyncManager.sync_airlines 不再執行實際的 API 同步或數據庫操作。航空公司數據應由 DbManager 或管理腳本處理。")
        return []
    
    def sync_flights(self, departure: str, arrival: str, date: Union[dt_datetime, str], days: int = 1) -> List[Dict]:
        """
        同步航班數據。
        如果提供了日期，則獲取指定日期的數據 (TDX過濾, FlightStats取1天)。
        如果未提供日期，則獲取所有未來的TDX數據和未來7天的FlightStats數據。
        
        Args:
            departure: 出發機場 IATA 代碼
            arrival: 目的機場 IATA 代碼
            date: 起始日期 (可選)，可以是 datetime 對象或 "YYYY-MM-DD" 格式的字符串。
                   如果為 None，則獲取未來數據。
            
        Returns:
            航班數據列表
        """
        target_date_str: Optional[str] = None # 用於過濾 TDX 或傳遞給 FlightStats 的單日日期
        days_to_fetch_fs = 7 # FlightStats 預設獲取天數
        
        # 處理傳入的 date 參數
        if date:
            if isinstance(date, str):
                try:
                    target_dt = dt_datetime.strptime(date, "%Y-%m-%d")
                    target_date_str = date # 格式正確，直接使用
                    days_to_fetch_fs = 1 # 指定日期時，FlightStats 只取 1 天
                except ValueError:
                    logger.error(f"提供的日期字串格式錯誤: {date}")
                    return []
            elif isinstance(date, dt_datetime):
                target_dt = date
                target_date_str = date.strftime("%Y-%m-%d")
                days_to_fetch_fs = 1
            else:
                logger.error(f"未知的日期參數類型: {type(date)}")
                return []
        else:
            # 未提供日期，獲取未來數據，設置 FlightStats 的起始日期為今天
            target_dt = dt_datetime.now()
            target_date_str = target_dt.strftime("%Y-%m-%d")
            # days_to_fetch_fs 保持預設 7
            logger.info(f"未指定日期，將獲取 {departure}->{arrival} 的未來航班 (TDX: 所有未來, FlightStats: 未來 {days_to_fetch_fs} 天從 {target_date_str})")

        # -- (後面邏輯使用 target_date_str 和 days_to_fetch_fs) --
        
        flights = []
        flight_dict = {}  # *** 修改：將 flight_keys 初始化為字典 ***
        tdx_processed_flights = [] # 初始化為空列表
        
        # --- 檢查非台灣出發邏輯 --- 
        if departure not in TAIWAN_AIRPORTS:
            logger.warning(f"出發機場 {departure} 不在台灣機場列表中，僅使用FlightStats API獲取數據")
            if self.flightstats_api:
                try:
                    # 使用 target_date_str 和 days_to_fetch_fs 調用 FlightStats
                    fs_flights = self.flightstats_api.get_flights(
                        departure, arrival, target_date_str, days_to_fetch=days_to_fetch_fs
                    )
                    if fs_flights:
                        filtered_flights = [f for f in fs_flights if f.get('airline_id') in TARGET_AIRLINES]
                        if filtered_flights:
                            logger.info(f"已從 FlightStats 獲取並篩選出 {len(filtered_flights)} 個目標航空公司航班")
                            self._add_unique_flights(flights, filtered_flights, flight_dict) # *** 修改：傳遞 flight_dict ***
                        else:
                            logger.warning(f"從 FlightStats 獲取航班後未找到目標航空公司航班")
                except Exception as e:
                    logger.error(f"從 FlightStats 獲取非台灣出發航班數據失敗: {str(e)}")
            return flights
        
        # --- 台灣出發的處理邏輯 --- 
        is_domestic = self.is_domestic_route(departure, arrival)
        # use_tdx 判斷依賴機場，與日期無關（除非特殊機場 WOT）
        use_tdx = self.should_use_tdx_for_airport(departure, target_dt)
        
        # --- TDX API 邏輯 (修改後) ---
        if self.tdx_api and use_tdx:
            try:
                DOMESTIC_AIRLINES = ['AE', 'B7', 'DA'] # 國內航空公司列表
                all_tdx_flights_raw = [] # 用於收集所有航空公司的原始數據

                logger.info(f"嘗試從 TDX DailySchedule 獲取以下航空公司的所有未來航班: {DOMESTIC_AIRLINES}")

                for airline_iata in DOMESTIC_AIRLINES:
                    try:
                        # 為每個國內航空公司調用 API
                        flights_for_airline = self.tdx_api.get_domestic_flight_schedules(airline_iata)
                        if isinstance(flights_for_airline, list):
                            all_tdx_flights_raw.extend(flights_for_airline)
                            logger.debug(f"從 TDX ({airline_iata}) 獲取了 {len(flights_for_airline)} 筆記錄")
                        else:
                            logger.warning(f"TDX DailySchedule ({airline_iata}) 未返回列表: {type(flights_for_airline)}")
                        time.sleep(0.1) # 短暫延遲避免過快請求
                    except Exception as airline_ex:
                        logger.error(f"調用 TDX DailySchedule ({airline_iata}) 時出錯: {airline_ex}", exc_info=False) # 避免過多堆棧追蹤
                        continue

                logger.info(f"從 TDX (所有國內航司) 共獲取 {len(all_tdx_flights_raw)} 筆原始未來記錄，準備篩選航線 {departure}->{arrival}")

                # --- 在這裡對合併後的 all_tdx_flights_raw 進行篩選 ---
                flights_to_format = []
                for flight_data in all_tdx_flights_raw:
                    # 篩選條件：出發機場匹配 + 到達機場匹配
                    if flight_data.get('departure_airport_id') == departure and flight_data.get('arrival_airport_id') == arrival:
                        # (可選) 再次確認航空公司是否在國內列表中，雖然理論上應該是的
                        if flight_data.get('airline_id') in DOMESTIC_AIRLINES:
                             flights_to_format.append(flight_data)

                logger.info(f"篩選 TDX 所有未來數據和航線 {departure}->{arrival} 結果: {len(flights_to_format)} 個航班")
                # --- 結束篩選 ---

                # 格式化篩選後的 TDX 航班 (這部分邏輯不變)
                for raw_flight in flights_to_format:
                    formatted = format_tdx_flight(raw_flight)
                    if formatted:
                        tdx_processed_flights.append(formatted)
                        
                if tdx_processed_flights:
                    logger.info(f"已格式化 {len(tdx_processed_flights)} 個來自 TDX 的航班")
                    self._add_unique_flights(flights, tdx_processed_flights, flight_dict)
                else:
                    pass # 沒有從 TDX 獲取到符合條件的航班

            except Exception as e:
                logger.error(f"處理 TDX 獲取 {departure}->{arrival} 航班數據失敗: {str(e)}")
        # --- 結束 TDX API 邏輯 ---
        
        # --- FlightStats API 邏輯 --- 
        if self.flightstats_api:
            try:
                time.sleep(self.request_delay)
                 # 使用 target_date_str 和 days_to_fetch_fs
                logger.info(f"嘗試從 FlightStats 獲取 {departure}->{arrival} 的航班 (起始日期: {target_date_str}, 天數: {days_to_fetch_fs})")
                fs_flights_raw = self.flightstats_api.get_flights(departure, arrival, target_date_str, days_to_fetch=days_to_fetch_fs) 
                
                fs_processed_flights = [] 
                if fs_flights_raw:
                    logger.info(f"FlightStats 返回 {len(fs_flights_raw)} 筆原始記錄 ({days_to_fetch_fs}天)，開始篩選...")
                    for flight in fs_flights_raw:
                        airline_id = flight.get('airline_id')
                        if airline_id in TARGET_AIRLINES:
                            flight_number = flight.get('flight_number', '')
                            dep_dt_str = flight.get('scheduled_departure')
                            dep_date = dep_dt_str[:10] if isinstance(dep_dt_str, str) and len(dep_dt_str) >= 10 else ''
                            flight_key = f"{flight_number}_{dep_date}" if flight_number and dep_date else None
                            
                            is_new = flight_key and flight_key not in flight_dict

                            if is_new:
                                fs_processed_flights.append(flight)
                                
                    if fs_processed_flights:
                        logger.info(f"從 FlightStats 篩選出 {len(fs_processed_flights)} 個新的目標航班")
                        self._add_unique_flights(flights, fs_processed_flights, flight_dict)
                    else:
                        logger.info(f"從 FlightStats 未篩選出需要補充的新航班")
                else:
                    logger.warning(f"從 FlightStats 獲取 {departure}->{arrival} 航班返回空結果 (起始: {target_date_str}, 天數: {days_to_fetch_fs})")
            except Exception as e:
                logger.error(f"從 FlightStats 獲取 {departure}->{arrival} 航班數據失敗: {str(e)}")
        # --- 結束 FlightStats API 邏輯 ---
        
        logger.info(f"航線 {departure}->{arrival} 同步完成，共獲得 {len(flights)} 個唯一航班。")
        return flights # 返回合併去重後的結果
    
    def _add_unique_flights(self, target_list: List[Dict], source_flights: List[Dict], flight_dict: Dict[str, Dict]):
        """
        將新航班添加到目標列表中，或合併信息到現有航班，避免重複。
        現在使用字典來快速查找和更新現有記錄。
        
        Args:
            target_list: 目標航班列表 (會被直接修改)
            source_flights: 來源航班列表 (應為內部格式)
            flight_dict: 已存在航班鍵到航班字典的映射 (會被修改)
        """
        added_count = 0
        merged_count = 0
        skipped_invalid_count = 0
        skipped_no_key_count = 0
        
        for flight in source_flights:
            if not isinstance(flight, dict) or not flight:
                logger.warning(f"跳過無效的航班數據: {flight}")
                skipped_invalid_count += 1
                continue
                
            flight_number = flight.get('flight_number', '')
            departure_dt_str = flight.get('scheduled_departure') or flight.get('departure_time')
            if isinstance(departure_dt_str, dt_datetime):
                departure_date = departure_dt_str.strftime('%Y-%m-%d')
            elif isinstance(departure_dt_str, str) and len(departure_dt_str) >= 10:
                departure_date = departure_dt_str[:10]
            else:
                departure_date = ''
            
            if not flight_number or not departure_date:
                 logger.warning(f"無法為航班生成唯一鍵，缺少 flight_number 或 departure_date: {flight}")
                 skipped_no_key_count += 1
                 continue
                 
            flight_key = f"{flight_number}_{departure_date}"
            
            if 'flight_id' in flight and not isinstance(flight['flight_id'], uuid.UUID):
                try:
                    if isinstance(flight['flight_id'], str):
                        flight['flight_id'] = uuid.UUID(flight['flight_id'])
                    else:
                        flight['flight_id'] = uuid.uuid4()
                except ValueError:
                    flight['flight_id'] = uuid.uuid4()
            elif 'flight_id' not in flight:
                    flight['flight_id'] = uuid.uuid4()
                
            keys_to_remove = ['status', 'departure_gate', 'arrival_gate', 'source']
            for key in keys_to_remove:
                if key in flight:
                    flight.pop(key)
            
            if flight_key not in flight_dict:
                target_list.append(flight)
                flight_dict[flight_key] = flight
                added_count += 1
            else:
                existing_flight = flight_dict[flight_key]
                merged_this_flight = False
                
                new_dep_terminal = flight.get('departure_terminal')
                if not existing_flight.get('departure_terminal') and new_dep_terminal:
                    existing_flight['departure_terminal'] = new_dep_terminal
                    logger.debug(f"合併 {flight_key}: 更新 departure_terminal 為 {new_dep_terminal}")
                    merged_this_flight = True
                    
                new_arr_terminal = flight.get('arrival_terminal')
                if not existing_flight.get('arrival_terminal') and new_arr_terminal:
                    existing_flight['arrival_terminal'] = new_arr_terminal
                    logger.debug(f"合併 {flight_key}: 更新 arrival_terminal 為 {new_arr_terminal}")
                    merged_this_flight = True
                    
                new_aircraft = flight.get('aircraft')
                if not existing_flight.get('aircraft') and new_aircraft:
                    existing_flight['aircraft'] = new_aircraft
                    logger.debug(f"合併 {flight_key}: 更新 aircraft 為 {new_aircraft}")
                    merged_this_flight = True
                    
                if merged_this_flight:
                    merged_count += 1
            
        logger.info(f"處理 {len(source_flights)} 筆來源航班：新增 {added_count}, 合併 {merged_count}, 跳過(無效) {skipped_invalid_count}, 跳過(無鍵) {skipped_no_key_count}")
    
    # --- 新增方法：獲取指定航線的所有未來航班 --- 
    def sync_future_flights(self, departure: str, arrival: str) -> List[Dict]:
        """
        獲取指定航線的所有未來航班數據。
        TDX 獲取所有未來數據，FlightStats 獲取未來 7 天數據。
        
        Args:
            departure: 出發機場 IATA 代碼
            arrival: 目的機場 IATA 代碼
            
        Returns:
            合併後的未來航班數據列表
        """
        logger.info(f"開始獲取航線 {departure}->{arrival} 的所有未來航班數據 (FlightStats 限未來 7 天)")
        
        flights = []
        processed_flights_dict: Dict[str, Dict] = {}
        tdx_processed_flights = []
        fs_processed_flights = []
        
        today_date_str = dt_datetime.now().strftime("%Y-%m-%d")
        target_dt_for_tdx_check = dt_datetime.now()
        is_domestic = self.is_domestic_route(departure, arrival)
        use_tdx = self.should_use_tdx_for_airport(departure, target_dt_for_tdx_check)
        
        if self.tdx_api and use_tdx:
            try:
                logger.info(f"[Future] 嘗試從 TDX DailySchedule 獲取 {departure} 的所有未來航班")
                all_future_tdx_flights = self.tdx_api.get_domestic_flight_schedules(departure)
                
                if isinstance(all_future_tdx_flights, list):
                    logger.info(f"[Future] TDX 返回 {len(all_future_tdx_flights)} 筆 {departure} 的未來記錄，篩選航線 {arrival}...")
                    flights_to_format = []
                    for flight_data in all_future_tdx_flights:
                        if is_domestic and self.is_tdx_target_airline(flight_data.get('airline_id')) and flight_data.get('arrival_airport_id') == arrival:
                            flights_to_format.append(flight_data)
                        elif not is_domestic and self.is_target_airline(flight_data.get('airline_id')) and flight_data.get('arrival_airport_id') == arrival:
                            flights_to_format.append(flight_data)
                            
                    logger.info(f"[Future] 篩選 TDX 航線 {departure}->{arrival} 結果: {len(flights_to_format)} 個航班")
                    for raw_flight in flights_to_format:
                        formatted = format_tdx_flight(raw_flight)
                        if formatted:
                            tdx_processed_flights.append(formatted)
                else:
                    logger.warning(f"[Future] TDX DailySchedule 未返回列表: {type(all_future_tdx_flights)}")
                    
                if tdx_processed_flights:
                    logger.info(f"[Future] 已格式化 {len(tdx_processed_flights)} 個來自 TDX 的航班")
                    self._add_unique_flights(flights, tdx_processed_flights, processed_flights_dict)

            except Exception as e:
                logger.error(f"[Future] 處理 TDX 獲取 {departure}->{arrival} 航班數據失敗: {str(e)}")
        
        if self.flightstats_api:
            try:
                time.sleep(self.request_delay)
                logger.info(f"[Future] 嘗試從 FlightStats 獲取 {departure}->{arrival} 的未來 7 天航班 (從 {today_date_str})")
                fs_flights_raw = self.flightstats_api.get_flights(departure, arrival, today_date_str, days_to_fetch=7) 
                
                if fs_flights_raw:
                    logger.info(f"[Future] FlightStats 返回 {len(fs_flights_raw)} 筆原始記錄 (7天)，開始篩選...")
                    for flight in fs_flights_raw:
                        airline_id = flight.get('airline_id')
                        if airline_id in TARGET_AIRLINES:
                            flight_number = flight.get('flight_number', '')
                            dep_dt_str = flight.get('scheduled_departure')
                            dep_date = dep_dt_str[:10] if isinstance(dep_dt_str, str) and len(dep_dt_str) >= 10 else ''
                            flight_key = f"{flight_number}_{dep_date}" if flight_number and dep_date else None
                            
                            is_new = flight_key and flight_key not in processed_flights_dict
                            if is_new:
                                fs_processed_flights.append(flight)
                                
                    if fs_processed_flights:
                        logger.info(f"[Future] 從 FlightStats 篩選出 {len(fs_processed_flights)} 個新的目標航班")
                        self._add_unique_flights(flights, fs_processed_flights, processed_flights_dict)
                    else:
                        logger.info(f"[Future] 從 FlightStats 未篩選出需要補充的新航班")
                else:
                    logger.warning(f"[Future] 從 FlightStats 獲取 {departure}->{arrival} 航班返回空結果 (未來 7 天)")
            except Exception as e:
                logger.error(f"[Future] 從 FlightStats 獲取 {departure}->{arrival} 航班數據失敗: {str(e)}")
        
        logger.info(f"[Future] 航線 {departure}->{arrival} 同步完成，共獲得 {len(flights)} 個唯一/合併後航班。")
        return flights
    # --- 結束新增方法 --- 
    
    # 修改 sync_popular_routes：移除 date/days 參數，調用新方法
    def sync_popular_routes(self) -> Dict[Tuple[str, str], List[Dict]]:
        """
        同步熱門航線的所有未來航班數據。
        TDX 獲取所有未來數據，FlightStats 獲取未來 7 天數據。
            
        Returns:
            一個字典，鍵是 (departure, arrival) 的元組，值是該航線的航班列表
        """
        all_flights_by_route = {} 
        popular_routes = POPULAR_DOMESTIC_ROUTES_TUPLES + POPULAR_INTERNATIONAL_ROUTES_TUPLES

        logger.info(f"開始同步 {len(popular_routes)} 條熱門航線的所有未來航班數據 (FlightStats 限未來 7 天)")

        for dep, arr in popular_routes:
            logger.info(f"正在處理熱門航線: {dep} -> {arr}")
            try:
                # 調用新的 sync_future_flights 方法
                route_flights = self.sync_future_flights(dep, arr) 
                if route_flights:
                    logger.info(f"為 {dep}->{arr} 找到 {len(route_flights)} 個未來航班")
                    all_flights_by_route[(dep, arr)] = route_flights 
                else:
                    logger.warning(f"為 {dep}->{arr} 未找到未來航班")
                
                time.sleep(self.request_delay)
            except Exception as e:
                logger.error(f"同步熱門航線 {dep}->{arr} 時發生錯誤: {e}")
                continue

        logger.info(f"熱門航線同步完成，共處理 {len(all_flights_by_route)} 條有效航線")
        return all_flights_by_route 

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
        flights = sync_manager.sync_flights(args.departure, args.arrival, args.date)
        print(json.dumps(flights, ensure_ascii=False, indent=2))
    
    elif args.command == 'popular':
        popular_routes = sync_manager.sync_popular_routes()
        # 轉換結果為可序列化的格式
        result = {}
        for route, flights in popular_routes.items():
            result[f"{route[0]}-{route[1]}"] = flights
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 