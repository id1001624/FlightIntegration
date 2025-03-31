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

@flight_bp.route('/search', methods=['GET'])
def search_flights():
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
    
    # 驗證必須參數
    if not departure or not arrival or not departure_date:
        return jsonify({
            'error': '必須提供出發機場、到達機場和出發日期'
        }), 400
    
    # 處理航空公司參數
    airlines = None
    if airlines_str:
        airlines = airlines_str.split(',')
    
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
    
    # 使用搜索服務進行查詢
    result = SearchService.search_flights(
        departure, arrival, departure_date, return_date,
        airlines, price_min, price_max, class_type
    )
    
    # 檢查是否有錯誤
    if 'error' in result:
        return jsonify(result), 400
        
    return jsonify(result)

@flight_bp.route('/<string:flight_id>', methods=['GET'])
def get_flight_details(flight_id):
    """獲取航班詳細信息"""
    # 查詢航班
    flight = Flight.get_by_id(flight_id)
    
    if not flight:
        return jsonify({'error': '找不到該航班'}), 404
    
    # 格式化結果
    result = {
        'flight_id': str(flight.flight_id),
        'flight_number': flight.flight_number,
        'airline': {
            'id': str(flight.airline.airline_id),
            'code': flight.airline.iata_code,
            'name': flight.airline.name_zh
        },
        'departure': {
            'airport_id': str(flight.departure_airport.airport_id),
            'code': flight.departure_airport.iata_code,
            'name': flight.departure_airport.name_zh,
            'city': flight.departure_airport.city,
            'country': flight.departure_airport.country,
            'time': flight.scheduled_departure.isoformat()
        },
        'arrival': {
            'airport_id': str(flight.arrival_airport.airport_id),
            'code': flight.arrival_airport.iata_code,
            'name': flight.arrival_airport.name_zh,
            'city': flight.arrival_airport.city,
            'country': flight.arrival_airport.country,
            'time': flight.scheduled_arrival.isoformat()
        },
        'status': flight.status,
        'duration': str(flight.duration) if flight.duration else None,
        'is_domestic': flight.is_domestic
    }
    
    # 獲取票價
    prices = []
    for price in flight.ticket_prices:
        prices.append({
            'class_type': price.class_type,
            'price': float(price.base_price),
            'available_seats': price.available_seats,
            'updated_at': price.price_updated_at.isoformat() if price.price_updated_at else None
        })
    
    result['prices'] = prices
    
    return jsonify(result)

@flight_bp.route('/airlines', methods=['GET'])
@cache.cached(timeout=3600)  # 緩存1小時
def get_available_airlines():
    """獲取所有可用的航空公司列表，用於篩選條件"""
    airlines = SearchService.get_available_airlines()
    return jsonify(airlines)

@flight_bp.route('/taiwan-airports', methods=['GET'])
@cache.cached(timeout=7200)  # 緩存2小時
def get_taiwan_airports():
    """獲取台灣所有機場列表，用於出發地選項"""
    airports = SearchService.get_taiwan_airports()
    return jsonify(airports)

@flight_bp.route('/destinations/<string:departure_iata>', methods=['GET'])
def get_available_destinations(departure_iata):
    """獲取從指定出發地可以到達的所有目的地"""
    destinations = SearchService.get_available_destinations(departure_iata)
    return jsonify(destinations)

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