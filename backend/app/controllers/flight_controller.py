#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
from ..database.db import get_pool # <-- Import get_pool instead of get_db/release_db
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
from ..schemas.flight_schema import (
    flight_search_args_schema, 
    flights_search_result_schema, 
    flight_schema,
    flights_from_taiwan_args_schema, # 新增導入
    flight_status_schema, # 新增導入
    sync_taiwan_flights_args_schema, # 新增導入
    generate_test_data_args_schema, # 新增導入
    FlightSchema,
    FlightSearchArgsSchema
)
from ..schemas.airline_schema import airlines_schema, airlines_basic_schema
from ..schemas.airport_schema import airports_basic_schema
from webargs.flaskparser import use_args
import logging
import asyncpg

# 創建藍圖
flight_bp = Blueprint('flight', __name__)
logger = logging.getLogger(__name__)

# 初始化 Schema
flight_schema = FlightSchema()
flight_schema_many = FlightSchema(many=True)
search_args_schema = FlightSearchArgsSchema()

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
@use_args(search_args_schema, location="query")
async def search_flights(args):
    """搜索航班"""
    # 1. 參數驗證 (保持不變)
    try:
        args = flight_search_args_schema.load(request.args)
    except ValidationError as err:
        return _error_response(f"請求參數驗證失敗: {err.messages}", 400)

    # 提取驗證後的參數 (保持不變)
    departure = args['departure'].upper()
    arrival = args['arrival'].upper()
    departure_date = args['date'].strftime('%Y-%m-%d')
    return_date = args.get('return_date').strftime('%Y-%m-%d') if args.get('return_date') else None
    airlines_input = args.get('airlines')
    price_min = args.get('price_min')
    price_max = args.get('price_max')
    class_type = args['class_type'] # e.g., "經濟", "商務"
    only_target_airlines = args['only_target_airlines']
    passengers_int = args['passengers']
    max_results_int = args['max_results']
    sort_by = args['sort_by']

    # 處理 airlines 列表 (保持不變)
    airlines = None
    if airlines_input:
        airlines = airlines_input
    elif only_target_airlines:
        airlines = TARGET_AIRLINES.copy()

    pool = None
    conn = None
    try:
        # --- Connection Management Start ---
        pool = await get_pool()
        conn = await pool.acquire()
        # -----------------------------------
        
        # 2. 調用服務層獲取數據，傳入 conn
        service_result = await SearchService.search_flights(
            conn, # Pass the acquired connection
            departure, arrival, departure_date,
            airlines, return_date,
            price_min, price_max, class_type,
            passengers_int, max_results_int, sort_by
        )
        
        # 3. ***修正: 直接從 service_result 提取 departure 和 return 列表***
        departure_flights_list = service_result.get("departure", [])
        return_flights_list = service_result.get("return", []) # 如果沒有回程，會是空列表

        # 4. 使用 Schema 序列化提取出的航班列表
        serialized_departure = flights_search_result_schema.dump(departure_flights_list)
        serialized_return = flights_search_result_schema.dump(return_flights_list)

        # 5. ***修正: 構建包含新鍵名的最終響應***
        final_response = {
            'departure': serialized_departure, # 使用 'departure'
            # 可以選擇性地包含總數或其他元數據
            # 'total_departure': len(serialized_departure)
        }
        # 只有當請求了回程且實際有回程數據時才添加 return 鍵
        if return_date and serialized_return: 
            final_response['return'] = serialized_return # 使用 'return'
            # 'total_return': len(serialized_return)

        # 返回包含新鍵名的成功響應
        return _success_response(final_response)

    except Exception as e: 
        # Catch errors from service layer or connection management
        current_app.logger.error(f"搜索航班控制器層發生錯誤: {e}", exc_info=True)
        return _error_response('搜索航班時發生內部錯誤', 500)
    finally:
        # --- Connection Management End ---
        if conn and pool:
            try:
                await pool.release(conn)
            except (RuntimeError, asyncpg.exceptions.InterfaceError) as e:
                current_app.logger.warning(f"在釋放搜索航班連接時發生可忽略的異常: {e}")
            except Exception as e:
                current_app.logger.error(f"在釋放搜索航班連接時發生未預期的異常: {e}", exc_info=True)
        # -------------------------------

