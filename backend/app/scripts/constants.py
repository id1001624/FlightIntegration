"""
共享常量模組 - 存儲所有腳本和客戶端共用的常量
"""

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
]

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

# API返回的航班狀態代碼翻譯
FLIGHT_STATUS_TRANSLATIONS = {
    # FlightStats狀態代碼
    'A': '活躍',     # Active
    'C': '取消',     # Canceled
    'D': '改航',     # Diverted
    'DN': '改航',    # Diverted
    'L': '已降落',   # Landed
    'NO': '未運營',  # Not Operational
    'R': '重定向',   # Redirected
    'S': '計劃',     # Scheduled
    'U': '未知',     # Unknown
    
    # TDX狀態代碼/文字
    'CANCELLED': '取消',
    'DELAYED': '延誤',
    'ARRIVED': '已抵達',
    'DEPARTED': '已起飛',
    'SCHEDULED': '計劃',
    'UNKNOWN': '未知',
    'LANDING': '著陸中',
    'TAKE-OFF': '起飛中',
    'BOARDING': '登機中',
    'CHECK-IN': '報到中',
}

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
        'CDG': '巴黎戴高樂', 'MZG': '澎湖', 'TTT':'台東', 'KNH':'金門', 'TNN':'台南'}
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

# 熱門國際航線 (元組格式，用於內部邏輯如 sync_manager) - 根據用戶提供更新
# TPE 出發
_tpe_destinations = ['HKG', 'NRT', 'HND', 'KIX', 'ICN', 'BKK', 'SIN', 'PVG', 'MNL', 'SGN', 'KUL', 'MFM', 'NGO', 'CTS', 'FUK', 'LAX', 'SFO', 'YVR', 'JFK', 'LHR', 'CDG']
# TSA 出發 (精簡)
_tsa_destinations = ['HND', 'PVG', 'HKG', 'ICN'] # 假設松山主要飛這些
# KHH 出發
_khh_destinations = ['HKG', 'BKK', 'NRT', 'KIX', 'ICN', 'MNL', 'SIN', 'MFM']
# RMQ 出發
_rmq_destinations = ['HKG', 'MFM', 'SGN']
# HUN 出發 (包機為主，可選)
_hun_destinations = ['HKG']

POPULAR_INTERNATIONAL_ROUTES_TUPLES = []
POPULAR_INTERNATIONAL_ROUTES_TUPLES.extend([('TPE', dest) for dest in _tpe_destinations])
POPULAR_INTERNATIONAL_ROUTES_TUPLES.extend([('TSA', dest) for dest in _tsa_destinations])
POPULAR_INTERNATIONAL_ROUTES_TUPLES.extend([('KHH', dest) for dest in _khh_destinations])
POPULAR_INTERNATIONAL_ROUTES_TUPLES.extend([('RMQ', dest) for dest in _rmq_destinations])
# POPULAR_INTERNATIONAL_ROUTES_TUPLES.extend([('HUN', dest) for dest in _hun_destinations]) # 暫不包含花蓮包機

# 熱門國內航線 (字典格式，用於 API 回應)
POPULAR_DOMESTIC_ROUTES_DICTS = [
    {'departure': dep, 'arrival': arr, 'name': _get_route_name(dep, arr)}
    for dep, arr in POPULAR_DOMESTIC_ROUTES_TUPLES
]

# 熱門國際航線 (字典格式，用於 API 回應)
POPULAR_INTERNATIONAL_ROUTES_DICTS = [
    {'departure': dep, 'arrival': arr, 'name': _get_route_name(dep, arr)}
    for dep, arr in POPULAR_INTERNATIONAL_ROUTES_TUPLES
]