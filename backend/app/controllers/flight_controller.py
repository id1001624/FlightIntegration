"""
航班控制器
處理與航班相關的API請求
"""
from flask import Blueprint, jsonify, request, current_app
from datetime import datetime # 導入 datetime
from werkzeug.exceptions import NotFound, BadRequest # 導入錯誤類型
from marshmallow import ValidationError # 導入 ValidationError
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
    get_routes_for_frontend, # 導入新函數
    POPULAR_DOMESTIC_ROUTES_TUPLES, # 保持導入以備其他用途
    POPULAR_INTERNATIONAL_ROUTES_TUPLES # 保持導入以備其他用途
)
# 從 Schema 模組導入
from ..schemas.flight_schema import flight_search_args_schema, flights_search_result_schema, flight_schema
from ..schemas.airline_schema import airlines_basic_schema
from ..schemas.airport_schema import airports_basic_schema

# 創建藍圖
flight_bp = Blueprint('flight', __name__)

# --- 輔助函數 --- 
def _success_response(data):
    return jsonify({'success': True, 'data': data})

def _error_response(message, status_code):
    if status_code >= 500:
        current_app.logger.error(f"Server Error ({status_code}): {message}")
    else:
        current_app.logger.warning(f"Client Error ({status_code}): {message}")
    # 對於驗證錯誤，message 可能是一個字典
    response_message = message if isinstance(message, str) else str(message)
    return jsonify({'success': False, 'message': response_message}), status_code

# --- API 端點 --- 

@flight_bp.route('/search', methods=['GET'])
async def search_flights():
    """搜索航班"""
    # 1. 使用 Schema 驗證請求參數
    try:
        # request.args 包含查詢參數
        args = flight_search_args_schema.load(request.args)
    except ValidationError as err:
        # 返回清晰的驗證錯誤信息
        # err.messages 是一個字典，包含了錯誤字段和錯誤信息
        return _error_response(f"請求參數驗證失敗: {err.messages}", 400)

    # 提取驗證和處理後的參數
    departure = args['departure'].upper()
    arrival = args['arrival'].upper()
    departure_date = args['date'].strftime('%Y-%m-%d') # 確保是字串格式
    return_date = args.get('return_date').strftime('%Y-%m-%d') if args.get('return_date') else None
    airlines_input = args.get('airlines') # 獲取驗證後的列表或 None
    price_min = args.get('price_min')
    price_max = args.get('price_max')
    class_type = args['class_type']
    only_target_airlines = args['only_target_airlines']
    passengers_int = args['passengers']
    max_results_int = args['max_results']
    sort_by = args['sort_by']

    # 根據 only_target_airlines 決定最終的 airlines 列表
    airlines = None
    if airlines_input:
        airlines = airlines_input # 如果客戶端提供了，使用客戶端提供的
    elif only_target_airlines:
        airlines = TARGET_AIRLINES.copy() # 否則，如果標記為 true，使用目標航司

    try:
        # 使用搜索服務進行查詢，傳遞驗證後的參數
        result_data = await SearchService.search_flights(
            departure, arrival, departure_date,
            airlines, return_date,
            price_min, price_max, class_type,
            passengers_int, max_results_int, sort_by
        )

        # 2. 使用 Schema 序列化響應數據
        # 假設 SearchService 返回的是包含 Flight 模型對象的列表或其他可序列化結構
        # dump 方法會根據 FlightSearchResultSchema 將數據轉換為 JSON 友好的格式
        serialized_flights = flights_search_result_schema.dump(result_data.get('flights', [])) # 假設返回結構中有 'flights' 鍵

        # 構建最終響應
        final_response = {
            'flights': serialized_flights,
            'total': result_data.get('total', len(serialized_flights)) # 使用服務層返回的總數或序列化後的數量
            # 可能還有分頁信息等
        }
        return _success_response(final_response)

    except Exception as e: # 捕捉服務層或其他地方的錯誤
        current_app.logger.error(f"搜索航班時發生未預期錯誤: {e}", exc_info=True)
        return _error_response('搜索航班時發生內部錯誤', 500)

