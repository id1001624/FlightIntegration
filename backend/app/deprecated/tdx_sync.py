#!/usr/bin/env python
"""
TDX API 用戶端
用於同步台灣國內航班數據
"""
import os
import sys
import json
import logging
import requests
import time
from datetime import datetime, timedelta
from urllib.parse import quote
import base64
import hashlib

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('tdx_api')

class TdxApiClient:
    """TDX API 用戶端"""
    
    # 指定台灣機場列表
    TAIWAN_AIRPORTS = ['TPE', 'TSA', 'RMQ', 'KHH', 'TNN', 'CYI', 'HUN', 'TTT', 'KNH', 'MZG', 'LZN', 'MFK', 'KYD', 'GNI', 'WOT', 'CMJ']
    
    # 指定航空公司列表
    TARGET_AIRLINES = ['AE', 'B7', 'BR', 'CI', 'CX', 'DA', 'IT', 'JL', 'JX', 'OZ']
    
    def __init__(self):
        """初始化TDX API用戶端"""
        self.client_id = os.environ.get('TDX_CLIENT_ID')
        self.client_secret = os.environ.get('TDX_CLIENT_SECRET')
        if not self.client_id or not self.client_secret:
            raise ValueError("請設置TDX_CLIENT_ID和TDX_CLIENT_SECRET環境變數")
        
        self.token_url = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
        self.base_url = "https://tdx.transportdata.tw/api/basic"
        self.access_token = None
        self.token_expiry = 0
        
        # 用於緩存數據的字典
        self.airports_cache = None
        self.airlines_cache = None
    
    def _get_token(self):
        """獲取API訪問令牌"""
        if self.access_token and time.time() < self.token_expiry:
            return self.access_token
        
        try:
            logger.info("正在獲取TDX API訪問令牌")
            headers = {'content-type': 'application/x-www-form-urlencoded'}
            data = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }
            
            response = requests.post(self.token_url, headers=headers, data=data)
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get('access_token')
                self.token_expiry = time.time() + token_data.get('expires_in', 1800) - 60  # 提前60秒過期
                logger.info("成功獲取TDX API訪問令牌")
                return self.access_token
            else:
                logger.error(f"獲取TDX API訪問令牌失敗: {response.status_code}")
                logger.error(f"錯誤訊息: {response.text}")
                return None
        except Exception as e:
            logger.error(f"獲取TDX API訪問令牌時出錯: {str(e)}")
            return None
    
    def _make_request(self, url, params=None):
        """向API發送請求"""
        token = self._get_token()
        if not token:
            return None
        
        if params is None:
            params = {}
        
        params['$format'] = 'JSON'
        headers = {
            'Authorization': f'Bearer {token}'
        }
        
        # 重試機制
        max_retries = 3
        retry_count = 0
        retry_delay = 5
        
        while retry_count < max_retries:
            try:
                response = requests.get(url, headers=headers, params=params)
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:  # 請求次數過多
                    retry_delay = min(retry_delay * 2, 60)
                    logger.warning(f"請求次數過多，等待 {retry_delay} 秒後重試")
                    time.sleep(retry_delay)
                    retry_count += 1
                    continue
                elif response.status_code == 401:  # 令牌過期
                    logger.warning("令牌過期，重新獲取")
                    self.access_token = None  # 重置令牌
                    self._get_token()
                    retry_count += 1
                    continue
                else:
                    logger.error(f"API請求失敗: {response.status_code}")
                    logger.error(f"URL: {url}")
                    logger.error(f"錯誤訊息: {response.text}")
                    return None
            except Exception as e:
                logger.error(f"API請求時出錯: {str(e)}")
                retry_count += 1
                if retry_count < max_retries:
                    time.sleep(retry_delay)
                else:
                    return None
        
        return None
    
    def get_airports(self, refresh=False):
        """獲取台灣機場列表，僅返回指定的機場"""
        if not refresh and self.airports_cache:
            return self.airports_cache
        
        logger.info("正在獲取台灣機場列表")
        url = f"{self.base_url}/v2/Air/Airport"
        data = self._make_request(url)
        
        if data:
            # 處理數據格式
            if isinstance(data, list):
                airports = data
            else:
                airports = data.get('Airports', [])
            
            # 格式化機場數據，僅包含指定機場
            formatted_airports = []
            for airport in airports:
                try:
                    iata_code = airport.get('AirportIATA')
                    # 只處理指定的台灣機場
                    if iata_code in self.TAIWAN_AIRPORTS:
                        airport_data = {
                            'iata_code': iata_code,
                            'icao_code': airport.get('AirportICAO'),
                            'name': airport.get('AirportName', {}).get('Zh_tw', ''),
                            'name_en': airport.get('AirportName', {}).get('En', ''),
                            'city': airport.get('AirportCityName', {}).get('Zh_tw', ''),
                            'city_en': airport.get('AirportCityName', {}).get('En', ''),
                            'country': 'TW',
                            'country_name': '台灣',
                            'latitude': airport.get('AirportPosition', {}).get('PositionLat', 0),
                            'longitude': airport.get('AirportPosition', {}).get('PositionLon', 0),
                            'data_source': 'TDX'
                        }
                        formatted_airports.append(airport_data)
                except Exception as e:
                    logger.error(f"處理機場數據時出錯: {str(e)}")
                    continue
            
            logger.info(f"成功獲取 {len(formatted_airports)} 個台灣機場")
            self.airports_cache = formatted_airports
            return formatted_airports
        else:
            logger.error("獲取台灣機場列表失敗")
            return []
    
    def get_airport(self, iata_code):
        """獲取特定機場信息，僅處理指定的機場"""
        if iata_code not in self.TAIWAN_AIRPORTS:
            logger.warning(f"機場 {iata_code} 不在指定的台灣機場清單中")
            return None
            
        # 先查詢緩存
        if self.airports_cache:
            for airport in self.airports_cache:
                if airport.get('iata_code') == iata_code:
                    return airport
        
        # 緩存未命中，嘗試獲取所有機場再查詢
        airports = self.get_airports(refresh=True)
        for airport in airports:
            if airport.get('iata_code') == iata_code:
                return airport
        
        logger.error(f"找不到機場 {iata_code}")
        return None
    
    def get_airlines(self, refresh=False):
        """獲取指定航空公司列表"""
        if not refresh and self.airlines_cache:
            return self.airlines_cache
        
        logger.info("正在從航班資料中提取指定航空公司")
        
        try:
            # 使用FIDS航班資料來獲取航空公司資訊
            date_str = datetime.now().strftime('%Y-%m-%d')
            url = f"{self.base_url}/v2/Air/FIDS/Airport/Departure/TPE"
            params = {
                '$filter': f"date(ScheduleDepartureTime) eq {date_str}"
            }
            
            data = self._make_request(url, params)
            
            if data:
                # 處理數據格式
                if isinstance(data, list):
                    flights = data
                else:
                    flights = data.get('FIDSAirport', [])
                
                # 從航班中提取航空公司代碼，僅處理指定的航空公司
                airlines = []
                for flight in flights:
                    airline_code = flight.get('AirlineID')
                    if airline_code and airline_code in self.TARGET_AIRLINES:
                        # 檢查是否已添加
                        if not any(a.get('iata_code') == airline_code for a in airlines):
                            airline_data = {
                                'iata_code': airline_code,
                                'name': f"{airline_code} 航空",  # 無法從TDX API獲取航空公司名稱
                                'data_source': 'TDX'
                            }
                            airlines.append(airline_data)
                
                logger.info(f"從航班時刻表提取了 {len(airlines)} 個指定航空公司")
                self.airlines_cache = airlines
                return airlines
            else:
                logger.error("從航班時刻表提取航空公司失敗")
                return []
        except Exception as e:
            logger.error(f"獲取航空公司列表時出錯: {str(e)}")
            return []
    
    def get_airline(self, iata_code):
        """獲取特定航空公司信息，僅處理指定的航空公司"""
        if iata_code not in self.TARGET_AIRLINES:
            logger.warning(f"航空公司 {iata_code} 不在指定清單中")
            return None
            
        # 先查詢緩存
        if self.airlines_cache:
            for airline in self.airlines_cache:
                if airline.get('iata_code') == iata_code:
                    return airline
        
        # 緩存未命中，嘗試獲取所有航空公司再查詢
        airlines = self.get_airlines(refresh=True)
        for airline in airlines:
            if airline.get('iata_code') == iata_code:
                return airline
        
        # 如果仍未找到，創建一個基本記錄
        logger.warning(f"找不到航空公司 {iata_code}，創建基本記錄")
        return {
            'iata_code': iata_code,
            'name': f"{iata_code} 航空",
            'data_source': 'TDX'
        }
    
    def get_fids_flights(self, iata_code, date_str=None):
        """
        獲取特定機場的FIDS航班信息
        
        Args:
            iata_code: 機場IATA代碼
            date_str: 日期字符串，格式為YYYY-MM-DD
        
        Returns:
            航班數據列表
        """
        if date_str is None:
            date_str = datetime.now().strftime('%Y-%m-%d')
            
        logger.info(f"正在獲取 {date_str} {iata_code} 機場的FIDS航班資訊")
        
        # 檢查是否為指定機場
        if iata_code not in self.TAIWAN_AIRPORTS:
            logger.warning(f"機場 {iata_code} 不在指定的台灣機場清單中")
            return []
            
        url = f"{self.base_url}/v2/Air/FIDS/Airport/Departure/{iata_code}"
        params = {
            '$filter': f"date(ScheduleDepartureTime) eq {date_str}"
        }
        
        data = self._make_request(url, params)
        
        if not data:
            logger.error(f"獲取 {iata_code} 機場的FIDS航班資訊失敗")
            return []
            
        # 處理數據格式
        if isinstance(data, list):
            flights = data
        else:
            flights = data.get('FIDSAirport', [])
            
        # 篩選指定航空公司的航班
        filtered_flights = []
        for flight in flights:
            airline_code = flight.get('AirlineID')
            if airline_code in self.TARGET_AIRLINES:
                filtered_flights.append(flight)
                
        logger.info(f"成功獲取 {len(filtered_flights)} 個 {iata_code} 機場的指定航空公司航班")
        return filtered_flights
    
    def get_international_schedule(self, date_str=None):
        """
        獲取國際航空定期時刻表
        
        Args:
            date_str: 日期字符串，格式為YYYY-MM-DD
            
        Returns:
            航班時刻表數據列表
        """
        if date_str is None:
            date_str = datetime.now().strftime('%Y-%m-%d')
            
        logger.info(f"正在獲取 {date_str} 的國際航空定期時刻表")
        
        url = f"{self.base_url}/v2/Air/GeneralSchedule/International"
        params = {
            '$filter': f"date(ScheduleStartDate) le {date_str} and date(ScheduleEndDate) ge {date_str}"
        }
        
        data = self._make_request(url, params)
        
        if not data:
            logger.error("獲取國際航空定期時刻表失敗")
            return []
            
        # 處理數據格式
        if isinstance(data, list):
            schedules = data
        else:
            schedules = data.get('GeneralSchedules', [])
            
        # 篩選指定機場和航空公司的航班
        filtered_schedules = []
        for schedule in schedules:
            airline_code = schedule.get('AirlineID')
            departure = schedule.get('DepartureAirportID')
            arrival = schedule.get('ArrivalAirportID')
            
            # 檢查是否符合指定條件
            departure_match = departure in self.TAIWAN_AIRPORTS
            airline_match = airline_code in self.TARGET_AIRLINES
            
            if departure_match and airline_match:
                filtered_schedules.append(schedule)
                
        logger.info(f"成功獲取 {len(filtered_schedules)} 個指定條件的國際航班")
        return filtered_schedules
    
    def get_domestic_schedule(self, date_str=None):
        """
        獲取國內航空定期時刻表
        
        Args:
            date_str: 日期字符串，格式為YYYY-MM-DD
            
        Returns:
            航班時刻表數據列表
        """
        if date_str is None:
            date_str = datetime.now().strftime('%Y-%m-%d')
            
        logger.info(f"正在獲取 {date_str} 的國內航空定期時刻表")
        
        url = f"{self.base_url}/v2/Air/GeneralSchedule/Domestic"
        params = {
            '$filter': f"date(ScheduleStartDate) le {date_str} and date(ScheduleEndDate) ge {date_str}"
        }
        
        data = self._make_request(url, params)
        
        if not data:
            logger.error("獲取國內航空定期時刻表失敗")
            return []
            
        # 處理數據格式
        if isinstance(data, list):
            schedules = data
        else:
            schedules = data.get('GeneralSchedules', [])
            
        # 篩選指定航空公司的航班
        filtered_schedules = []
        for schedule in schedules:
            airline_code = schedule.get('AirlineID')
            
            # 檢查是否符合指定條件（國內航班已經確保是台灣機場）
            if airline_code in self.TARGET_AIRLINES:
                filtered_schedules.append(schedule)
                
        logger.info(f"成功獲取 {len(filtered_schedules)} 個指定條件的國內航班")
        return filtered_schedules
    
    def get_flights(self, departure_iata, arrival_iata, date=None, days=1):
        """獲取特定日期從出發機場到目的機場的航班，綜合使用FIDS和時刻表"""
        if departure_iata not in self.TAIWAN_AIRPORTS:
            logger.warning(f"出發機場 {departure_iata} 不在指定的台灣機場清單中")
            return []
        
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        flight_list = []
        
        # 獲取指定天數的航班
        for day in range(days):
            current_date = date_obj + timedelta(days=day)
            current_date_str = current_date.strftime('%Y-%m-%d')
            
            # 1. 嘗試使用FIDS航班信息
            logger.info(f"正在獲取 {current_date_str} 從 {departure_iata} 到 {arrival_iata} 的航班")
            
            try:
                # 獲取機場FIDS時刻表
                fids_flights = self.get_fids_flights(departure_iata, current_date_str)
                
                # 篩選目的地為指定機場的航班
                filtered_flights = [flight for flight in fids_flights if flight.get('ArrivalAirportID') == arrival_iata]
                
                # 格式化航班數據
                for flight in filtered_flights:
                    try:
                        airline_code = flight.get('AirlineID', '')
                        flight_number = flight.get('FlightNumber', '')
                        
                        # 只處理指定航空公司
                        if airline_code not in self.TARGET_AIRLINES:
                            continue
                        
                        # 解析時間
                        dep_time = None
                        sched_dep_time = flight.get('ScheduleDepartureTime')
                        if sched_dep_time:
                            try:
                                dep_time = datetime.strptime(sched_dep_time, '%Y-%m-%dT%H:%M')
                            except ValueError:
                                try:
                                    dep_time = datetime.strptime(sched_dep_time, '%Y-%m-%dT%H:%M:%S')
                                except ValueError:
                                    logger.warning(f"無法解析出發時間: {sched_dep_time}")
                        
                        # 從TDX API無法獲取到達時間，估算
                        arr_time = None
                        if dep_time:
                            # 國內航班約1小時，國際航班約3小時
                            is_domestic = arrival_iata in self.TAIWAN_AIRPORTS
                            flight_hours = 1 if is_domestic else 3
                            arr_time = dep_time + timedelta(hours=flight_hours)
                        
                        # 獲取航班狀態
                        status = self._map_flight_status(flight.get('DepartureRemark', ''))
                        
                        # 模擬價格
                        price_data = self._generate_simulated_prices()
                        
                        flight_data = {
                            'flight_id': f"{airline_code}{flight_number}_{dep_time.strftime('%Y%m%d')}",
                            'flight_number': f"{airline_code}{flight_number}",
                            'airline_code': airline_code,
                            'departure_airport': departure_iata,
                            'arrival_airport': arrival_iata,
                            'departure_time': dep_time.strftime('%Y-%m-%dT%H:%M:%S') if dep_time else None,
                            'arrival_time': arr_time.strftime('%Y-%m-%dT%H:%M:%S') if arr_time else None,
                            'status': status,
                            'terminal': flight.get('Terminal', ''),
                            'gate': flight.get('Gate', ''),
                            'economy_price': price_data['economy'],
                            'business_price': price_data['business'],
                            'first_price': price_data['first'],
                            'available_seats': price_data['available_seats'],
                            'duration_minutes': 60 if arrival_iata in self.TAIWAN_AIRPORTS else 180,
                            'aircraft_type': 'Unknown',  # TDX API無此數據
                            'data_source': 'TDX'
                        }
                        flight_list.append(flight_data)
                    except Exception as e:
                        logger.error(f"處理航班數據時出錯: {str(e)}")
                        continue
                
                # 2. 如果FIDS沒有足夠數據，嘗試使用定期時刻表補充
                if len(filtered_flights) < 1:
                    is_domestic = arrival_iata in self.TAIWAN_AIRPORTS
                    
                    if is_domestic:
                        schedules = self.get_domestic_schedule(current_date_str)
                    else:
                        schedules = self.get_international_schedule(current_date_str)
                    
                    # 篩選指定路線的航班
                    route_schedules = [
                        s for s in schedules 
                        if s.get('DepartureAirportID') == departure_iata and 
                           s.get('ArrivalAirportID') == arrival_iata
                    ]
                    
                    # 處理時刻表數據
                    for schedule in route_schedules:
                        try:
                            airline_code = schedule.get('AirlineID', '')
                            flight_number = schedule.get('FlightNumber', '')
                            
                            # 只處理指定航空公司
                            if airline_code not in self.TARGET_AIRLINES:
                                continue
                            
                            # 解析時間 - 時刻表通常只有時間沒有日期
                            dep_time_str = schedule.get('DepartureTime')
                            if dep_time_str:
                                # 結合當前日期和時刻表時間
                                hour, minute = dep_time_str.split(':')
                                dep_time = current_date.replace(
                                    hour=int(hour), 
                                    minute=int(minute),
                                    second=0, 
                                    microsecond=0
                                )
                            else:
                                logger.warning(f"時刻表缺少出發時間: {schedule}")
                                continue
                            
                            # 解析到達時間
                            arr_time_str = schedule.get('ArrivalTime')
                            if arr_time_str:
                                hour, minute = arr_time_str.split(':')
                                arr_time = current_date.replace(
                                    hour=int(hour), 
                                    minute=int(minute),
                                    second=0, 
                                    microsecond=0
                                )
                                # 調整跨日航班
                                if arr_time < dep_time:
                                    arr_time += timedelta(days=1)
                            else:
                                # 估算到達時間
                                is_domestic = arrival_iata in self.TAIWAN_AIRPORTS
                                flight_hours = 1 if is_domestic else 3
                                arr_time = dep_time + timedelta(hours=flight_hours)
                            
                            # 模擬價格
                            price_data = self._generate_simulated_prices()
                            
                            flight_data = {
                                'flight_id': f"{airline_code}{flight_number}_{dep_time.strftime('%Y%m%d')}",
                                'flight_number': f"{airline_code}{flight_number}",
                                'airline_code': airline_code,
                                'departure_airport': departure_iata,
                                'arrival_airport': arrival_iata,
                                'departure_time': dep_time.strftime('%Y-%m-%dT%H:%M:%S'),
                                'arrival_time': arr_time.strftime('%Y-%m-%dT%H:%M:%S'),
                                'status': 'scheduled',  # 時刻表數據預設為已排程
                                'terminal': schedule.get('DepartureTerminal', ''),
                                'gate': '',  # 時刻表通常無登機門信息
                                'economy_price': price_data['economy'],
                                'business_price': price_data['business'],
                                'first_price': price_data['first'],
                                'available_seats': price_data['available_seats'],
                                'duration_minutes': 60 if arrival_iata in self.TAIWAN_AIRPORTS else 180,
                                'aircraft_type': 'Unknown',
                                'data_source': 'TDX_SCHEDULE'
                            }
                            flight_list.append(flight_data)
                        except Exception as e:
                            logger.error(f"處理時刻表數據時出錯: {str(e)}")
                            continue
                
                logger.info(f"成功獲取 {current_date_str} 從 {departure_iata} 到 {arrival_iata} 的 {len(flight_list)} 個航班")
            except Exception as e:
                logger.error(f"獲取航班時出錯: {str(e)}")
                continue
        
        return flight_list
    
    def _map_flight_status(self, status_text):
        """將TDX API的航班狀態映射到標準狀態"""
        if not status_text:
            return 'scheduled'
        
        status_text = status_text.lower()
        if '取消' in status_text or 'cancel' in status_text:
            return 'cancelled'
        elif '延誤' in status_text or 'delay' in status_text:
            return 'delayed'
        elif '出發' in status_text or 'depart' in status_text:
            return 'in-air'
        elif '抵達' in status_text or 'arriv' in status_text:
            return 'landed'
        elif '登機' in status_text or 'board' in status_text:
            return 'boarding'
        else:
            return 'scheduled'
    
    def _generate_simulated_prices(self):
        """生成模擬票價"""
        import random
        
        economy_base = random.randint(2500, 5000)
        business_multiplier = random.uniform(1.8, 2.5)
        first_multiplier = random.uniform(3.0, 4.5)
        
        return {
            'economy': economy_base,
            'business': int(economy_base * business_multiplier),
            'first': int(economy_base * first_multiplier),
            'available_seats': random.randint(5, 180)
        }

