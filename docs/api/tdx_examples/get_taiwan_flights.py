#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
TDX 航空API範例 - 獲取台灣航班資訊
此範例展示如何獲取台灣主要機場的航班資訊
"""

import requests
import json
import time
from datetime import datetime, timedelta

class TDXAuth:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.auth_url = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
        self.token = None
        self.token_expire_time = None
        
    def get_token(self):
        """取得 TDX API 的 Access Token，含過期時間管理"""
        # 如果已有未過期的 token，直接返回
        if self.token and self.token_expire_time and datetime.now() < self.token_expire_time:
            return self.token
            
        # 準備取得 token 的請求資料
        headers = {"content-type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        # 發送請求取得 token
        response = requests.post(self.auth_url, headers=headers, data=data)
        
        # 檢查回應狀態
        if response.status_code != 200:
            raise Exception(f"取得 token 失敗: {response.status_code} {response.text}")
            
        # 解析回應並儲存 token
        response_data = json.loads(response.text)
        self.token = response_data.get("access_token")
        
        # 設置 token 過期時間 (預留 10 分鐘緩衝)
        expires_in = response_data.get("expires_in", 3600)  # 預設 1 小時
        self.token_expire_time = datetime.now() + timedelta(seconds=expires_in - 600)
        
        return self.token
    
    def get_auth_header(self):
        """取得用於 API 請求的認證 header"""
        token = self.get_token()
        return {
            "authorization": f"Bearer {token}",
            "Accept-Encoding": "gzip"  # 建議加入，可減少回傳資料量
        }

class TDXAirAPI:
    def __init__(self, auth):
        self.auth = auth
        self.base_url = "https://tdx.transportdata.tw/api/basic/v2/Air"
    
    def get_taiwan_airports(self):
        """獲取台灣主要機場基本資訊"""
        url = f"{self.base_url}/Airport?$filter=contains(Country,'中華民國')&$format=JSON"
        
        response = requests.get(url, headers=self.auth.get_auth_header())
        
        if response.status_code != 200:
            raise Exception(f"獲取台灣機場資訊失敗: {response.status_code} {response.text}")
            
        return json.loads(response.text)
    
    def get_flight_departure_by_date(self, airport_code, date=None):
        """獲取指定機場和日期的出發航班資訊
        
        Args:
            airport_code: 機場 IATA 代碼
            date: 日期，格式為 "YYYY-MM-DD"，若不指定則使用今天的日期
            
        Returns:
            出發航班資訊的 JSON 資料
        """
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
            
        url = f"{self.base_url}/FIDS/Airport/Departure/{airport_code}/{date}?$format=JSON"
        
        response = requests.get(url, headers=self.auth.get_auth_header())
        
        if response.status_code != 200:
            raise Exception(f"獲取出發航班資訊失敗: {response.status_code} {response.text}")
            
        return json.loads(response.text)
    
    def get_flight_arrival_by_date(self, airport_code, date=None):
        """獲取指定機場和日期的抵達航班資訊
        
        Args:
            airport_code: 機場 IATA 代碼
            date: 日期，格式為 "YYYY-MM-DD"，若不指定則使用今天的日期
            
        Returns:
            抵達航班資訊的 JSON 資料
        """
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
            
        url = f"{self.base_url}/FIDS/Airport/Arrival/{airport_code}/{date}?$format=JSON"
        
        response = requests.get(url, headers=self.auth.get_auth_header())
        
        if response.status_code != 200:
            raise Exception(f"獲取抵達航班資訊失敗: {response.status_code} {response.text}")
            
        return json.loads(response.text)
    
    def get_taiwan_airlines(self):
        """獲取台灣航空公司基本資訊"""
        url = f"{self.base_url}/Airline?$filter=contains(Country,'中華民國')&$format=JSON"
        
        response = requests.get(url, headers=self.auth.get_auth_header())
        
        if response.status_code != 200:
            raise Exception(f"獲取台灣航空公司資訊失敗: {response.status_code} {response.text}")
            
        return json.loads(response.text)
    
    def get_flights_between_airports(self, from_airport, to_airport, date=None):
        """獲取兩機場間的航班資訊
        
        Args:
            from_airport: 出發機場 IATA 代碼
            to_airport: 目的地機場 IATA 代碼
            date: 日期，格式為 "YYYY-MM-DD"，若不指定則使用今天的日期
            
        Returns:
            航班資訊的 JSON 資料
        """
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
            
        url = f"{self.base_url}/FIDS/Flight?$filter=DepartureAirportID eq '{from_airport}' and ArrivalAirportID eq '{to_airport}' and date(ScheduleDepartureTime) eq {date}&$format=JSON"
        
        response = requests.get(url, headers=self.auth.get_auth_header())
        
        if response.status_code != 200:
            raise Exception(f"獲取航班資訊失敗: {response.status_code} {response.text}")
            
        return json.loads(response.text)

def save_to_json(data, filename):
    """將資料儲存為 JSON 檔案"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"資料已儲存至 {filename}")

def main():
    # 請替換為您的 Client ID 和 Client Secret
    client_id = "YOUR_CLIENT_ID"
    client_secret = "YOUR_CLIENT_SECRET"
    
    # 創建認證實例
    auth = TDXAuth(client_id, client_secret)
    
    # 創建航空 API 實例
    air_api = TDXAirAPI(auth)
    
    try:
        # 取得台灣機場資訊
        print("取得台灣機場資訊...")
        taiwan_airports = air_api.get_taiwan_airports()
        save_to_json(taiwan_airports, 'taiwan_airports.json')
        
        # 取得台灣航空公司資訊
        print("取得台灣航空公司資訊...")
        taiwan_airlines = air_api.get_taiwan_airlines()
        save_to_json(taiwan_airlines, 'taiwan_airlines.json')
        
        # 取得桃園機場今日出發航班
        print("取得桃園機場今日出發航班...")
        today = datetime.now().strftime("%Y-%m-%d")
        tpe_departures = air_api.get_flight_departure_by_date("TPE", today)
        save_to_json(tpe_departures, f'tpe_departures_{today}.json')
        
        # 取得桃園機場今日抵達航班
        print("取得桃園機場今日抵達航班...")
        tpe_arrivals = air_api.get_flight_arrival_by_date("TPE", today)
        save_to_json(tpe_arrivals, f'tpe_arrivals_{today}.json')
        
        # 取得桃園到松山機場的航班
        print("取得桃園到松山機場的航班...")
        tpe_to_tsa_flights = air_api.get_flights_between_airports("TPE", "TSA", today)
        save_to_json(tpe_to_tsa_flights, f'tpe_to_tsa_flights_{today}.json')
        
        print("所有資料已成功獲取並儲存")
        
    except Exception as e:
        print(f"發生錯誤: {str(e)}")

if __name__ == "__main__":
    main() 