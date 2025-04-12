"""
機場控制器
處理與機場相關的API請求
"""
from flask import Blueprint, jsonify, request, current_app
from ..models import Airport, Flight
from ..models.base import db
from .. import cache
from sqlalchemy import distinct

# 創建藍圖
airport_bp = Blueprint('airport', __name__)

@airport_bp.route('/', methods=['GET'])
@cache.cached(timeout=7200)  # 緩存2小時
def get_airports():
    """獲取所有機場"""
    try:
        # 直接使用query查詢，避免使用Base類的get_all方法
        airports = db.session.query(
            Airport.airport_id, Airport.name_zh, 
            Airport.name_en, Airport.city, Airport.city_en, 
            Airport.country, Airport.timezone, Airport.contact_info, 
            Airport.website_url
        ).all()
        
        # 轉換為JSON格式
        result = []
        for airport in airports:
            result.append({
                'id': airport.airport_id,
                'name_zh': airport.name_zh,
                'name_en': airport.name_en,
                'city': airport.city,
                'city_en': airport.city_en,
                'country': airport.country,
                'timezone': airport.timezone,
                'contact_info': airport.contact_info,
                'website_url': airport.website_url
            })
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'獲取機場列表失敗: {str(e)}'}), 500

@airport_bp.route('/taiwan', methods=['GET'])
@cache.cached(timeout=7200)  # 緩存2小時
def get_taiwan_airports():
    """獲取台灣所有機場"""
    try:
        # 直接使用query查詢，避免使用類方法
        airports = db.session.query(
            Airport.airport_id, Airport.name_zh, 
            Airport.name_en, Airport.city, Airport.city_en, 
            Airport.timezone, Airport.contact_info, Airport.website_url
        ).filter(Airport.country == 'Taiwan').all()
        
        # 轉換為JSON格式
        result = []
        for airport in airports:
            result.append({
                'id': airport.airport_id,
                'name_zh': airport.name_zh,
                'name_en': airport.name_en,
                'city': airport.city,
                'city_en': airport.city_en,
                'timezone': airport.timezone,
                'contact_info': airport.contact_info,
                'website_url': airport.website_url
            })
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'獲取台灣機場列表失敗: {str(e)}'}), 500

@airport_bp.route('/<string:airport_id>', methods=['GET'])
@cache.cached(timeout=7200)  # 緩存2小時
def get_airport_by_id(airport_id):
    """通過ID獲取機場"""
    try:
        # 直接使用query查詢
        airport = db.session.query(
            Airport.airport_id, Airport.name_zh, 
            Airport.name_en, Airport.city, Airport.city_en, 
            Airport.country, Airport.timezone, Airport.contact_info, 
            Airport.website_url
        ).filter(Airport.airport_id == airport_id).first()
        
        if not airport:
            return jsonify({'error': '找不到該機場'}), 404
        
        # 轉換為JSON格式
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
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'獲取機場詳情失敗: {str(e)}'}), 500

@airport_bp.route('/country/<string:country>', methods=['GET'])
@cache.cached(timeout=7200)  # 緩存2小時
def get_airports_by_country(country):
    """獲取指定國家的所有機場"""
    try:
        # 直接使用query查詢
        airports = db.session.query(
            Airport.airport_id, Airport.name_zh, 
            Airport.name_en, Airport.city, Airport.city_en, 
            Airport.country, Airport.timezone, Airport.contact_info, 
            Airport.website_url
        ).filter(Airport.country == country).all()
        
        # 轉換為JSON格式
        result = []
        for airport in airports:
            result.append({
                'id': airport.airport_id,
                'name_zh': airport.name_zh,
                'name_en': airport.name_en,
                'city': airport.city,
                'city_en': airport.city_en,
                'country': airport.country,
                'timezone': airport.timezone,
                'contact_info': airport.contact_info,
                'website_url': airport.website_url
            })
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'獲取國家機場列表失敗: {str(e)}'}), 500

@airport_bp.route('/city/<string:city>', methods=['GET'])
def get_airports_by_city(city):
    """獲取指定城市的所有機場"""
    try:
        # 直接使用query查詢
        airports = db.session.query(
            Airport.airport_id, Airport.name_zh, 
            Airport.name_en, Airport.city, Airport.city_en, 
            Airport.country, Airport.timezone, Airport.contact_info, 
            Airport.website_url
        ).filter(Airport.city == city).all()
        
        # 轉換為JSON格式
        result = []
        for airport in airports:
            result.append({
                'id': airport.airport_id,
                'name_zh': airport.name_zh,
                'name_en': airport.name_en,
                'city': airport.city,
                'city_en': airport.city_en,
                'country': airport.country,
                'timezone': airport.timezone,
                'contact_info': airport.contact_info,
                'website_url': airport.website_url
            })
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'獲取城市機場列表失敗: {str(e)}'}), 500