@flight_bp.route('/from_taiwan/<string:arrival_iata>', methods=['GET'])
async def flights_from_taiwan(arrival_iata):
    """獲取從台灣飛往指定目的地的航班"""
    # 使用 Schema 進行驗證
    try:
        args = flights_from_taiwan_args_schema.load(request.args)
    except ValidationError as err:
        return _error_response(f"請求參數驗證失敗: {err.messages}", 400)

    # 提取驗證後的參數
    departure_date = args['date'].strftime('%Y-%m-%d')
    airlines_input = args.get('airlines') # 獲取驗證後的列表或 None
    price_min = args.get('price_min')
    price_max = args.get('price_max')
    class_type = args['class_type']
    passengers_int = args['passengers']
    max_results_total = args['max_results']
    sort_by = args['sort_by']
    only_target_airlines = args['only_target_airlines']

    # 處理 only_target_airlines 邏輯
    airlines = None
    if airlines_input:
        # Schema 返回的是字符串列表，不需要再 split
        airlines = [a.strip().upper() for a in airlines_input if a.strip()]
    elif only_target_airlines:
        airlines = TARGET_AIRLINES.copy()

    try:
        # 調用新的服務層方法
        all_outbound_flights_list = await SearchService.search_flights_from_taiwan(
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

        # 序列化結果 (直接序列化返回的列表)
        serialized_flights = flights_search_result_schema.dump(all_outbound_flights_list)

        # 返回結果
        return _success_response({
            'flights': serialized_flights,
            'total': len(serialized_flights) # 計算返回列表的長度
        })

    except BadRequest as e:
        return _error_response(str(e), 400)
    except Exception as e:
        current_app.logger.error(f"獲取從台灣出發的航班控制器層發生錯誤: {e}", exc_info=True)
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
@cache.cached(timeout=3600)  # 快取1小時
async def get_airlines():
    """獲取可用航空公司列表"""
    try:
        airlines = await SearchService.get_available_airlines()
        # 直接返回服務提供的數據，不使用 Schema 序列化
        return _success_response(airlines)
    except Exception as e:
        current_app.logger.error(f"獲取航空公司列表失敗: {str(e)}")
        return _error_response("獲取航空公司列表失敗", 500)

@flight_bp.route('/<string:departure_code>/destinations', methods=['GET'])
@cache.cached(timeout=3600, query_string=True)  # 緩存1小時，考慮查詢參數
async def get_available_destinations(departure_code):
    """獲取從指定出發地可以到達的所有目的地（所有航班記錄）
    
    Note:
        日期參數現在是可選的，返回結果包含所有日期的航班目的地
    """
    try:
        # 日期參數現在是可選的，但為了向後兼容，仍然處理它
        date_str = request.args.get('date')
        
        # 如果提供了日期，驗證格式
        if date_str:
            try:
                datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                raise BadRequest('日期格式錯誤，請使用 YYYY-MM-DD')

        # 調用服務獲取目的地，不再強制要求日期參數
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
    # 使用 Schema 驗證請求體
    try:
        args = sync_taiwan_flights_args_schema.load(request.json or {})
    except ValidationError as err:
        return _error_response(f"請求參數驗證失敗: {err.messages}", 400)
        
    # 提取驗證後的參數
    date_str = args['date'].strftime('%Y-%m-%d')
    days = args['days']
        
    try:
        sync_service = DataSyncService()
        result = sync_service.sync_taiwan_flights(date_str, days)
        return _success_response(result)
    # except BadRequest as e: # 服務層一般不應拋出 BadRequest，控制器層處理驗證
    #     return _error_response(str(e), 400)
    except Exception as e:
        current_app.logger.error(f"同步台灣航班失敗: {e}", exc_info=True)
        return _error_response(f'同步失敗: {str(e)}', 500)

@flight_bp.route('/generate-test-data', methods=['POST'])
def generate_test_data():
    """生成測試數據"""
    # 使用 Schema 驗證請求體
    try:
        args = generate_test_data_args_schema.load(request.json or {})
    except ValidationError as err:
        return _error_response(f"請求參數驗證失敗: {err.messages}", 400)
            
    # 提取驗證後的參數
    departure_iata = args['departure']
    arrival_iata = args['arrival']
    start_date = args['start_date'].strftime('%Y-%m-%d')
    num_days = args['num_days']
    flights_per_day = args['flights_per_day']
        
    try:
        result = DataSyncService.generate_test_data(
            departure_iata.upper(), 
            arrival_iata.upper(), 
            start_date, 
            num_days, 
            flights_per_day
        )
        
        if isinstance(result, dict) and 'error' in result:
            # 服務層返回的特定錯誤 (如找不到機場) 可以保持 400
            return _error_response(result['error'], 400)
            
        return _success_response(result)
    # except BadRequest as e: # 服務層一般不應拋出 BadRequest
    #      return _error_response(str(e), 400)
    except Exception as e:
        current_app.logger.error(f"生成測試數據失敗: {e}", exc_info=True)
        return _error_response('生成測試數據時發生內部錯誤', 500)

@flight_bp.route('/<string:flight_id>/status', methods=['GET'])
@cache.cached(timeout=300) # 添加 5 分鐘緩存
async def refresh_flight_status(flight_id):
    """獲取並返回特定航班的最新狀態 (來自FlightStats)"""
    # TODO: 考慮為 flight_id 格式添加驗證 (e.g., UUID)
    pool = None
    try:
        current_app.logger.info(f"請求刷新航班狀態: {flight_id}")
        
        pool = await get_pool()
        flight_info_query = """
            SELECT 
                f.airline_id, 
                f.flight_number, 
                f.scheduled_departure 
            FROM flights f 
            WHERE f.flight_id = $1
        """
        flight_record = await pool.fetchrow(flight_info_query, flight_id)
        
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
            # 準備要序列化的數據
            status_data = {
                'status': status_info.get('status'),
                'status_en': status_info.get('status_en'),
                'actual_departure_time': status_info.get('actual_departure_time'),
                'actual_arrival_time': status_info.get('actual_arrival_time'),
                'gate': status_info.get('gate'),
                'terminal': status_info.get('terminal'),
                'source': 'FlightStats',
                'retrieved_at': datetime.now() # 直接使用 datetime 對象
            }
            # 使用 Schema 序列化
            serialized_status = flight_status_schema.dump(status_data)
            return _success_response(serialized_status)
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

@flight_bp.route('/popular', methods=['GET'])
async def get_popular_flights_endpoint():
    """
    獲取熱門航線的未來航班
    ---
    tags:
      - Flights
    parameters:
      - in: query
        name: limit
        schema:
          type: integer
          default: 20
        description: 返回的最大航班數量
      - in: query
        name: cabin_class
        schema:
          type: string
          default: "經濟"
        description: 用於格式化價格的艙等 (經濟, 商務, 頭等)
    responses:
      200:
        description: 熱門航班列表
        content:
          application/json:
            schema:
              type: array
              items: FlightSchema
      500:
        description: 伺服器內部錯誤
    """
    try:
        limit = request.args.get('limit', 20, type=int)
        cabin_class = request.args.get('cabin_class', "經濟")
        
        # 限制最大結果數，防止濫用
        limit = min(limit, 100) 

        logger.info(f"接收到熱門航班請求: limit={limit}, cabin_class={cabin_class}")
        flights = await SearchService.get_popular_flights(max_results=limit, cabin_class=cabin_class)
        
        # 使用 Schema 序列化結果
        result = flight_schema_many.dump(flights)
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"處理 /popular 請求時出錯: {e}", exc_info=True)
        return jsonify({"error": "無法獲取熱門航班信息"}), 500

