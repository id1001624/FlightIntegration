from flask import Blueprint, request, jsonify, current_app
from app.services import flight_service, price_service, prediction_service
from app.utils.api_helper import api_response
from datetime import datetime
import logging

# 設置日誌
logger = logging.getLogger(__name__)

# 建立航班相關API藍圖
flight_bp = Blueprint('flight', __name__, url_prefix='/api/flights')

# 不再需要在控制器中初始化服務
# flight_service = None
# price_service = None
# prediction_service = None

# @flight_bp.before_app_first_request
# def setup_services():
#     global flight_service, price_service, prediction_service
#     test_mode = current_app.config.get('TESTING', False)
#     flight_service = FlightService(test_mode=test_mode)
#     price_service = PriceService(test_mode=test_mode)
#     prediction_service = PredictionService(test_mode=test_mode)

@flight_bp.route('/search', methods=['GET'])
def search_flights():
    """搜尋航班API"""
    # 解析請求參數
    departure_airport = request.args.get('departure_airport')
    arrival_airport = request.args.get('arrival_airport')
    departure_date = request.args.get('departure_date')
    return_date = request.args.get('return_date')
    airline = request.args.get('airline_code')
    sort_by = request.args.get('sort_by', 'departure_time')
    
    # 獲取用戶ID (如果有)
    user_id = request.args.get('user_id')
    token = request.headers.get('Authorization')
    
    if token and not user_id:
        # 去掉Bearer前綴
        if token.startswith('Bearer '):
            token = token[7:]
        
        from app.services import auth_service
        success, result = auth_service.verify_token(token)
        
        if success:
            user_id = result
    
    # 調用服務層方法
    result = flight_service.search_flights(
        departure_airport=departure_airport,
        arrival_airport=arrival_airport,
        departure_date=departure_date,
        return_date=return_date,
        airline=airline,
        sort_by=sort_by,
        user_id=user_id
    )
    
    if not result['success']:
        return api_response(False, message=result.get('message', '搜索航班失敗'), status_code=400)
    
    return api_response(True, data=result.get('data'))

@flight_bp.route('/<flight_id>', methods=['GET'])
def get_flight_details(flight_id):
    """獲取航班詳細資訊API"""
    result = flight_service.get_flight_details(flight_id)
    
    if not result['success']:
        return api_response(False, message=result.get('message', '獲取航班詳情失敗'), status_code=404)
    
    return api_response(True, data=result.get('data'))

@flight_bp.route('/status/update', methods=['POST'])
def update_flight_status():
    """更新航班狀態API - 管理員功能"""
    force_update = request.json.get('force_update', False)
    result = flight_service.update_flight_status(force_update=force_update)
    
    if not result['success']:
        return api_response(False, message=result.get('message', '更新航班狀態失敗'), status_code=500)
    
    return api_response(True, data=result.get('data'), message=result.get('message', '更新航班狀態成功'))

@flight_bp.route('/<flight_id>/price-trend', methods=['GET'])
def analyze_price_trend(flight_id):
    """分析票價趨勢API"""
    class_type = request.args.get('class_type', '經濟')
    result = price_service.analyze_price_trend(flight_id, class_type)
    
    if not result['success']:
        return api_response(False, message=result.get('message', '分析票價趨勢失敗'), status_code=404)
    
    return api_response(True, data=result.get('data'))

@flight_bp.route('/delays/predict', methods=['GET'])
def predict_flight_delays():
    """預測航班延誤API"""
    airport_code = request.args.get('airport_code')
    date = request.args.get('date')
    
    result = prediction_service.predict_flight_delays(airport_code, date)
    
    if not result['success']:
        return api_response(False, message=result.get('message', '預測航班延誤失敗'), status_code=500)
    
    return api_response(True, data=result.get('data'))