"""
票價控制器
處理與票價相關的API請求
"""
from flask import Blueprint, jsonify, request
from ..models import TicketPrice, Flight
# 只導入 PriceAnalysisService (注意: 現在它包含了 PriceService 的所有功能)
from ..services.price_analysis_service import PriceAnalysisService
# 導入必要的輔助工具和異常
from datetime import datetime
from werkzeug.exceptions import BadRequest, NotFound
from flask import current_app # 用於日誌
from marshmallow import ValidationError
from ..schemas.price_schema import (
    ticket_price_by_flight_args_schema,
    lowest_prices_args_schema,
    price_history_args_schema,
    price_analysis_args_schema
)

# --- 輔助函數 (如果沒有共享的，可以在這裡定義) ---
def _success_response(data):
    return jsonify({'success': True, 'data': data})

def _error_response(message, status_code):
    if status_code >= 500:
        current_app.logger.error(f"Server Error ({status_code}): {message}")
    else:
        current_app.logger.warning(f"Client Error ({status_code}): {message}")
    return jsonify({'success': False, 'message': message}), status_code
# -----------------------------------------------------

# 創建藍圖
ticket_price_bp = Blueprint('ticket_price', __name__)

@ticket_price_bp.route('/flight/<string:flight_id>', methods=['GET'])
async def get_prices_by_flight(flight_id):
    """獲取特定航班的票價信息"""
    try:
        # 使用 Schema 驗證請求參數
        try:
            args = ticket_price_by_flight_args_schema.load(request.args)
        except ValidationError as err:
            return _error_response(f"請求參數驗證失敗: {err.messages}", 400)
        
        # 提取驗證後的參數
        cabin_preference = args.get('cabin_preference')
        
        # 使用 PriceAnalysisService 查詢票價
        prices = await PriceAnalysisService.get_price_by_flight(flight_id, cabin_preference)
        
        # 如果服務層返回空列表，也視為成功（只是沒有數據）
        return _success_response(prices)
        
    except Exception as e:
        # 捕捉所有未預期的錯誤
        current_app.logger.error(f"獲取航班 {flight_id} 票價時出錯: {e}", exc_info=True)
        return _error_response('獲取航班票價時發生內部錯誤', 500)

@ticket_price_bp.route('/lowest', methods=['GET'])
async def get_lowest_prices():
    """獲取特定路線和日期範圍的最低票價"""
    try:
        # 使用 Schema 驗證請求參數
        try:
            args = lowest_prices_args_schema.load(request.args)
        except ValidationError as err:
            return _error_response(f"請求參數驗證失敗: {err.messages}", 400)
        
        # 提取驗證後的參數
        departure = args['departure'].upper()
        arrival = args['arrival'].upper()
        start_date = args['start_date'].strftime('%Y-%m-%d')
        end_date = args.get('end_date').strftime('%Y-%m-%d') if args.get('end_date') else None
        cabin_preference = args.get('cabin_preference')
        
        # 使用 PriceAnalysisService 查詢
        prices = await PriceAnalysisService.get_lowest_prices(
            departure_code=departure, 
            arrival_code=arrival, 
            start_date=start_date,
            end_date=end_date,
            cabin_preference=cabin_preference
        )
        
        # 服務層可能返回錯誤字典
        if isinstance(prices, dict) and 'error' in prices:
             # 根據服務層錯誤決定狀態碼，這裡假設400或404
             if "找不到" in prices['error']:
                 return _error_response(prices['error'], 404)
             else:
                 return _error_response(prices['error'], 400) 
            
        return _success_response(prices)
        
    except Exception as e:
        current_app.logger.error(f"獲取最低票價時出錯: {e}", exc_info=True)
        return _error_response('獲取最低票價時發生內部錯誤', 500)

@ticket_price_bp.route('/history/<string:flight_id>', methods=['GET'])
async def get_price_history(flight_id):
    """獲取航班的歷史票價"""
    try:
        # 使用 Schema 驗證請求參數
        try:
            args = price_history_args_schema.load(request.args)
        except ValidationError as err:
            return _error_response(f"請求參數驗證失敗: {err.messages}", 400)
        
        # 提取驗證後的參數
        cabin_info = args['cabin_info']
        days = args['days']
        
        # 使用 PriceAnalysisService 查詢
        history = await PriceAnalysisService.get_price_history(flight_id, cabin_info, days)
        
        # 服務層可能返回錯誤，但在當前實現中，找不到數據會返回空列表
        return _success_response(history)

    except Exception as e:
        current_app.logger.error(f"獲取航班 {flight_id} 歷史票價時出錯: {e}", exc_info=True)
        return _error_response('獲取歷史票價時發生內部錯誤', 500)

@ticket_price_bp.route('/analyze/<string:flight_id>', methods=['GET'])
async def analyze_price_trend(flight_id):
    """分析票價趨勢並提供購買建議"""
    try:
        # 使用 Schema 驗證請求參數
        try:
            args = price_analysis_args_schema.load(request.args)
        except ValidationError as err:
            return _error_response(f"請求參數驗證失敗: {err.messages}", 400)
        
        # 提取驗證後的參數
        cabin_info = args.get('cabin_info', 'economy_price')
        
        # 使用 PriceAnalysisService 進行分析
        analysis = await PriceAnalysisService.analyze_price_trend(flight_id, cabin_info)
        
        # 服務層會處理找不到數據的情況並返回特定結構
        return _success_response(analysis)
        
    except Exception as e:
        current_app.logger.error(f"分析航班 {flight_id} 票價趨勢時出錯: {e}", exc_info=True)
        return _error_response('分析票價趨勢時發生內部錯誤', 500) 