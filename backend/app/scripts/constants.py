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
    'CMJ',  # 七美機場
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

# --- 前端熱門航線 --- 

# 根據用戶提供的表格定義前端熱門航線
_fe_tpe_dest = ['HKG', 'NRT', 'HND', 'KIX', 'ICN', 'BKK', 'SIN', 'PVG', 'MNL', 'SGN', 'KUL', 'MFM', 'NGO', 'CTS', 'FUK', 'LAX', 'SFO', 'YVR', 'JFK', 'LHR', 'CDG']
_fe_tsa_dest = ['HKG', 'HND', 'GMP', 'PVG', 'SHA'] # GMP 代表首爾金浦, SHA 代表上海虹橋
_fe_khh_dest = ['HKG', 'BKK', 'NRT', 'KIX', 'ICN', 'MNL', 'SIN', 'MFM']
_fe_rmq_dest = ['HKG', 'MFM', 'SGN']
_fe_hun_dest = ['HKG'] # 花蓮包機

FRONTEND_POPULAR_ROUTES_TUPLES: list[tuple[str, str]] = [
    ("TPE", "NRT"), ("TPE", "KIX"), ("TPE", "ICN"), ("TPE", "SIN"), ("TPE", "BKK"),
    ("TPE", "HKG"), ("TPE", "PVG"), ("TPE", "SFO"), ("TPE", "LAX"), ("TPE", "JFK"),
    ("TSA", "HND"), ("TSA", "GMP"), ("TSA", "SHA"),
    ("RMQ", "HKG"), ("RMQ", "KIX"),
    ("KHH", "NRT"), ("KHH", "KIX"), ("KHH", "ICN"), ("KHH", "HKG"), ("KHH", "SIN")
]

# --- 所有航線資料 ---

# 台灣桃園國際機場 (TPE) 直飛航線
TPE_ROUTES = [
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

# 台北松山機場 (TSA) 直飛航線
TSA_ROUTES = [
    # 日本
    'HND', 'ITM', 'OKA', 'CTS',
    # 韓國
    'GMP', 'ICN',
    # 中國大陸
    'PVG', 'SHA', 'XMN', 'FOC', 'WUH', 'CKG', 'TSN', 'TFU',
    # 港澳
    'HKG',
    # 台灣國內
    'KHH', 'RMQ', 'TNN', 'MZG', 'KNH', 'LZN', 'MFK', 'TTT', 'HUN'
]

# 高雄國際機場 (KHH) 直飛航線
KHH_ROUTES = [
    # 日本
    'NRT', 'KIX', 'FUK', 'OKA', 'KMJ',
    # 韓國
    'ICN', 'GMP', 'PUS',
    # 中國大陸
    'PVG', 'SZX', 'CKG', 'NKG',
    # 港澳
    'HKG', 'MFM',
    # 東南亞
    'BKK', 'SIN', 'MNL', 'KUL', 'BKI',
    # 台灣國內
    'TSA', 'KNH', 'MZG', 'CMJ', 'WOT'
]

# 台中清泉崗機場 (RMQ) 直飛航線
RMQ_ROUTES = [
    # 日本
    'KIX', 'NRT', 'OKA', 'TAK', 'UKB',
    # 韓國
    'ICN', 'PUS',
    # 中國大陸
    'NKG',
    # 港澳
    'HKG', 'MFM',
    # 東南亞
    'SGN', 'HAN', 'DAD', 'PQC',
    # 台灣國內
    'TSA', 'KNH', 'MZG', 'LZN', 'HUN'
]

# 台南機場 (TNN) 直飛航線
TNN_ROUTES = [
    # 台灣國內
    'TSA', 'MZG'
]

# 花蓮機場 (HUN) 直飛航線
HUN_ROUTES = [
    # 港澳
    'HKG',
    # 台灣國內
    'TSA', 'RMQ'
]

# 所有台灣直飛航線元組
ALL_ROUTES_TUPLES = []

# 從 TPE 出發的航線
for dest in TPE_ROUTES:
    if dest not in TAIWAN_AIRPORTS:  # 國際航線
        ALL_ROUTES_TUPLES.append(('TPE', dest))

# 從 TSA 出發的航線
for dest in TSA_ROUTES:
    ALL_ROUTES_TUPLES.append(('TSA', dest))

# 從 KHH 出發的航線
for dest in KHH_ROUTES:
    ALL_ROUTES_TUPLES.append(('KHH', dest))

# 從 RMQ 出發的航線
for dest in RMQ_ROUTES:
    ALL_ROUTES_TUPLES.append(('RMQ', dest))

# 從 TNN 出發的航線
for dest in TNN_ROUTES:
    ALL_ROUTES_TUPLES.append(('TNN', dest))

# 從 HUN 出發的航線
for dest in HUN_ROUTES:
    ALL_ROUTES_TUPLES.append(('HUN', dest))

# 確保熱門航線是所有航線的子集
def ensure_routes_included(routes_to_check, all_routes):
    """確保指定的航線集合是所有航線的子集，若不是則添加"""
    for route in routes_to_check:
        if route not in all_routes:
            all_routes.append(route)

# 確保熱門國內和國際航線都包含在所有航線中
ensure_routes_included(POPULAR_DOMESTIC_ROUTES_TUPLES, ALL_ROUTES_TUPLES)
ensure_routes_included(POPULAR_INTERNATIONAL_ROUTES_TUPLES, ALL_ROUTES_TUPLES)

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
    """取得所有熱門航線（國內+國際）"""
    return POPULAR_DOMESTIC_ROUTES_TUPLES + POPULAR_INTERNATIONAL_ROUTES_TUPLES

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
    
    # 處理所有航線
    for dep, arr in ALL_ROUTES_TUPLES:
        is_popular = is_popular_route(dep, arr)
        route_info = {
            'departure': dep,
            'arrival': arr,
            'name': _get_route_name(dep, arr),
            'is_popular': is_popular
        }
        all_routes.append(route_info)
        
        # 如果是熱門航線，也加入熱門航線列表
        if is_popular:
            # 移除 is_popular 欄位，因為熱門航線列表中所有航線都是熱門的
            popular_route_info = route_info.copy()
            popular_route_info.pop('is_popular', None)
            popular_routes.append(popular_route_info)
    
    return {
        'all_routes': all_routes,
        'popular_routes': popular_routes
    }