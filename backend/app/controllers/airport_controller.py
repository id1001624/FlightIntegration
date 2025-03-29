from flask import Blueprint, jsonify, current_app
from app.models import db, Airport, Airline
from app.utils.api_helper import api_response
import logging

# 設置日誌
logger = logging.getLogger(__name__)

# 建立機場與航空公司相關API藍圖
airport_bp = Blueprint('airport', __name__, url_prefix='/api')

@airport_bp.route('/airports', methods=['GET'])
def get_airports():
    """獲取所有機場資訊API"""
    try:
        airports = Airport.query.all()
        return api_response(True, data=[airport.to_dict() for airport in airports])
    except Exception as e:
        logger.error(f"獲取機場列表時發生錯誤: {str(e)}")
        return api_response(False, message="獲取機場列表時發生錯誤", status_code=500)

@airport_bp.route('/airlines', methods=['GET'])
def get_airlines():
    """獲取所有航空公司資訊API"""
    try:
        airlines = Airline.query.all()
        return api_response(True, data=[airline.to_dict() for airline in airlines])
    except Exception as e:
        logger.error(f"獲取航空公司列表時發生錯誤: {str(e)}")
        return api_response(False, message="獲取航空公司列表時發生錯誤", status_code=500)

@airport_bp.route('/airports/<code>', methods=['GET'])
def get_airport_details(code):
    """獲取機場詳細資訊API"""
    try:
        airport = Airport.query.filter_by(iata_code=code).first()
        
        if not airport:
            return api_response(False, message='找不到指定機場', status_code=404)
        
        return api_response(True, data=airport.to_dict())
    except Exception as e:
        logger.error(f"獲取機場詳情時發生錯誤: {str(e)}")
        return api_response(False, message="獲取機場詳情時發生錯誤", status_code=500)