@flight_bp.route('/from_taiwan/<string:arrival_iata>', methods=['GET'])
async def get_from_taiwan_flights_endpoint(arrival_iata: str):
    """
    獲取從台灣機場出發到指定目的地的航班
    ---
    tags:
      - Flights
    parameters:
      - in: path
        name: arrival_iata
        required: true
        schema:
          type: string
        description: 到達機場的IATA代碼 (例如 NRT, HKG)
      - in: query
        name: date
        required: true
        schema:
          type: string
          format: date
        description: 查詢日期 (YYYY-MM-DD)
      - in: query
        name: limit
        schema:
          type: integer
          default: 50
        description: 返回的最大航班數量
      - in: query
        name: cabin_class
        schema:
          type: string
          default: "經濟"
        description: 用於格式化價格的艙等 (經濟, 商務, 頭等)
    responses:
      200:
        description: 從台灣出發的航班列表
        content:
          application/json:
            schema:
              type: array
              items: FlightSchema
      400:
        description: 請求參數錯誤 (例如日期格式錯誤)
      500:
        description: 伺服器內部錯誤
    """
    date_str = request.args.get('date')
    limit = request.args.get('limit', 50, type=int)
    cabin_class = request.args.get('cabin_class', "經濟")

    if not date_str:
        return jsonify({"error": "必須提供 'date' 查詢參數 (YYYY-MM-DD)"}), 400

    # 驗證日期格式
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return jsonify({"error": f"日期格式錯誤: '{date_str}', 請使用 YYYY-MM-DD 格式"}), 400
        
    # 限制最大結果數
    limit = min(limit, 150)

    try:
        arrival_iata_upper = arrival_iata.upper()
        logger.info(f"接收到台灣出發請求: arrival={arrival_iata_upper}, date={date_str}, limit={limit}, cabin_class={cabin_class}")
        
        flights = await SearchService.get_flights_from_taiwan(
            arrival_iata=arrival_iata_upper, 
            date_str=date_str, 
            max_results=limit, 
            cabin_class=cabin_class
        )
        
        # 使用 Schema 序列化結果
        result = flight_schema_many.dump(flights)
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"處理 /from_taiwan/{arrival_iata} 請求時出錯: {e}", exc_info=True)
        return jsonify({"error": f"無法獲取從台灣到 {arrival_iata} 的航班信息"}), 500

@flight_bp.route('/api/debug/airports', methods=['GET'])
async def debug_airports():
    """列出資料庫中所有機場，用於偵錯"""
    # 使用連接池初始化函數代替舊的方式
    
    # ... 代碼實現 ...