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

# 台灣桃園 (TPE) 出發
tpe_destinations = [
    'NRT', 'HND', 'KIX', 'NGO', 'CTS', 'FUK', 'OKA', # 日本
    'ICN', 'PUS', # 韓國
    'PVG', 'PEK', 'CAN', # 中國大陸 (使用 PEK 和 CAN 代表北京、廣州)
    'HKG', # 香港
    'SIN', # 新加坡
    'BKK', 'KUL', 'SGN', 'DPS', 'MNL', # 東南亞
    'SYD', 'MEL', 'BNE', # 澳洲
    'LHR', 'FRA', # 歐洲
    'SFO', 'LAX', 'JFK', 'HNL' # 美國
]

# 台北松山 (TSA) 出發 (僅國際/區域)
tsa_destinations = [
    'HND', 'ITM', 'OKA', 'CTS', # 日本
    'GMP', 'ICN', # 韓國 (GMP, ICN 兩個都有可能，都加入)
    'PVG', 'SHA', # 中國大陸
    'HKG', # 香港
    'BKK', # 泰國
    'KUL', # 馬來西亞
    'MFM'  # 澳門
]

# 高雄 (KHH) 出發
khh_destinations = [
    'NRT', 'KIX', 'FUK', 'OKA', # 日本
    'ICN', # 韓國
    'PVG', # 中國大陸
    'BKK', 'SIN', # 東南亞
    'MFM'  # 澳門 (也加入)
]

# 台中 (RMQ) 出發
rmq_destinations = [
    'KIX', 'NRT', 'OKA', # 日本
    'ICN', # 韓國
    'HKG', 'MFM', 'SGN' # 香港/澳門/越南 (根據用戶之前的定義)
]

POPULAR_INTERNATIONAL_ROUTES_TUPLES = [
    ('TPE', 'NRT'), ('TPE', 'KIX'), ('TPE', 'ICN'), ('TPE', 'HKG'),
    ('TPE', 'SIN'), ('TPE', 'BKK'), ('TPE', 'LAX'), ('TPE', 'SFO'),
    ('TPE', 'JFK'), ('TPE', 'HNL'),
    ('TSA', 'HND'), ('TSA', 'ITM'), ('TSA', 'OKA'), ('TSA', 'CTS'),
    ('TSA', 'GMP'), ('TSA', 'ICN'), ('TSA', 'PVG'), ('TSA', 'SHA'),
    ('KHH', 'NRT'), ('KHH', 'KIX'), ('KHH', 'ICN'), ('KHH', 'HKG'),
    ('RMQ', 'KIX'), ('RMQ', 'NRT'), ('RMQ', 'OKA'), ('RMQ', 'ICN'),
    ('RMQ', 'HKG'), ('RMQ', 'MFM'), ('RMQ', 'SGN')
]

# 熱門國內航線 (字典格式，用於 API 回應)
# 注意：POPULAR_DOMESTIC_ROUTES_DICTS 應在需要它的 API 端點中動態生成，
# 因為它需要查詢 airport_names。Constants 檔案不應執行數據庫查詢。
# POPULAR_DOMESTIC_ROUTES_DICTS = []
# for dep, arr in POPULAR_DOMESTIC_ROUTES_TUPLES:
#     dep_name = airport_names.get(dep, dep)
#     arr_name = airport_names.get(arr, arr)
#     # 簡化台北名稱
#     if dep in ['TPE', 'TSA']: dep_name = '台北'
#     POPULAR_DOMESTIC_ROUTES_DICTS.append({'departure': dep, 'arrival': arr, 'name': f"{dep_name}-{arr_name}"})

# 熱門國際航線 (字典格式，用於 API 回應)
# 注意：POPULAR_INTERNATIONAL_ROUTES_DICTS 應在需要它的 API 端點中動態生成，
# 因為它需要查詢 airport_names。Constants 檔案不應執行數據庫查詢。
# POPULAR_INTERNATIONAL_ROUTES_DICTS = [
#     {'departure': dep, 'arrival': arr, 'name': _get_route_name(dep, arr)}
#     for dep, arr in POPULAR_INTERNATIONAL_ROUTES_TUPLES
# ]

# --- 新增：專門給前端使用的熱門航線列表 --- 

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

# FRONTEND_POPULAR_ROUTES_DICTS: list[dict[str, str]] = [
#     {"departure": dep, "arrival": arr, "departure_name": airport_names.get(dep, dep), "arrival_name": airport_names.get(arr, arr)}
#     for dep, arr in FRONTEND_POPULAR_ROUTES_TUPLES
# ]
# 注意：FRONTEND_POPULAR_ROUTES_DICTS 應在需要它的 API 端點中動態生成，
# 因為它需要查詢 airport_names。Constants 檔案不應執行數據庫查詢。

# --- 結束新增 ---