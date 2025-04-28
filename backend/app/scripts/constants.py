"""
共享常量模組 - 存儲所有腳本和客戶端共用的常量
"""

import os
import sys
import uuid
import io
import gzip
import json
import logging
import datetime
import base64
from datetime import datetime as dt_datetime
from datetime import timedelta as dt_timedelta
from typing import Dict, List, Optional, Any, Union, Tuple 
# *** Logger 配置 (添加) ***
logger = logging.getLogger(__name__) # 在頂層定義 logger



# --- 常量定義 --- (以下保持不變)

# 台灣機場IATA代碼
TAIWAN_AIRPORTS = [
    'TPE',  # 台灣桃園國際機場
    'TSA',  # 台北松山機場
    'KHH',  # 高雄國際機場
    'RMQ',  # 台中清泉崗機場
    'TNN',  # 台南機場
    'HUN',  # 花蓮機場
    'TTT',  # 台東機場
    'KNH',  # 金門機場
    'MZG',  # 馬公機場
    'GNI',  # 綠島機場
    'KYD',  # 蘭嶼機場
    'CYI',  # 嘉義機場
    'MFK',  # 馬祖北竿機場
    'LZN',  # 馬祖南竿機場
    'WOT',  # 望安機場
    'CMJ',  # 七美機場
]

# 台北機場IATA代碼 (新增)
TAIPEI_AIRPORTS = ['TPE', 'TSA']

# 目標航空公司IATA代碼
TARGET_AIRLINES = [
    'AE',  # 華信航空 (Mandarin Airlines)
    'B7',  # 立榮航空 (TransAsia Airways)
    'DA',  # 德安航空 (Daliy Air)
    'BR',  # 長榮航空 (EVA Air)
    'CI',  # 中華航空 (China Airlines)
    'CX',  # 國泰航空 (Cathay Pacific)
    'JX',  # 星宇航空 (STARLUX Airlines)
    'IT',  # 台灣虎航 (Tiger Air Taiwan)
    'JL',  # 日本航空 (Japan Airlines)
    'NH',  # 全日空航空 (All Nippon Airways)
    'AK',  # 亞洲航空 (AirAsia Berhad)
    'KE',  # 大韓航空 (Korean Air)
    'OZ',  # 韓亞航空 (Asiana Airlines)
    'MU',  # 中國東方航空 (China Eastern Airlines)
    'SQ',  # 新加坡航空 (Singapore Airlines)
]

# 常用時間格式
DATETIME_FORMATS = [
    '%Y-%m-%dT%H:%M:%S.%f',  # ISO格式帶毫秒
    '%Y-%m-%dT%H:%M:%S',     # ISO格式
    '%Y-%m-%dT%H:%M',        # ISO格式不帶秒
    '%Y-%m-%d %H:%M:%S',     # 標準格式
    '%Y-%m-%d %H:%M',        # 標準格式不帶秒
    '%m/%d/%Y %H:%M',        # FlightStats格式
    '%m/%d/%Y %H:%M:%S'      # FlightStats格式帶秒
]

# API配置
TDX_API_CONFIG = {
    'base_url': 'https://tdx.transportdata.tw/api/basic',
    'auth_url': 'https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token',
    'max_retries': 3,
    'retry_delay': 5,
    'request_interval': 0.5  # 秒
}

FLIGHTSTATS_API_CONFIG = {
    'base_url': 'https://api.flightstats.com/flex',
    'max_retries': 3,
    'retry_delay': 5,
    'request_interval': 1.0  # 秒
}

# 緩存配置
CACHE_CONFIG = {
    'default_ttl': 3600,             # 默認緩存有效期為1小時
    'airports_ttl': 86400,           # 機場信息緩存1天
    'airlines_ttl': 86400,           # 航空公司信息緩存1天
    'flight_schedules_ttl': 7200,    # 航班時刻表緩存2小時
    'flight_status_ttl': 1800        # 航班狀態緩存30分鐘
}

# 資料庫同步配置
DB_SYNC_CONFIG = {
    'batch_size': 100,               # 批量處理數量
    'sync_interval': 43200,          # 同步間隔（秒），默認12小時
    'taiwan_airports_sync_days': 7,  # 台灣機場同步天數
    'int_flights_sync_days': 3       # 國際航班同步天數
}

# --- 熱門航線 ---

