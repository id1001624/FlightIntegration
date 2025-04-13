"""
共享常量模組 - 存儲所有腳本和客戶端共用的常量
"""

# 台灣機場IATA代碼
TAIWAN_AIRPORTS = [
    'TPE',  # 台灣桃園國際機場
    'TSA',  # 台北松山機場
    'KHH',  # 高雄國際機場
    'RMQ',  # 台中國際機場
    'TNN',  # 台南機場
    'HUN',  # 花蓮機場
    'TTT',  # 台東機場
    'KNH',  # 金門機場
    'MZG',  # 馬公機場
    'PIF',  # 屏東機場
    'GNI',  # 綠島機場
    'KYD',  # 蘭嶼機場
    'TXG',  # 台中清泉崗機場
    'CYI',  # 嘉義機場
    'MFK',  # 馬祖北竿機場
    'LZN',  # 馬祖南竿機場
]

# 目標航空公司IATA代碼
TARGET_AIRLINES = [
    # 台灣主要航空公司
    'CI',  # 中華航空
    'BR',  # 長榮航空
    'AE',  # 華信航空
    'B7',  # 立榮航空
    'GE',  # 復興航空
    'ZH',  # 遠東航空
    'JX',  # 星宇航空
    
    # 主要國際航空公司
    'CX',  # 國泰航空
    'KA',  # 國泰港龍航空
    'AY',  # 芬蘭航空
    'CZ',  # 中國南方航空
    'MU',  # 中國東方航空
    'CA',  # 中國國際航空
    'NH',  # 全日空航空
    'JL',  # 日本航空
    'KE',  # 大韓航空
    'OZ',  # 韓亞航空
    'TG',  # 泰國航空
    'SQ',  # 新加坡航空
    'TR',  # 酷航
    'VJ',  # 越捷航空
    'VN',  # 越南航空
    'MH',  # 馬來西亞航空
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