@flight_bp.route('/from_taiwan/<string:arrival_iata>', methods=['GET'])
async def flights_from_taiwan(arrival_iata):
    """獲取從台灣飛往指定目的地的航班"""
    # TODO: 為此端點添加請求參數驗證 (類似 /search)
    # 可以創建一個新的 Schema 或複用部分 FlightSearchArgsSchema
    try:
        # 獲取請求參數 (這裡暫時保留手動處理，建議後續用 Schema 替換)
        departure_date = request.args.get('date')
        airlines_str = request.args.get('airlines')
        price_min_str = request.args.get('price_min')
        price_max_str = request.args.get('price_max')
        class_type = request.args.get('class_type', '經濟')
        passengers = request.args.get('passengers', '1')
        max_results = request.args.get('max_results', '20') # 增加默認限制
        sort_by = request.args.get('sort_by', 'price')
        only_target_airlines = request.args.get('only_target_airlines', 'true').lower() == 'true'

        # 驗證必須參數
        if not departure_date:
            raise BadRequest('必須提供出發日期')

        # 驗證日期格式 (應由 Schema 處理)
        try:
            datetime.strptime(departure_date, '%Y-%m-%d')
        except ValueError:
            raise BadRequest('出發日期格式錯誤，請使用 YYYY-MM-DD')

        # 處理航空公司參數 (應由 Schema 處理)
        airlines = None
        if airlines_str:
            airlines = [a.strip().upper() for a in airlines_str.split(',') if a.strip()]
        elif only_target_airlines:
            airlines = TARGET_AIRLINES.copy()

        # 處理數字參數 (應由 Schema 處理)
        try:
            price_min = float(price_min_str) if price_min_str else None
            price_max = float(price_max_str) if price_max_str else None
            passengers_int = int(passengers)
            max_results_total = int(max_results)
            if passengers_int <= 0 or max_results_total <= 0:
                raise ValueError()
        except (ValueError, TypeError):
            raise BadRequest('價格、乘客數和最大結果數必須是有效的正數')

        # 調用新的服務層方法
        all_outbound_flights_data = await SearchService.search_flights_from_taiwan(
            arrival_iata=arrival_iata.upper(),
            date_str=departure_date,
            airlines=airlines,
            price_min=price_min,
            price_max=price_max,
            class_type=class_type,
            passengers=passengers_int,
            max_results_total=max_results_total,
            sort_by=sort_by
        )

        # 序列化結果
        serialized_flights = flights_search_result_schema.dump(all_outbound_flights_data.get('flights', []))

        # 直接返回服務層處理後的結果
        return _success_response({
            'flights': serialized_flights,
            'total': all_outbound_flights_data.get('total', len(serialized_flights))
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
        flight_details_data = await SearchService.get_flight_details_by_id(flight_id)
        if flight_details_data is None:
            raise NotFound('找不到該航班')
        
        # 序列化結果
        serialized_data = flight_schema.dump(flight_details_data)
        return _success_response(serialized_data)
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
        airlines_data = await SearchService.get_available_airlines()
        
        # 標記目標航空公司
        processed_airlines = []
        for airline_dict in airlines_data:
            airline_dict['is_target'] = airline_dict.get('airline_id') in TARGET_AIRLINES
            processed_airlines.append(airline_dict)

        # 序列化結果
        serialized_data = airlines_basic_schema.dump(processed_airlines)
        return _success_response(serialized_data)
    except Exception as e:
        current_app.logger.error(f"獲取可用航空公司列表失敗: {e}", exc_info=True)
        return _error_response('獲取可用航空公司列表失敗', 500)

@flight_bp.route('/<string:departure_code>/destinations', methods=['GET'])
@cache.cached(timeout=3600, query_string=True)  # 緩存1小時，考慮查詢參數
async def get_available_destinations(departure_code):
    """獲取從指定出發地可以到達的所有目的地（未來航班）"""
    try:
        # TODO: 添加日期參數驗證 (可以使用一個簡單的 Schema)
        date_str = request.args.get('date')
        if not date_str: # 日期是必須的，因為我們要查未來航班的目的地
            raise BadRequest("必須提供日期參數 (date=YYYY-MM-DD)")
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            raise BadRequest('日期格式錯誤，請使用 YYYY-MM-DD')

        destinations_data = await SearchService.get_available_destinations(departure_code.upper(), date_str)
        # 序列化結果
        serialized_data = airports_basic_schema.dump(destinations_data)
        return _success_response(serialized_data)
    except BadRequest as e:
        return _error_response(str(e), 400)
    except Exception as e:
        current_app.logger.error(f"獲取從 {departure_code} 的可用目的地失敗: {e}", exc_info=True)
        return _error_response('獲取可用目的地失敗', 500)

@flight_bp.route('/popular-routes', methods=['GET'])
@cache.cached(timeout=3600)  # 緩存1小時
def get_popular_routes_api(): # 重命名函數避免與 constants 重名
    """獲取熱門航線列表 (分類 domestic/international)"""
    try:
        # 調用 constants 中的函數獲取格式化數據
        routes_data = get_routes_for_frontend()
        # 只返回 popular_routes 部分，已經是格式化好的字典列表
        popular_list = routes_data['popular_routes']

        # 分類
        domestic = [r for r in popular_list if r['departure'] in TAIWAN_AIRPORTS and r['arrival'] in TAIWAN_AIRPORTS]
        international = [r for r in popular_list if not (r['departure'] in TAIWAN_AIRPORTS and r['arrival'] in TAIWAN_AIRPORTS)]

        return _success_response({
            'domestic': domestic,
            'international': international
        })
    except Exception as e:
        current_app.logger.error(f"獲取熱門航線時發生錯誤: {e}", exc_info=True)
        return _error_response('獲取熱門航線失敗', 500)

@flight_bp.route('/all-routes', methods=['GET'])
@cache.cached(timeout=3600) # 緩存1小時
def get_all_routes_api():
    """獲取所有直飛航線列表，包含是否熱門標記"""
    try:
        routes_data = get_routes_for_frontend()
        # 返回 all_routes 部分，已經是格式化好的字典列表
        return _success_response(routes_data['all_routes'])
    except Exception as e:
        current_app.logger.error(f"獲取所有航線時發生錯誤: {e}", exc_info=True)
        return _error_response('獲取所有航線失敗', 500)

@flight_bp.route('/sync-taiwan-flights', methods=['POST'])
def sync_taiwan_flights():
    """同步台灣出發的航班數據"""
    # TODO: 使用 Schema 驗證請求體 ({'date': 'YYYY-MM-DD', 'days': 1})
    try:
        data = request.json or {}
        date = data.get('date')
        days_str = data.get('days', '1')
        
        if not date:
            raise BadRequest('必須提供日期參數')
        # 驗證日期 (應由 Schema 處理)
        try:
            datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
             raise BadRequest('日期格式錯誤，請使用 YYYY-MM-DD')
        
        # 驗證天數 (應由 Schema 處理)
        try:
            days = int(days_str)
            if days <= 0:
                raise ValueError()
        except (ValueError, TypeError):
            raise BadRequest('天數必須是有效的正整數')
        
        sync_service = DataSyncService()
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
    # TODO: 使用 Schema 驗證請求體
    try:
        data = request.json
        if not data:
            raise BadRequest('缺少請求數據')
            
        departure_iata = data.get('departure')
        arrival_iata = data.get('arrival')
        start_date = data.get('start_date')
        num_days_str = data.get('num_days', '30')
        flights_per_day_str = data.get('flights_per_day', '5')
        
        # 驗證必須參數 (應由 Schema 處理)
        if not departure_iata or not arrival_iata or not start_date:
             raise BadRequest('必須提供出發機場、到達機場和開始日期')
        # 驗證日期 (應由 Schema 處理)
        try:
            datetime.strptime(start_date, '%Y-%m-%d')
        except ValueError:
             raise BadRequest('開始日期格式錯誤，請使用 YYYY-MM-DD')
        
        # 驗證數字 (應由 Schema 處理)
        try:
            num_days = int(num_days_str)
            flights_per_day = int(flights_per_day_str)
            if num_days <= 0 or flights_per_day <= 0:
                raise ValueError()
        except (ValueError, TypeError):
            raise BadRequest('天數和每日航班數必須是有效的正整數')

        result = DataSyncService.generate_test_data(
            departure_iata.upper(), arrival_iata.upper(), start_date, num_days, flights_per_day
        )
        
        if isinstance(result, dict) and 'error' in result:
            return _error_response(result['error'], 400)
            
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
    # TODO: 考慮為 flight_id 格式添加驗證 (e.g., UUID)
    db_conn = None
    try:
        current_app.logger.info(f"請求刷新航班狀態: {flight_id}")
        
        db_conn = await get_db()
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

        numerical_flight_number = ''.join(filter(str.isdigit, full_flight_number))
        if not numerical_flight_number:
             current_app.logger.warning(f"無法從 {full_flight_number} 提取數字航班號")
             raise BadRequest("無法解析航班號")

        if not scheduled_departure:
             raise BadRequest("數據庫中航班缺少計劃起飛時間")
             
        date_str = scheduled_departure.strftime('%Y-%m-%d')

        client = FlightStatsApiClient()
        status_info = client.get_flight_status(airline_code, numerical_flight_number, date_str)

        if status_info:
            current_app.logger.info(f"成功從 FlightStats 獲取航班 {flight_id} 的狀態")
            # TODO: 使用 Schema 序列化 status_info
            return _success_response({
                'status': status_info.get('status'),
                'status_en': status_info.get('status_en'),
                'actual_departure_time': status_info.get('actual_departure_time'),
                'actual_arrival_time': status_info.get('actual_arrival_time'),
                'gate': status_info.get('gate'),
                'terminal': status_info.get('terminal'),
                'source': 'FlightStats',
                'retrieved_at': datetime.now().isoformat()
            })
        else:
            current_app.logger.warning(f"無法從 FlightStats 獲取航班 {flight_id} 的狀態")
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