@airport_bp.route('/available-departures', methods=['GET'])
def get_available_departures():
    """獲取所有有航班的出發機場"""
    try:
        current_app.logger.info("開始查詢有航班的出發機場")
        
        # 查詢所有有航班的出發機場ID
        current_app.logger.debug("執行資料庫查詢: 獲取有航班的出發機場ID")
        departure_ids_query = db.session.query(distinct(Flight.departure_airport_id))
        current_app.logger.debug(f"執行查詢SQL: {str(departure_ids_query.statement)}")
        departure_ids = departure_ids_query.all()
        departure_ids = [id[0] for id in departure_ids]
        
        current_app.logger.info(f"找到 {len(departure_ids)} 個出發機場ID: {departure_ids}")
        
        # 獲取這些機場的詳細資訊
        current_app.logger.debug("執行資料庫查詢: 獲取機場詳細資訊")
        airports_query = db.session.query(
            Airport.airport_id, Airport.name_zh, 
            Airport.name_en, Airport.city, Airport.city_en
        ).filter(Airport.airport_id.in_(departure_ids))
        current_app.logger.debug(f"執行查詢SQL: {str(airports_query.statement)}")
        airports = airports_query.all()
        
        # 轉換為JSON格式
        result = []
        for airport in airports:
            result.append({
                'id': airport.airport_id,
                'code': airport.airport_id,
                'name': airport.name_zh or airport.name_en,
                'city': airport.city
            })
        
        current_app.logger.info(f"成功返回 {len(result)} 個有航班的出發機場")
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"獲取有航班的出發機場失敗: {str(e)}", exc_info=True)
        current_app.logger.error(f"錯誤類型: {type(e)}")
        # 嘗試獲取更多錯誤信息
        import traceback
        error_traceback = traceback.format_exc()
        current_app.logger.error(f"錯誤堆疊: {error_traceback}")
        return jsonify({'error': f'獲取有航班的出發機場失敗: {str(e)}'}), 500

@airport_bp.route('/available-destinations/<string:departure_code>', methods=['GET'])
def get_available_destinations(departure_code):
    """獲取指定出發機場的所有可用目的地"""
    try:
        current_app.logger.info(f"開始查詢從 {departure_code} 出發的可用目的地")
        
        # 先獲取出發機場ID - 現在 departure_code 就是 airport_id
        departure_id = departure_code
        current_app.logger.info(f"使用出發機場ID: {departure_id}")
        
        # 查詢所有從該機場出發的航班的目的地機場ID
        current_app.logger.debug(f"執行資料庫查詢: 獲取從機場ID {departure_id} 出發的目的地機場ID")
        destinations_query = db.session.query(distinct(Flight.arrival_airport_id)).filter(
            Flight.departure_airport_id == departure_id
        )
        current_app.logger.debug(f"執行查詢SQL: {str(destinations_query.statement)}")
        destination_ids = destinations_query.all()
        destination_ids = [id[0] for id in destination_ids]
        
        current_app.logger.info(f"找到 {len(destination_ids)} 個目的地機場ID: {destination_ids}")
        
        if not destination_ids:
            return jsonify([])
        
        # 獲取這些機場的詳細資訊
        current_app.logger.debug("執行資料庫查詢: 獲取目的地機場詳細資訊")
        airports_query = db.session.query(
            Airport.airport_id, Airport.name_zh, 
            Airport.name_en, Airport.city, Airport.city_en
        ).filter(Airport.airport_id.in_(destination_ids))
        current_app.logger.debug(f"執行查詢SQL: {str(airports_query.statement)}")
        airports = airports_query.all()
        
        # 轉換為JSON格式
        result = []
        for airport in airports:
            result.append({
                'id': airport.airport_id,
                'code': airport.airport_id,
                'name': airport.name_zh or airport.name_en,
                'city': airport.city
            })
        
        current_app.logger.info(f"成功返回 {len(result)} 個目的地機場")
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"獲取可用目的地失敗: {str(e)}", exc_info=True)
        return jsonify({'error': f'獲取可用目的地失敗: {str(e)}'}), 500 