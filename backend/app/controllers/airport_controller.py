"""
機場控制器
處理與機場相關的API請求
"""
from flask import Blueprint, jsonify, request, current_app
from ..models import Airport, Flight
from ..models.base import db
from ..services.airport_service import AirportService  # 使用新的服務
from .. import cache
from sqlalchemy import distinct
from werkzeug.exceptions import NotFound

# 輔助函數，用於生成標準回應
def _success_response(data):
    return jsonify({'success': True, 'data': data})

def _error_response(message, status_code):
    if status_code >= 500:
        current_app.logger.error(f"Server Error ({status_code}): {message}")
    else:
        current_app.logger.warning(f"Client Error ({status_code}): {message}")
    return jsonify({'success': False, 'message': message}), status_code

# 創建藍圖
airport_bp = Blueprint('airport', __name__)

@airport_bp.route('/', methods=['GET'])
# @cache.cached(timeout=7200)  # 緩存2小時 - 暫時註解以進行調試
async def get_airports():
    """獲取所有機場，並為台灣機場附加活躍度分數"""
    try:
        # 使用新的 AirportService 方法
        # 可以考慮從請求參數獲取 days_ahead，如果需要更靈活的配置
        days_ahead_param = request.args.get('days_ahead', default=7, type=int)
        airports = await AirportService.get_all_airports_with_activity(days_ahead=days_ahead_param)
        return _success_response(airports)
    except Exception as e:
        current_app.logger.error(f"獲取所有機場列表（含活躍度）失敗: {e}", exc_info=True)
        return _error_response('獲取機場列表時發生內部錯誤', 500)

@airport_bp.route('/taiwan', methods=['GET'])
@cache.cached(timeout=7200)  # 緩存2小時
async def get_taiwan_airports():
    """獲取台灣所有機場"""
    try:
        # 使用新的 AirportService，並調用正確的方法
        airports = await AirportService.get_taiwan_airports()
        return _success_response(airports)
    except Exception as e:
        current_app.logger.error(f"獲取台灣機場列表失敗: {e}", exc_info=True)
        return _error_response('獲取台灣機場列表失敗', 500)

@airport_bp.route('/<string:airport_id>', methods=['GET'])
@cache.cached(timeout=7200)  # 緩存2小時
async def get_airport_by_id(airport_id):
    """通過ID獲取機場"""
    try:
        airport_id_upper = airport_id.upper()
        # 使用新的 AirportService
        airport = await AirportService.get_airport_by_id(airport_id_upper)
        
        if not airport:
            raise NotFound('找不到該機場')
        
        return _success_response(airport)
    except NotFound as e:
        return _error_response(str(e), 404)
    except Exception as e:
        current_app.logger.error(f"獲取機場 {airport_id} 詳情失敗: {e}", exc_info=True)
        return _error_response('獲取機場詳情時發生內部錯誤', 500)

@airport_bp.route('/available-departures', methods=['GET'])
@cache.cached(timeout=3600) # 縮短快取時間
async def get_available_departures():
    """獲取所有有有效出發航班的機場（未來航班）"""
    try:
        current_app.logger.info("開始查詢有有效出發航班的機場")
        
        # 使用新的 AirportService
        airports = await AirportService.get_available_departure_airports()
        
        current_app.logger.info(f"成功返回 {len(airports)} 個有未來航班的出發機場")
        return _success_response(airports)
    except Exception as e:
        current_app.logger.error(f"獲取有航班的出發機場失敗: {e}", exc_info=True)
        return _error_response('獲取可用出發機場失敗', 500)

@airport_bp.route('/available-destinations/<string:departure_code>', methods=['GET'])
@cache.cached(timeout=3600, query_string=True) # 添加緩存
async def get_available_destinations(departure_code):
    """獲取指定出發機場的所有可用目的地（未來航班）"""
    try:
        departure_id = departure_code.upper()
        current_app.logger.info(f"開始查詢從 {departure_id} 出發的可用目的地（未來航班）")
        
        # 使用新的 AirportService
        airports = await AirportService.get_available_destination_airports(departure_id)
        
        current_app.logger.info(f"成功返回 {len(airports)} 個目的地機場")
        return _success_response(airports)
    except Exception as e:
        current_app.logger.error(f"獲取從 {departure_id} 出發的可用目的地失敗: {e}", exc_info=True)
        return _error_response('獲取可用目的地失敗', 500) 