# 輔助函數：生成航線名稱 (可根據需要擴展)
def _get_route_name(dep, arr):
    airport_names = {
        'TPE': '台北桃園', 'TSA': '台北松山', 'KHH': '高雄', 'RMQ': '台中', 'HUN': '花蓮',
        'NRT': '東京成田', 'HND': '東京羽田', 'KIX': '大阪關西', 'ICN': '首爾仁川', 'HKG': '香港',
        'BKK': '曼谷', 'SIN': '新加坡', 'PVG': '上海浦東', 'MNL': '馬尼拉', 'SGN': '胡志明市',
        'KUL': '吉隆坡', 'MFM': '澳門', 'NGO': '名古屋', 'CTS': '札幌', 'FUK': '福岡',
        'LAX': '洛杉磯', 'SFO': '舊金山', 'YVR': '溫哥華', 'JFK': '紐約JFK', 'LHR': '倫敦希斯洛',
        'CDG': '巴黎戴高樂', 'MZG': '澎湖', 'TTT':'台東', 'KNH':'金門', 'TNN':'台南',
        'PUS': '釜山', 'OKA': '沖繩', 'GMP': '首爾金浦', 'SHA': '上海虹橋', 'DPS': '峇里島',
        'DAD': '峴港', 'CNX': '清邁', 'ITM': '大阪伊丹', 'DMK': '曼谷廊曼', 'CAN': '廣州',
        'PEK': '北京', 'HAN': '河內', 'PEN': '檳城', 'CGK': '雅加達', 'CEB': '宿霧',
        'SEA': '西雅圖', 'AMS': '阿姆斯特丹', 'FRA': '法蘭克福', 'BNE': '布里斯本', 'MEL': '墨爾本',
        'SYD': '悉尼', 'HNL': '檀香山', 'LZN': '南竿', 'MFK': '北竿', 'CMJ': '七美',
        'WOT': '望安', 'SZX': '深圳', 'XMN': '廈門', 'FOC': '福州', 'WUH': '武漢',
        'CKG': '重慶', 'TSN': '天津', 'NKG': '南京', 'TAO': '青島', 'NGB': '寧波',
        'TFU': '成都', 'KMJ': '熊本', 'PQC': '富國島', 'UKB': '神戶', 'TAK': '高松',
        'CJU': '濟州', 'BKI': '亞庇', 'SDJ': '仙台', 'KMQ': '小松', 'OKJ': '岡山',
        'HKD': '函館', 'HSG': '佐賀', 'HKT': '普吉', 'HNA': '花卷', 'KIJ': '新潟',
        'KMI': '宮崎', 'AXT': '秋田', 'IBR': '茨城', 'KCZ': '高知', 'OIT': '大分',
        'FKS': '福島', 'AKJ': '旭川', 'PNH': '金邊', 'NGS': '長崎', 'SPK': '札幌'
    }
    dep_name = airport_names.get(dep, dep)
    arr_name = airport_names.get(arr, arr)
    # 簡化台北名稱
    if dep in ['TPE', 'TSA']: dep_name = '台北'
    return f"{dep_name}-{arr_name}"

# 熱門國內航線 (元組格式，用於內部邏輯如 sync_manager)
POPULAR_DOMESTIC_ROUTES_TUPLES = [
    ('TPE', 'KHH'), ('TSA', 'KHH'), ('TSA', 'RMQ'), ('TSA', 'TNN'),
    ('TSA', 'MZG'), ('TSA', 'HUN'), ('TSA', 'TTT'), ('TSA', 'KNH'),
    ('KHH', 'TSA'), ('RMQ', 'TSA'), ('TNN', 'TSA'), ('MZG', 'TSA')
]

# 熱門國際航線 (元組格式，用於內部邏輯如 sync_manager)
POPULAR_INTERNATIONAL_ROUTES_TUPLES = [
    # 台北桃園國際機場 (TPE) 熱門航線
    ('TPE', 'HKG'), ('TPE', 'NRT'), ('TPE', 'HND'), ('TPE', 'KIX'), ('TPE', 'ICN'),
    ('TPE', 'BKK'), ('TPE', 'SIN'), ('TPE', 'PVG'), ('TPE', 'MNL'), ('TPE', 'SGN'),
    ('TPE', 'KUL'), ('TPE', 'MFM'), ('TPE', 'NGO'), ('TPE', 'CTS'), ('TPE', 'FUK'),
    ('TPE', 'LAX'), ('TPE', 'SFO'), ('TPE', 'YVR'), ('TPE', 'JFK'), ('TPE', 'LHR'),
    ('TPE', 'CDG'), ('TPE', 'HNL'),
    
    # 台北松山機場 (TSA) 熱門航線
    ('TSA', 'HND'), ('TSA', 'HKG'), ('TSA', 'GMP'), ('TSA', 'PVG'), ('TSA', 'SHA'),
    ('TSA', 'ITM'), ('TSA', 'OKA'), ('TSA', 'CTS'), ('TSA', 'ICN'),
    
    # 高雄國際機場 (KHH) 熱門航線
    ('KHH', 'HKG'), ('KHH', 'BKK'), ('KHH', 'NRT'), ('KHH', 'KIX'), ('KHH', 'ICN'),
    ('KHH', 'MNL'), ('KHH', 'SIN'), ('KHH', 'MFM'),
    
    # 台中清泉崗機場 (RMQ) 熱門航線
    ('RMQ', 'HKG'), ('RMQ', 'MFM'), ('RMQ', 'SGN'), ('RMQ', 'KIX'), ('RMQ', 'NRT'),
    ('RMQ', 'OKA'), ('RMQ', 'ICN'),
    
    # 花蓮機場 (HUN) 熱門航線
    ('HUN', 'HKG')
]

