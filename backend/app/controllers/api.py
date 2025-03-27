# 引入需要的工具
from flask import Blueprint, request, jsonify
from app.models.flights import Flights
from app.models.airports import Airports
from app.models.airlines import Airlines
from app import db
from datetime import datetime, timedelta
from sqlalchemy import and_, or_

# 建立一個藍圖，用來組織相關的路由
api = Blueprint('api', __name__)

# 定義一個路由，用來獲取所有機場列表
@api.route('/airports', methods=['GET'])
def get_airports():
    """獲取所有機場資訊，前端下拉選單會用到"""
    airports = Airports.query.all()  # 從資料庫獲取所有機場
    return jsonify({
        'success': True,
        'data': [airport.to_dict() for airport in airports]  # 將每個機場轉成字典並放入列表
    })

# 定義一個路由，用來獲取所有航空公司列表
@api.route('/airlines', methods=['GET'])
def get_airlines():
    """獲取所有航空公司資訊，前端下拉選單會用到"""
    airlines = Airlines.query.all()  # 從資料庫獲取所有航空公司
    return jsonify({
        # 後端API使用 jsonify() 函數將Python物件轉換為JSON格式
        'success': True,
        'data': [airline.to_dict() for airline in airlines]  # 將每個航空公司轉成字典並放入列表
    })

# 定義一個路由，用來查詢航班
@api.route('/flights/search', methods=['GET'])
def search_flights():
    # 基本參數
    departure_code = request.args.get('departure_airport')
    arrival_code = request.args.get('arrival_airport')
    departure_date_str = request.args.get('departure_date')
    is_round_trip = request.args.get('is_round_trip', 'false').lower() == 'true'
    return_date_str = request.args.get('return_date')
    
    # 新增參數
    direct_only = request.args.get('direct_only', 'false').lower() == 'true'
    sort_by = request.args.get('sort_by', 'price')  # 預設按價格排序
    sort_order = request.args.get('sort_order', 'asc')  # 預設升序
    
    # 檢查必要參數是否存在
    if not (departure_code and arrival_code and departure_date_str):
        return jsonify({
            'success': False,
            'message': '請提供出發機場、目的地機場和出發日期'
        }), 400  # 400 代表錯誤的請求
    
    if is_round_trip and not return_date_str:
        return jsonify({
            'success': False,
            'message': '來回機票必須提供回程日期'
        }), 400
    
    try:
        # 將日期字串轉成日期對象
        departure_date = datetime.strptime(departure_date_str, '%Y-%m-%d')
        
        # 獲取出發和目的地機場的ID
        departure_airport = Airports.query.filter_by(code=departure_code).first()
        arrival_airport = Airports.query.filter_by(code=arrival_code).first()
        
        if not departure_airport or not arrival_airport:
            return jsonify({
                'success': False,
                'message': '無法找到指定的機場'
            }), 404  # 404 代表找不到資源
        
        # 開始構建查詢條件
        query_conditions = [
            Flights.departure_airport_id == departure_airport.id,
            Flights.arrival_airport_id == arrival_airport.id
        ]
        
        # 處理日期範圍查詢
        date_range = request.args.get('date_range', 'false').lower() == 'true'
        if date_range:
            # 取得日期範圍天數，預設為7天，最大為30天
            date_range_days = min(int(request.args.get('date_range_days', 7)), 30)
            end_date = departure_date + timedelta(days=date_range_days)
            
            # 查詢條件：出發日期在指定範圍內
            query_conditions.append(
                and_(
                    db.func.date(Flights.departure_time) >= departure_date.date(),
                    db.func.date(Flights.departure_time) <= end_date.date()
                )
            )
        else:
            # 如果不是範圍查詢，就只查詢指定日期
            query_conditions.append(db.func.date(Flights.departure_time) == departure_date.date())

        # 如果要求只顯示直飛航班
        if direct_only:
            query_conditions.append(Flights.is_direct == True)

        # 根據排序參數決定排序方式
        if sort_by == 'price':
            if sort_order == 'asc':
                flights = Flights.query.filter(and_(*query_conditions)).order_by(Flights.price.asc()).all()
            else:
                flights = Flights.query.filter(and_(*query_conditions)).order_by(Flights.price.desc()).all()
        elif sort_by == 'departure_time':
            if sort_order == 'asc':
                flights = Flights.query.filter(and_(*query_conditions)).order_by(Flights.departure_time.asc()).all()
            else:
                flights = Flights.query.filter(and_(*query_conditions)).order_by(Flights.departure_time.desc()).all()
        else:
            # 預設排序
            flights = Flights.query.filter(and_(*query_conditions)).all()
        
        # 處理航空公司篩選
        airline_id = request.args.get('airline_id')
        if airline_id:
            query_conditions.append(Flights.airline_id == int(airline_id))
        
        # 處理價格範圍篩選
        min_price = request.args.get('min_price')
        if min_price:
            query_conditions.append(Flights.price >= float(min_price))
            
        max_price = request.args.get('max_price')
        if max_price:
            query_conditions.append(Flights.price <= float(max_price))
        
        # 執行查詢
        flights = Flights.query.filter(and_(*query_conditions)).all()
        # 將去程航班轉換為字典列表
        result_data = [flight.to_dict() for flight in flights]

         # 如果是去程航班，添加類型標記
        if is_round_trip:
            for flight in result_data:
                flight['trip_type'] = 'outbound'
        
        # 如果是來回機票，查詢回程航班
        if is_round_trip and return_date_str:
            return_date = datetime.strptime(return_date_str, '%Y-%m-%d')
            
            # 構建回程查詢條件 (起點和終點對調)
            return_conditions = [
                Flights.departure_airport_id == arrival_airport.id,
                Flights.arrival_airport_id == departure_airport.id,
                db.func.date(Flights.departure_time) == return_date.date()
            ]
            
            # 附加其他篩選條件（航空公司、價格等）
            if airline_id:
                return_conditions.append(Flights.airline_id == int(airline_id))
            if min_price:
                return_conditions.append(Flights.price >= float(min_price))
            if max_price:
                return_conditions.append(Flights.price <= float(max_price))
            
            # 查詢回程航班
            return_flights = Flights.query.filter(and_(*return_conditions)).all()
            
            # 處理回程結果並合併
            return_data = [flight.to_dict() for flight in return_flights]
            for flight in return_data:
                flight['trip_type'] = 'return'
            
            # 合併結果
            result_data.extend(return_data)
        
        # 將查詢結果返回
        return jsonify({
            'success': True,
            'data': result_data
        })
        
    except Exception as e:
        # 捕獲可能的錯誤
        return jsonify({
            'success': False,
            'message': f'搜尋時發生錯誤: {str(e)}'
        }), 500

