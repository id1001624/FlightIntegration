"""
機場控制器
處理與機場相關的API請求
"""
from flask import Blueprint, jsonify, request, current_app
from ..services.airport_service import airport_service  # 使用新的服務實例
from .. import cache
from werkzeug.exceptions import NotFound
from app.schemas.airport_schema import AirportSchema
from datetime import datetime

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

@airport_bp.route('/taiwan-international', methods=['GET'], endpoint='get_taiwan_international_airports')
@cache.cached(timeout=7200)
async def get_taiwan_international_airports():
    """獲取台灣國際機場（僅有國際航班的機場）"""
    try:
        # 直接指定台灣的國際機場代碼
        international_airport_codes = ['TPE', 'TSA', 'KHH', 'RMQ', 'HUN']
        airports = await airport_service.get_airports_by_codes(international_airport_codes)
        return _success_response(airports)
    except Exception as e:
        current_app.logger.error(f"獲取台灣國際機場列表失敗: {e}", exc_info=True)
        return _error_response('獲取台灣國際機場列表失敗', 500)

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

@airport_bp.route('/batch', methods=['GET'], endpoint='get_airports_batch')
@cache.cached(timeout=7200, query_string=True)
async def get_airports_batch():
    """批量獲取機場資訊，用於前端中文名稱轉換"""
    try:
        codes_param = request.args.get('codes', '')
        if not codes_param:
            return _error_response('缺少 codes 參數', 400)
        
        # 解析機場代碼
        airport_codes = [code.strip().upper() for code in codes_param.split(',') if code.strip()]
        if not airport_codes:
            return _error_response('無效的機場代碼列表', 400)
        
        # 批量獲取機場資訊
        airports = await airport_service.get_airports_by_codes(airport_codes)
        return _success_response(airports)
        
    except Exception as e:
        current_app.logger.error(f"批量獲取機場資訊失敗: {e}", exc_info=True)
        return _error_response('批量獲取機場資訊時發生內部錯誤', 500)

@airport_bp.route('/<string:departure_code>/destinations-cached', methods=['GET'], endpoint='get_destinations_cached')
@cache.cached(timeout=1800, query_string=True)  # 30 分鐘快取
async def get_destinations_cached(departure_code):
    """
    從本地緩存獲取指定出發機場的目的地（快速響應，解決延遲問題）
    優先使用本地 AirportDestination 表，如果沒有數據則可選擇回退到 Amadeus API
    """
    try:
        departure_id = departure_code.upper()
        
        # 檢查是否允許回退到 Amadeus API
        fallback_param = request.args.get('fallback', default='true', type=str)
        fallback_to_amadeus = fallback_param.lower() in ['true', '1', 'yes']
        
        # 使用緩存服務獲取目的地
        destinations = await airport_service.get_destinations_cached(
            departure_id, 
            fallback_to_amadeus=fallback_to_amadeus
        )
        
        if not destinations:
            message = f"暫無從 {departure_id} 出發的目的地數據"
            if not fallback_to_amadeus:
                message += "（未啟用 API 回退）"
            return _success_response([])
        
        current_app.logger.info(f"成功返回 {len(destinations)} 個從 {departure_id} 出發的緩存目的地")
        return _success_response(destinations)
        
    except Exception as e:
        current_app.logger.error(f"獲取從 {departure_id} 出發的緩存目的地失敗: {e}", exc_info=True)
        return _error_response('獲取緩存目的地時發生內部錯誤', 500)

@airport_bp.route('/<string:departure_code>/destinations-popular', methods=['GET'], endpoint='get_popular_destinations')
@cache.cached(timeout=3600, query_string=True)  # 1 小時快取
def get_popular_destinations(departure_code):
    """
    獲取指定出發機場的熱門目的地（按航班數量排序）
    僅使用本地緩存數據，響應極快
    """
    try:
        departure_id = departure_code.upper()
        limit_param = request.args.get('limit', default=10, type=int)
        
        # 限制 limit 參數範圍
        limit = max(1, min(limit_param, 50))
        
        # 使用緩存服務獲取熱門目的地
        popular_destinations = airport_service.get_popular_destinations_cached(
            departure_id, 
            limit=limit
        )
        
        current_app.logger.info(f"成功返回 {len(popular_destinations)} 個從 {departure_id} 出發的熱門目的地")
        return _success_response(popular_destinations)
        
    except Exception as e:
        current_app.logger.error(f"獲取從 {departure_id} 出發的熱門目的地失敗: {e}", exc_info=True)
        return _error_response('獲取熱門目的地時發生內部錯誤', 500)

@airport_bp.route('/<string:departure_code>/sync-destinations', methods=['POST'], endpoint='sync_destinations')
async def sync_destinations(departure_code):
    """
    手動觸發指定機場的目的地緩存同步
    僅允許管理員或開發環境使用
    """
    try:
        departure_id = departure_code.upper()
        
        # 簡單的安全檢查（生產環境建議加強）
        # 可以添加 API Key 或其他驗證機制
        if not current_app.config.get('DEBUG', False):
            # 生產環境可以要求特定的授權標頭
            auth_header = request.headers.get('X-Admin-Key')
            if not auth_header or auth_header != current_app.config.get('ADMIN_API_KEY'):
                return _error_response('需要管理員權限', 403)
        
        # 執行同步
        success = await airport_service.sync_destination_cache_for_airport(departure_id)
        
        if success:
            current_app.logger.info(f"成功同步機場 {departure_id} 的目的地緩存")
            return _success_response({
                'message': f'成功同步機場 {departure_id} 的目的地緩存',
                'synced_at': current_app.current_time or datetime.utcnow().isoformat()
            })
        else:
            return _error_response(f'同步機場 {departure_id} 的目的地緩存失敗', 500)
        
    except Exception as e:
        current_app.logger.error(f"同步機場 {departure_id} 目的地緩存失敗: {e}", exc_info=True)
        return _error_response('同步目的地緩存時發生內部錯誤', 500)