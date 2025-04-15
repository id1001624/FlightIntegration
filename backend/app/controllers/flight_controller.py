"""
航班控制器
處理與航班相關的API請求
"""
from flask import Blueprint, jsonify, request, current_app
from datetime import datetime # 導入 datetime
from werkzeug.exceptions import NotFound, BadRequest # 導入錯誤類型
from ..models import Flight, Airport, Airline
from ..services.search_service import SearchService
from ..services.data_sync_service import DataSyncService
from ..clients.flightstats_client import FlightStatsApiClient
from ..database.db import get_db, release_db # 導入異步 DB 工具
from .. import cache
# 從常量模組導入
from ..scripts.constants import (
    TAIWAN_AIRPORTS,
    TARGET_AIRLINES,
    POPULAR_DOMESTIC_ROUTES_DICTS,
    POPULAR_INTERNATIONAL_ROUTES_DICTS
)

# 創建藍圖
flight_bp = Blueprint('flight', __name__)

# --- 輔助函數 --- 
def _validate_date(date_str, param_name):
    """驗證日期字符串格式"""
    if not date_str:
        return # 日期為可選時允許為空
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
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

# --- API 端點 --- 

@flight_bp.route('/search', methods=['GET'])
async def search_flights():
    """搜索航班"""
    try:
        # 獲取請求參數
        departure = request.args.get('departure')
        arrival = request.args.get('arrival')
        departure_date = request.args.get('date')
        return_date = request.args.get('return_date')
        airlines_str = request.args.get('airlines')
        price_min_str = request.args.get('price_min')
        price_max_str = request.args.get('price_max')
        class_type = request.args.get('class_type', '經濟')
        only_target_airlines = request.args.get('only_target_airlines', 'true').lower() == 'true'
        passengers = request.args.get('passengers', '1')
        max_results = request.args.get('max_results', '20')
        sort_by = request.args.get('sort_by', 'price')

        # 驗證必須參數
        if not departure or not arrival or not departure_date:
            raise BadRequest('必須提供出發機場、到達機場和出發日期')

        # 驗證日期格式
        _validate_date(departure_date, '出發日期')
        _validate_date(return_date, '返回日期') # 驗證返回日期，如果提供的話

        # 處理航空公司參數
        airlines = None
        if airlines_str:
            airlines = [a.strip().upper() for a in airlines_str.split(',') if a.strip()]
        elif only_target_airlines:
            airlines = TARGET_AIRLINES.copy()

        # 處理數字參數
        try:
            price_min = float(price_min_str) if price_min_str else None
            price_max = float(price_max_str) if price_max_str else None
            passengers_int = int(passengers)
            max_results_int = int(max_results)
            if passengers_int <= 0 or max_results_int <= 0:
                raise ValueError()
        except (ValueError, TypeError):
            raise BadRequest('價格、乘客數和最大結果數必須是有效的正數')

        # 使用搜索服務進行查詢
        result = await SearchService.search_flights(
            departure.upper(), arrival.upper(), departure_date, 
            airlines, return_date,
            price_min, price_max, class_type,
            passengers_int, max_results_int, sort_by
        )
            
        return _success_response(result)

    except BadRequest as e:
        return _error_response(str(e), 400)
    # 可以添加更多特定的服務層錯誤捕捉
    # except NotFoundError as e:
    #     return _error_response(str(e), 404)
    except Exception as e:
        current_app.logger.error(f"搜索航班時發生未預期錯誤: {e}", exc_info=True)
        return _error_response('搜索航班時發生內部錯誤', 500)

