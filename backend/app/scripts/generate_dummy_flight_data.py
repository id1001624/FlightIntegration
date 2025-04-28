#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
虛擬航班資料生成腳本

用途:
    生成模擬真實航班的虛擬資料，用於開發和測試環境，避免消耗真實API配額。
    基於混合生成法：結合模板和概率模型，產生具有真實性的隨機航班資料。

用法:
    python generate_dummy_flight_data.py --days 7 --flights-per-day 200 --start-date 2023-12-01

參數:
    --days: 要生成的天數，默認為3天
    --flights-per-day: 每天生成的航班數量基準值，默認為200
    --start-date: 起始日期，格式為YYYY-MM-DD，默認為今天
    --clear-existing: 是否清空已有的航班資料，默認為False
"""

import sys
import os
import argparse
import logging
import random
import datetime
import pandas as pd
from typing import List, Dict, Tuple, Any, Optional
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

# --- 添加正確的導入路徑 (確保在導入 app 之前) ---
current_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.dirname(current_dir)
backend_dir = os.path.dirname(app_dir)
sys.path.insert(0, backend_dir)
# sys.path.insert(0, app_dir) # 移到下面，在嘗試導入 app 之前
# --- 結束路徑設置 ---

# --- 配置日誌 (必須在導入 app 之前，因為 app 可能會配置日誌) ---
logs_dir = os.path.join(os.path.dirname(os.path.dirname(current_dir)), 'logs')
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(logs_dir, 'generate_flights.log'))
    ]
)
logger = logging.getLogger('generate_dummy_flight_data')
# --- 結束日誌配置 ---


# --- 導入並創建 Flask app 以獲取上下文 ---
try:
    # 確保 app 目錄在 path 中
    if app_dir not in sys.path:
        sys.path.insert(0, app_dir)
    from app import create_app
    flask_app = create_app() # 使用默認配置 (例如 development)
    flask_app.app_context().push()
    logger.info("Flask app context 已創建並推入。")
except ImportError as e:
    logger.error(f"無法導入或創建 Flask app ({e})。請確保腳本可以訪問 Flask app 實例。")
    sys.exit(1)
# --- 結束 app 創建 ---


# --- 現在導入 db 對象 ---
try:
    # 由於已經有了 app context，db 應該已經初始化
    from app.models.base import db
    logger.info("成功導入 db 對象。")
except ImportError:
    logger.error("即使創建了 app context，仍然無法從 app.models.base 導入 db 對象。請檢查 Flask app 初始化過程。")
    sys.exit(1)
# --- 結束 db 導入 ---

# --- 導入其他必要的模塊 (可以放在這裡或頂部) ---
from app.scripts.constants import (
    TAIWAN_AIRPORTS, TARGET_AIRLINES, 
    POPULAR_DOMESTIC_ROUTES_TUPLES, POPULAR_INTERNATIONAL_ROUTES_TUPLES,
    ALL_ROUTES_TUPLES
)
from app.models.flight import Flight
from app.models.ticket_price import TicketPrice
# --- 結束模塊導入 ---

# 平均飛行時間 (小時) - 根據航線類型
FLIGHT_DURATIONS = {
    'domestic': (0.5, 1.5),     # 國內航班 30分鐘 - 1.5小時
    'northeast_asia': (2, 4),   # 東北亞 2-4小時 (日本、韓國)
    'southeast_asia': (3, 5),   # 東南亞 3-5小時
    'china': (1.5, 3),          # 中國大陸 1.5-3小時
    'australia': (7, 9),        # 澳洲 7-9小時
    'europe': (12, 14),         # 歐洲 12-14小時
    'america': (11, 15),        # 美洲 11-15小時
}

# 地區機場分類
REGIONS = {
    'domestic': TAIWAN_AIRPORTS,
    'japan': ['NRT', 'HND', 'KIX', 'ITM', 'NGO', 'FUK', 'CTS', 'OKA', 'SDJ', 'KMJ', 'UKB', 'TAK'],
    'korea': ['ICN', 'GMP', 'PUS', 'CJU'],
    'china': ['PVG', 'PEK', 'SHA', 'CAN', 'SZX', 'XMN', 'FOC', 'TFU', 'CKG', 'WUH', 'TSN', 'NKG', 'TAO', 'NGB'],
    'hongkong_macau': ['HKG', 'MFM'],
    'southeast_asia': ['SIN', 'BKK', 'KUL', 'MNL', 'SGN', 'HAN', 'DPS', 'CGK', 'PEN', 'DAD', 'HKT', 'CNX', 'PNH', 'PQC', 'BKI'],
    'australia': ['SYD', 'MEL', 'BNE'],
    'europe': ['LHR', 'CDG', 'FRA', 'AMS'],
    'america': ['LAX', 'SFO', 'JFK', 'SEA', 'YVR', 'HNL'],
}

def parse_arguments():
    """解析命令行參數"""
    parser = argparse.ArgumentParser(description='生成虛擬航班資料')
    parser.add_argument('--days', type=int, default=3, help='要生成的天數，默認為3天')
    parser.add_argument('--flights-per-day', type=int, default=200, help='每天生成的航班數量基準值，默認為200')
    parser.add_argument('--start-date', type=str, default=None, help='起始日期，格式為YYYY-MM-DD，默認為今天')
    
    return parser.parse_args()

def get_region_for_airport(airport_code: str) -> str:
    """判斷機場所屬地區"""
    for region, airports in REGIONS.items():
        if airport_code in airports:
            return region
    return 'other'

def get_flight_duration(dep_airport: str, arr_airport: str) -> float:
    """根據出發和到達機場獲取飛行時間"""
    # 檢查是否為國內航線
    if dep_airport in TAIWAN_AIRPORTS and arr_airport in TAIWAN_AIRPORTS:
        min_duration, max_duration = FLIGHT_DURATIONS['domestic']
    else:
        # 國際航線，根據目的地區域確定飛行時間
        arr_region = get_region_for_airport(arr_airport)
        
        if arr_region in ['japan', 'korea']:
            min_duration, max_duration = FLIGHT_DURATIONS['northeast_asia']
        elif arr_region in ['southeast_asia']:
            min_duration, max_duration = FLIGHT_DURATIONS['southeast_asia']
        elif arr_region in ['china', 'hongkong_macau']:
            min_duration, max_duration = FLIGHT_DURATIONS['china']
        elif arr_region == 'australia':
            min_duration, max_duration = FLIGHT_DURATIONS['australia']
        elif arr_region == 'europe':
            min_duration, max_duration = FLIGHT_DURATIONS['europe']
        elif arr_region == 'america':
            min_duration, max_duration = FLIGHT_DURATIONS['america']
        else:
            # 默認國際航線時間
            min_duration, max_duration = 3, 6
    
    # 添加一些隨機性
    base_duration = random.uniform(min_duration, max_duration)
    # 轉換為分鐘並取整
    return round(base_duration * 60)

def generate_flight_number(airline_code: str) -> str:
    """生成航班號"""
    # 航班號數字部分通常是3-4位數字
    number = random.randint(100, 9999)
    return f"{airline_code}{number}"

def generate_departure_times(date: datetime.date, count: int) -> List[datetime.datetime]:
    """生成一天內的起飛時間，使用多峰高斯分佈模擬早、中、晚高峰"""
    # 定義三個高峰期 (早 7-9點, 中 12-14點, 晚 17-20點)
    peaks = [
        (8, 1),    # 早上高峰，均值8點，標準差1小時
        (13, 1),   # 中午高峰，均值13點，標準差1小時
        (18, 1.5)  # 晚上高峰，均值18點，標準差1.5小時
    ]
    
    # 每個高峰期的權重 (早中晚的航班分佈比例)
    weights = [0.4, 0.3, 0.3]
    
    departure_times = []
    # 計算每個峰值的數量
    peak_counts = [int(count * w) for w in weights]
    # 確保總數匹配
    diff = count - sum(peak_counts)
    if diff > 0:
        # 將差額添加到權重最大的峰值
        peak_counts[weights.index(max(weights))] += diff
    elif diff < 0:
        # 從權重最小的峰值減去差額
        peak_counts[weights.index(min(weights))] += diff # diff is negative

    
    for i, (peak_mean, peak_std) in enumerate(peaks):
        peak_count = peak_counts[i]
        if peak_count <= 0:
            continue
            
        # 使用高斯分佈生成小時
        # 需要 import numpy as np 或 random.gauss
        # hours = np.random.normal(peak_mean, peak_std, peak_count)
        hours = [random.gauss(peak_mean, peak_std) for _ in range(peak_count)]
        # 限制小時在0-23範圍內
        # hours = np.clip(hours, 0, 23)
        hours = [max(0, min(h, 23)) for h in hours]

        # 生成分鐘 (均勻分佈)
        # minutes = np.random.randint(0, 60, peak_count)
        minutes = [random.randint(0, 59) for _ in range(peak_count)]
        
        # 組合為時間戳
        for hour, minute in zip(hours, minutes):
            h, m = int(hour), int(minute)
            try:
                departure_time = datetime.datetime.combine(
                    date, datetime.time(h, m)
                )
                departure_times.append(departure_time)
            except ValueError:
                 logger.warning(f"產生無效的時間: {h}:{m}, 跳過.")


    # 確保生成了足夠的時間，以防 clip 導致數量減少
    while len(departure_times) < count:
         hour = random.randint(0, 23)
         minute = random.randint(0, 59)
         departure_times.append(datetime.datetime.combine(date, datetime.time(hour, minute)))

    # 排序時間
    departure_times.sort()
    # 如果數量超過，則截斷
    return departure_times[:count]

def select_route_templates(count: int) -> List[Tuple[str, str]]:
    """根據航線模板選擇航線，保持熱門航線比例較高"""
    # 不同航線類型的權重
    route_weights = {
        'popular_domestic': 0.2,      # 熱門國內航線
        'popular_international': 0.5, # 熱門國際航線
        'other': 0.3                  # 其他航線
    }
    
    # 計算每類航線數量
    popular_domestic_count = int(count * route_weights['popular_domestic'])
    popular_international_count = int(count * route_weights['popular_international'])
    other_count = count - popular_domestic_count - popular_international_count
    
    selected_routes = []
    
    # 選擇熱門國內航線
    if popular_domestic_count > 0:
        domestic_routes = random.choices(
            POPULAR_DOMESTIC_ROUTES_TUPLES,
            k=popular_domestic_count
        )
        selected_routes.extend(domestic_routes)
    
    # 選擇熱門國際航線
    if popular_international_count > 0:
        international_routes = random.choices(
            POPULAR_INTERNATIONAL_ROUTES_TUPLES,
            k=popular_international_count
        )
        selected_routes.extend(international_routes)
    
    # 選擇其他航線
    if other_count > 0:
        # 創建不在熱門航線中的航線列表
        other_routes = [
            route for route in ALL_ROUTES_TUPLES 
            if route not in POPULAR_DOMESTIC_ROUTES_TUPLES 
            and route not in POPULAR_INTERNATIONAL_ROUTES_TUPLES
        ]
        
        # 如果有其他航線可選
        if other_routes:
            other_selected = random.choices(other_routes, k=other_count)
            selected_routes.extend(other_selected)
        else:
            # 如果沒有其他航線，則從熱門航線中補充
            all_popular = POPULAR_DOMESTIC_ROUTES_TUPLES + POPULAR_INTERNATIONAL_ROUTES_TUPLES
            extra_routes = random.choices(all_popular, k=other_count)
            selected_routes.extend(extra_routes)
    
    return selected_routes

def generate_airline_distribution() -> Dict[str, float]:
    """生成航空公司分佈權重"""
    # 為各航空公司設置基礎權重
    # 台灣主要航空公司權重較高
    weights = {
        'BR': 0.20,  # 長榮航空
        'CI': 0.20,  # 中華航空
        'AE': 0.10,  # 華信航空
        'B7': 0.08,  # 立榮航空
        'JX': 0.07,  # 星宇航空
        'IT': 0.07,  # 台灣虎航
        'CX': 0.05,  # 國泰航空
        'JL': 0.04,  # 日本航空
        'NH': 0.04,  # 全日空航空
        'KE': 0.03,  # 大韓航空
        'OZ': 0.03,  # 韓亞航空
        'MU': 0.03,  # 中國東方航空
        'SQ': 0.03,  # 新加坡航空
        'AK': 0.02,  # 亞洲航空
        'DA': 0.01,  # 德安航空
    }
    
    # 確保所有TARGET_AIRLINES都有權重
    for airline in TARGET_AIRLINES:
        if airline not in weights:
            weights[airline] = 0.01
    
    # 歸一化權重
    total = sum(weights.values())
    for airline in weights:
        weights[airline] /= total
    
    return weights

def select_airline_for_route(dep: str, arr: str, airline_weights: Dict[str, float]) -> str:
    """根據航線選擇合適的航空公司"""
    # 針對特定航線調整航空公司選擇
    
    # 國內航線偏好
    if dep in TAIWAN_AIRPORTS and arr in TAIWAN_AIRPORTS:
        domestic_airlines = ['CI', 'AE', 'B7', 'DA']
        return random.choices(
            domestic_airlines,
            weights=[airline_weights.get(a, 0.1) for a in domestic_airlines],
            k=1
        )[0]
    
    # 針對日本航線偏好
    japan_airports = REGIONS['japan']
    if arr in japan_airports:
        japan_route_airlines = ['BR', 'CI', 'JL', 'NH', 'JX', 'IT']
        return random.choices(
            japan_route_airlines,
            weights=[airline_weights.get(a, 0.1) for a in japan_route_airlines],
            k=1
        )[0]
    
    # 針對韓國航線偏好
    korea_airports = REGIONS['korea']
    if arr in korea_airports:
        korea_route_airlines = ['BR', 'CI', 'KE', 'OZ', 'JX', 'IT']
        return random.choices(
            korea_route_airlines,
            weights=[airline_weights.get(a, 0.1) for a in korea_route_airlines],
            k=1
        )[0]
    
    # 默認使用全局權重選擇
    return random.choices(
        list(airline_weights.keys()),
        weights=list(airline_weights.values()),
        k=1
    )[0]

def generate_ticket_prices(flight_info: Dict) -> Dict:
    """根據航線生成票價信息"""
    # 根據航線距離/地區設置基準價格
    dep = flight_info['departure_airport']
    arr = flight_info['arrival_airport']
    
    # 國內航線
    if dep in TAIWAN_AIRPORTS and arr in TAIWAN_AIRPORTS:
        base_price = random.randint(1500, 5000)
    # 國際航線 - 根據地區分類
    else:
        arr_region = get_region_for_airport(arr)
        
        if arr_region in ['japan', 'korea', 'china', 'hongkong_macau']:
            # 東北亞
            base_price = random.randint(5000, 15000)
        elif arr_region == 'southeast_asia':
            # 東南亞
            base_price = random.randint(7000, 18000)
        elif arr_region == 'australia':
            # 澳洲
            base_price = random.randint(25000, 40000)
        elif arr_region in ['europe', 'america']:
            # 歐美
            base_price = random.randint(30000, 60000)
        else:
            # 其他國際航線
            base_price = random.randint(10000, 25000)
    
    # 生成各艙等價格
    # 經濟艙價格接近基準價格
    economy_price = int(base_price * random.uniform(0.9, 1.1))
    # 商務艙價格為經濟艙的2-3倍
    business_price = int(economy_price * random.uniform(2.0, 3.0))
    # 頭等艙價格為經濟艙的4-6倍
    first_price = int(economy_price * random.uniform(4.0, 6.0))
    
    # 部分航班可能沒有頭等艙或商務艙
    if random.random() < 0.3:  # 30%的航班沒有頭等艙
        first_price = None
    
    if random.random() < 0.1 and dep in ['MZG', 'TTT', 'KNH', 'HUN', 'CYI', 'MFK', 'LZN']:
        # 10%的小機場航班沒有商務艙
        business_price = None
        first_price = None
    
    return {
        'economy_price': economy_price,
        'business_price': business_price,
        'first_price': first_price
    }

def generate_flights_for_day(date: datetime.date, count: int, airline_weights: Dict[str, float]) -> List[Dict]:
    """為指定日期生成航班數據"""
    # 選擇航線
    routes = select_route_templates(count)
    
    # 生成起飛時間
    departure_times = generate_departure_times(date, count)
    
    flights = []
    for i in range(count): # 確保生成所需數量的航班
        if i >= len(routes) or i >= len(departure_times):
            logger.warning(f"無法為第 {i+1} 個航班生成數據 (路由或時間不足)")
            continue

        (dep, arr) = routes[i]
        departure_time = departure_times[i]

        # 選擇航空公司
        airline = select_airline_for_route(dep, arr, airline_weights)
        
        # 生成航班號
        flight_number = generate_flight_number(airline)
        
        # 計算飛行時間（分鐘）
        flight_duration = get_flight_duration(dep, arr)
        
        # 計算計劃到達時間
        scheduled_arrival = departure_time + datetime.timedelta(minutes=flight_duration)
        
        # 生成航班信息 (移除不再需要的欄位)
        flight_info = {
            'flight_number': flight_number,
            'airline': airline,
            'departure_airport': dep,
            'arrival_airport': arr,
            'scheduled_departure': departure_time,
            'scheduled_arrival': scheduled_arrival,
            'date': date
        }
        
        # 生成票價信息
        ticket_prices = generate_ticket_prices(flight_info)
        flight_info.update(ticket_prices)
        
        flights.append(flight_info)
    
    return flights

def prepare_flight_objects(flights_data: List[Dict]) -> Tuple[List[Flight], List[TicketPrice]]:
    """將生成的數據轉換為Flight和TicketPrice對象"""
    flight_objects = []
    ticket_price_objects = []
    
    for flight_data in flights_data:
        # 創建Flight對象
        flight = Flight(
            flight_number=flight_data['flight_number'],
            airline_id=flight_data['airline'],
            departure_airport_id=flight_data['departure_airport'],
            arrival_airport_id=flight_data['arrival_airport'],
            scheduled_departure=flight_data['scheduled_departure'],
            scheduled_arrival=flight_data['scheduled_arrival'],
            aircraft=f"DUMMY-{random.choice(['B737', 'A320', 'B777', 'A350', 'B787'])}",
            departure_terminal=random.choice([None, 'T1', 'T2', 'T3']) if random.random() > 0.3 else None,
            arrival_terminal=random.choice([None, 'T1', 'T2', 'T3']) if random.random() > 0.3 else None,
            is_test_data=True
        )
        flight_objects.append(flight)
        
        # 創建TicketPrice對象
        # 為每個航班創建經濟艙價格記錄
        # 注意：flight_id 將在插入後由 SQLAlchemy 自動關聯
        economy_price_obj = TicketPrice(
            # flight_id=None, # 不需要手動設置，SQLAlchemy 會處理
            # flight_number=flight_data['flight_number'], # 移除：無效參數
            # airline=flight_data['airline'],             # 移除：無效參數
            # date=flight_data['date'],                   # 移除：TicketPrice 模型沒有 date 欄位
            class_type='經濟',
            base_price=flight_data['economy_price'],
            economy_price=flight_data['economy_price'],
            business_price=None,
            first_price=None,
            available_seats=random.randint(5, 200)
        )
        # 將 price object 與 flight object 關聯
        # 假設 Flight 模型有 ticket_prices 關係 (通常是 list)
        # flight.ticket_prices.append(economy_price_obj) # <-- 不直接 append，讓 SQLAlchemy 處理
        ticket_price_objects.append(economy_price_obj)

        
        # 如果有商務艙價格，創建商務艙記錄
        if flight_data['business_price']:
            business_price_obj = TicketPrice(
                # flight_id=None,
                # flight_number=flight_data['flight_number'], # 移除
                # airline=flight_data['airline'],             # 移除
                # date=flight_data['date'],                   # 移除
                class_type='商務',
                base_price=flight_data['business_price'],
                economy_price=None,
                business_price=flight_data['business_price'],
                first_price=None,
                available_seats=random.randint(0, 30)
            )
            # flight.ticket_prices.append(business_price_obj)
            ticket_price_objects.append(business_price_obj)
        
        # 如果有頭等艙價格，創建頭等艙記錄
        if flight_data['first_price']:
            first_price_obj = TicketPrice(
                # flight_id=None,
                # flight_number=flight_data['flight_number'], # 移除
                # airline=flight_data['airline'],             # 移除
                # date=flight_data['date'],                   # 移除
                class_type='頭等',
                base_price=flight_data['first_price'],
                economy_price=None,
                business_price=None,
                first_price=flight_data['first_price'],
                available_seats=random.randint(0, 10)
            )
            # flight.ticket_prices.append(first_price_obj)
            ticket_price_objects.append(first_price_obj)
    
    # 注意：這裡返回的是獨立的列表，關聯需要在插入時由 SQLAlchemy 處理
    return flight_objects, ticket_price_objects

def clear_old_test_data() -> None:
    """清除今天以前的虛擬測試資料 (is_test_data = True)"""
    session = db.session # 直接獲取會話
    try:
        today = datetime.date.today()
        today_str = today.strftime('%Y-%m-%d')
        
        # 首先獲取需要刪除的測試航班號
        flight_numbers_query = text("""
            SELECT flight_number FROM flights 
            WHERE DATE(scheduled_departure) < :today_date
            AND is_test_data = TRUE
        """)
        
        result = session.execute(flight_numbers_query, {"today_date": today_str})
        flight_numbers = [row[0] for row in result]
        
        if flight_numbers:
            logger.info(f"找到 {len(flight_numbers)} 個今天 ({today_str}) 之前的虛擬航班需要清除")
            
            # 刪除相關的票價數據
            delete_ticket_prices_query = text("""
                DELETE FROM ticket_prices 
                WHERE flight_number IN :flight_numbers
            """)
            deleted_prices_count = session.execute(delete_ticket_prices_query, {"flight_numbers": tuple(flight_numbers)}).rowcount
            logger.info(f"已清除 {deleted_prices_count} 筆相關票價數據")

            # 刪除航班數據
            delete_flights_query = text("""
                DELETE FROM flights 
                WHERE flight_number IN :flight_numbers 
                AND is_test_data = TRUE
            """)
            deleted_flights_count = session.execute(delete_flights_query, {"flight_numbers": tuple(flight_numbers)}).rowcount
            logger.info(f"已清除 {deleted_flights_count} 筆虛擬航班數據")

            session.commit() # 提交事務
        else:
            logger.info(f"沒有找到今天 ({today_str}) 之前的虛擬航班資料需要清除")

    except SQLAlchemyError as e:
        logger.error(f"清除舊虛擬資料時發生資料庫錯誤: {str(e)}")
        session.rollback() # 回滾事務
        raise
    except Exception as e:
        logger.error(f"清除舊虛擬資料時發生未預期錯誤: {str(e)}")
        session.rollback() # 回滾事務
        raise
    finally:
        session.remove() # 或 session.close() - 確保會話關閉

def batch_insert_data(flights: List[Flight], ticket_prices: List[TicketPrice], batch_size: int = 100) -> None:
    """批量插入數據到資料庫"""
    session = db.session # 直接獲取會話
    try:
        total_flights = len(flights)
        total_prices = len(ticket_prices)
        
        logger.info(f"開始批量插入 {total_flights} 筆航班數據和 {total_prices} 筆票價數據")
        
        # 分批插入航班數據
        for i in range(0, total_flights, batch_size):
            batch_flights = flights[i:i + batch_size]
            session.add_all(batch_flights)
            # 不需要 session.flush()，commit 會處理
            logger.info(f"準備插入航班數據 {i+1} 至 {min(i+batch_size, total_flights)}")
        
        # 分批插入票價數據
        for i in range(0, total_prices, batch_size):
            batch_prices = ticket_prices[i:i + batch_size]
            session.add_all(batch_prices)
            logger.info(f"準備插入票價數據 {i+1} 至 {min(i+batch_size, total_prices)}")
        
        # 提交事務
        session.commit()
        logger.info("數據插入完成")
    
    except SQLAlchemyError as e:
        logger.error(f"批量插入數據時發生資料庫錯誤: {str(e)}")
        session.rollback() # 回滾事務
        raise
    except Exception as e:
        logger.error(f"批量插入數據時發生未預期錯誤: {str(e)}")
        session.rollback() # 回滾事務
        raise
    finally:
        session.remove() # 或 session.close() - 確保會話關閉

def main():
    """主函數"""
    # 解析命令行參數
    args = parse_arguments()
    
    # 設置日期
    if args.start_date:
        try:
            start_date = datetime.datetime.strptime(args.start_date, '%Y-%m-%d').date()
        except ValueError:
            logger.error("日期格式不正確，請使用 YYYY-MM-DD 格式")
            return
    else:
        start_date = datetime.date.today()
    
    end_date = start_date + datetime.timedelta(days=args.days - 1)
    
    logger.info(f"開始生成從 {start_date} 至 {end_date} 的虛擬航班數據")
    logger.info(f"每天將生成約 {args.flights_per_day} 個航班")
    
    try:
        # *** 清除舊的測試數據 ***
        logger.info("開始清除今天之前的舊虛擬航班數據...")
        clear_old_test_data() # 直接調用，不需要傳遞 db_manager
        logger.info("舊虛擬航班數據清除完成。")

        # 生成航空公司分佈權重
        airline_weights = generate_airline_distribution()
        
        all_flights = []
        all_ticket_prices = []
        
        # 為每一天生成航班
        for day_offset in range(args.days):
            current_date = start_date + datetime.timedelta(days=day_offset)
            
            # 根據週幾調整航班數量
            weekday = current_date.weekday()
            # 週末(5,6)航班量增加，週中(0-4)略有波動
            if weekday >= 5:  # 週末
                day_flights_count = int(args.flights_per_day * random.uniform(1.1, 1.3))
            else:
                day_flights_count = int(args.flights_per_day * random.uniform(0.9, 1.1))
            
            logger.info(f"為 {current_date} (週{weekday+1}) 生成 {day_flights_count} 個航班")
            
            # 生成當天航班
            flights_data = generate_flights_for_day(current_date, day_flights_count, airline_weights)
            
            # 準備資料庫對象
            flights, ticket_prices = prepare_flight_objects(flights_data)
            
            all_flights.extend(flights)
            all_ticket_prices.extend(ticket_prices)
            
            logger.info(f"{current_date} 的航班數據生成完成")
        
        # 批量插入到資料庫
        batch_insert_data(all_flights, all_ticket_prices) # 直接調用，不需要傳遞 db_manager
        
        logger.info(f"成功生成並插入 {len(all_flights)} 個航班的資料")
    
    except Exception as e:
        logger.error(f"生成數據時發生錯誤: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main() 