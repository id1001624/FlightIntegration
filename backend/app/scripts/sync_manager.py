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
    
    # 台灣機場代碼列表（移除小機場 WOT, CMJ）
    TAIWAN_AIRPORTS = ['TPE', 'TSA', 'RMQ', 'KHH', 'TNN', 'CYI', 'HUN', 'TTT', 'KNH', 'MZG', 'LZN', 'MFK', 'KYD', 'GNI']
    
    # 指定航空公司列表
    TARGET_AIRLINES = ['AE', 'B7', 'BR', 'CI', 'CX', 'DA', 'IT', 'JL', 'JX', 'OZ']
    
    # 熱門國際航線（優化為最常用路線）
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
        
        # 先從 TDX API 獲取
        if self.tdx_api and iata_code in self.TAIWAN_AIRPORTS:
            try:
                airport = self.tdx_api.get_airport(iata_code)
                if airport:
                    logger.info(f"已從 TDX API 獲取機場 {iata_code}")
                    self.airports_cache[iata_code] = airport
                    return airport
            except Exception as e:
                logger.error(f"從 TDX API 獲取機場 {iata_code} 失敗: {str(e)}")
        
        # 如果 TDX 獲取失敗，嘗試從 FlightStats 獲取
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
        同步航空公司數據，優先處理目標航空公司
        
        Returns:
            航空公司數據列表
        """
        airlines = []
        
        # 先從 TDX API 獲取目標航空公司資料
        if self.tdx_api:
            try:
                tdx_airlines = self.tdx_api.get_airlines()
                if tdx_airlines:
                    logger.info(f"已從 TDX API 獲取 {len(tdx_airlines)} 個航空公司")
                    airlines.extend(tdx_airlines)
            except Exception as e:
                logger.error(f"從 TDX API 獲取航空公司資料失敗: {str(e)}")
        
        # 從 FlightStats 獲取目標航空公司資料
        if self.flightstats_api:
            tdx_iata_codes = set(airline.get('iata_code') for airline in airlines)
            missing_airlines = [code for code in self.TARGET_AIRLINES if code not in tdx_iata_codes]
            
            if missing_airlines:
                logger.info(f"從 TDX API 缺少 {len(missing_airlines)} 個目標航空公司，嘗試從 FlightStats 獲取")
                for iata_code in missing_airlines:
                    try:
                        airline = self.flightstats_api.get_airline(iata_code)
                        if airline:
                            airline['data_source'] = 'FlightStats'
                            airlines.append(airline)
                            logger.info(f"已從 FlightStats 獲取航空公司 {iata_code}")
                    except Exception as e:
                        logger.error(f"從 FlightStats 獲取航空公司 {iata_code} 失敗: {str(e)}")
        
        # 更新緩存
        for airline in airlines:
            if 'iata_code' in airline:
                self.airlines_cache[airline['iata_code']] = airline
            elif 'iata' in airline:
                self.airlines_cache[airline['iata']] = airline
        
        logger.info(f"總共獲取了 {len(airlines)} 個航空公司")
        return airlines
    
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
                            flights.extend(filtered_flights)
                        else:
                            logger.warning(f"從 FlightStats 獲取航班後未找到目標航空公司航班")
                except Exception as e:
                    logger.error(f"從 FlightStats 獲取航班數據失敗: {str(e)}")
            return flights
        
        # 判斷航線類型（國內或國際）
        is_domestic = self.is_domestic_route(departure, arrival)
        
        if is_domestic:
            logger.info(f"檢測到國內航線，優先使用 TDX API")
            # 國內航線優先使用 TDX API
            if self.tdx_api:
                try:
                    tdx_flights = self.tdx_api.get_flights(departure, arrival, date.strftime('%Y-%m-%d'), days)
                    if tdx_flights:
                        logger.info(f"已從 TDX 獲取 {len(tdx_flights)} 個航班")
                        flights.extend(tdx_flights)
                    else:
                        logger.warning(f"從 TDX 獲取 {departure}->{arrival} 航班返回空結果")
                except Exception as e:
                    logger.error(f"從 TDX 獲取航班數據失敗: {str(e)}")
            
            # 如果 TDX 獲取失敗或結果為空，嘗試從 FlightStats 獲取
            if not flights and self.flightstats_api:
                try:
                    logger.info("嘗試使用 FlightStats API 獲取國內航班作為備用")
                    fs_flights = self.flightstats_api.get_flights(
                        departure, arrival, date.strftime('%Y-%m-%d'), days
                    )
                    if fs_flights:
                        # 篩選目標航空公司
                        filtered_flights = [f for f in fs_flights if f.get('airline_code') in self.TARGET_AIRLINES]
                        if filtered_flights:
                            logger.info(f"已從 FlightStats 獲取並篩選出 {len(filtered_flights)} 個目標航空公司航班")
                            flights.extend(filtered_flights)
                        else:
                            logger.warning(f"從 FlightStats 獲取航班後未找到目標航空公司航班")
                except Exception as e:
                    logger.error(f"從 FlightStats 獲取航班數據失敗: {str(e)}")
        else:
            logger.info(f"檢測到國際航線，使用 FlightStats API 和 TDX API 綜合查詢")
            
            # 國際航線優先使用 FlightStats API
            fs_flights = []
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
                            flights.extend(filtered_flights)
                        else:
                            logger.warning(f"從 FlightStats 獲取航班後未找到目標航空公司航班")
                except Exception as e:
                    logger.error(f"從 FlightStats 獲取航班數據失敗: {str(e)}")
            
            # 使用 TDX API 查詢國際航班數據
            if (not fs_flights or len(flights) < 3) and self.tdx_api:
                try:
                    tdx_flights = self.tdx_api.get_flights(departure, arrival, date.strftime('%Y-%m-%d'), days)
                    if tdx_flights:
                        logger.info(f"已從 TDX 獲取 {len(tdx_flights)} 個國際航班")
                        # 與已有的FlightStats航班數據進行合併，避免重複
                        for tdx_flight in tdx_flights:
                            # 檢查是否已存在相同航班
                            flight_exists = False
                            for existing_flight in flights:
                                if (existing_flight.get('flight_number') == tdx_flight.get('flight_number') and 
                                    existing_flight.get('departure_time')[:10] == tdx_flight.get('departure_time')[:10]):
                                    flight_exists = True
                                    break
                            
                            if not flight_exists:
                                flights.append(tdx_flight)
                        
                        logger.info(f"合併後總共有 {len(flights)} 個航班")
                    else:
                        logger.warning(f"從 TDX 獲取 {departure}->{arrival} 航班返回空結果")
                except Exception as e:
                    logger.error(f"從 TDX 獲取航班數據失敗: {str(e)}")
        
        return flights
    
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
        """同步所有從台灣出發的航班"""
        if date is None:
            date = datetime.now()
        elif isinstance(date, str):
            date = datetime.strptime(date, "%Y-%m-%d")
        
        results = {}
        
        # 優化：按機場重要性排序處理
        priority_airports = ['TPE', 'TSA', 'KHH']  # 主要機場優先
        other_airports = [ap for ap in self.TAIWAN_AIRPORTS if ap not in priority_airports]
        
        # 處理所有機場
        for departure in priority_airports + other_airports:
            if self.tdx_api:
                try:
                    logger.info(f"正在獲取從 {departure} 出發的所有航班")
                    all_flights = []
                    
                    # 使用TDX API的FIDS功能獲取航班信息
                    try:
                        date_str = date.strftime('%Y-%m-%d')
                        fids_flights = self.tdx_api.get_fids_flights(departure, date_str)
                        
                        if fids_flights:
                            processed_flights = self._process_tdx_flights(fids_flights, departure)
                            all_flights.extend(processed_flights)
                            logger.info(f"從 {departure} 獲取了 {len(processed_flights)} 個航班")
                    except Exception as e:
                        logger.error(f"從TDX獲取 {departure} 航班數據失敗: {str(e)}")
                    
                    # 如果TDX數據不足，使用FlightStats補充
                    if not all_flights and self.flightstats_api:
                        logger.info(f"從TDX獲取 {departure} 航班數據為空，嘗試從FlightStats獲取")
                        
                        # 根據機場類型選擇路線
                        routes = []
                        if departure in priority_airports:
                            # 主要機場使用完整路線
                            routes = [r for r in (self.POPULAR_DOMESTIC_ROUTES + self.POPULAR_INTERNATIONAL_ROUTES) if r[0] == departure]
                        else:
                            # 次要機場只查詢國內航線
                            routes = [r for r in self.POPULAR_DOMESTIC_ROUTES if r[0] == departure]
                        
                        # 批次處理航線查詢
                        for route in routes:
                            try:
                                fs_flights = self.flightstats_api.get_flights(
                                    route[0], route[1], 
                                    date.strftime('%Y-%m-%d'),
                                    days,
                                    max_retries=2  # 減少重試次數
                                )
                                if fs_flights:
                                    filtered_flights = [f for f in fs_flights if f.get('airline_code') in self.TARGET_AIRLINES]
                                    all_flights.extend(filtered_flights)
                                    
                                # 添加延遲以避免請求過快
                                time.sleep(0.5)
                            except Exception as e:
                                logger.error(f"從FlightStats獲取 {route} 航班失敗: {str(e)}")
                                continue
                    
                    results[departure] = all_flights
                    
                except Exception as e:
                    logger.error(f"獲取 {departure} 出發航班時出錯: {str(e)}")
                    results[departure] = []
                
                # 主要機場之間添加較長延遲，避免請求過快
                if departure in priority_airports:
                    time.sleep(1)
                else:
                    time.sleep(0.5)
        
        return results

    def _process_tdx_flights(self, fids_flights: List[Dict], departure: str) -> List[Dict]:
        """處理TDX航班數據的輔助方法"""
        processed_flights = []
        for flight in fids_flights:
            try:
                airline_code = flight.get('AirlineID', '')
                if not airline_code or airline_code not in self.TARGET_AIRLINES:
                    continue
                
                flight_number = flight.get('FlightNumber', '').replace(airline_code, '')
                arrival_airport = flight.get('ArrivalAirportID', '')
                
                # 解析時間
                dep_time = datetime.strptime(flight.get('ScheduleDepartureTime', ''), '%Y-%m-%d %H:%M:%S')
                arr_time = datetime.strptime(flight.get('ScheduleArrivalTime', ''), '%Y-%m-%d %H:%M:%S')
                
                processed_flight = {
                    'flight_id': f"{airline_code}{flight_number}_{dep_time.strftime('%Y%m%d')}",
                    'flight_number': f"{airline_code}{flight_number}",
                    'airline_code': airline_code,
                    'departure_airport': departure,
                    'arrival_airport': arrival_airport,
                    'departure_time': dep_time.strftime('%Y-%m-%dT%H:%M:%S'),
                    'arrival_time': arr_time.strftime('%Y-%m-%dT%H:%M:%S'),
                    'status': self.tdx_api._map_flight_status(flight.get('DepartureRemark', '')),
                    'data_source': 'TDX'
                }
                processed_flights.append(processed_flight)
            except Exception as e:
                logger.error(f"處理航班數據時出錯: {str(e)}")
                continue
        
        return processed_flights


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