@flight_bp.route('/from_taiwan/<string:arrival_iata>', methods=['GET'])
async def flights_from_taiwan(arrival_iata):
    """獲取從台灣飛往指定目的地的航班 (此方法效率不高，待改進)"""
    try:
        # 獲取請求參數
        departure_date = request.args.get('date')
        airlines_str = request.args.get('airlines')
        price_min_str = request.args.get('price_min')
        price_max_str = request.args.get('price_max')
        class_type = request.args.get('class_type', '經濟')
        passengers = request.args.get('passengers', '1')
        max_results = request.args.get('max_results', '5') # 每個機場限制少一點
        sort_by = request.args.get('sort_by', 'price')
        only_target_airlines = request.args.get('only_target_airlines', 'true').lower() == 'true'

        # 驗證必須參數
        if not departure_date:
            raise BadRequest('必須提供出發日期')

        # 驗證日期格式
        _validate_date(departure_date, '出發日期')

        # 處理航空公司參數
        airlines = None
        if airlines_str:
            airlines = [a.strip().upper() for a in airlines_str.split(',') if a.strip()]
        elif only_target_airlines:
            airlines = TARGET_AIRLINES.copy()

        # 處理數字參數
        try:
            price_min = float(price_min_str) if price_min_str else None
            price_max = float(price_max_str) if price_max_str else None
            passengers_int = int(passengers)
            max_results_per_airport = int(max_results) # 這個參數現在傳給服務層處理總數限制
            if passengers_int <= 0 or max_results_per_airport <= 0:
                raise ValueError()
        except (ValueError, TypeError):
            raise BadRequest('價格、乘客數和最大結果數必須是有效的正數')
        
        # 調用新的服務層方法
        all_outbound_flights = await SearchService.search_flights_from_taiwan(
            arrival_iata=arrival_iata.upper(),
            date_str=departure_date,
            airlines=airlines,
            price_min=price_min,
            price_max=price_max,
            class_type=class_type,
            passengers=passengers_int,
            max_results_total=max_results_per_airport, # 使用修改後的變量名
            sort_by=sort_by
        )

        # 直接返回服務層處理後的結果
        return _success_response({
            'flights': all_outbound_flights,
            'total': len(all_outbound_flights)
        })

    except BadRequest as e:
        return _error_response(str(e), 400)
    except Exception as e:
        current_app.logger.error(f"獲取從台灣出發的航班時發生錯誤: {e}", exc_info=True)
        return _error_response('獲取從台灣出發的航班時發生內部錯誤', 500)

@flight_bp.route('/<string:flight_id>', methods=['GET'])
async def get_flight_details(flight_id):
    """獲取航班詳細信息"""
    try:
        flight_details = await SearchService.get_flight_details_by_id(flight_id)
        # get_flight_details_by_id 應在找不到時返回 None 或拋出 NotFoundError
        if flight_details is None:
            raise NotFound('找不到該航班')
        return _success_response(flight_details)
    except NotFound as e:
        return _error_response(str(e), 404)
    except Exception as e:
        current_app.logger.error(f"獲取航班 {flight_id} 詳情時發生錯誤: {e}", exc_info=True)
        return _error_response('獲取航班詳情時發生內部錯誤', 500)

@flight_bp.route('/airlines', methods=['GET'])
@cache.cached(timeout=3600)  # 緩存1小時
async def get_available_airlines():
    """獲取所有可用的航空公司列表，用於篩選條件"""
    try:
        # SearchService 的方法應該處理數據庫錯誤
        airlines = await SearchService.get_available_airlines()
        
        # 標記目標航空公司 (這個邏輯也可以放在 Service 層)
        for airline in airlines:
            airline['is_target'] = airline.get('airline_id') in TARGET_AIRLINES
            
        return _success_response(airlines)
    except Exception as e:
        current_app.logger.error(f"獲取可用航空公司列表失敗: {e}", exc_info=True)
        return _error_response('獲取可用航空公司列表失敗', 500)

@flight_bp.route('/taiwan-airports', methods=['GET'])
async def get_taiwan_airports_api():
    """獲取台灣所有有有效航班的機場列表"""
    try:
        # 移除日期參數，Service 層應處理只返回 relevant 機場
        # date_str = request.args.get('date') 
        airports = await SearchService.get_taiwan_airports()
        return _success_response(airports)
    except Exception as e:
        current_app.logger.error(f"獲取台灣機場列表失敗: {e}", exc_info=True)
        return _error_response('獲取台灣機場列表失敗', 500)