# --- 新增：合併後的熱門航線 (用於前端或統一邏輯) ---
COMBINED_POPULAR_ROUTES_TUPLES = sorted(list(set(POPULAR_DOMESTIC_ROUTES_TUPLES + POPULAR_INTERNATIONAL_ROUTES_TUPLES)))

# --- 前端熱門航線 (可以保留或移除，取決於是否還需要獨立定義) --- 
# 根據用戶提供的表格定義前端熱門航線
_fe_tpe_dest = ['HKG', 'NRT', 'HND', 'KIX', 'ICN', 'BKK', 'SIN', 'PVG', 'MNL', 'SGN', 'KUL', 'MFM', 'NGO', 'CTS', 'FUK', 'LAX', 'SFO', 'YVR', 'JFK', 'LHR', 'CDG']
_fe_tsa_dest = ['HKG', 'HND', 'GMP', 'PVG', 'SHA'] # GMP 代表首爾金浦, SHA 代表上海虹橋
_fe_khh_dest = ['HKG', 'BKK', 'NRT', 'KIX', 'ICN', 'MNL', 'SIN', 'MFM']
_fe_rmq_dest = ['HKG', 'MFM', 'SGN']
_fe_hun_dest = ['HKG'] # 花蓮包機

# --- 所有航線資料 (修改) ---

# 1. 直接定義所有已知的國內航線元組 (包含雙向)
ALL_DOMESTIC_ROUTES_TUPLES = [
    # From/To TSA (Taipei Songshan)
    ('TSA', 'KHH'), ('KHH', 'TSA'),
    ('TSA', 'RMQ'), ('RMQ', 'TSA'),
    ('TSA', 'TNN'), ('TNN', 'TSA'),
    ('TSA', 'MZG'), ('MZG', 'TSA'),
    ('TSA', 'HUN'), ('HUN', 'TSA'),
    ('TSA', 'TTT'), ('TTT', 'TSA'),
    ('TSA', 'KNH'), ('KNH', 'TSA'),
    ('TSA', 'MFK'), ('MFK', 'TSA'),
    ('TSA', 'LZN'), ('LZN', 'TSA'),

    # From/To KHH (Kaohsiung)
    ('KHH', 'MZG'), ('MZG', 'KHH'),
    ('KHH', 'KNH'), ('KNH', 'KHH'),
    ('KHH', 'WOT'), ('WOT', 'KHH'),
    ('KHH', 'CMJ'), ('CMJ', 'KHH'),
    ('KHH', 'LZN'), ('LZN', 'KHH'), 
    ('KHH', 'HUN'), ('HUN', 'KHH'),

    # From/To RMQ (Taichung)
    ('RMQ', 'KNH'), ('KNH', 'RMQ'),
    ('RMQ', 'MZG'), ('MZG', 'RMQ'),
    ('RMQ', 'LZN'), ('LZN', 'RMQ'),
    ('RMQ', 'HUN'), ('HUN', 'RMQ'),

    # From/To TNN (Tainan)
    ('TNN', 'MZG'), ('MZG', 'TNN'),
    ('TNN', 'KNH'), ('KNH', 'TNN'),

    # From/To TTT (Taitung)
    ('TTT', 'GNI'), ('GNI', 'TTT'),
    ('TTT', 'KYD'), ('KYD', 'TTT'),

    # From/To KNH (Kinmen)
    ('KNH', 'CYI'), ('CYI', 'KNH'),
    ('KNH', 'MZG'), ('MZG', 'KNH'),

    # From/To MZG (Magong/Penghu)
    ('MZG', 'CYI'), ('CYI', 'MZG'),
    ('MZG', 'CMJ'), ('CMJ', 'MZG'),

    # From/To GNI (Green Island)
    # (Included above)

    # From/To KYD (Lanyu)
    # (Included above)

    # From/To CYI (Chiayi)
    # (Included above)

    # From/To MFK (Matsu Beigan)
    # (Included above)

    # From/To LZN (Matsu Nangan)
    # (Included above)

    # From/To WOT (Wangan)
    # (Included above)

    # From/To CMJ (Qimei)
    # (Included above)
]
# 去重並排序
ALL_DOMESTIC_ROUTES_TUPLES = sorted(list(set(ALL_DOMESTIC_ROUTES_TUPLES)))

