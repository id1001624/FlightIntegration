#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
TDX API 整合範例 - 航班與氣象資訊整合
此範例展示如何整合航班資訊與目的地氣象資訊
"""

import requests
import json
import pandas as pd
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

class TDXIntegrationAPI:
    def __init__(self, auth):
        self.auth = auth
        self.air_base_url = "https://tdx.transportdata.tw/api/basic/v2/Air"
        self.weather_base_url = "https://tdx.transportdata.tw/api/basic/v2/Weather"
        
        # 機場與城市對應表 (簡化版)
        self.airport_city_map = {
            "TPE": "Taipei",    # 桃園機場
            "TSA": "Taipei",    # 松山機場
            "KHH": "Kaohsiung", # 高雄機場
            "RMQ": "Taichung",  # 台中機場
            "TNN": "Tainan",    # 台南機場
            "HUN": "Hualien",   # 花蓮機場
            "TTT": "Taitung",   # 台東機場
            "MZG": "Penghu",    # 澎湖馬公機場
            "KNH": "Kinmen",    # 金門機場
            "LZN": "Matsu"      # 馬祖機場
        }
        
        # 國際機場與城市對應 (範例)
        self.intl_airport_city_map = {
            "HKG": "Hong Kong", # 香港國際機場
            "NRT": "Tokyo",     # 東京成田機場
            "KIX": "Osaka",     # 大阪關西機場
            "ICN": "Seoul",     # 首爾仁川機場
            "PVG": "Shanghai",  # 上海浦東機場
            "BKK": "Bangkok",   # 曼谷機場
            "SIN": "Singapore", # 新加坡樟宜機場
            "KUL": "Kuala Lumpur" # 吉隆坡機場
        }
    
    def get_airport_info(self, airport_code=None):
        """獲取機場基本資訊"""
        url = f"{self.air_base_url}/Airport"
        if airport_code:
            url = f"{url}/{airport_code}"
        url = f"{url}?$format=JSON"
        
        response = requests.get(url, headers=self.auth.get_auth_header())
        
        if response.status_code != 200:
            raise Exception(f"獲取機場資訊失敗: {response.status_code} {response.text}")
            
        return json.loads(response.text)
    
    def get_flight_departure(self, airport_code, date=None):
        """獲取指定機場的出發航班資訊"""
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
            
        url = f"{self.air_base_url}/FIDS/Airport/Departure/{airport_code}/{date}?$format=JSON"
        
        response = requests.get(url, headers=self.auth.get_auth_header())
        
        if response.status_code != 200:
            raise Exception(f"獲取出發航班資訊失敗: {response.status_code} {response.text}")
            
        return json.loads(response.text)
    
    def get_city_weather(self, city, language="zh-tw"):
        """獲取城市氣象資訊
        
        Args:
            city: 城市名稱 (英文)
            language: 語言設定 (預設繁體中文)
            
        Returns:
            城市氣象資訊
        """
        # 注意: 此處使用的是氣象 API 的示範用法
        # 實際上 TDX 的氣象 API 可能需要不同的路徑或參數
        url = f"{self.weather_base_url}/Weather/City/{city}?$format=JSON&language={language}"
        
        response = requests.get(url, headers=self.auth.get_auth_header())
        
        if response.status_code != 200:
            # 天氣 API 可能不存在或格式不同，這裡作為演示
            return {"message": f"無法獲取 {city} 的天氣資訊", "status": response.status_code}
            
        return json.loads(response.text)
    
    def get_observation_station_weather(self, station_id):
        """獲取特定氣象觀測站的天氣資料
        
        Args:
            station_id: 氣象站編號
            
        Returns:
            觀測站氣象資訊
        """
        url = f"{self.weather_base_url}/Station/OBS/Weather/StationID/{station_id}?$format=JSON"
        
        response = requests.get(url, headers=self.auth.get_auth_header())
        
        if response.status_code != 200:
            return {"message": f"無法獲取 {station_id} 觀測站的天氣資訊", "status": response.status_code}
            
        return json.loads(response.text)

    def get_nearby_stations(self, latitude, longitude, distance=5):
        """根據經緯度獲取附近氣象觀測站
        
        Args:
            latitude: 緯度
            longitude: 經度
            distance: 搜尋距離 (公里)
            
        Returns:
            附近氣象觀測站列表
        """
        url = f"{self.weather_base_url}/Station?$spatialFilter=nearby({latitude}, {longitude}, {distance})&$format=JSON"
        
        response = requests.get(url, headers=self.auth.get_auth_header())
        
        if response.status_code != 200:
            return {"message": f"無法獲取附近的氣象觀測站資訊", "status": response.status_code}
            
        return json.loads(response.text)
    
    def get_weather_forecast(self, city_or_county=""):
        """獲取氣象預報資訊
        
        Args:
            city_or_county: 縣市名稱，如 "臺北市"。如不指定則獲取全台灣的預報
            
        Returns:
            氣象預報資訊
        """
        base = f"{self.weather_base_url}/F-C0032-001"
        if city_or_county:
            filter_param = f"?$filter=contains(LocationName, '{city_or_county}')&"
        else:
            filter_param = "?"
            
        url = f"{base}{filter_param}$format=JSON"
        
        response = requests.get(url, headers=self.auth.get_auth_header())
        
        if response.status_code != 200:
            return {"message": f"無法獲取氣象預報資訊", "status": response.status_code}
            
        return json.loads(response.text)
    
    def integrate_flight_weather(self, departure_airport, date=None):
        """整合出發航班與目的地氣象資訊
        
        Args:
            departure_airport: 出發機場代碼
            date: 查詢日期，預設為今天
            
        Returns:
            整合後的航班與氣象資訊
        """
        try:
            # 獲取出發航班資訊
            flights = self.get_flight_departure(departure_airport, date)
            
            if not flights:
                return {"message": f"無法獲取 {departure_airport} 的出發航班資訊"}
            
            integrated_data = []
            
            # 針對每個航班，嘗試獲取目的地的天氣資訊
            for flight in flights:
                flight_data = {
                    "AirlineID": flight.get("AirlineID", ""),
                    "FlightNumber": flight.get("FlightNumber", ""),
                    "DepartureAirport": departure_airport,
                    "ArrivalAirport": flight.get("ArrivalAirportID", ""),
                    "ScheduleDepartureTime": flight.get("ScheduleDepartureTime", ""),
                    "ScheduleArrivalTime": flight.get("ScheduleArrivalTime", ""),
                    "ActualDepartureTime": flight.get("ActualDepartureTime", ""),
                    "DepartureRemark": flight.get("DepartureRemark", ""),
                    "ArrivalRemark": flight.get("ArrivalRemark", ""),
                    "FlightStatus": flight.get("FlightStatus", ""),
                    "WeatherInfo": {}
                }
                
                # 根據目的地機場代碼尋找對應城市
                arrival_airport = flight.get("ArrivalAirportID", "")
                
                city = self.intl_airport_city_map.get(arrival_airport) or self.airport_city_map.get(arrival_airport)
                
                if city:
                    # 嘗試獲取目的地城市的天氣資訊
                    try:
                        if city.startswith("Tai") or city in ["Kaohsiung", "Penghu", "Kinmen", "Matsu", "Hualien"]:
                            # 台灣的城市，使用氣象預報
                            city_mapping = {
                                "Taipei": "臺北市",
                                "Taichung": "臺中市",
                                "Tainan": "臺南市",
                                "Kaohsiung": "高雄市",
                                "Taitung": "臺東縣",
                                "Hualien": "花蓮縣",
                                "Penghu": "澎湖縣",
                                "Kinmen": "金門縣",
                                "Matsu": "連江縣"
                            }
                            weather = self.get_weather_forecast(city_mapping.get(city, ""))
                            flight_data["WeatherInfo"] = {
                                "Source": "Central Weather Bureau",
                                "Data": self._extract_weather_forecast(weather, city_mapping.get(city, ""))
                            }
                        else:
                            # 國際城市，假設使用其他氣象 API
                            flight_data["WeatherInfo"] = {
                                "Source": "International Weather API",
                                "Message": f"需使用國際氣象 API 獲取 {city} 的天氣資訊"
                            }
                    except Exception as e:
                        flight_data["WeatherInfo"] = {
                            "Error": f"獲取 {city} 天氣時發生錯誤: {str(e)}"
                        }
                
                integrated_data.append(flight_data)
            
            return integrated_data
            
        except Exception as e:
            return {"error": f"整合航班和天氣資訊時發生錯誤: {str(e)}"}
    
    def _extract_weather_forecast(self, weather_data, city_name):
        """提取氣象預報中的重要資訊
        
        Args:
            weather_data: 氣象預報原始資料
            city_name: 城市名稱
            
        Returns:
            格式化後的天氣資訊
        """
        if not weather_data or "records" not in weather_data:
            return {"message": "無天氣資料可提取"}
            
        try:
            locations = weather_data["records"]["location"]
            
            for location in locations:
                if location["locationName"] == city_name or not city_name:
                    weather_elements = location["weatherElement"]
                    
                    weather_info = {}
                    
                    for element in weather_elements:
                        element_name = element["elementName"]
                        time_data = element["time"][0]  # 取得最近的預報
                        
                        if element_name == "Wx":  # 天氣狀況
                            weather_info["Weather"] = time_data["parameter"]["parameterName"]
                            weather_info["WeatherCode"] = time_data["parameter"]["parameterValue"]
                        elif element_name == "PoP":  # 降雨機率
                            weather_info["RainChance"] = f"{time_data['parameter']['parameterName']}%"
                        elif element_name == "MinT":  # 最低溫度
                            weather_info["MinTemp"] = f"{time_data['parameter']['parameterName']}°C"
                        elif element_name == "MaxT":  # 最高溫度
                            weather_info["MaxTemp"] = f"{time_data['parameter']['parameterName']}°C"
                        elif element_name == "CI":  # 舒適度
                            weather_info["Comfort"] = time_data["parameter"]["parameterName"]
                    
                    weather_info["LocationName"] = location["locationName"]
                    weather_info["ForecastTime"] = time_data["startTime"]
                    
                    return weather_info
            
            return {"message": f"找不到 {city_name} 的天氣資料"}
            
        except Exception as e:
            return {"error": f"提取天氣資料時發生錯誤: {str(e)}"}

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
    
    # 創建整合 API 實例
    api = TDXIntegrationAPI(auth)
    
    try:
        # 獲取台北松山機場的航班和目的地天氣
        today = datetime.now().strftime("%Y-%m-%d")
        print(f"獲取台北松山機場 (TSA) {today} 的出發航班和目的地天氣資訊...")
        
        tsa_flights_weather = api.integrate_flight_weather("TSA", today)
        save_to_json(tsa_flights_weather, f'tsa_flights_weather_{today}.json')
        
        # 輸出部分結果
        print("\n部分航班與天氣整合資訊:")
        for i, flight in enumerate(tsa_flights_weather[:3], 1):
            print(f"\n{i}. {flight['AirlineID']}{flight['FlightNumber']} 前往 {flight['ArrivalAirport']}")
            print(f"   預計出發: {flight['ScheduleDepartureTime']}")
            print(f"   狀態: {flight['FlightStatus']}")
            
            weather = flight.get("WeatherInfo", {})
            if weather and "Data" in weather and isinstance(weather["Data"], dict):
                w_data = weather["Data"]
                if "Weather" in w_data:
                    print(f"   目的地天氣: {w_data.get('Weather', '無資料')}")
                    print(f"   溫度: {w_data.get('MinTemp', '無資料')} - {w_data.get('MaxTemp', '無資料')}")
                    print(f"   降雨機率: {w_data.get('RainChance', '無資料')}")
                else:
                    print(f"   目的地天氣: {weather.get('Message', '無資料')}")
            else:
                print(f"   目的地天氣: 無法獲取")
        
        # 獲取台灣地區天氣預報
        print("\n獲取台灣地區天氣預報...")
        taiwan_weather = api.get_weather_forecast()
        save_to_json(taiwan_weather, f'taiwan_weather_{today}.json')
        
        print("\n資料整合與儲存完成")
        
    except Exception as e:
        print(f"發生錯誤: {str(e)}")

if __name__ == "__main__":
    main() 