# 定義一個路由，用來測試TDX API連線
@api.route('/tdx/test', methods=['GET'])
def test_tdx_api():
    """測試TDX API連線"""
    from app.services.tdx_service import TDXService
    
    tdx = TDXService()
    result = tdx.get_airport_flights()
    
    return jsonify(result)

# 定義路由，用來從TDX同步航班資料
@api.route('/admin/sync-flights', methods=['POST'])
def sync_flights():
    """從TDX同步航班資料，並初始化必要的基礎資料"""
    from app.services.tdx_service import TDXService
    
    tdx = TDXService()
    
    # 更新基本資料 (航空公司和機場)
    try:
        # 先更新航空公司資料
        airlines_result = tdx.update_airlines()
        if not airlines_result['success']:
            return jsonify({
                'success': False,
                'message': f'更新航空公司資料失敗: {airlines_result["message"]}'
            }), 500
            
        # 然後更新機場資料
        airports_result = tdx.update_airports()
        if not airports_result['success']:
            return jsonify({
                'success': False,
                'message': f'更新機場資料失敗: {airports_result["message"]}'
            }), 500
            
        # 最後同步航班資料
        flights_result = tdx.sync_flight_data()
        
        # 回傳完整結果
        return jsonify({
            'success': flights_result['success'],
            'message': flights_result['message'],
            'details': {
                'airlines': airlines_result['message'],
                'airports': airports_result['message']
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'同步資料過程發生錯誤: {str(e)}'
        }), 500