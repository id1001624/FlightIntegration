"""
航班控制器
處理與航班相關的API請求
"""
from flask import Blueprint, jsonify, request, current_app
from ..models import Flight, Airport, Airline
from ..services.search_service import SearchService
from ..services.data_sync_service import DataSyncService
from .. import cache

# 創建藍圖
flight_bp = Blueprint('flight', __name__)

# 台灣機場列表
TAIWAN_AIRPORTS = ['TPE', 'TSA', 'RMQ', 'KHH', 'TNN', 'CYI', 'HUN', 'TTT', 'KNH', 'MZG', 'LZN', 'MFK', 'KYD', 'GNI', 'WOT', 'CMJ']

# 目標航空公司列表
TARGET_AIRLINES = ['AE', 'B7', 'BR', 'CI', 'CX', 'DA', 'IT', 'JL', 'JX', 'OZ']

@flight_bp.route('/search', methods=['GET'])
async def search_flights():
    """
    搜索航班
    
    查詢參數:
        departure: 出發機場IATA代碼 (必須)
        arrival: 到達機場IATA代碼 (必須)
        date: 出發日期 YYYY-MM-DD格式 (必須)
        return_date: 返回日期 YYYY-MM-DD格式 (可選)
        airlines: 航空公司IATA代碼列表，逗號分隔 (可選)
        price_min: 最低價格 (可選)
        price_max: 最高價格 (可選)
        class_type: 艙位類型 (可選，默認為經濟)
        only_target_airlines: 是否只顯示指定航空公司 (可選，默認為true)
    """
    # 獲取請求參數
    departure = request.args.get('departure')
    arrival = request.args.get('arrival')
    departure_date = request.args.get('date')
    return_date = request.args.get('return_date')
    airlines_str = request.args.get('airlines')
    price_min = request.args.get('price_min')
    price_max = request.args.get('price_max')
    class_type = request.args.get('class_type', '經濟')
    only_target_airlines = request.args.get('only_target_airlines', 'true').lower() == 'true'
    
    # 驗證必須參數
    if not departure or not arrival or not departure_date:
        return jsonify({
            'error': '必須提供出發機場、到達機場和出發日期'
        }), 400
    
    # 處理航空公司參數
    airlines = None
    if airlines_str:
        airlines = airlines_str.split(',')
    elif only_target_airlines:
        airlines = TARGET_AIRLINES.copy()
    
    # 處理價格範圍
    try:
        if price_min:
            price_min = float(price_min)
        if price_max:
            price_max = float(price_max)
    except ValueError:
        return jsonify({
            'error': '價格必須是數字'
        }), 400
    
    # 創建 SearchService 實例
    search_service = SearchService()
    
    # 使用搜索服務進行查詢，加上 await 關鍵字
    result = await search_service.search_flights(
        departure, arrival, departure_date, 
        airlines, return_date,
        price_min, price_max, class_type
    )
    
    # 檢查是否有錯誤
    if 'error' in result:
        return jsonify(result), 400
        
    return jsonify(result)

@flight_bp.route('/from_taiwan/<string:arrival_iata>', methods=['GET'])
async def flights_from_taiwan(arrival_iata):
    """
    獲取從台灣飛往指定目的地的航班
    
    查詢參數:
        date: 出發日期 YYYY-MM-DD格式 (必須)
        airlines: 航空公司IATA代碼列表，逗號分隔 (可選)
        price_min: 最低價格 (可選)
        price_max: 最高價格 (可選)
        class_type: 艙位類型 (可選，默認為經濟)
    """
    # 獲取請求參數
    departure_date = request.args.get('date')
    airlines_str = request.args.get('airlines')
    price_min = request.args.get('price_min')
    price_max = request.args.get('price_max')
    class_type = request.args.get('class_type', '經濟')
    
    # 驗證必須參數
    if not departure_date:
        return jsonify({
            'error': '必須提供出發日期'
        }), 400
    
    # 處理航空公司參數
    airlines = None
    if airlines_str:
        airlines = airlines_str.split(',')
    else:
        airlines = TARGET_AIRLINES.copy()
    
    # 處理價格範圍
    try:
        if price_min:
            price_min = float(price_min)
        if price_max:
            price_max = float(price_max)
    except ValueError:
        return jsonify({
            'error': '價格必須是數字'
        }), 400
    
    # 創建 SearchService 實例
    search_service = SearchService()
    
    # 整合所有台灣機場出發的航班
    all_flights = []
    for departure in TAIWAN_AIRPORTS:
        # 只需要考慮幾個主要機場，提高效率
        if departure not in ['TPE', 'TSA', 'KHH', 'RMQ', 'TNN']:
            continue
            
        # 獲取航班
        flights = await search_service.search_flights(
            departure, arrival_iata, departure_date, 
            airlines, None,
            price_min, price_max, class_type
        )
        
        # 檢查結果是否有效
        if 'data' in flights and 'flights' in flights['data']:
            all_flights.extend(flights['data']['flights'])
    
    # 排序航班（按價格和時間）
    all_flights.sort(key=lambda x: (x.get('lowest_price', float('inf')), x.get('departure_time', '')))
    
    result = {
        'data': {
            'flights': all_flights,
            'total': len(all_flights)
        }
    }
    
    return jsonify(result)

