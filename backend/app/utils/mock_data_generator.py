"""
模擬數據生成器模組 - 提供測試用的模擬數據
"""
import random
import json
from datetime import datetime, timedelta

class MockDataGenerator:
    """
    模擬數據生成器類 - 用於產生各類測試數據
    """
    
    @staticmethod
    def generate_airport_data(airport_code=None):
        """
        生成模擬機場數據
        
        Args:
            airport_code (str, optional): 指定機場代碼，若不提供則返回多個機場
            
        Returns:
            list/dict: 機場數據
        """
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
            },
            "HKG": {
                "AirportID": "HKG",
                "AirportName": {"Zh_tw": "香港國際機場", "En": "Hong Kong International Airport"},
                "AirportCode": "VHHH",
                "CityName": {"Zh_tw": "香港", "En": "Hong Kong"},
                "CountryCode": "HK",
                "CountryName": {"Zh_tw": "香港", "En": "Hong Kong"},
                "PositionLat": 22.308889,
                "PositionLon": 113.914444,
                "is_test_data": True
            },
            "NRT": {
                "AirportID": "NRT",
                "AirportName": {"Zh_tw": "東京成田國際機場", "En": "Narita International Airport"},
                "AirportCode": "RJAA",
                "CityName": {"Zh_tw": "東京", "En": "Tokyo"},
                "CountryCode": "JP",
                "CountryName": {"Zh_tw": "日本", "En": "Japan"},
                "PositionLat": 35.765556,
                "PositionLon": 140.386389,
                "is_test_data": True
            }
        }
        
        if airport_code:
            if airport_code in mock_airports:
                return mock_airports[airport_code]
            else:
                return None
        
        return list(mock_airports.values())
    
    @staticmethod
    def generate_airline_data(airline_code=None):
        """
        生成模擬航空公司數據
        
        Args:
            airline_code (str, optional): 指定航空公司代碼，若不提供則返回多個航空公司
            
        Returns:
            list/dict: 航空公司數據
        """
        mock_airlines = {
            "CI": {
                "AirlineID": "CI",
                "AirlineName": {"Zh_tw": "中華航空", "En": "China Airlines"},
                "is_test_data": True
            },
            "BR": {
                "AirlineID": "BR",
                "AirlineName": {"Zh_tw": "長榮航空", "En": "EVA Air"},
                "is_test_data": True
            },
            "AE": {
                "AirlineID": "AE",
                "AirlineName": {"Zh_tw": "華信航空", "En": "Mandarin Airlines"},
                "is_test_data": True
            },
            "B7": {
                "AirlineID": "B7",
                "AirlineName": {"Zh_tw": "立榮航空", "En": "UNI Air"},
                "is_test_data": True
            },
            "JX": {
                "AirlineID": "JX",
                "AirlineName": {"Zh_tw": "星宇航空", "En": "STARLUX Airlines"},
                "is_test_data": True
            }
        }
        
        if airline_code:
            if airline_code in mock_airlines:
                return mock_airlines[airline_code]
            else:
                return None
        
        return list(mock_airlines.values())
    
    @staticmethod
    def generate_flight_data(airport_code="TPE", direction="Departure", date=None, count=10):
        """
        生成模擬航班數據
        
        Args:
            airport_code (str): 機場代碼
            direction (str): "Departure" 或 "Arrival"
            date (str, optional): 日期，格式為YYYY-MM-DD，若不提供則使用今天
            count (int, optional): 生成的航班數量
            
        Returns:
            list: 航班數據列表
        """
        mock_data = []
        airlines = ["CI", "BR", "AE", "B7", "JX"]
        destinations = {
            "TPE": ["HKG", "NRT", "ICN", "SIN", "BKK"],
            "KHH": ["TPE", "HKG", "MNL"],
            "TSA": ["KHH", "MZG", "HUN"]
        }
        origins = {
            "TPE": ["HKG", "NRT", "ICN", "SIN", "BKK"],
            "KHH": ["TPE", "HKG", "MNL"],
            "TSA": ["KHH", "MZG", "HUN"]
        }
                 
        airport_list = destinations.get(airport_code, ["TPE"]) if direction == "Departure" else origins.get(airport_code, ["TPE"])
        
        # 生成日期，如果未提供則使用今天
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        # 產生指定數量的模擬航班
        for i in range(count):
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
            
        return mock_data
    
    @staticmethod
    def generate_weather_data(city_code=None, date=None):
        """
        生成模擬天氣數據
        
        Args:
            city_code (str, optional): 城市代碼
            date (str, optional): 日期，格式為YYYY-MM-DD，若不提供則使用今天
            
        Returns:
            dict: 天氣數據
        """
        # 隨機氣象條件
        weather_conditions = [
            "晴天", "多雲", "陰天", "小雨", "中雨", "大雨", "雷雨",
            "Sunny", "Cloudy", "Overcast", "Light Rain", "Rain", "Heavy Rain", "Thunderstorm"
        ]
        
        # 隨機城市
        cities = {
            "TPE": {"name": "臺北", "country": "TW"},
            "KHH": {"name": "高雄", "country": "TW"},
            "HKG": {"name": "香港", "country": "HK"},
            "NRT": {"name": "東京", "country": "JP"},
            "BKK": {"name": "曼谷", "country": "TH"}
        }
        
        if not city_code:
            city_code = random.choice(list(cities.keys()))
        
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        # 生成隨機天氣數據
        city_info = cities.get(city_code, {"name": "未知城市", "country": "UN"})
        weather_condition = random.choice(weather_conditions)
        is_rainy = "雨" in weather_condition or "Rain" in weather_condition
        
        return {
            "city_code": city_code,
            "city_name": city_info["name"],
            "country_code": city_info["country"],
            "date": date,
            "weather_condition": weather_condition,
            "temperature": random.randint(15, 35),
            "humidity": random.randint(30, 95),
            "wind_speed": random.randint(0, 50),
            "precipitation": random.randint(5, 100) if is_rainy else 0,
            "forecast_time": f"{date}T08:00:00",
            "is_test_data": True
        }
    
    @staticmethod
    def generate_price_data(flight_id, days_back=30):
        """
        生成模擬票價數據
        
        Args:
            flight_id (str): 航班ID
            days_back (int): 生成過去多少天的數據
            
        Returns:
            dict: 票價數據和歷史數據
        """
        # 基礎票價
        base_economy = random.randint(3000, 8000)
        base_business = base_economy * random.uniform(2.0, 3.0)
        base_first = base_economy * random.uniform(3.5, 5.0)
        
        # 當前票價
        current_prices = {
            "economy": round(base_economy * random.uniform(0.9, 1.1)),
            "business": round(base_business * random.uniform(0.95, 1.05)),
            "first": round(base_first * random.uniform(0.98, 1.02))
        }
        
        # 歷史票價趨勢
        price_history = {
            "dates": [],
            "economy": [],
            "business": [],
            "first": []
        }
        
        today = datetime.now().date()
        for i in range(days_back, 0, -1):
            date = today - timedelta(days=i)
            
            # 基於日期的波動係數 (離出發日期越近，價格波動越大)
            volatility = 1.0 - (i / days_back) * 0.5
            
            # 添加日期和價格
            price_history["dates"].append(date.strftime("%Y-%m-%d"))
            price_history["economy"].append(round(base_economy * random.uniform(0.8, 1.2) * volatility))
            price_history["business"].append(round(base_business * random.uniform(0.9, 1.1) * volatility))
            price_history["first"].append(round(base_first * random.uniform(0.95, 1.05) * volatility))
        
        return {
            "current_prices": current_prices,
            "price_history": price_history
        }