@flight_bp.route('/<string:departure_code>/destinations', methods=['GET'])
@cache.cached(timeout=3600, query_string=True)  # 緩存1小時，考慮查詢參數
async def get_available_destinations(departure_code):
    """獲取從指定出發地可以到達的所有目的地（未來航班）"""
    try:
        date_str = request.args.get('date')
        _validate_date(date_str, '日期') # 驗證日期格式

        destinations = await SearchService.get_available_destinations(departure_code.upper(), date_str)
        return _success_response(destinations)
    except BadRequest as e:
        return _error_response(str(e), 400)
    except Exception as e:
        current_app.logger.error(f"獲取從 {departure_code} 的可用目的地失敗: {e}", exc_info=True)
        return _error_response('獲取可用目的地失敗', 500)

@flight_bp.route('/popular-routes', methods=['GET'])
@cache.cached(timeout=3600)  # 緩存1小時
def get_popular_routes():
    """獲取熱門航線列表"""
    try:
        # 使用從 constants 導入的熱門航線列表
        return _success_response({
            'domestic': POPULAR_DOMESTIC_ROUTES_DICTS,
            'international': POPULAR_INTERNATIONAL_ROUTES_DICTS
        })
    except Exception as e:
        # 雖然目前是靜態數據，但仍添加錯誤處理以防未來改動
        current_app.logger.error(f"獲取熱門航線時發生錯誤: {e}", exc_info=True)
        return _error_response('獲取熱門航線失敗', 500)

@flight_bp.route('/sync-taiwan-flights', methods=['POST'])
def sync_taiwan_flights():
    """同步台灣出發的航班數據"""
    try:
        data = request.json or {}
        date = data.get('date')
        days_str = data.get('days', '1')
        
        if not date:
            raise BadRequest('必須提供日期參數')
        _validate_date(date, '日期')
        
        try:
            days = int(days_str)
            if days <= 0:
                raise ValueError()
        except (ValueError, TypeError):
            raise BadRequest('天數必須是有效的正整數')
        
        # 初始化同步服務 (如果 DataSyncService 需要 await 初始化，需調整)
        sync_service = DataSyncService() # 假設不需要 await
        
        # 執行同步 (如果 sync_taiwan_flights 是異步，需 await)
        # result = await sync_service.sync_taiwan_flights(date, days)
        # 假設 sync_taiwan_flights 是同步方法
        result = sync_service.sync_taiwan_flights(date, days) 
        return _success_response(result)
    except BadRequest as e:
        return _error_response(str(e), 400)
    except Exception as e:
        current_app.logger.error(f"同步台灣航班失敗: {e}", exc_info=True)
        return _error_response(f'同步失敗: {str(e)}', 500)

@flight_bp.route('/generate-test-data', methods=['POST'])
def generate_test_data():
    """生成測試數據"""
    try:
        data = request.json
        if not data:
            raise BadRequest('缺少請求數據')
            
        departure_iata = data.get('departure')
        arrival_iata = data.get('arrival')
        start_date = data.get('start_date')
        num_days_str = data.get('num_days', '30')
        flights_per_day_str = data.get('flights_per_day', '5')
        
        # 驗證必須參數
        if not departure_iata or not arrival_iata or not start_date:
             raise BadRequest('必須提供出發機場、到達機場和開始日期')
             
        _validate_date(start_date, '開始日期')
        
        try:
            num_days = int(num_days_str)
            flights_per_day = int(flights_per_day_str)
            if num_days <= 0 or flights_per_day <= 0:
                raise ValueError()
        except (ValueError, TypeError):
            raise BadRequest('天數和每日航班數必須是有效的正整數')

        # 使用數據同步服務生成測試數據 (假設是同步靜態方法)
        result = DataSyncService.generate_test_data(
            departure_iata.upper(), arrival_iata.upper(), start_date, num_days, flights_per_day
        )
        
        # 檢查是否有錯誤 (假設服務方法內部會處理並返回帶有 error 鍵的字典)
        if isinstance(result, dict) and 'error' in result:
            return _error_response(result['error'], 400) # 或其他適當狀態碼
            
        return _success_response(result)
    except BadRequest as e:
         return _error_response(str(e), 400)
    except Exception as e:
        current_app.logger.error(f"生成測試數據失敗: {e}", exc_info=True)
        return _error_response('生成測試數據時發生內部錯誤', 500)

