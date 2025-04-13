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
    def generate_taiwan_departures_data(date=None, days=1):
        """
        生成模擬台灣出發航班數據，格式與sync_taiwan_departures方法一致

        Args:
            date (str, optional): 日期，格式為YYYY-MM-DD，若不提供則使用今天
            days (int, optional): 查詢天數

        Returns:
            dict: 以機場代碼為鍵，航班列表為值的字典，格式與sync_taiwan_departures返回值一致
        """
        # 台灣機場列表
        taiwan_airports = ['TPE', 'TSA', 'RMQ', 'KHH', 'TNN', 'CYI', 'HUN', 'TTT', 'KNH', 'MZG', 'LZN', 'MFK', 'KYD', 'GNI', 'CMJ', 'WOT']

        # 目標航空公司
        target_airlines = ['AE', 'B7', 'BR', 'CI', 'CX', 'DA', 'IT', 'JL', 'JX', 'OZ']

        # 國內外目的地
        domestic_destinations = ['TPE', 'TSA', 'RMQ', 'KHH', 'TNN', 'CYI', 'HUN', 'TTT', 'KNH', 'MZG', 'LZN', 'MFK', 'KYD', 'GNI', 'CMJ', 'WOT']
        international_destinations = ['HKG', 'NRT', 'HND', 'ICN', 'BKK', 'SIN', 'KUL', 'PVG', 'PEK', 'LAX', 'SFO', 'JFK', 'CDG', 'LHR', 'FRA', 'SYD']

        results = {}

        # 生成日期，如果未提供則使用今天
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        elif isinstance(date, datetime):
            date = date.strftime("%Y-%m-%d")

        # 為每個台灣機場生成航班
        for airport in taiwan_airports:
            # 決定該機場的航班數量 (根據機場大小調整)
            flight_count = 0
            if airport in ['TPE', 'TSA', 'KHH']:  # 主要機場
                flight_count = random.randint(15, 30)
            elif airport in ['RMQ', 'TNN']:  # 中型機場
                flight_count = random.randint(5, 15)
            else:  # 小型機場
                flight_count = random.randint(1, 8)

            flights = []
            flight_keys = set()  # 避免重複航班

            # 生成國內航班 (約60%)
            domestic_count = int(flight_count * 0.6)
            for i in range(domestic_count):
                # 隨機選擇一個不同於出發地的國內目的地
                destinations = [d for d in domestic_destinations if d != airport]
                arrival = random.choice(destinations)

                # 國內航班主要由AE, B7, DA運營
                domestic_airlines = ['AE', 'B7', 'DA']
                airline = random.choice(domestic_airlines)

                # 生成航班號
                flight_number = f"{airline}{random.randint(100, 999)}"

                # 生成出發時間在當天的隨機時間
                hour = random.randint(6, 22)
                minute = random.choice([0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55])
                scheduled_departure = f"{date}T{hour:02d}:{minute:02d}:00"

                # 國內航班飛行時間較短，1-2小時
                flight_duration = random.randint(40, 120)
                departure_dt = datetime.strptime(scheduled_departure, "%Y-%m-%dT%H:%M:%S")
                arrival_dt = departure_dt + timedelta(minutes=flight_duration)
                scheduled_arrival = arrival_dt.strftime("%Y-%m-%dT%H:%M:%S")

                # 生成航班唯一鍵
                flight_key = f"{flight_number}_{scheduled_departure}"
                if flight_key in flight_keys:
                    continue
                
                flight_keys.add(flight_key)

                # 隨機決定是否有實際時間（代表航班是否已起飛）
                has_actual = random.random() > 0.5
                actual_departure = scheduled_departure if has_actual else None
                actual_arrival = scheduled_arrival if has_actual and random.random() > 0.6 else None

                # 創建航班字典
                flight = {
                    "flight_id": f"MOCK-{airline}-{i}",
                    "airline_code": airline,
                    "flight_number": flight_number,
                    "departure_airport": airport,
                    "arrival_airport": arrival,
                    "scheduled_departure": scheduled_departure,
                    "scheduled_arrival": scheduled_arrival,
                    "actual_departure": actual_departure,
                    "actual_arrival": actual_arrival,
                    "status": "A" if random.random() > 0.2 else "D",  # A:正常, D:延誤
                    "status_description": "正常" if random.random() > 0.2 else "延誤",
                    "terminal": str(random.randint(1, 2)),
                    "gate": f"{random.choice(['A', 'B', 'C'])}{random.randint(1, 20)}",
                    "is_test_data": True
                }

                flights.append(flight)

            # 生成國際航班 (約40%)
            international_count = flight_count - domestic_count
            for i in range(international_count):
                # 隨機選擇一個國際目的地
                arrival = random.choice(international_destinations)

                # 國際航班由各種目標航空公司運營
                international_airlines = [a for a in target_airlines if a not in ['AE', 'B7', 'DA']]
                airline = random.choice(international_airlines)

                # 生成航班號
                flight_number = f"{airline}{random.randint(100, 999)}"

                # 生成出發時間在當天的隨機時間
                hour = random.randint(6, 22)
                minute = random.choice([0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55])
                scheduled_departure = f"{date}T{hour:02d}:{minute:02d}:00"

                # 國際航班飛行時間較長，2-12小時
                flight_duration = random.randint(120, 720)
                departure_dt = datetime.strptime(scheduled_departure, "%Y-%m-%dT%H:%M:%S")
                arrival_dt = departure_dt + timedelta(minutes=flight_duration)
                scheduled_arrival = arrival_dt.strftime("%Y-%m-%dT%H:%M:%S")

                # 生成航班唯一鍵
                flight_key = f"{flight_number}_{scheduled_departure}"
                if flight_key in flight_keys:
                    continue
                
                flight_keys.add(flight_key)

                # 隨機決定是否有實際時間（代表航班是否已起飛）
                has_actual = random.random() > 0.5
                actual_departure = scheduled_departure if has_actual else None
                actual_arrival = scheduled_arrival if has_actual and random.random() > 0.7 else None

                # 創建航班字典
                flight = {
                    "flight_id": f"MOCK-{airline}-{i+domestic_count}",
                    "airline_code": airline,
                    "flight_number": flight_number,
                    "departure_airport": airport,
                    "arrival_airport": arrival,
                    "scheduled_departure": scheduled_departure,
                    "scheduled_arrival": scheduled_arrival,
                    "actual_departure": actual_departure,
                    "actual_arrival": actual_arrival,
                    "status": "A" if random.random() > 0.2 else "D",  # A:正常, D:延誤
                    "status_description": "正常" if random.random() > 0.2 else "延誤",
                    "terminal": str(random.randint(1, 2)),
                    "gate": f"{random.choice(['A', 'B', 'C'])}{random.randint(1, 20)}",
                    "is_test_data": True
                }

                flights.append(flight)

            # 將該機場的航班列表添加到結果中
            results[airport] = flights

        return results
    
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