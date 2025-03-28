import requests
import json
from datetime import datetime, timedelta
import os
from flask import current_app
from app.models import db, Airport, Airline, Flight, Weather

class TDXService:
    """交通部TDX平台服務"""
    
    def __init__(self, test_mode=False):
        # 使用您的金鑰
        self.client_id = "n1116440-eff4950c-7994-47de"
        self.client_secret = "efc87a00-3930-4be2-bca9-37f3b8f46d1d"
        self.auth_url = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
        self.base_url = "https://tdx.transportdata.tw/api/basic/v2/Air"
        self._access_token = None
        self._token_expiry = None
        self.test_mode = test_mode
        
    def _get_access_token(self):
        """取得API存取權杖"""
        # 檢查是否已有有效權杖
        if self._access_token and datetime.now().timestamp() < self._token_expiry:
            return self._access_token
            
        # 測試模式可選擇使用假權杖
        if self.test_mode and os.environ.get('SKIP_REAL_API_CALLS', 'False') == 'True':
            self._access_token = "test_token"
            self._token_expiry = datetime.now().timestamp() + 86400
            return self._access_token
            
        # 設定請求標頭與資料
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        try:
            # 發送POST請求取得權杖
            response = requests.post(self.auth_url, headers=headers, data=data)
            response.raise_for_status()
            auth_data = response.json()
            
            # 儲存權杖與到期時間
            self._access_token = auth_data.get('access_token')
            # 設定到期時間 (權杖有效期1天，這裡提前1小時更新)
            self._token_expiry = datetime.now().timestamp() + auth_data.get('expires_in', 86400) - 3600
            current_app.logger.info("TDX API 權杖已更新")
            
            return self._access_token
        except Exception as e:
            current_app.logger.error(f"TDX取得權杖失敗: {e}")
            return None
    
    def _get_request_headers(self):
        """取得API請求標頭"""
        token = self._get_access_token()
        if not token:
            return None
            
        return {
            'authorization': f'Bearer {token}',
            'Accept-Encoding': 'gzip'
        }
    
    def get_airport_flights(self, airport_code="TPE", direction="Departure", date=None):
        """獲取機場航班資訊
        
        參數:
        - airport_code: 機場代碼 (IATA)，預設臺灣桃園國際機場
        - direction: Departure(出發) 或 Arrival(抵達)
        - date: 日期，格式為YYYY-MM-DD，預設為今天
        """
        # 測試模式且設置跳過API調用時返回測試數據
        if self.test_mode and os.environ.get('SKIP_REAL_API_CALLS', 'False') == 'True':
            return self._get_mock_airport_flights(airport_code, direction, date)
            
        # 設定API網址
        url = f"{self.base_url}/FIDS/Airport/{direction}/{airport_code}"
        
        # 設定查詢參數
        params = {'$format': 'JSON'}
        if date:
            params['$filter'] = f"contains({direction}Time,'{date}')"
        
        # 取得請求標頭
        headers = self._get_request_headers()
        if not headers:
            return {'success': False, 'message': '無法取得TDX授權'}
        
        try:
            # 發送GET請求
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            # 標記這些數據是測試數據還是正式數據
            for item in data:
                item['is_test_data'] = self.test_mode
                
            return {'success': True, 'data': data}
        except Exception as e:
            current_app.logger.error(f"TDX獲取航班資訊失敗: {e}")
            return {'success': False, 'message': f'獲取航班資訊失敗: {str(e)}'}
    
    def _get_mock_airport_flights(self, airport_code, direction, date):
        """產生模擬航班資料（測試用）"""
        current_app.logger.info(f"使用模擬航班資料: {airport_code}, {direction}")
        
        mock_data = []
        airlines = ["CI", "BR", "AE", "B7", "JX"]
        destinations = {"TPE": ["HKG", "NRT", "ICN", "SIN", "BKK"],
                      "KHH": ["TPE", "HKG", "MNL"],
                      "TSA": ["KHH", "MZG", "HUN"]}
        origins = {"TPE": ["HKG", "NRT", "ICN", "SIN", "BKK"],
                 "KHH": ["TPE", "HKG", "MNL"],
                 "TSA": ["KHH", "MZG", "HUN"]}
                 
        airport_list = destinations.get(airport_code, ["TPE"]) if direction == "Departure" else origins.get(airport_code, ["TPE"])
        
        # 生成日期，如果未提供則使用今天
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        # 產生10筆模擬資料
        for i in range(10):
            airline = airlines[i % len(airlines)]
            flight_number = f"{airline}{100 + i}"
            
            if direction == "Departure":
                dest_airport = airport_list[i % len(airport_list)]
                mock_flight = {
                    "FlightID": f"TEST-{airline}-{i}",
                    "AirlineID": airline,
                    "FlightNumber": flight_number,
                    "DepartureAirportID": airport_code,
                    "ArrivalAirportID": dest_airport,
                    "ScheduleDepartureTime": f"{date}T{(8 + i) % 24:02d}:00:00",
                    "ScheduleArrivalTime": f"{date}T{(10 + i) % 24:02d}:30:00",
                    "ActualDepartureTime": None if i % 3 == 0 else f"{date}T{(8 + i) % 24:02d}:{(i * 5) % 60:02d}:00",
                    "ActualArrivalTime": None,
                    "FlightStatusCode": "A" if i % 4 != 0 else "D",  # A:正常, D:延誤
                    "FlightStatus": "正常" if i % 4 != 0 else "延誤",
                    "Terminal": str(1 + (i % 2)),
                    "Gate": f"A{i+1}",
                    "is_test_data": True
                }
            else:  # Arrival
                orig_airport = airport_list[i % len(airport_list)]
                mock_flight = {
                    "FlightID": f"TEST-{airline}-{i}",
                    "AirlineID": airline,
                    "FlightNumber": flight_number,
                    "DepartureAirportID": orig_airport,
                    "ArrivalAirportID": airport_code,
                    "ScheduleDepartureTime": f"{date}T{(6 + i) % 24:02d}:00:00",
                    "ScheduleArrivalTime": f"{date}T{(8 + i) % 24:02d}:30:00",
                    "ActualDepartureTime": f"{date}T{(6 + i) % 24:02d}:{(i * 3) % 60:02d}:00",
                    "ActualArrivalTime": None if i % 3 == 0 else f"{date}T{(8 + i) % 24:02d}:{(i * 5) % 60:02d}:00",
                    "FlightStatusCode": "A" if i % 4 != 0 else "D",
                    "FlightStatus": "正常" if i % 4 != 0 else "延誤",
                    "Terminal": str(1 + (i % 2)),
                    "Gate": f"B{i+1}",
                    "is_test_data": True
                }
            
            mock_data.append(mock_flight)
            
        return {'success': True, 'data': mock_data}
    
    def get_airport_info(self, airport_code=None):
        """獲取機場基本資訊"""
        # 測試模式且設置跳過API調用時返回測試數據
        if self.test_mode and os.environ.get('SKIP_REAL_API_CALLS', 'False') == 'True':
            return self._get_mock_airport_info(airport_code)
            
        url = f"{self.base_url}/Airport"
        if airport_code:
            url = f"{url}/{airport_code}"
        
        url = f"{url}?$format=JSON"
        
        headers = self._get_request_headers()
        if not headers:
            return {'success': False, 'message': '無法取得TDX授權'}
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return {'success': True, 'data': response.json()}
        except Exception as e:
            current_app.logger.error(f"TDX獲取機場資訊失敗: {e}")
            return {'success': False, 'message': f'獲取機場資訊失敗: {str(e)}'}
    
    def _get_mock_airport_info(self, airport_code=None):
        """產生模擬機場資料（測試用）"""
        mock_airports = {
            "TPE": {
                "AirportID": "TPE",
                "AirportName": {"Zh_tw": "臺灣桃園國際機場", "En": "Taiwan Taoyuan International Airport"},
                "AirportCode": "RCTP",
                "CityName": {"Zh_tw": "桃園", "En": "Taoyuan"},
                "CountryCode": "TW",
                "CountryName": {"Zh_tw": "臺灣", "En": "Taiwan"},
                "PositionLat": 25.077731,
                "PositionLon": 121.232822,
                "is_test_data": True
            },
            "TSA": {
                "AirportID": "TSA",
                "AirportName": {"Zh_tw": "臺北松山機場", "En": "Taipei Songshan Airport"},
                "AirportCode": "RCSS",
                "CityName": {"Zh_tw": "臺北", "En": "Taipei"},
                "CountryCode": "TW",
                "CountryName": {"Zh_tw": "臺灣", "En": "Taiwan"},
                "PositionLat": 25.069444,
                "PositionLon": 121.552778,
                "is_test_data": True
            },
            "KHH": {
                "AirportID": "KHH",
                "AirportName": {"Zh_tw": "高雄國際機場", "En": "Kaohsiung International Airport"},
                "AirportCode": "RCKH",
                "CityName": {"Zh_tw": "高雄", "En": "Kaohsiung"},
                "CountryCode": "TW",
                "CountryName": {"Zh_tw": "臺灣", "En": "Taiwan"},
                "PositionLat": 22.577778,
                "PositionLon": 120.350833,
                "is_test_data": True
            }
        }
        
        if airport_code:
            if airport_code in mock_airports:
                return {'success': True, 'data': mock_airports[airport_code]}
            else:
                return {'success': False, 'message': f'找不到機場: {airport_code}'}
        else:
            return {'success': True, 'data': list(mock_airports.values())}
    
    def sync_to_database(self, check_last_day=False):
        """將TDX資料同步到資料庫
        
        參數:
        - check_last_day: 若為True，則只在月底執行
        """
        # 如果check_last_day=True，但今天不是本月最後一天，則跳過
        if check_last_day:
            today = datetime.now()
            last_day = (today.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            if today.day != last_day.day:
                current_app.logger.info(f"今天不是本月最後一天 ({today.day} != {last_day.day})，跳過同步")
                return {'success': False, 'message': '今天不是本月最後一天，跳過同步'}
                
        # 同步機場資料
        self._sync_airports()
        
        # 同步航空公司資料
        self._sync_airlines()
        
        # 同步航班資料
        result = self._sync_flights()
        
        return result
    
    def _sync_airports(self):
        """同步機場資料到資料庫"""
        # 獲取機場資料
        result = self.get_airport_info()
        if not result['success']:
            return result
            
        airports_data = result['data']
        
        # 更新或新增機場資料
        for airport_data in airports_data:
            airport_id = airport_data.get('AirportID')
            
            # 檢查機場是否已存在
            airport = Airport.query.filter_by(iata_code=airport_id).first()
            
            if not airport:
                # 新增機場
                airport = Airport(
                    iata_code=airport_id,
                    icao_code=airport_data.get('AirportCode'),
                    name_zh=airport_data.get('AirportName', {}).get('Zh_tw'),
                    name_en=airport_data.get('AirportName', {}).get('En'),
                    city=airport_data.get('CityName', {}).get('Zh_tw'),
                    city_en=airport_data.get('CityName', {}).get('En'),
                    country=airport_data.get('CountryName', {}).get('Zh_tw'),
                    country_code=airport_data.get('CountryCode'),
                    timezone=None,  # TDX API沒提供時區資訊
                    latitude=airport_data.get('PositionLat'),
                    longitude=airport_data.get('PositionLon'),
                    is_test_data=self.test_mode
                )
                db.session.add(airport)
            else:
                # 更新機場
                airport.icao_code = airport_data.get('AirportCode')
                airport.name_zh = airport_data.get('AirportName', {}).get('Zh_tw')
                airport.name_en = airport_data.get('AirportName', {}).get('En')
                airport.city = airport_data.get('CityName', {}).get('Zh_tw')
                airport.city_en = airport_data.get('CityName', {}).get('En')
                airport.country = airport_data.get('CountryName', {}).get('Zh_tw')
                airport.country_code = airport_data.get('CountryCode')
                airport.latitude = airport_data.get('PositionLat')
                airport.longitude = airport_data.get('PositionLon')
                airport.is_test_data = self.test_mode
        
        try:
            db.session.commit()
            current_app.logger.info("成功同步機場資料")
            return {'success': True, 'message': '成功同步機場資料'}
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"同步機場資料失敗: {e}")
            return {'success': False, 'message': f'同步機場資料失敗: {str(e)}'}
    
    def _sync_airlines(self):
        """同步航空公司資料到資料庫"""
        # 測試模式的話，就使用固定資料
        mock_airlines = [
            {"AirlineID": "CI", "AirlineName": {"Zh_tw": "中華航空", "En": "China Airlines"}},
            {"AirlineID": "BR", "AirlineName": {"Zh_tw": "長榮航空", "En": "EVA Air"}},
            {"AirlineID": "AE", "AirlineName": {"Zh_tw": "華信航空", "En": "Mandarin Airlines"}},
            {"AirlineID": "B7", "AirlineName": {"Zh_tw": "立榮航空", "En": "UNI Air"}},
            {"AirlineID": "JX", "AirlineName": {"Zh_tw": "星宇航空", "En": "STARLUX Airlines"}}
        ]
        
        if self.test_mode and os.environ.get('SKIP_REAL_API_CALLS', 'False') == 'True':
            airlines_data = mock_airlines
        else:
            # 獲取航空公司資料
            url = f"{self.base_url}/Airline?$format=JSON"
            
            headers = self._get_request_headers()
            if not headers:
                return {'success': False, 'message': '無法取得TDX授權'}
            
            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                airlines_data = response.json()
            except Exception as e:
                current_app.logger.error(f"TDX獲取航空公司資訊失敗: {e}")
                return {'success': False, 'message': f'獲取航空公司資訊失敗: {str(e)}'}
        
        # 更新或新增航空公司資料
        for airline_data in airlines_data:
            airline_id = airline_data.get('AirlineID')
            
            # 檢查航空公司是否已存在
            airline = Airline.query.filter_by(iata_code=airline_id).first()
            
            if not airline:
                # 新增航空公司
                airline = Airline(
                    iata_code=airline_id,
                    icao_code=None,  # TDX API沒提供ICAO代碼
                    name_zh=airline_data.get('AirlineName', {}).get('Zh_tw'),
                    name_en=airline_data.get('AirlineName', {}).get('En'),
                    country=None,
                    website=None,
                    is_test_data=self.test_mode
                )
                db.session.add(airline)
            else:
                # 更新航空公司
                airline.name_zh = airline_data.get('AirlineName', {}).get('Zh_tw')
                airline.name_en = airline_data.get('AirlineName', {}).get('En')
                airline.is_test_data = self.test_mode
        
        try:
            db.session.commit()
            current_app.logger.info("成功同步航空公司資料")
            return {'success': True, 'message': '成功同步航空公司資料'}
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"同步航空公司資料失敗: {e}")
            return {'success': False, 'message': f'同步航空公司資料失敗: {str(e)}'}
    
    def _sync_flights(self):
        """同步航班資料到資料庫"""
        # 取得今天的日期
        today = datetime.now().strftime('%Y-%m-%d')
        
        # 同步TPE出發的航班
        result_tpe_dep = self.get_airport_flights(airport_code="TPE", direction="Departure")
        if not result_tpe_dep['success']:
            return result_tpe_dep
            
        # 同步TSA出發的航班
        result_tsa_dep = self.get_airport_flights(airport_code="TSA", direction="Departure")
        
        # 同步KHH出發的航班
        result_khh_dep = self.get_airport_flights(airport_code="KHH", direction="Departure")
        
        # 合併所有航班資料
        all_flights = []
        if result_tpe_dep['success']:
            all_flights.extend(result_tpe_dep['data'])
        if result_tsa_dep['success']:
            all_flights.extend(result_tsa_dep['data'])
        if result_khh_dep['success']:
            all_flights.extend(result_khh_dep['data'])
        
        # 更新或新增航班資料
        sync_count = 0
        for flight_data in all_flights:
            flight_id = flight_data.get('FlightID')
            airline_id = flight_data.get('AirlineID')
            flight_number = flight_data.get('FlightNumber')
            
            # 處理出發與抵達機場
            dep_airport_id = flight_data.get('DepartureAirportID')
            arr_airport_id = flight_data.get('ArrivalAirportID')
            
            # 檢查航空公司和機場是否存在
            airline = Airline.query.filter_by(iata_code=airline_id).first()
            dep_airport = Airport.query.filter_by(iata_code=dep_airport_id).first()
            arr_airport = Airport.query.filter_by(iata_code=arr_airport_id).first()
            
            # 如果不存在關鍵資料，則跳過
            if not airline or not dep_airport or not arr_airport:
                if not airline:
                    current_app.logger.warning(f"未找到航空公司 {airline_id}")
                if not dep_airport:
                    current_app.logger.warning(f"未找到出發機場 {dep_airport_id}")
                if not arr_airport:
                    current_app.logger.warning(f"未找到到達機場 {arr_airport_id}")
                continue
            
            # 處理日期時間
            dep_time_str = flight_data.get('ScheduleDepartureTime')
            arr_time_str = flight_data.get('ScheduleArrivalTime')
            
            if not dep_time_str or not arr_time_str:
                current_app.logger.warning(f"航班 {flight_number} 缺少時間資訊")
                continue
                
            dep_time = datetime.strptime(dep_time_str, '%Y-%m-%dT%H:%M:%S')
            arr_time = datetime.strptime(arr_time_str, '%Y-%m-%dT%H:%M:%S')
            
            # 處理實際出發/抵達時間
            actual_dep_time_str = flight_data.get('ActualDepartureTime')
            actual_dep_time = None
            if actual_dep_time_str:
                actual_dep_time = datetime.strptime(actual_dep_time_str, '%Y-%m-%dT%H:%M:%S')
                
            actual_arr_time_str = flight_data.get('ActualArrivalTime')
            actual_arr_time = None
            if actual_arr_time_str:
                actual_arr_time = datetime.strptime(actual_arr_time_str, '%Y-%m-%dT%H:%M:%S')
            
            # 處理狀態
            status = flight_data.get('FlightStatusCode', 'A')  # 預設為A (正常)
            status_desc = flight_data.get('FlightStatus', '正常')
            
            # 處理登機門與航廈
            terminal = flight_data.get('Terminal')
            gate = flight_data.get('Gate')
            
            # 檢查航班是否已存在
            flight = Flight.query.filter_by(flight_id=flight_id).first()
            
            if not flight:
                # 建立新航班
                flight = Flight(
                    flight_id=flight_id,
                    airline_id=airline.id,
                    flight_number=flight_number,
                    departure_airport_id=dep_airport.id,
                    arrival_airport_id=arr_airport.id,
                    scheduled_departure_time=dep_time,
                    scheduled_arrival_time=arr_time,
                    actual_departure_time=actual_dep_time,
                    actual_arrival_time=actual_arr_time,
                    status=status,
                    status_description=status_desc,
                    terminal=terminal,
                    gate=gate,
                    aircraft_type=None,  # TDX API沒提供
                    is_test_data=self.test_mode
                )
                db.session.add(flight)
                sync_count += 1
            else:
                # 更新現有航班
                flight.airline_id=airline.id
                flight.flight_number=flight_number
                flight.departure_airport_id=dep_airport.id
                flight.arrival_airport_id=arr_airport.id
                flight.scheduled_departure_time=dep_time
                flight.scheduled_arrival_time=arr_time
                flight.actual_departure_time=actual_dep_time
                flight.actual_arrival_time=actual_arr_time
                flight.status=status
                flight.status_description=status_desc
                flight.terminal=terminal
                flight.gate=gate
                flight.is_test_data=self.test_mode
        
        try:
            # 提交所有變更
            db.session.commit()
            current_app.logger.info(f"成功同步 {sync_count} 筆航班資料")
            return {'success': True, 'message': f'成功同步 {sync_count} 筆航班資料'}
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"提交航班資料失敗: {e}")
            return {'success': False, 'message': f'提交航班資料失敗: {str(e)}'}