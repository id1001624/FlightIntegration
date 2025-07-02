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

# --- 常量定義 ---

# --- 調整後：只保留有穩定國際航班的台灣機場 ---
TAIWAN_AIRPORTS = [
    'TPE',  # 台灣桃園國際機場
    'TSA',  # 台北松山機場
    'KHH',  # 高雄國際機場
    'RMQ',  # 台中清泉崗機場
]

# 台北機場IATA代碼
TAIPEI_AIRPORTS = ['TPE', 'TSA']

# --- 調整後：統一的航空公司代碼 (移除國內線為主的航空公司) ---
AIRLINE_CODES = [
    "CI",  # 中華航空
    "BR",  # 長榮航空
    "AE",  # 華信航空
    "JX",  # 星宇航空
    "CX",  # 國泰航空
    "SQ",  # 新加坡航空
    "JL",  # 日本航空
    "NH",  # 全日空航空
    "KE",  # 大韓航空
    "OZ",  # 韓亞航空
    "IT",  # 台灣虎航
    "TR",  # 酷航
    "AK",  # 亞洲航空
    "TW",  # 德威航空
    "GK",  # 捷星日本航空
    "NX",  # 澳門航空
    "MF",  # 廈門航空
    "MU"   # 中國東方航空
]

# 常用時間格式 (移除舊註解)
DATETIME_FORMATS = [
    '%Y-%m-%dT%H:%M:%S.%f',  # ISO格式帶毫秒
    '%Y-%m-%dT%H:%M:%S',     # ISO格式
    '%Y-%m-%dT%H:%M',        # ISO格式不帶秒
    '%Y-%m-%d %H:%M:%S',     # 標準格式
    '%Y-%m-%d %H:%M',        # 標準格式不帶秒
]

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

# Amadeus API 相關配置
AMADEUS_API_CONFIG = {
    'base_url': 'https://test.api.amadeus.com',
    'token_url': '/v1/security/oauth2/token'
}

# --- 調整後：專注於國際航線 ---

# 輔助函數：生成航線名稱
def _get_route_name(dep, arr):
    airport_names = {
        'TPE': '台北桃園', 'TSA': '台北松山', 'KHH': '高雄', 'RMQ': '台中', 'HUN': '花蓮',
        'NRT': '東京成田', 'HND': '東京羽田', 'KIX': '大阪關西', 'ICN': '首爾仁川', 'HKG': '香港',
        'BKK': '曼谷', 'SIN': '新加坡', 'PVG': '上海浦東', 'MNL': '馬尼拉', 'SGN': '胡志明市',
        'KUL': '吉隆坡', 'MFM': '澳門', 'NGO': '名古屋', 'CTS': '札幌', 'FUK': '福岡',
        'LAX': '洛杉磯', 'SFO': '舊金山', 'YVR': '溫哥華', 'JFK': '紐約JFK', 'LHR': '倫敦希斯洛',
        'CDG': '巴黎戴高樂', 'PUS': '釜山', 'OKA': '沖繩', 'GMP': '首爾金浦', 'SHA': '上海虹橋',
        'DPS': '峇里島', 'DAD': '峴港', 'CNX': '清邁', 'ITM': '大阪伊丹', 'DMK': '曼谷廊曼',
        'CAN': '廣州', 'PEK': '北京', 'HAN': '河內', 'PEN': '檳城', 'CGK': '雅加達', 'CEB': '宿霧',
        'SEA': '西雅圖', 'AMS': '阿姆斯特丹', 'FRA': '法蘭克福', 'BNE': '布里斯本', 'MEL': '墨爾本',
        'SYD': '悉尼', 'HNL': '檀香山', 'SZX': '深圳', 'XMN': '廈門', 'FOC': '福州', 'WUH': '武漢',
        'CKG': '重慶', 'TSN': '天津', 'NKG': '南京', 'TAO': '青島', 'NGB': '寧波',
        'TFU': '成都', 'KMJ': '熊本', 'PQC': '富國島', 'UKB': '神戶', 'TAK': '高松',
        'CJU': '濟州', 'BKI': '亞庇', 'SDJ': '仙台', 'KMQ': '小松', 'OKJ': '岡山',
        'HKD': '函館', 'HSG': '佐賀', 'HKT': '普吉', 'HNA': '花卷', 'KIJ': '新潟',
        'KMI': '宮崎', 'AXT': '秋田', 'IBR': '茨城', 'KCZ': '高知', 'OIT': '大分',
        'FKS': '福島', 'AKJ': '旭川', 'PNH': '金邊', 'NGS': '長崎', 'SPK': '札幌'
    }
    dep_name = airport_names.get(dep, dep)
    arr_name = airport_names.get(arr, arr)
    if dep in ['TPE', 'TSA']: dep_name = '台北'
    return f"{dep_name}-{arr_name}"

