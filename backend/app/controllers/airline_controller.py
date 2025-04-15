"""
航空公司控制器
處理與航空公司相關的API請求
"""
from flask import Blueprint, jsonify, request, current_app
from ..models.airline import Airline # 確保正確導入
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
def get_airlines():
    """獲取所有航空公司"""
    try:
        # 使用 .with_entities() 選擇需要的欄位，提高效率
        airlines = db.session.query(Airline).order_by(Airline.name_zh).all()
        result = [{
            'id': airline.airline_id,
            'name_zh': airline.name_zh,
            'name_en': airline.name_en,
            'is_domestic': airline.is_domestic
        } for airline in airlines]
        return _success_response(result)
    except Exception as e:
        current_app.logger.error(f"獲取航空公司列表失敗: {e}", exc_info=True)
        return _error_response('獲取航空公司列表時發生內部錯誤', 500)

@airline_bp.route('/domestic', methods=['GET'])
@cache.cached(timeout=3600)  # 緩存1小時
def get_domestic_airlines():
    """獲取所有國內航空公司"""
    try:
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
def get_airline_by_id(airline_id):
    """根據ID獲取航空公司"""
    try:
        airline_id_upper = airline_id.upper()
        # 使用 query.get() 可能更高效如果 airline_id 是主鍵
        airline = db.session.query(Airline).get(airline_id_upper) 
        if not airline:
             raise NotFound('找不到該航空公司')
        
        result = {
            'id': airline.airline_id,
            'name_zh': airline.name_zh,
            'name_en': airline.name_en,
            'is_domestic': airline.is_domestic,
            'website': airline.website,
            'contact_phone': airline.contact_phone
        }
        return _success_response(result)
    except NotFound as e:
        return _error_response(str(e), 404)
    except Exception as e:
        current_app.logger.error(f"獲取航空公司 {airline_id} 失敗: {e}", exc_info=True)
        return _error_response('獲取航空公司詳情時發生內部錯誤', 500)

@airline_bp.route('/search', methods=['GET'])
def search_airlines():
    """搜索航空公司"""
    try:
        name = request.args.get('name')
        country = request.args.get('country') # country 參數已無用
        
        if not name:
             return _error_response('必須提供搜索名稱 (name) 參數', 400)

        # 判斷使用中文還是英文搜索
        lang = 'en' if all(ord(c) < 128 for c in name) else 'zh'
        airlines = Airline.get_by_name(name, lang)
        
        result = [{
            'id': airline.airline_id,
            'name_zh': airline.name_zh,
            'name_en': airline.name_en,
            'is_domestic': airline.is_domestic
        } for airline in airlines]
        
        return _success_response(result)
    except Exception as e:
        current_app.logger.error(f"搜索航空公司失敗: {e}", exc_info=True)
        return _error_response('搜索航空公司時發生錯誤', 500) 