@flight_bp.route('/<string:flight_id>', methods=['GET'])
async def get_flight_details(flight_id):
    """獲取航班詳細信息"""
    # 查詢航班
    from app.database.db import get_db, release_db
    
    db = await get_db()
    try:
        # 使用 asyncpg 直接查詢
        query = """
        SELECT 
            f.flight_id, 
            f.flight_number, 
            f.scheduled_departure, 
            f.scheduled_arrival, 
            f.status,
            al.is_domestic,
            a_dep.airport_id as departure_id, 
            a_dep.name_zh as departure_name,
            a_dep.city as departure_city,
            a_dep.country as departure_country,
            a_arr.airport_id as arrival_id, 
            a_arr.name_zh as arrival_name,
            a_arr.city as arrival_city,
            a_arr.country as arrival_country,
            al.airline_id, 
            al.name_zh as airline_name
        FROM 
            flights f
        JOIN 
            airports a_dep ON f.departure_airport_id = a_dep.airport_id
        JOIN 
            airports a_arr ON f.arrival_airport_id = a_arr.airport_id
        JOIN 
            airlines al ON f.airline_id = al.airline_id
        WHERE 
            f.flight_id = $1
        """
        
        flight = await db.fetchrow(query, flight_id)
        
        if not flight:
            return jsonify({'error': '找不到該航班'}), 404
        
        # 格式化結果
        result = {
            'flight_id': flight['flight_id'],
            'flight_number': flight['flight_number'],
            'airline': {
                'id': flight['airline_id'],
                'code': flight['airline_id'],
                'name': flight['airline_name']
            },
            'departure': {
                'airport_id': flight['departure_id'],
                'code': flight['departure_id'],
                'name': flight['departure_name'],
                'city': flight['departure_city'],
                'country': flight['departure_country'],
                'time': flight['scheduled_departure'].isoformat()
            },
            'arrival': {
                'airport_id': flight['arrival_id'],
                'code': flight['arrival_id'],
                'name': flight['arrival_name'],
                'city': flight['arrival_city'],
                'country': flight['arrival_country'],
                'time': flight['scheduled_arrival'].isoformat()
            },
            'status': flight['status'],
            'is_domestic': flight['is_domestic']
        }
        
        # 計算飛行時間
        try:
            dep_time = flight['scheduled_departure']
            arr_time = flight['scheduled_arrival']
            duration_minutes = int((arr_time - dep_time).total_seconds() / 60)
            result['duration'] = str(duration_minutes) + " 分鐘"
        except:
            result['duration'] = None
        
        # 獲取票價
        price_query = """
        SELECT 
            class_type, 
            base_price, 
            available_seats, 
            price_updated_at 
        FROM 
            ticket_prices 
        WHERE 
            flight_id = $1
        """
        
        prices_rows = await db.fetch(price_query, flight_id)
        prices = []
        
        for price in prices_rows:
            prices.append({
                'class_type': price['class_type'],
                'price': float(price['base_price']),
                'available_seats': price['available_seats'],
                'updated_at': price['price_updated_at'].isoformat() if price['price_updated_at'] else None
            })
        
        result['prices'] = prices
        
        return jsonify(result)
    finally:
        await release_db(db)

@flight_bp.route('/airlines', methods=['GET'])
@cache.cached(timeout=3600)  # 緩存1小時
async def get_available_airlines():
    """獲取所有可用的航空公司列表，用於篩選條件"""
    search_service = SearchService()
    airlines = await search_service.get_available_airlines()
    
    # 標記目標航空公司
    for airline in airlines:
        airline['is_target'] = airline.get('airline_id') in TARGET_AIRLINES
        
    return jsonify(airlines)

@flight_bp.route('/taiwan-airports', methods=['GET'])
async def get_taiwan_airports_api():
    """
    獲取台灣所有有航班的機場列表，用於出發地選項
    
    查詢參數:
        date: 出發日期 YYYY-MM-DD格式 (可選)，如提供將只返回該日期有航班的機場
    """
    try:
        date_str = request.args.get('date')
        search_service = SearchService()
        airports = await search_service.get_taiwan_airports()
        
        # 調試輸出
        app = current_app
        app.logger.info(f"獲取台灣機場成功，找到 {len(airports)} 個機場")
        
        return jsonify(airports)
    except Exception as e:
        current_app.logger.error(f"獲取台灣機場失敗: {str(e)}", exc_info=True)
        return jsonify({'error': f'獲取台灣機場失敗: {str(e)}'}), 500