# 1. 熱門國際航線
POPULAR_ROUTES_TUPLES = [
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
    ('RMQ', 'OKA'), ('RMQ', 'ICN')
]

# 2. 所有國際航線目的地
TPE_INTERNATIONAL_DESTINATIONS = [
    'NRT', 'HND', 'KIX', 'NGO', 'CTS', 'FUK', 'OKA', 'SDJ', 'ICN', 'PUS', 'CJU',
    'PVG', 'PEK', 'CAN', 'NKG', 'NGB', 'TAO', 'WUH', 'SZX', 'TFU', 'HKG', 'MFM',
    'SIN', 'BKK', 'KUL', 'SGN', 'DPS', 'MNL', 'HAN', 'CNX', 'PNH', 'CGK', 'PEN', 'DAD', 'HKT',
    'SYD', 'MEL', 'BNE', 'LHR', 'FRA', 'CDG', 'AMS', 'SFO', 'LAX', 'JFK', 'HNL', 'SEA', 'YVR'
]
TSA_INTERNATIONAL_DESTINATIONS = ['HND', 'HKG', 'GMP', 'PVG', 'SHA', 'ITM', 'OKA', 'CTS', 'ICN']
KHH_INTERNATIONAL_DESTINATIONS = ['HKG', 'BKK', 'NRT', 'KIX', 'ICN', 'MNL', 'SIN', 'MFM']
RMQ_INTERNATIONAL_DESTINATIONS = ['HKG', 'MFM', 'SGN', 'KIX', 'NRT', 'OKA', 'ICN']

# 3. 創建所有國際航線元組
ALL_ROUTES_TUPLES = []
ALL_ROUTES_TUPLES.extend([('TPE', dest) for dest in TPE_INTERNATIONAL_DESTINATIONS])
ALL_ROUTES_TUPLES.extend([('TSA', dest) for dest in TSA_INTERNATIONAL_DESTINATIONS])
ALL_ROUTES_TUPLES.extend([('KHH', dest) for dest in KHH_INTERNATIONAL_DESTINATIONS])
ALL_ROUTES_TUPLES.extend([('RMQ', dest) for dest in RMQ_INTERNATIONAL_DESTINATIONS])



# 4. 確保熱門航線包含在內 (作為安全檢查)
def ensure_routes_included(routes_to_check, all_routes):
    """確保指定的航線集合是所有航線的子集，若不是則添加"""  
    for route in routes_to_check:
        if route not in all_routes:
            logger.warning(f"警告：熱門航線 {route} 未包含在 ALL_ROUTES_TUPLES 中，已自動添加。請檢查定義。")
            all_routes.append(route)

ensure_routes_included(POPULAR_ROUTES_TUPLES, ALL_ROUTES_TUPLES)
ALL_ROUTES_TUPLES = sorted(list(set(ALL_ROUTES_TUPLES))) # 最終排序和去重

# --- API 查詢與前端顯示輔助函數 ---

def is_popular_route(departure, arrival):
    """判斷一個航線是否為熱門航線"""
    return (departure, arrival) in POPULAR_ROUTES_TUPLES

def get_all_direct_routes():
    """取得所有直飛航線"""
    return ALL_ROUTES_TUPLES

def get_popular_routes():
    """取得所有熱門航線"""
    return POPULAR_ROUTES_TUPLES

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
    
    popular_set = set(POPULAR_ROUTES_TUPLES)
    
    for dep, arr in ALL_ROUTES_TUPLES:
        is_popular = (dep, arr) in popular_set
        route_info = {
            'departure': dep,
            'arrival': arr,
            'name': _get_route_name(dep, arr),
            'is_popular': is_popular
        }
        all_routes.append(route_info)
        
    for dep, arr in POPULAR_ROUTES_TUPLES:
        popular_route_info = {
            'departure': dep,
            'arrival': arr,
            'name': _get_route_name(dep, arr),
        }
        popular_routes.append(popular_route_info)
    
    return {
        'all_routes': all_routes,
        'popular_routes': popular_routes
    }