# 2. 定義國際航線 (目前主要從 TPE)
TPE_INTERNATIONAL_ROUTES = [
    # 日本
    'NRT', 'HND', 'KIX', 'NGO', 'CTS', 'FUK', 'OKA', 'SDJ',
    # 韓國
    'ICN', 'PUS', 'CJU',
    # 中國大陸
    'PVG', 'PEK', 'CAN', 'NKG', 'NGB', 'TAO', 'WUH', 'SZX', 'TFU',
    # 港澳
    'HKG', 'MFM',
    # 東南亞
    'SIN', 'BKK', 'KUL', 'SGN', 'DPS', 'MNL', 'HAN', 'CNX', 'PNH', 'CGK', 'PEN', 'DAD', 'HKT',
    # 澳洲
    'SYD', 'MEL', 'BNE',
    # 歐洲
    'LHR', 'FRA', 'CDG', 'AMS',
    # 美洲
    'SFO', 'LAX', 'JFK', 'HNL', 'SEA', 'YVR'
]
# 創建國際航線元組 (可以擴展 KHH, RMQ 等)
ALL_INTERNATIONAL_ROUTES_TUPLES = [('TPE', dest) for dest in TPE_INTERNATIONAL_ROUTES]

# 3. 合併國內與國際航線
ALL_ROUTES_TUPLES = sorted(list(set(ALL_DOMESTIC_ROUTES_TUPLES + ALL_INTERNATIONAL_ROUTES_TUPLES)))

# 4. 確保熱門航線包含在內 (作為安全檢查)
def ensure_routes_included(routes_to_check, all_routes):
    """確保指定的航線集合是所有航線的子集，若不是則添加"""
    for route in routes_to_check:
        if route not in all_routes:
            logger.warning(f"警告：熱門航線 {route} 未包含在 ALL_ROUTES_TUPLES 中，已自動添加。請檢查定義。")
            all_routes.append(route)

# 執行檢查與最終去重排序
ensure_routes_included(POPULAR_DOMESTIC_ROUTES_TUPLES, ALL_ROUTES_TUPLES)
ensure_routes_included(POPULAR_INTERNATIONAL_ROUTES_TUPLES, ALL_ROUTES_TUPLES)
ALL_ROUTES_TUPLES = sorted(list(set(ALL_ROUTES_TUPLES))) # 最終排序和去重

# --- API 查詢與前端顯示輔助函數 ---

def is_popular_route(departure, arrival):
    """判斷一個航線是否為熱門航線（包括國內和國際）"""
    route = (departure, arrival)
    return (route in POPULAR_DOMESTIC_ROUTES_TUPLES or 
            route in POPULAR_INTERNATIONAL_ROUTES_TUPLES)

def get_all_direct_routes():
    """取得所有直飛航線"""
    return ALL_ROUTES_TUPLES

def get_popular_routes():
    """取得所有合併後的熱門航線（國內+國際）"""
    return COMBINED_POPULAR_ROUTES_TUPLES # 返回合併後的列表

def get_routes_for_frontend():
    """
    取得格式化的航線資訊，用於前端顯示
    返回格式: {
        'all_routes': [{'departure': 'TPE', 'arrival': 'NRT', 'name': '台北-東京成田', 'is_popular': True}, ...],
        'popular_routes': [{'departure': 'TPE', 'arrival': 'NRT', 'name': '台北-東京成田'}, ...]
    }
    """
    all_routes = []
    popular_routes = []
    
    # 創建一個熱門航線的集合以便快速查找
    popular_set = set(COMBINED_POPULAR_ROUTES_TUPLES) # 使用合併後的集合
    
    # 處理所有航線
    for dep, arr in ALL_ROUTES_TUPLES:
        # --- 修改：使用合併後的 popular_set 判斷 --- 
        is_popular = (dep, arr) in popular_set 
        route_info = {
            'departure': dep,
            'arrival': arr,
            'name': _get_route_name(dep, arr),
            'is_popular': is_popular
        }
        all_routes.append(route_info)
        
    # --- 修改：基於合併後的 COMBINED_POPULAR_ROUTES_TUPLES 生成前端熱門列表 --- 
    for dep, arr in COMBINED_POPULAR_ROUTES_TUPLES:
        popular_route_info = {
            'departure': dep,
            'arrival': arr,
            'name': _get_route_name(dep, arr),
        }
        popular_routes.append(popular_route_info)
    # --- 結束修改 --- 
    
    return {
        'all_routes': all_routes,
        'popular_routes': popular_routes
    }