"""
票價控制器
處理與票價相關的API請求
"""
from flask import Blueprint, jsonify, request
from ..models import TicketPrice, Flight
from ..services.price_service import PriceService
# 導入必要的輔助工具和異常
from datetime import datetime
from werkzeug.exceptions import BadRequest, NotFound
from flask import current_app # 用於日誌

# --- 輔助函數 (如果沒有共享的，可以在這裡定義) ---
def _validate_date(date_str, param_name):
    """驗證日期字符串格式"""
    if not date_str:
        raise BadRequest(f'必須提供 {param_name}')
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        raise BadRequest(f'{param_name} 日期格式錯誤，請使用 YYYY-MM-DD')

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
def get_prices_by_flight(flight_id):
    """獲取特定航班的票價信息"""
    try:
        # 獲取請求參數
        class_type = request.args.get('class_type')
        
        # 使用票價服務查詢
        # 假設服務層在找不到 flight_id 時會處理（例如返回空列表或None）
        prices = PriceService.get_price_by_flight(flight_id, class_type)
        
        # 如果服務層返回空列表，也視為成功（只是沒有數據）
        return _success_response(prices)
        
    except Exception as e:
        # 捕捉所有未預期的錯誤
        current_app.logger.error(f"獲取航班 {flight_id} 票價時出錯: {e}", exc_info=True)
        return _error_response('獲取航班票價時發生內部錯誤', 500)

@ticket_price_bp.route('/lowest', methods=['GET'])
def get_lowest_prices():
    """獲取特定路線和日期範圍的最低票價"""
    try:
        # 獲取請求參數
        departure = request.args.get('departure')
        arrival = request.args.get('arrival')
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        # 驗證必須參數
        if not departure or not arrival:
            raise BadRequest('必須提供出發機場和到達機場代碼')
        
        # 驗證日期
        start_date = _validate_date(start_date_str, '開始日期')
        end_date = None
        if end_date_str:
            end_date = _validate_date(end_date_str, '結束日期')
            if end_date < start_date:
                raise BadRequest('結束日期不能早於開始日期')
        
        # 使用票價服務查詢
        prices = PriceService.get_lowest_prices(
            departure.upper(), 
            arrival.upper(), 
            start_date.isoformat(), # 傳遞 ISO 格式日期字符串給服務層
            end_date.isoformat() if end_date else None
        )
        
        # 服務層可能返回錯誤字典
        if isinstance(prices, dict) and 'error' in prices:
             # 根據服務層錯誤決定狀態碼，這裡假設400或404
             if "找不到" in prices['error']:
                 return _error_response(prices['error'], 404)
             else:
                 return _error_response(prices['error'], 400) 
            
        return _success_response(prices)
        
    except BadRequest as e:
        return _error_response(str(e), 400)
    except Exception as e:
        current_app.logger.error(f"獲取最低票價時出錯: {e}", exc_info=True)
        return _error_response('獲取最低票價時發生內部錯誤', 500)

@ticket_price_bp.route('/history/<string:flight_id>', methods=['GET'])
def get_price_history(flight_id):
    """獲取航班的歷史票價"""
    try:
        # 獲取請求參數
        class_type = request.args.get('class_type', '經濟艙')
        days_str = request.args.get('days', '30') # 將預設值改為字串
        
        try:
            days = int(days_str)
            if days <= 0:
                 raise ValueError('天數必須是正整數')
        except ValueError as ve:
            raise BadRequest(str(ve))
        
        # 使用票價服務查詢
        history = PriceService.get_price_history(flight_id, class_type, days)
        
        # 服務層可能返回錯誤，但在當前實現中，找不到數據會返回空列表
        return _success_response(history)

    except BadRequest as e:
        return _error_response(str(e), 400)
    except Exception as e:
        current_app.logger.error(f"獲取航班 {flight_id} 歷史票價時出錯: {e}", exc_info=True)
        return _error_response('獲取歷史票價時發生內部錯誤', 500)

@ticket_price_bp.route('/analyze/<string:flight_id>', methods=['GET'])
def analyze_price_trend(flight_id):
    """分析票價趨勢並提供購買建議"""
    try:
        # 獲取請求參數
        class_type = request.args.get('class_type', '經濟艙')
        
        # 使用票價服務分析
        analysis = PriceService.analyze_price_trend(flight_id, class_type)
        
        # 服務層會處理找不到數據的情況並返回特定結構
        return _success_response(analysis)
        
    except Exception as e:
        current_app.logger.error(f"分析航班 {flight_id} 票價趨勢時出錯: {e}", exc_info=True)
        return _error_response('分析票價趨勢時發生內部錯誤', 500) 