@flight_bp.route('/<string:flight_id>/status', methods=['GET'])
@cache.cached(timeout=300) # 添加 5 分鐘緩存
async def refresh_flight_status(flight_id):
    """獲取並返回特定航班的最新狀態 (來自FlightStats)"""
    db_conn = None # 初始化 db_conn
    try:
        current_app.logger.info(f"請求刷新航班狀態: {flight_id}")
        
        # 1. 從數據庫獲取航班信息以調用 FlightStats API
        db_conn = await get_db() # 獲取異步連接
        flight_info_query = """
            SELECT 
                f.airline_id, 
                f.flight_number, 
                f.scheduled_departure 
            FROM flights f 
            WHERE f.flight_id = $1
        """
        flight_record = await db_conn.fetchrow(flight_info_query, flight_id)
        
        if not flight_record:
            raise NotFound(f"在數據庫中找不到航班 ID: {flight_id}")
            
        airline_code = flight_record['airline_id']
        full_flight_number = flight_record['flight_number']
        scheduled_departure = flight_record['scheduled_departure']

        # 提取純數字航班號 (假設格式是 AA123 或 AA 123)
        numerical_flight_number = ''.join(filter(str.isdigit, full_flight_number))
        if not numerical_flight_number:
             # 如果無法提取數字航班號，記錄警告並可能返回錯誤
             current_app.logger.warning(f"無法從 {full_flight_number} 提取數字航班號")
             raise BadRequest("無法解析航班號")

        if not scheduled_departure:
             raise BadRequest("數據庫中航班缺少計劃起飛時間")
             
        date_str = scheduled_departure.strftime('%Y-%m-%d')

        # 2. 調用 FlightStats API
        client = FlightStatsApiClient() 
        # 注意：get_flight_status 是同步方法，如果此控制器在異步環境下運行，
        # 可能需要將其放入線程池執行或將客戶端方法改為異步。
        # 這裡暫時假設可以直接調用。
        status_info = client.get_flight_status(airline_code, numerical_flight_number, date_str)

        # 3. 處理結果
        if status_info:
            current_app.logger.info(f"成功從 FlightStats 獲取航班 {flight_id} 的狀態")
            # 可以只返回需要的狀態信息
            return _success_response({
                'status': status_info.get('status'),
                'status_en': status_info.get('status_en'),
                'actual_departure_time': status_info.get('actual_departure_time'),
                'actual_arrival_time': status_info.get('actual_arrival_time'),
                'gate': status_info.get('gate'),
                'terminal': status_info.get('terminal'),
                'source': 'FlightStats',
                'retrieved_at': datetime.now().isoformat() # 標記刷新時間
            })
        else:
            # FlightStats 未找到或 API 出錯
            current_app.logger.warning(f"無法從 FlightStats 獲取航班 {flight_id} 的狀態")
            # 返回 404 或許更合適，表示在外部源找不到
            return _error_response(f'無法從 FlightStats 獲取航班 {airline_code}{numerical_flight_number} 在 {date_str} 的狀態', 404)

    except NotFound as e:
        return _error_response(str(e), 404)
    except BadRequest as e:
        return _error_response(str(e), 400)
    except Exception as e:
        current_app.logger.error(f"刷新航班 {flight_id} 狀態時發生內部錯誤: {e}", exc_info=True)
        return _error_response('刷新航班狀態時發生內部錯誤', 500)
    finally:
        if db_conn:
            await release_db(db_conn) # 釋放連接