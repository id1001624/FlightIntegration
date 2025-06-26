"""
機場控制器
處理與機場相關的API請求
"""
from flask import Blueprint, jsonify, request, current_app
from ..services.airport_service import airport_service  # 使用新的服務實例
from .. import cache
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
airport_bp = Blueprint('airport', __name__, url_prefix='/api/airports') # 建議 URL 使用複數

@airport_bp.route('/', methods=['GET'], endpoint='get_airports')
async def get_airports():
    """獲取所有機場，並為台灣機場附加活躍度分數"""
    try:
        days_ahead_param = request.args.get('days_ahead', default=7, type=int)
        airports = await airport_service.get_all_airports_with_activity(days_ahead=days_ahead_param)
        return _success_response(airports)
    except Exception as e:
        current_app.logger.error(f"獲取所有機場列表（含活躍度）失敗: {e}", exc_info=True)
        return _error_response('獲取機場列表時發生內部錯誤', 500)

@airport_bp.route('/taiwan', methods=['GET'], endpoint='get_taiwan_airports')
@cache.cached(timeout=7200)
async def get_taiwan_airports():
    """獲取台灣所有機場"""
    try:
        airports = await airport_service.get_taiwan_airports()
        return _success_response(airports)
    except Exception as e:
        current_app.logger.error(f"獲取台灣機場列表失敗: {e}", exc_info=True)
        return _error_response('獲取台灣機場列表失敗', 500)

@airport_bp.route('/<string:airport_id>', methods=['GET'], endpoint='get_airport_by_id')
@cache.cached(timeout=7200)
async def get_airport_by_id(airport_id):
    """通過ID獲取機場"""
    try:
        airport_id_upper = airport_id.upper()
        airport = await airport_service.get_airport_by_id(airport_id_upper)
        if not airport:
            raise NotFound('找不到該機場')
        return _success_response(airport)
    except NotFound as e:
        return _error_response(str(e), 404)
    except Exception as e:
        current_app.logger.error(f"獲取機場 {airport_id} 詳情失敗: {e}", exc_info=True)
        return _error_response('獲取機場詳情時發生內部錯誤', 500)

@airport_bp.route('/available-departures', methods=['GET'], endpoint='get_available_departures')
@cache.cached(timeout=3600)
async def get_available_departures():
    """獲取所有有有效出發航班的機場（未來航班）"""
    try:
        airports = await airport_service.get_available_departure_airports()
        return _success_response(airports)
    except Exception as e:
        current_app.logger.error(f"獲取有航班的出發機場失敗: {e}", exc_info=True)
        return _error_response('獲取可用出發機場失敗', 500)

@airport_bp.route('/<string:departure_code>/destinations', methods=['GET'], endpoint='get_available_destinations')
# @cache.cached(timeout=3600, query_string=True) # 暫時禁用快取以進行調試
async def get_available_destinations(departure_code):
    """獲取指定出發機場的所有可用目的地（未來航班）"""
    try:
        departure_id = departure_code.upper()
        date_param = request.args.get('date', default=None, type=str) # 允許傳入日期參數
        airports = await airport_service.get_available_destinations(departure_id, date=date_param)
        return _success_response(airports)
    except Exception as e:
        current_app.logger.error(f"獲取從 {departure_id} 出發的可用目的地失敗: {e}", exc_info=True)
        return _error_response('獲取可用目的地失敗', 500)