"""
航空公司控制器
處理與航空公司相關的API請求
"""
from flask import Blueprint, jsonify, request
from ..models import Airline
from .. import cache
from flask import current_app

# 創建藍圖
airline_bp = Blueprint('airline', __name__)

@airline_bp.route('/', methods=['GET'])
@cache.cached(timeout=3600)  # 緩存1小時
def get_airlines():
    """獲取所有航空公司"""
    try:
        airlines = Airline.query.all()
        result = []
        for airline in airlines:
            result.append({
                'id': str(airline.airline_id),
                'iata_code': airline.iata_code,
                'name_zh': airline.name_zh,
                'name_en': airline.name_en,
                'is_domestic': airline.is_domestic,
                'website': airline.website,
                'contact_phone': airline.contact_phone
            })
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"獲取航空公司列表失敗: {str(e)}")
        return jsonify({'error': '獲取航空公司列表失敗'}), 500

@airline_bp.route('/domestic', methods=['GET'])
@cache.cached(timeout=3600)  # 緩存1小時
def get_domestic_airlines():
    """獲取所有國內航空公司"""
    try:
        airlines = Airline.get_domestic()
        result = []
        for airline in airlines:
            result.append({
                'id': str(airline.airline_id),
                'iata_code': airline.iata_code,
                'name_zh': airline.name_zh,
                'name_en': airline.name_en,
                'website': airline.website,
                'contact_phone': airline.contact_phone
            })
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"獲取國內航空公司失敗: {str(e)}")
        return jsonify({'error': '獲取國內航空公司失敗'}), 500

@airline_bp.route('/international', methods=['GET'])
@cache.cached(timeout=3600)  # 緩存1小時
def get_international_airlines():
    """獲取所有國際航空公司"""
    try:
        airlines = Airline.get_international()
        result = []
        for airline in airlines:
            result.append({
                'id': str(airline.airline_id),
                'iata_code': airline.iata_code,
                'name_zh': airline.name_zh,
                'name_en': airline.name_en,
                'website': airline.website,
                'contact_phone': airline.contact_phone
            })
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"獲取國際航空公司失敗: {str(e)}")
        return jsonify({'error': '獲取國際航空公司失敗'}), 500

@airline_bp.route('/<string:iata_code>', methods=['GET'])
@cache.cached(timeout=3600)  # 緩存1小時
def get_airline_by_iata(iata_code):
    """根據IATA代碼獲取航空公司"""
    try:
        airline = Airline.get_by_iata(iata_code)
        if not airline:
            return jsonify({'error': '找不到該航空公司'}), 404
        
        result = {
            'id': str(airline.airline_id),
            'iata_code': airline.iata_code,
            'name_zh': airline.name_zh,
            'name_en': airline.name_en,
            'is_domestic': airline.is_domestic,
            'website': airline.website,
            'contact_phone': airline.contact_phone
        }
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"獲取航空公司失敗: {str(e)}")
        return jsonify({'error': '獲取航空公司失敗'}), 500

@airline_bp.route('/search', methods=['GET'])
def search_airlines():
    """搜索航空公司"""
    # 獲取請求參數
    name = request.args.get('name')
    country = request.args.get('country')
    
    # 根據參數執行不同的查詢
    if name:
        # 判斷使用中文還是英文搜索
        lang = 'en' if all(ord(c) < 128 for c in name) else 'zh'
        airlines = Airline.get_by_name(name, lang)
    elif country:
        # 因移除 country 欄位，現在返回空列表
        airlines = []
    else:
        return jsonify({'error': '請提供搜索參數'}), 400
    
    # 轉換為JSON格式
    result = []
    for airline in airlines:
        result.append({
            'id': str(airline.airline_id),
            'iata_code': airline.iata_code,
            'name_zh': airline.name_zh,
            'name_en': airline.name_en,
            # 已移除 country 欄位引用
            'is_domestic': airline.is_domestic,
            'website': airline.website,
            'contact_phone': airline.contact_phone
        })
    
    return jsonify(result) 