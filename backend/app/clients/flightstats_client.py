"""
FlightStats API客戶端 - 專門處理FlightStats API的交互
"""
import os
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple

from app.clients.base_client import BaseAPIClient
from app.utils.date_utils import parse_datetime, format_datetime, get_date_range
from app.utils.cache_utils import cached

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
        
        # 台灣機場列表
        self.taiwan_airports = ['TPE', 'TSA', 'RMQ', 'KHH', 'TNN', 'CYI', 'HUN', 'TTT', 'KNH', 'LZN', 'MFK', 'KYD', 'GNI']
        
        # 目標航空公司 - 只處理國際航班的航空公司，不包含AE、B7、DA
        # BR: 長榮航空 (EVA Air)
        # CI: 中華航空 (China Airlines)
        # CX: 國泰航空 (Cathay Pacific)
        # IT: 台灣虎航 (Tiger Air Taiwan)
        # JL: 日本航空 (Japan Airlines)
        # JX: 星宇航空 (STARLUX Airlines)
        # OZ: 韓亞航空 (Asiana Airlines)
        self.target_airlines = ['BR', 'CI', 'CX', 'IT', 'JL', 'JX', 'OZ']
        
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
            'appKey': self.app_key
        }
        
        if extra_params:
            params.update(extra_params)
            
        return params
    
    @cached(ttl=86400, key_prefix="flightstats_airports")
    def get_airports(self) -> List[Dict]:
        """
        獲取機場列表
        
        Returns:
            機場信息列表
        """
        self.logger.info("獲取FlightStats機場列表")
        
        # 嘗試從API獲取機場列表
        url = f"{self.base_url}/airports/rest/v1/json/active"
        
        response = self.make_request(
            url=url,
            params=self._build_params({
                'extendedOptions': 'includeNewFields'
            })
        )
        
        if response and 'airports' in response:
            try:
                airports = []
                for item in response['airports']:
                    airport = {
                        'iata_code': item.get('iata', ''),
                        'name': item.get('name', ''),
                        'name_en': item.get('name', ''),
                        'city': item.get('city', ''),
                        'city_en': item.get('city', ''),
                        'country': item.get('countryName', ''),
                        'country_en': item.get('countryName', ''),
                        'position': {
                            'lat': item.get('latitude', 0),
                            'lon': item.get('longitude', 0)
                        },
                        'timezone': item.get('timeZoneRegionName', ''),
                        'fs_code': item.get('fs', '')
                    }
                    
                    # 只包含有IATA代碼的機場
                    if airport['iata_code']:
                        airports.append(airport)
                        
                self.logger.info(f"成功獲取{len(airports)}個機場信息")
                return airports
            except Exception as e:
                self.logger.error(f"解析機場數據時出錯: {str(e)}")
        
        # 如果API獲取失敗，使用預定義的機場列表
        self.logger.warning("從API獲取機場列表失敗，使用預定義列表")
        return self._get_predefined_airports()
    
    def _get_predefined_airports(self) -> List[Dict]:
        """
        獲取預定義的主要機場列表
        
        Returns:
            機場信息列表
        """
        # 主要國際機場的基本信息
        predefined_airports = [
            {
                'iata_code': 'TPE',
                'name': '臺灣桃園國際機場',
                'name_en': 'Taiwan Taoyuan International Airport',
                'city': '臺北',
                'city_en': 'Taipei',
                'country': '臺灣',
                'country_en': 'Taiwan',
                'position': {'lat': 25.0777, 'lon': 121.2322},
                'timezone': 'Asia/Taipei',
                'fs_code': 'TPE'
            },
            {
                'iata_code': 'TSA',
                'name': '臺北松山機場',
                'name_en': 'Taipei Songshan Airport',
                'city': '臺北',
                'city_en': 'Taipei',
                'country': '臺灣',
                'country_en': 'Taiwan',
                'position': {'lat': 25.0694, 'lon': 121.5522},
                'timezone': 'Asia/Taipei',
                'fs_code': 'TSA'
            },
            {
                'iata_code': 'NRT',
                'name': '成田國際機場',
                'name_en': 'Narita International Airport',
                'city': '東京',
                'city_en': 'Tokyo',
                'country': '日本',
                'country_en': 'Japan',
                'position': {'lat': 35.7647, 'lon': 140.3864},
                'timezone': 'Asia/Tokyo',
                'fs_code': 'NRT'
            },
            {
                'iata_code': 'HND',
                'name': '東京羽田國際機場',
                'name_en': 'Tokyo Haneda International Airport',
                'city': '東京',
                'city_en': 'Tokyo',
                'country': '日本',
                'country_en': 'Japan',
                'position': {'lat': 35.5494, 'lon': 139.7798},
                'timezone': 'Asia/Tokyo',
                'fs_code': 'HND'
            },
            {
                'iata_code': 'KIX',
                'name': '關西國際機場',
                'name_en': 'Kansai International Airport',
                'city': '大阪',
                'city_en': 'Osaka',
                'country': '日本',
                'country_en': 'Japan',
                'position': {'lat': 34.4272, 'lon': 135.2441},
                'timezone': 'Asia/Tokyo',
                'fs_code': 'KIX'
            }
        ]
        
        # 確保所有台灣機場都包含在列表中
        taiwan_codes = [airport['iata_code'] for airport in predefined_airports if airport['country'] == '臺灣']
        for code in self.taiwan_airports:
            if code not in taiwan_codes:
                predefined_airports.append({
                    'iata_code': code,
                    'name': f'臺灣機場 ({code})',
                    'name_en': f'Taiwan Airport ({code})',
                    'city': '臺灣',
                    'city_en': 'Taiwan',
                    'country': '臺灣',
                    'country_en': 'Taiwan',
                    'position': {'lat': 0, 'lon': 0},
                    'timezone': 'Asia/Taipei',
                    'fs_code': code
                })
                
        return predefined_airports
    
    @cached(ttl=86400, key_prefix="flightstats_airport")
    def get_airport(self, iata_code: str) -> Optional[Dict]:
        """
        獲取特定機場信息
        
        Args:
            iata_code: 機場IATA代碼
            
        Returns:
            機場信息字典，未找到時返回None
        """
        if not iata_code:
            self.logger.error("IATA代碼為空")
            return None
            
        iata_code = iata_code.strip().upper()
        self.logger.info(f"獲取機場信息: {iata_code}")
        
        # 從API獲取機場信息
        url = f"{self.base_url}/airports/rest/v1/json/{iata_code}/today"
        
        response = self.make_request(
            url=url,
            params=self._build_params({
                'extendedOptions': 'includeNewFields'
            })
        )
        
        if response and 'airport' in response:
            try:
                item = response['airport']
                airport = {
                    'iata_code': item.get('iata', ''),
                    'name': item.get('name', ''),
                    'name_en': item.get('name', ''),
                    'city': item.get('city', ''),
                    'city_en': item.get('city', ''),
                    'country': item.get('countryName', ''),
                    'country_en': item.get('countryName', ''),
                    'position': {
                        'lat': item.get('latitude', 0),
                        'lon': item.get('longitude', 0)
                    },
                    'timezone': item.get('timeZoneRegionName', ''),
                    'fs_code': item.get('fs', '')
                }
                return airport
            except Exception as e:
                self.logger.error(f"解析機場數據時出錯: {str(e)}")
        
        # 如果API獲取失敗，從預定義列表查找
        self.logger.warning(f"從API獲取機場信息失敗: {iata_code}，從預定義列表查找")
        predefined_airports = self._get_predefined_airports()
        
        for airport in predefined_airports:
            if airport['iata_code'] == iata_code:
                return airport
                
        # 尚未找到，嘗試從所有機場列表查找
        all_airports = self.get_airports()
        for airport in all_airports:
            if airport['iata_code'] == iata_code:
                return airport
                
        self.logger.warning(f"未找到機場: {iata_code}")
        return None
    
    @cached(ttl=86400, key_prefix="flightstats_airlines")
    def get_airlines(self) -> List[Dict]:
        """
        獲取航空公司列表
        
        Returns:
            航空公司信息列表
        """
        self.logger.info("獲取FlightStats航空公司列表")
        
        # 從API獲取航空公司列表
        url = f"{self.base_url}/airlines/rest/v1/json/active"
        
        response = self.make_request(
            url=url,
            params=self._build_params()
        )
        
        if response and 'airlines' in response:
            try:
                airlines = []
                for item in response['airlines']:
                    airline = {
                        'iata_code': item.get('iata', ''),
                        'name': item.get('name', ''),
                        'name_en': item.get('name', ''),
                        'fs_code': item.get('fs', ''),
                        'icao_code': item.get('icao', ''),
                        'is_active': item.get('active', False),
                        'country': item.get('countryName', ''),
                        'country_en': item.get('countryName', '')
                    }
                    
                    # 只包含有IATA代碼的航空公司，並優先處理目標航空公司
                    if airline['iata_code']:
                        airlines.append(airline)
                        
                self.logger.info(f"成功獲取{len(airlines)}個航空公司信息")
                
                # 對航空公司列表進行排序，將目標航空公司放在前面
                airlines.sort(key=lambda x: (x['iata_code'] not in self.target_airlines, x['iata_code']))
                
                return airlines
            except Exception as e:
                self.logger.error(f"解析航空公司數據時出錯: {str(e)}")
        
        # 如果API獲取失敗，返回預定義的航空公司列表
        self.logger.warning("從API獲取航空公司列表失敗，使用預定義列表")
        return self._get_predefined_airlines()
    
    def _get_predefined_airlines(self) -> List[Dict]:
        """
        獲取預定義的主要航空公司列表
        
        Returns:
            航空公司信息列表
        """
        # 主要航空公司的基本信息
        predefined_airlines = [
            {
                'iata_code': 'CI',
                'name': '中華航空',
                'name_en': 'China Airlines',
                'fs_code': 'CAL',
                'icao_code': 'CAL',
                'is_active': True,
                'country': '臺灣',
                'country_en': 'Taiwan'
            },
            {
                'iata_code': 'BR',
                'name': '長榮航空',
                'name_en': 'EVA Air',
                'fs_code': 'EVA',
                'icao_code': 'EVA',
                'is_active': True,
                'country': '臺灣',
                'country_en': 'Taiwan'
            },
            {
                'iata_code': 'CX',
                'name': '中國國際航空',
                'name_en': 'Air China',
                'fs_code': 'CA',
                'icao_code': 'CCA',
                'is_active': True,
                'country': '中國',
                'country_en': 'China'
            },
            {
                'iata_code': 'IT',
                'name': '中國國際航空',
                'name_en': 'Air China',
                'fs_code': 'CA',
                'icao_code': 'CCA',
                'is_active': True,
                'country': '中國',
                'country_en': 'China'
            },
            {
                'iata_code': 'JL',
                'name': '日本航空',
                'name_en': 'Japan Airlines',
                'fs_code': 'JL',
                'icao_code': 'JAL',
                'is_active': True,
                'country': '日本',
                'country_en': 'Japan'
            },
            {
                'iata_code': 'JX',
                'name': '日本航空',
                'name_en': 'Japan Airlines',
                'fs_code': 'JL',
                'icao_code': 'JAL',
                'is_active': True,
                'country': '日本',
                'country_en': 'Japan'
            },
            {
                'iata_code': 'OZ',
                'name': '大韓航空',
                'name_en': 'Korean Air',
                'fs_code': 'KE',
                'icao_code': 'KAL',
                'is_active': True,
                'country': '韓國',
                'country_en': 'Korea'
            }
        ]
        
        # 確保所有目標航空公司都包含在列表中
        existing_codes = [airline['iata_code'] for airline in predefined_airlines]
        for code in self.target_airlines:
            if code not in existing_codes:
                predefined_airlines.append({
                    'iata_code': code,
                    'name': f'航空公司 ({code})',
                    'name_en': f'Airline ({code})',
                    'fs_code': code,
                    'icao_code': code,
                    'is_active': True,
                    'country': '未知',
                    'country_en': 'Unknown'
                })
                
        return predefined_airlines
    
    @cached(ttl=86400, key_prefix="flightstats_airline")
    def get_airline(self, iata_code: str) -> Optional[Dict]:
        """
        獲取特定航空公司信息
        
        Args:
            iata_code: 航空公司IATA代碼
            
        Returns:
            航空公司信息字典，未找到時返回None
        """
        if not iata_code:
            self.logger.error("IATA代碼為空")
            return None
            
        iata_code = iata_code.strip().upper()
        self.logger.info(f"獲取航空公司信息: {iata_code}")
        
        # 檢查代碼是否在目標航空公司中
        if iata_code not in self.target_airlines:
            self.logger.warning(f"航空公司 {iata_code} 不在目標列表中")
            # 返回一個基本信息，避免API請求
            return {
                'iata_code': iata_code,
                'name': f'航空公司 ({iata_code})',
                'name_en': f'Airline ({iata_code})',
                'fs_code': iata_code,
                'icao_code': iata_code,
                'is_active': True,
                'country': '未知',
                'country_en': 'Unknown'
            }
            
        # 從API獲取航空公司信息
        url = f"{self.base_url}/airlines/rest/v1/json/{iata_code}"
        
        response = self.make_request(
            url=url,
            params=self._build_params()
        )
        
        if response and 'airline' in response:
            try:
                item = response['airline']
                airline = {
                    'iata_code': item.get('iata', ''),
                    'name': item.get('name', ''),
                    'name_en': item.get('name', ''),
                    'fs_code': item.get('fs', ''),
                    'icao_code': item.get('icao', ''),
                    'is_active': item.get('active', False),
                    'country': item.get('countryName', ''),
                    'country_en': item.get('countryName', '')
                }
                return airline
            except Exception as e:
                self.logger.error(f"解析航空公司數據時出錯: {str(e)}")
        
        # 如果API獲取失敗，從預定義列表查找
        self.logger.warning(f"從API獲取航空公司信息失敗: {iata_code}，從預定義列表查找")
        predefined_airlines = self._get_predefined_airlines()
        
        for airline in predefined_airlines:
            if airline['iata_code'] == iata_code:
                return airline
                
        # 尚未找到，嘗試從所有航空公司列表查找
        all_airlines = self.get_airlines()
        for airline in all_airlines:
            if airline['iata_code'] == iata_code:
                return airline
                
        self.logger.warning(f"未找到航空公司: {iata_code}")
        return None
    
    @cached(ttl=7200, key_prefix="flightstats_flights")
    def get_flights(self, dep_airport: str, arr_airport: str, date: str) -> List[Dict]:
        """
        獲取特定出發地、目的地和日期的航班信息
        
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
        
        # 嘗試使用 flightstatus 接口獲取航班信息（適用於API v2格式）
        url = f"{self.base_url}/flightstatus/rest/v2/json/route/status/{dep_airport}/{arr_airport}/dep/{year}/{month}/{day}"
        
        response = self.make_request(
            url=url,
            params=self._build_params({
                'extendedOptions': 'includeNewFields,useInlinedReferences',
                'numHours': 24
            })
        )
        
        flights = []
        
        # 處理 flightStatuses 格式的回應（API v2）
        if response and 'flightStatuses' in response:
            self.logger.info(f"接收到 flightStatuses 回應，包含 {len(response['flightStatuses'])} 個航班")
            try:
                for item in response['flightStatuses']:
                    # 篩選目標航空公司
                    airline_code = item.get('carrierFsCode', '')
                    if airline_code not in self.target_airlines and len(self.target_airlines) > 0:
                        continue
                    
                    # 解析日期時間
                    scheduled_dep_time = None
                    scheduled_arr_time = None
                    actual_dep_time = None
                    actual_arr_time = None
                    
                    try:
                        # 從 departureDate.dateLocal 和 arrivalDate.dateLocal 獲取時間
                        if 'departureDate' in item and 'dateLocal' in item['departureDate']:
                            scheduled_dep_time = parse_datetime(item['departureDate']['dateLocal'])
                        
                        if 'arrivalDate' in item and 'dateLocal' in item['arrivalDate']:
                            scheduled_arr_time = parse_datetime(item['arrivalDate']['dateLocal'])
                        
                        # 獲取實際起降時間（如果有）
                        if 'operationalTimes' in item:
                            op_times = item['operationalTimes']
                            if 'actualRunwayDeparture' in op_times and 'dateLocal' in op_times['actualRunwayDeparture']:
                                actual_dep_time = parse_datetime(op_times['actualRunwayDeparture']['dateLocal'])
                            elif 'actualGateDeparture' in op_times and 'dateLocal' in op_times['actualGateDeparture']:
                                actual_dep_time = parse_datetime(op_times['actualGateDeparture']['dateLocal'])
                            
                            if 'actualRunwayArrival' in op_times and 'dateLocal' in op_times['actualRunwayArrival']:
                                actual_arr_time = parse_datetime(op_times['actualRunwayArrival']['dateLocal'])
                            elif 'actualGateArrival' in op_times and 'dateLocal' in op_times['actualGateArrival']:
                                actual_arr_time = parse_datetime(op_times['actualGateArrival']['dateLocal'])
                    except Exception as e:
                        self.logger.warning(f"解析日期時間出錯: {str(e)}")
                    
                    # 獲取航班狀態
                    status = item.get('status', '')
                    # 將 FlightStats 狀態映射到系統的 Flight 模型使用的狀態常數
                    model_status = self._map_flight_status(status)
                    
                    # 獲取設備信息
                    aircraft = ''
                    if 'flightEquipment' in item and 'scheduledEquipmentIataCode' in item['flightEquipment']:
                        aircraft = item['flightEquipment']['scheduledEquipmentIataCode']
                    
                    # 獲取航站樓和登機口信息
                    dep_terminal = ''
                    dep_gate = ''
                    arr_terminal = ''
                    arr_gate = ''
                    if 'airportResources' in item:
                        resources = item['airportResources']
                        dep_terminal = resources.get('departureTerminal', '')
                        dep_gate = resources.get('departureGate', '')
                        arr_terminal = resources.get('arrivalTerminal', '')
                        arr_gate = resources.get('arrivalGate', '')
                    
                    # 創建航班信息字典
                    flight = {
                        'flight_number': airline_code + item.get('flightNumber', ''),
                        'airline_code': airline_code,
                        'airline_name': '',  # 需要單獨獲取
                        'flight_id': str(item.get('flightId', '')),
                        'departure_airport': dep_airport,
                        'arrival_airport': arr_airport,
                        'scheduled_departure': format_datetime(scheduled_dep_time) if scheduled_dep_time else None,
                        'scheduled_arrival': format_datetime(scheduled_arr_time) if scheduled_arr_time else None,
                        'actual_departure': format_datetime(actual_dep_time) if actual_dep_time else None,
                        'actual_arrival': format_datetime(actual_arr_time) if actual_arr_time else None,
                        'departure_terminal': dep_terminal,
                        'departure_gate': dep_gate,
                        'arrival_terminal': arr_terminal,
                        'arrival_gate': arr_gate,
                        'status': model_status,  # 使用映射後的狀態常數
                        'status_code': status,    # 保留原始狀態代碼
                        'aircraft': aircraft,
                        'source': 'FlightStats'
                    }
                    
                    flights.append(flight)
                
                self.logger.info(f"成功從flightStatus接口獲取{len(flights)}個航班信息")
                return flights
            except Exception as e:
                self.logger.error(f"解析flightStatus數據時出錯: {str(e)}")
                # 如果解析flightStatus失敗，嘗試使用schedules接口
        
        # 如果flightStatus接口未返回結果，嘗試使用schedules接口（適用於API v1格式）
        if not flights:
            self.logger.info(f"嘗試使用schedules接口獲取航班信息")
            url = f"{self.base_url}/schedules/rest/v1/json/from/{dep_airport}/to/{arr_airport}/departing/{year}/{month}/{day}"
            
            response = self.make_request(
                url=url,
                params=self._build_params({
                    'extendedOptions': 'includeNewFields'
                })
            )
            
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
                
                # 創建航班信息字典
                flight = {
                    'flight_number': item.get('carrierFsCode', '') + item.get('flightNumber', ''),
                    'airline_code': item.get('carrierFsCode', ''),
                    'airline_name': '',  # 需要單獨獲取
                            'flight_id': str(item.get('flightId', '')),
                    'departure_airport': dep_airport,
                    'arrival_airport': arr_airport,
                            'scheduled_departure': format_datetime(dep_time) if dep_time else None,
                            'scheduled_arrival': format_datetime(arr_time) if arr_time else None,
                            'departure_terminal': item.get('departureTerminal', ''),
                            'status': 'STATUS_ON_TIME',  # schedules接口不提供狀態，默認為準時
                    'aircraft': item.get('flightEquipmentIataCode', ''),
                    'source': 'FlightStats'
                }
                
                flights.append(flight)
                
                self.logger.info(f"成功從schedules接口獲取{len(flights)}個航班信息")
        except Exception as e:
                    self.logger.error(f"解析schedules數據時出錯: {str(e)}")
        
        if not flights:
            self.logger.warning(f"獲取航班信息失敗: {dep_airport} → {arr_airport}, 日期: {date}")
        
            return flights
    
    def _map_flight_status(self, fs_status: str) -> str:
        """
        將FlightStats狀態代碼映射到Flight模型的狀態常數
        
        Args:
            fs_status: FlightStats狀態代碼
            
        Returns:
            對應的Flight模型狀態常數
        """
        # 狀態映射表
        status_map = {
            'A': 'STATUS_DEPARTED',  # 活躍/飛行中 -> 已起飛
            'C': 'STATUS_CANCELLED', # 取消 -> 已取消
            'D': 'STATUS_DELAYED',   # 改航 -> 延誤
            'DN': 'STATUS_DELAYED',  # 改航 -> 延誤
            'L': 'STATUS_ARRIVED',   # 著陸 -> 已到達
            'NO': 'STATUS_CANCELLED',# 未運營 -> 已取消
            'R': 'STATUS_DELAYED',   # 重定向 -> 延誤
            'S': 'STATUS_ON_TIME',   # 計劃 -> 準時
            'U': 'STATUS_ON_TIME'    # 未知 -> 默認為準時
        }
        
        return status_map.get(fs_status, 'STATUS_ON_TIME')
    
    @cached(ttl=7200, key_prefix="flightstats_flight")
    def get_flight_status(self, airline: str, flight_number: str, date: str) -> Optional[Dict]:
        """
        獲取特定航班的狀態信息
        
        Args:
            airline: 航空公司IATA代碼
            flight_number: 航班號（不含航空公司代碼）
            date: 日期字符串，格式為YYYY-MM-DD
            
        Returns:
            航班狀態信息，未找到時返回None
        """
        if not airline or not flight_number or not date:
            self.logger.error("獲取航班狀態的參數不完整")
            return None
            
        airline = airline.strip().upper()
        flight_number = flight_number.strip()
        
        # 解析日期
        try:
            dt = datetime.strptime(date, '%Y-%m-%d')
            year, month, day = dt.year, dt.month, dt.day
        except ValueError:
            self.logger.error(f"日期格式無效: {date}")
            return None
            
        self.logger.info(f"獲取航班狀態: {airline}{flight_number}, 日期: {date}")
        
        # 從API獲取航班狀態
        url = f"{self.base_url}/flightstatus/rest/v2/json/flight/status/{airline}/{flight_number}/dep/{year}/{month}/{day}"
        
        response = self.make_request(
            url=url,
            params=self._build_params({
                'extendedOptions': 'includeNewFields,useInlinedReferences'
            })
        )
        
        if not response or 'flightStatuses' not in response or not response['flightStatuses']:
            self.logger.warning(f"獲取航班狀態失敗: {airline}{flight_number}, 日期: {date}")
            return None
            
        try:
            # 取第一個匹配的航班狀態
            item = response['flightStatuses'][0]
            
            # 解析日期時間
            scheduled_dep_time = None
            actual_dep_time = None
            scheduled_arr_time = None
            actual_arr_time = None
            
            try:
                if 'departureDate' in item:
                    dep_date = item['departureDate']
                    if 'dateLocal' in dep_date:
                        scheduled_dep_time = parse_datetime(dep_date['dateLocal'])
                    if 'dateUtc' in dep_date:
                        scheduled_dep_time_utc = parse_datetime(dep_date['dateUtc'])
                
                if 'arrivalDate' in item:
                    arr_date = item['arrivalDate']
                    if 'dateLocal' in arr_date:
                        scheduled_arr_time = parse_datetime(arr_date['dateLocal'])
                    if 'dateUtc' in arr_date:
                        scheduled_arr_time_utc = parse_datetime(arr_date['dateUtc'])
                
                if 'operationalTimes' in item:
                    op_times = item['operationalTimes']
                    if 'actualRunwayDeparture' in op_times and 'dateLocal' in op_times['actualRunwayDeparture']:
                        actual_dep_time = parse_datetime(op_times['actualRunwayDeparture']['dateLocal'])
                    if 'actualRunwayArrival' in op_times and 'dateLocal' in op_times['actualRunwayArrival']:
                        actual_arr_time = parse_datetime(op_times['actualRunwayArrival']['dateLocal'])
            except Exception as e:
                self.logger.warning(f"解析日期時間出錯: {str(e)}")
            
            # 獲取航班狀態
            status = item.get('status', '')
            status_translations = {
                'A': '活躍',  # 航班正在飛行中
                'C': '取消',  # 航班已取消
                'D': '改航',  # 航班改變航線
                'DN': '改航',
                'L': '著陸',  # 航班已降落
                'NO': '未運營',
                'R': '重定向',
                'S': '計劃',  # 航班按計劃運行
                'U': '未知'
            }
            status_zh = status_translations.get(status, '未知')
            
            # 獲取設備信息
            aircraft = ''
            if 'flightEquipment' in item and 'scheduledEquipmentIataCode' in item['flightEquipment']:
                aircraft = item['flightEquipment']['scheduledEquipmentIataCode']
            
            # 獲取航站樓和登機口信息
            terminal = ''
            gate = ''
            if 'airportResources' in item:
                terminal = item['airportResources'].get('departureTerminal', '')
                gate = item['airportResources'].get('departureGate', '')
            
            # 創建航班狀態字典
            flight_status = {
                'flight_number': airline + flight_number,
                'airline_code': airline,
                'flight_id': str(item.get('flightId', '')),
                'departure_airport': item.get('departureAirportFsCode', ''),
                'arrival_airport': item.get('arrivalAirportFsCode', ''),
                'scheduled_departure': format_datetime(scheduled_dep_time) if scheduled_dep_time else None,
                'scheduled_arrival': format_datetime(scheduled_arr_time) if scheduled_arr_time else None,
                'scheduled_departure_time': format_datetime(scheduled_dep_time) if scheduled_dep_time else None,
                'scheduled_arrival_time': format_datetime(scheduled_arr_time) if scheduled_arr_time else None,
                'actual_departure_time': format_datetime(actual_dep_time) if actual_dep_time else None,
                'actual_arrival_time': format_datetime(actual_arr_time) if actual_arr_time else None,
                'status': status_zh,
                'status_en': status,
                'terminal': terminal,
                'gate': gate,
                'aircraft': aircraft,
                'source': 'FlightStats'
            }
            
            return flight_status
        except Exception as e:
            self.logger.error(f"解析航班狀態數據時出錯: {str(e)}")
            return None