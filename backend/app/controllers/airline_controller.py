"""
航空公司控制器
處理與航空公司相關的API請求
"""
from flask import Blueprint, jsonify, request, current_app
from ..services.airline_service import AirlineService  # 使用新的服務
from ..models.airline import Airline # 保留，用於部分直接查詢
from ..models.base import db # 導入 db 實例
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
airline_bp = Blueprint('airline', __name__)

@airline_bp.route('/', methods=['GET'])
@cache.cached(timeout=3600)  # 緩存1小時
async def get_airlines():
    """獲取所有航空公司"""
    try:
        # 使用新的 AirlineService
        airlines = await AirlineService.get_available_airlines()
        return _success_response(airlines)
    except Exception as e:
        current_app.logger.error(f"獲取航空公司列表失敗: {e}", exc_info=True)
        return _error_response('獲取航空公司列表時發生內部錯誤', 500)

@airline_bp.route('/domestic', methods=['GET'])
@cache.cached(timeout=3600)  # 緩存1小時
def get_domestic_airlines():
    """獲取所有國內航空公司"""
    try:
        # 暫時保留使用 Airline 模型方法
        airlines = Airline.get_domestic() # 使用類方法
        result = [{
            'id': airline.airline_id,
            'name_zh': airline.name_zh,
            'name_en': airline.name_en,
            'is_domestic': airline.is_domestic
        } for airline in airlines]
        return _success_response(result)
    except Exception as e:
        current_app.logger.error(f"獲取國內航空公司失敗: {e}", exc_info=True)
        return _error_response('獲取國內航空公司失敗', 500)

@airline_bp.route('/international', methods=['GET'])
@cache.cached(timeout=3600)  # 緩存1小時
def get_international_airlines():
    """獲取所有國際航空公司"""
    try:
        # 暫時保留使用 Airline 模型方法
        airlines = Airline.get_international() # 使用類方法
        result = [{
            'id': airline.airline_id,
            'name_zh': airline.name_zh,
            'name_en': airline.name_en,
            'is_domestic': airline.is_domestic
        } for airline in airlines]
        return _success_response(result)
    except Exception as e:
        current_app.logger.error(f"獲取國際航空公司失敗: {e}", exc_info=True)
        return _error_response('獲取國際航空公司失敗', 500)

@airline_bp.route('/<string:airline_id>', methods=['GET'])
@cache.cached(timeout=3600)  # 緩存1小時
async def get_airline_by_id(airline_id):
    """根據ID獲取航空公司"""
    try:
        airline_id_upper = airline_id.upper()
        # 使用新的 AirlineService
        airline = await AirlineService.get_airline_by_id(airline_id_upper)
        
        if not airline:
             raise NotFound('找不到該航空公司')
        
        return _success_response(airline)
    except NotFound as e:
        return _error_response(str(e), 404)
    except Exception as e:
        current_app.logger.error(f"獲取航空公司 {airline_id} 失敗: {e}", exc_info=True)
        return _error_response('獲取航空公司詳情時發生內部錯誤', 500)

@airline_bp.route('/search', methods=['GET'])
async def search_airlines():
    """搜索航空公司"""
    try:
        name = request.args.get('name')
        
        if not name:
             return _error_response('必須提供搜索名稱 (name) 參數', 400)

        # 使用新的 AirlineService
        airlines = await AirlineService.search_airlines(name)
        return _success_response(airlines)
    except Exception as e:
        current_app.logger.error(f"搜索航空公司失敗: {e}", exc_info=True)
        return _error_response('搜索航空公司時發生錯誤', 500) 