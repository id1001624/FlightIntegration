import requests
import json
from datetime import datetime, timedelta
import os
import calendar
from flask import current_app

class TDXService:
    """交通部TDX平台服務"""
    
    def __init__(self):
        # 使用您的金鑰
        self.client_id = "n1116440-eff4950c-7994-47de"
        self.client_secret = "efc87a00-3930-4be2-bca9-37f3b8f46d1d"
        self.auth_url = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
        self.base_url = "https://tdx.transportdata.tw/api/basic/v2/Air"
        self._access_token = None
        self._token_expiry = None
        
    def _get_access_token(self):
        """取得API存取權杖"""
        # 檢查是否已有有效權杖
        if self._access_token and datetime.now().timestamp() < self._token_expiry:
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
            return {'success': True, 'data': response.json()}
        except Exception as e:
            current_app.logger.error(f"TDX獲取航班資訊失敗: {e}")
            return {'success': False, 'message': f'獲取航班資訊失敗: {str(e)}'}
    
    def sync_flight_data(self, check_last_day=False):
        """將TDX航班資料同步到資料庫
        
        參數:
        - check_last_day: 若為True，則只在月底執行
        """
        # 如果check_last_day=True，但今天不是本月最後一天，則跳過
        if check_last_day:
            today = datetime.now()
            last_day = calendar.monthrange(today.year, today.month)[1]
            if today.day != last_day:
                current_app.logger.info(f"今天不是本月最後一天 ({today.day} != {last_day})，跳過同步")
                return {'success': False, 'message': '今天不是本月最後一天，跳過同步'}
                
        from app import db
        from app.models.flights import Flights
        from app.models.airports import Airports
        from app.models.airlines import Airlines
        
        # 取得今天的日期
        today = datetime.now().strftime('%Y-%m-%d')
        
        # 取得未來30天的日期，用於抓取航班資料
        future_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        
        # 取得航班資料 (桃園機場出發)
        result = self.get_airport_flights(airport_code="TPE", direction="Departure", date=None)
        if not result['success']:
            return result
            
        flight_data = result['data']
        sync_count = 0
        
        for flight in flight_data:
            try:
                # 從TDX資料中提取資訊
                flight_id = flight.get('FlightID')
                airline_id = flight.get('AirlineID')
                flight_number = flight.get('FlightNumber')
                
                # 處理出發與抵達機場
                dep_airport_id = flight.get('DepartureAirportID')
                arr_airport_id = flight.get('ArrivalAirportID')
                
                # 檢查航空公司和機場是否存在
                airline = Airlines.query.filter_by(Airline_Id=airline_id).first()
                dep_airport = Airports.query.filter_by(Airport_Id=dep_airport_id).first()
                arr_airport = Airports.query.filter_by(Airport_Id=arr_airport_id).first()
                
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
                dep_time_str = flight.get('ScheduleDepartureTime')
                arr_time_str = flight.get('ScheduleArrivalTime')
                
                if not dep_time_str or not arr_time_str:
                    current_app.logger.warning(f"航班 {flight_number} 缺少時間資訊")
                    continue
                    
                dep_time = datetime.strptime(dep_time_str, '%Y-%m-%dT%H:%M:%S')
                arr_time = datetime.strptime(arr_time_str, '%Y-%m-%dT%H:%M:%S')
                
                # 處理狀態
                status = flight.get('FlightStatusCode', 'A')  # 預設為A (正常)
                
                # 尋找或建立航班
                flight_obj = Flights.query.filter_by(Flight_Id=flight_id).first()
                                                
                if not flight_obj:
                    # 建立新航班
                    flight_obj = Flights(
                        Flight_Id=flight_id,
                        Airline_Id=airline_id,
                        Scheduled_Departure_Airport_Id=dep_airport_id,
                        Scheduled_Arrival_Airport_Id=arr_airport_id,
                        Scheduled_Departure_Time=dep_time,
                        Scheduled_Arrival_Time=arr_time,
                        Status=status
                    )
                    db.session.add(flight_obj)
                    sync_count += 1
                else:
                    # 更新現有航班
                    flight_obj.Scheduled_Departure_Time = dep_time
                    flight_obj.Scheduled_Arrival_Time = arr_time
                    flight_obj.Status = status
            
            except Exception as e:
                current_app.logger.error(f"同步航班 {flight.get('FlightNumber')} 失敗: {e}")
                continue
        
        try:
            # 提交所有變更
            db.session.commit()
            current_app.logger.info(f"成功同步 {sync_count} 筆航班資料")
            return {'success': True, 'message': f'成功同步 {sync_count} 筆航班資料'}
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"提交航班資料失敗: {e}")
            return {'success': False, 'message': f'提交航班資料失敗: {str(e)}'}
    
    def update_airlines(self):
        """更新航空公司資料"""
        url = f"{self.base_url}/Airline"
        params = {'$format': 'JSON'}
        
        headers = self._get_request_headers()
        if not headers:
            return {'success': False, 'message': '無法取得TDX授權'}
        
        try:
            from app import db
            from app.models.airlines import Airlines
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            airlines_data = response.json()
            
            count = 0
            for airline in airlines_data:
                airline_id = airline.get('AirlineID')
                airline_obj = Airlines.query.filter_by(Airline_Id=airline_id).first()
                
                if not airline_obj:
                    airline_obj = Airlines(
                        Airline_Id=airline_id,
                        Airline_Name=airline.get('AirlineName', ''),
                        Airline_Name_ZH=airline.get('AirlineNameZH', ''),
                        IS_Domestic=airline.get('IsDomestic', 'N'),
                        Url=airline.get('AirlineWebsite', ''),
                        Contact_Info=airline.get('AirlinePhone', '')
                    )
                    db.session.add(airline_obj)
                    count += 1
                else:
                    # 更新現有航空公司
                    airline_obj.Airline_Name = airline.get('AirlineName', airline_obj.Airline_Name)
                    airline_obj.Airline_Name_ZH = airline.get('AirlineNameZH', airline_obj.Airline_Name_ZH)
                    airline_obj.IS_Domestic = airline.get('IsDomestic', airline_obj.IS_Domestic)
                    airline_obj.Url = airline.get('AirlineWebsite', airline_obj.Url)
                    airline_obj.Contact_Info = airline.get('AirlinePhone', airline_obj.Contact_Info)
            
            db.session.commit()
            return {'success': True, 'message': f'成功更新 {count} 筆航空公司資料'}
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"更新航空公司資料失敗: {e}")
            return {'success': False, 'message': f'更新航空公司資料失敗: {str(e)}'}
    
    def update_airports(self):
        """更新機場資料"""
        url = f"{self.base_url}/Airport"
        params = {'$format': 'JSON'}
        
        headers = self._get_request_headers()
        if not headers:
            return {'success': False, 'message': '無法取得TDX授權'}
        
        try:
            from app import db
            from app.models.airports import Airports
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            airports_data = response.json()
            
            count = 0
            for airport in airports_data:
                airport_id = airport.get('AirportID')
                airport_obj = Airports.query.filter_by(Airport_Id=airport_id).first()
                
                if not airport_obj:
                    airport_obj = Airports(
                        Airport_Id=airport_id,
                        Airport_Name=airport.get('AirportName', ''),
                        Airport_Name_ZH=airport.get('AirportNameZH', ''),
                        IS_Domestic=airport.get('IsDomestic', 'N'),
                        Url=airport.get('AirportWebsite', ''),
                        Contact_Info=airport.get('AirportPhone', ''),
                        City_Id=airport.get('CityID', '')
                    )
                    db.session.add(airport_obj)
                    count += 1
                else:
                    # 更新現有機場
                    airport_obj.Airport_Name = airport.get('AirportName', airport_obj.Airport_Name)
                    airport_obj.Airport_Name_ZH = airport.get('AirportNameZH', airport_obj.Airport_Name_ZH)
                    airport_obj.IS_Domestic = airport.get('IsDomestic', airport_obj.IS_Domestic)
                    airport_obj.Url = airport.get('AirportWebsite', airport_obj.Url)
                    airport_obj.Contact_Info = airport.get('AirportPhone', airport_obj.Contact_Info)
                    airport_obj.City_Id = airport.get('CityID', airport_obj.City_Id)
            
            db.session.commit()
            return {'success': True, 'message': f'成功更新 {count} 筆機場資料'}
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"更新機場資料失敗: {e}")
            return {'success': False, 'message': f'更新機場資料失敗: {str(e)}'}