@flight_bp.route('/<string:departure_code>/destinations', methods=['GET'])
@cache.cached(timeout=3600, query_string=True)  # 緩存1小時，考慮查詢參數
async def get_available_destinations(departure_code):
    """
    獲取從指定出發地可以到達的所有目的地
    
    路徑參數:
        departure_code: 出發地機場IATA代碼
    
    查詢參數:
        date: 日期 YYYY-MM-DD格式 (可選)，如提供將只返回該日期有航班的目的地
    """
    date_str = request.args.get('date')
    search_service = SearchService()
    destinations = await search_service.get_available_destinations(departure_code, date_str)
    return jsonify(destinations)

@flight_bp.route('/airports/<string:departure_code>/departures', methods=['GET'])
@cache.cached(timeout=3600, query_string=True)  # 緩存1小時，考慮查詢參數
async def get_airport_departures(departure_code):
    """
    獲取從指定出發地在特定日期出發的所有航班
    
    路徑參數:
        departure_code: 出發地機場IATA代碼
    
    查詢參數:
        date: 日期 YYYY-MM-DD格式 (必須)
    """
    date_str = request.args.get('date')
    
    if not date_str:
        return jsonify({'error': '必須提供日期參數'}), 400
        
    search_service = SearchService()
    destinations = await search_service.get_available_destinations(departure_code, date_str)
    return jsonify(destinations)

@flight_bp.route('/popular-routes', methods=['GET'])
@cache.cached(timeout=3600)  # 緩存1小時
def get_popular_routes():
    """獲取熱門航線列表"""
    # 台灣國內熱門航線
    domestic_routes = [
        {'departure': 'TPE', 'arrival': 'KHH', 'name': '台北-高雄'},
        {'departure': 'TSA', 'arrival': 'KHH', 'name': '台北-高雄'},
        {'departure': 'TSA', 'arrival': 'RMQ', 'name': '台北-台中'},
        {'departure': 'TSA', 'arrival': 'TNN', 'name': '台北-台南'},
        {'departure': 'TSA', 'arrival': 'MZG', 'name': '台北-澎湖'},
        {'departure': 'TSA', 'arrival': 'HUN', 'name': '台北-花蓮'},
        {'departure': 'TSA', 'arrival': 'KNH', 'name': '台北-金門'}
    ]
    
    # 國際熱門航線
    international_routes = [
        {'departure': 'TPE', 'arrival': 'NRT', 'name': '台北-東京成田'},
        {'departure': 'TPE', 'arrival': 'HND', 'name': '台北-東京羽田'},
        {'departure': 'TPE', 'arrival': 'KIX', 'name': '台北-大阪'},
        {'departure': 'TPE', 'arrival': 'ICN', 'name': '台北-首爾'},
        {'departure': 'TPE', 'arrival': 'HKG', 'name': '台北-香港'},
        {'departure': 'TPE', 'arrival': 'BKK', 'name': '台北-曼谷'},
        {'departure': 'TPE', 'arrival': 'SIN', 'name': '台北-新加坡'},
        {'departure': 'TPE', 'arrival': 'MNL', 'name': '台北-馬尼拉'}
    ]
    
    return jsonify({
        'domestic': domestic_routes,
        'international': international_routes
    })

@flight_bp.route('/sync-taiwan-flights', methods=['POST'])
def sync_taiwan_flights():
    """同步台灣出發的航班數據"""
    # 獲取請求參數
    data = request.json or {}
    date = data.get('date')
    days = data.get('days', 1)
    
    if not date:
        return jsonify({'error': '必須提供日期參數'}), 400
    
    # 初始化同步服務
    sync_service = DataSyncService()
    
    # 執行同步
    try:
        result = sync_service.sync_taiwan_flights(date, days)
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"同步台灣航班失敗: {str(e)}")
        return jsonify({'error': f'同步失敗: {str(e)}'}), 500

@flight_bp.route('/generate-test-data', methods=['POST'])
def generate_test_data():
    """生成測試數據"""
    # 獲取請求參數
    data = request.json
    
    if not data:
        return jsonify({'error': '缺少請求數據'}), 400
        
    departure_iata = data.get('departure')
    arrival_iata = data.get('arrival')
    start_date = data.get('start_date')
    num_days = data.get('num_days', 30)
    flights_per_day = data.get('flights_per_day', 5)
    
    # 驗證必須參數
    if not departure_iata or not arrival_iata or not start_date:
        return jsonify({
            'error': '必須提供出發機場、到達機場和開始日期'
        }), 400
    
    # 使用數據同步服務生成測試數據
    result = DataSyncService.generate_test_data(
        departure_iata, arrival_iata, start_date, num_days, flights_per_day
    )
    
    # 檢查是否有錯誤
    if 'error' in result:
        return jsonify(result), 400
        
    return jsonify(result)