if __name__ == "__main__":
    # 簡單測試代碼
    tdx = TdxApiClient()
    airports = tdx.get_airports()
    print(f"獲取了 {len(airports)} 個台灣機場")
    
    airlines = tdx.get_airlines()
    print(f"獲取了 {len(airlines)} 個指定航空公司")
    
    # 測試FIDS航班資訊
    tpe_flights = tdx.get_fids_flights('TPE')
    print(f"獲取了 {len(tpe_flights)} 個TPE機場的FIDS航班")
    
    # 測試國際航班時刻表
    intl_schedules = tdx.get_international_schedule()
    print(f"獲取了 {len(intl_schedules)} 個國際航班時刻表")
    
    # 測試國內航班時刻表
    dom_schedules = tdx.get_domestic_schedule()
    print(f"獲取了 {len(dom_schedules)} 個國內航班時刻表")
    
    # 測試特定路線航班
    tpe_to_khh = tdx.get_flights('TPE', 'KHH')
    print(f"獲取了 {len(tpe_to_khh)} 個TPE->KHH航班")
    if tpe_to_khh:
        print(f"範例航班: {tpe_to_khh[0]['flight_number']} ({tpe_to_khh[0]['departure_time']} -> {tpe_to_khh[0]['arrival_time']})")
        
    tpe_to_nrt = tdx.get_flights('TPE', 'NRT')
    print(f"獲取了 {len(tpe_to_nrt)} 個TPE->NRT航班")
    if tpe_to_nrt:
        print(f"範例航班: {tpe_to_nrt[0]['flight_number']} ({tpe_to_nrt[0]['departure_time']} -> {tpe_to_nrt[0]['arrival_time']})") 