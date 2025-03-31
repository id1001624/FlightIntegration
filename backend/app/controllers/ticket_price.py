"""
票價控制器
處理與票價相關的API請求
"""
from flask import Blueprint, jsonify, request
from ..models import TicketPrice, Flight
from ..services.price_service import PriceService

# 創建藍圖
ticket_price_bp = Blueprint('ticket_price', __name__)

@ticket_price_bp.route('/flight/<string:flight_id>', methods=['GET'])
def get_prices_by_flight(flight_id):
    """獲取特定航班的票價信息"""
    # 獲取請求參數
    class_type = request.args.get('class_type')
    
    # 使用票價服務查詢
    prices = PriceService.get_price_by_flight(flight_id, class_type)
    
    return jsonify(prices)

@ticket_price_bp.route('/lowest', methods=['GET'])
def get_lowest_prices():
    """獲取特定路線和日期範圍的最低票價"""
    # 獲取請求參數
    departure = request.args.get('departure')
    arrival = request.args.get('arrival')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # 驗證必須參數
    if not departure or not arrival or not start_date:
        return jsonify({
            'error': '必須提供出發機場、到達機場和開始日期'
        }), 400
    
    # 使用票價服務查詢
    prices = PriceService.get_lowest_prices(
        departure, arrival, start_date, end_date
    )
    
    # 檢查是否有錯誤
    if isinstance(prices, dict) and 'error' in prices:
        return jsonify(prices), 400
        
    return jsonify(prices)

@ticket_price_bp.route('/history/<string:flight_id>', methods=['GET'])
def get_price_history(flight_id):
    """獲取航班的歷史票價"""
    # 獲取請求參數
    class_type = request.args.get('class_type', '經濟艙')
    days = request.args.get('days', 30)
    
    try:
        days = int(days)
    except ValueError:
        return jsonify({'error': '天數必須是整數'}), 400
    
    # 使用票價服務查詢
    history = PriceService.get_price_history(flight_id, class_type, days)
    
    return jsonify(history)

@ticket_price_bp.route('/analyze/<string:flight_id>', methods=['GET'])
def analyze_price_trend(flight_id):
    """分析票價趨勢並提供購買建議"""
    # 獲取請求參數
    class_type = request.args.get('class_type', '經濟艙')
    
    # 使用票價服務分析
    analysis = PriceService.analyze_price_trend(flight_id, class_type)
    
    return jsonify(analysis) 