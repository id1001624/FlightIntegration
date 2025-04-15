"""
機場控制器
處理與機場相關的API請求
"""
from flask import Blueprint, jsonify, request, current_app
from ..models import Airport, Flight
from ..models.base import db
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
@cache.cached(timeout=7200)  # 緩存2小時
def get_airports():
    """獲取所有機場"""
    try:
        # 直接使用 query 查詢
        airports = db.session.query(
            Airport.airport_id, Airport.name_zh, 
            Airport.name_en, Airport.city, Airport.city_en,
            Airport.country, Airport.timezone # 移除 contact_info, website_url
        ).order_by(Airport.name_zh).all() # 添加排序
        
        result = [{
            'id': airport.airport_id,
            'name_zh': airport.name_zh,
            'name_en': airport.name_en,
            'city': airport.city,
            'city_en': airport.city_en,
            'country': airport.country,
            'timezone': airport.timezone # 移除 contact_info, website_url
        } for airport in airports]
        
        return _success_response(result)
    except Exception as e:
        current_app.logger.error(f"獲取機場列表失敗: {e}", exc_info=True)
        return _error_response('獲取機場列表時發生內部錯誤', 500)

@airport_bp.route('/taiwan', methods=['GET'])
@cache.cached(timeout=7200)  # 緩存2小時
def get_taiwan_airports():
    """獲取台灣所有機場"""
    try:
        # 直接使用 query 查詢
        airports = db.session.query(
            Airport.airport_id, Airport.name_zh, 
            Airport.name_en, Airport.city, Airport.city_en,
            Airport.country, Airport.timezone # 移除 contact_info, website_url
        ).filter(Airport.country == 'Taiwan').order_by(Airport.name_zh).all()
        
        result = [{
            'id': airport.airport_id,
            'name_zh': airport.name_zh,
            'name_en': airport.name_en,
            'city': airport.city,
            'city_en': airport.city_en,
            'timezone': airport.timezone # 移除 contact_info, website_url
        } for airport in airports]
        
        return _success_response(result)
    except Exception as e:
        current_app.logger.error(f"獲取台灣機場列表失敗: {e}", exc_info=True)
        return _error_response('獲取台灣機場列表失敗', 500)

@airport_bp.route('/<string:airport_id>', methods=['GET'])
@cache.cached(timeout=7200)  # 緩存2小時
def get_airport_by_id(airport_id):
    """通過ID獲取機場"""
    try:
        airport_id_upper = airport_id.upper()
        # 直接使用 query 查詢
        airport = db.session.query(
            Airport.airport_id, Airport.name_zh, 
            Airport.name_en, Airport.city, Airport.city_en, 
            Airport.country, Airport.timezone, Airport.contact_info, Airport.website_url
        ).filter(Airport.airport_id == airport_id_upper).first()
        
        if not airport:
            raise NotFound('找不到該機場')
        
        result = {
            'id': airport.airport_id,
            'name_zh': airport.name_zh,
            'name_en': airport.name_en,
            'city': airport.city,
            'city_en': airport.city_en,
            'country': airport.country,
            'timezone': airport.timezone,
            'contact_info': airport.contact_info,
            'website_url': airport.website_url
        }
        
        return _success_response(result)
    except NotFound as e:
        return _error_response(str(e), 404)
    except Exception as e:
        current_app.logger.error(f"獲取機場 {airport_id} 詳情失敗: {e}", exc_info=True)
        return _error_response('獲取機場詳情時發生內部錯誤', 500)

@airport_bp.route('/available-departures', methods=['GET'])
@cache.cached(timeout=3600) # 縮短快取時間
def get_available_departures():
    """獲取所有有有效出發航班的機場（未來航班）"""
    try:
        current_app.logger.info("開始查詢有有效出發航班的機場")
        
        # 查詢未來有航班的出發機場ID
        departure_ids_query = db.session.query(distinct(Flight.departure_airport_id)).filter(
            # 只考慮未來一週內的航班作為"有效"出發機場的依據，避免返回過多歷史數據機場
            Flight.scheduled_departure >= db.func.current_date(),
            Flight.scheduled_departure < db.func.current_date() + db.text("'7 days'::interval") 
        )
        departure_ids = [id[0] for id in departure_ids_query.all()]
        current_app.logger.info(f"找到 {len(departure_ids)} 個有未來航班的出發機場ID: {departure_ids}")

        if not departure_ids:
            return _success_response([]) # 如果沒有，返回空列表

        # 獲取這些機場的詳細資訊
        airports_query = db.session.query(
            Airport.airport_id, Airport.name_zh, 
            Airport.name_en, Airport.city, Airport.city_en # 移除 country, timezone 等不必要欄位
        ).filter(Airport.airport_id.in_(departure_ids)).order_by(Airport.name_zh)
        
        airports = airports_query.all()
        
        result = [{
            'id': airport.airport_id,
            'code': airport.airport_id, # 保留 code 方便前端
            'name': airport.name_zh or airport.name_en, # 優先顯示中文名
            'city': airport.city
        } for airport in airports]
        
        current_app.logger.info(f"成功返回 {len(result)} 個有未來航班的出發機場")
        return _success_response(result)
    except Exception as e:
        current_app.logger.error(f"獲取有航班的出發機場失敗: {e}", exc_info=True)
        return _error_response('獲取可用出發機場失敗', 500)

@airport_bp.route('/available-destinations/<string:departure_code>', methods=['GET'])
@cache.cached(timeout=3600, query_string=True) # 添加緩存
def get_available_destinations(departure_code):
    """獲取指定出發機場的所有可用目的地（未來航班）"""
    try:
        departure_id = departure_code.upper()
        current_app.logger.info(f"開始查詢從 {departure_id} 出發的可用目的地（未來航班）")
        
        # 查詢從該機場出發的未來航班的目的地機場ID
        destinations_query = db.session.query(distinct(Flight.arrival_airport_id)).filter(
            Flight.departure_airport_id == departure_id,
            Flight.scheduled_departure >= db.func.current_date() # 只考慮未來航班
        )
        destination_ids = [id[0] for id in destinations_query.all()]
        current_app.logger.info(f"找到 {len(destination_ids)} 個未來航班目的地機場ID: {destination_ids}")
        
        if not destination_ids:
            return _success_response([])

        # 獲取這些機場的詳細資訊
        airports_query = db.session.query(
            Airport.airport_id, Airport.name_zh, 
            Airport.name_en, Airport.city, Airport.city_en # 移除不必要欄位
        ).filter(Airport.airport_id.in_(destination_ids)).order_by(Airport.name_zh)

        airports = airports_query.all()
        
        result = [{
            'id': airport.airport_id,
            'code': airport.airport_id,
            'name': airport.name_zh or airport.name_en,
            'city': airport.city
        } for airport in airports]
        
        current_app.logger.info(f"成功返回 {len(result)} 個目的地機場")
        return _success_response(result)
    except Exception as e:
        current_app.logger.error(f"獲取從 {departure_id} 出發的可用目的地失敗: {e}", exc_info=True)
        return _error_response('獲取可用目的地失敗', 500) 