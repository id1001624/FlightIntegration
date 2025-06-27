from flask import Blueprint, current_app, jsonify
from flask_restx import Api, Resource, reqparse
from asgiref.sync import async_to_sync
from ..services.amadeus_service import amadeus_service
from ..adapters.amadeus_adapter import adapt_flight_destinations
from ..adapters.amadeus_offers_adapter import adapt_flight_offers

# 創建一個 Blueprint
amadeus_bp = Blueprint('amadeus', __name__, url_prefix='/api/amadeus')

# 將 Blueprint 與 flask-restx Api 關聯
# 這允許我們在 Blueprint 上定義路由，同時利用 swagger 文件功能
api = Api(amadeus_bp, version='1.0', title='Amadeus API',
          description='Endpoints for interacting with Amadeus API')

# 定義一個 namespace，用於組織相關的路由
ns = api.namespace('flights', description='Flight Search Operations')

@ns.route('/offers')
class FlightOffers(Resource):
    """
    獲取指定航線的具體航班報價。
    """
    @ns.doc(params={
        'origin': {'description': 'Origin airport IATA code', 'in': 'query', 'type': 'string', 'required': True},
        'destination': {'description': 'Destination airport IATA code', 'in': 'query', 'type': 'string', 'required': True},
        'date': {'description': 'Departure date in YYYY-MM-DD format', 'in': 'query', 'type': 'string', 'required': True}
    })
    @async_to_sync
    async def get(self):
        """
        根據出發地、目的地和日期搜索航班
        """
        parser = reqparse.RequestParser()
        parser.add_argument('origin', type=str, required=True, help='Origin airport code cannot be blank')
        parser.add_argument('destination', type=str, required=True, help='Destination airport code cannot be blank')
        parser.add_argument('date', type=str, required=True, help='Departure date cannot be blank')
        args = parser.parse_args()

        try:
            # 現在可以直接 await
            flight_offers_response = await amadeus_service.search_flight_offers(
                origin=args['origin'],
                destination=args['destination'],
                departure_date=args['date']
            )

            # 防禦性檢查：確保服務層沒有返回None
            if flight_offers_response is None:
                current_app.logger.error("Amadeus service returned None, indicating an internal issue.")
                return {"message": "伺服器內部查詢服務時發生未預期的錯誤。"}, 500

            # 首先檢查 Amadeus API 是否返回錯誤
            if 'errors' in flight_offers_response:
                current_app.logger.error(f"Amadeus API error: {flight_offers_response['errors']}")
                return flight_offers_response, 500

            # 其次檢查 data 陣列是否為空
            if not flight_offers_response.get('data'):
                return {
                    "message": "查詢成功，但未找到符合條件的航班。",
                    "data": []
                }, 200

            # 成功找到航班，應用新的數據適配器
            adapted_data = await adapt_flight_offers(flight_offers_response)

            return {
                "success": True,
                "message": f"成功處理了 {len(adapted_data)} 筆航班。",
                "data": adapted_data,
            }, 200

        except Exception as e:
            # 捕捉服務調用時可能發生的異常 (例如網絡問題)
            current_app.logger.error(f"Error in FlightOffers resource: {e}", exc_info=True)
            return {"message": "伺服器內部發生錯誤"}, 500

@ns.route('/destinations/<string:origin_iata_code>')
@ns.doc(params={'origin_iata_code': 'The IATA code of the origin airport (e.g., MAD for Madrid)'})
class FlightDestinations(Resource):
    """
    獲取指定出發地的航班目的地。
    """
    @ns.doc(description='Fetches a list of flight destinations from a given origin.')
    @ns.response(200, 'Success')
    @ns.response(404, 'No destinations found')
    @ns.response(500, 'Internal server error')
    @async_to_sync
    async def get(self, origin_iata_code):
        """
        根據出發機場 IATA 代碼查詢可飛往的目的地
        """
        try:
            # 現在可以直接 await
            raw_destinations = await amadeus_service.search_flight_destinations(origin_iata_code)
            
            if not raw_destinations or raw_destinations.get("errors"):
                # 如果沒有數據或 Amadeus 返回錯誤，直接回傳
                error_message = raw_destinations or {'message': 'No destinations found for the given origin.'}
                status_code = 500 if raw_destinations and raw_destinations.get("errors") else 404
                return error_message, status_code

            # 使用適配器轉換數據
            adapted_data = await adapt_flight_destinations(raw_destinations)
            
            return jsonify(adapted_data)
            
        except Exception as e:
            current_app.logger.error(f"Error in FlightDestinations resource: {e}", exc_info=True)
            return {"message": "伺服器內部發生錯誤"}, 500

@ns.route('/airport-destinations/<string:departure_airport_code>')
@ns.doc(params={'departure_airport_code': 'The IATA code of the departure airport (e.g., TPE for Taipei)'})
class AirportDestinations(Resource):
    """
    使用 Amadeus Airport Routes API 獲取從指定機場出發的所有直達目的地。
    這個端點提供即時的目的地資訊，與航班查詢使用相同的數據源。
    """
    @ns.doc(description='Fetches all direct destinations from a given airport using Amadeus Airport Routes API.')
    @ns.response(200, 'Success')
    @ns.response(404, 'No destinations found')
    @ns.response(500, 'Internal server error')
    @async_to_sync
    async def get(self, departure_airport_code):
        """
        根據出發機場 IATA 代碼查詢所有可直達的目的地機場
        """
        try:
            # 調用新的 Airport Routes API 方法
            raw_destinations = await amadeus_service.get_airport_destinations(departure_airport_code)
            
            # 檢查是否有錯誤
            if 'error' in raw_destinations:
                current_app.logger.error(f"Amadeus Airport Routes API error: {raw_destinations}")
                return {
                    "success": False, 
                    "message": f"無法獲取 {departure_airport_code} 機場的目的地資訊",
                    "error": raw_destinations.get('error')
                }, 500

            # 檢查是否有數據
            destinations_data = raw_destinations.get('data', [])
            if not destinations_data:
                return {
                    "success": False,
                    "message": f"未找到從 {departure_airport_code} 機場出發的目的地",
                    "data": []
                }, 404

            # 引入 airport_service 獲取中文名稱
            from ..services.airport_service import AirportService
            
            # 轉換數據格式以符合前端預期，並獲取中文名稱
            formatted_destinations = []
            for destination in destinations_data:
                iata_code = destination.get('iataCode', '')
                
                # 從本地資料庫獲取機場詳細資訊（包含中文名稱）
                local_airport_info = await AirportService.get_airport_by_iata(iata_code)
                
                # 優先使用本地資料庫的中文名稱，如果沒有則使用 Amadeus 的英文名稱
                if local_airport_info:
                    airport_name_zh = local_airport_info.get('name_zh', destination.get('name', ''))
                    airport_city = local_airport_info.get('city', destination.get('name', ''))
                    airport_country = local_airport_info.get('country', '')
                else:
                    airport_name_zh = destination.get('name', '')
                    airport_city = destination.get('name', '')
                    airport_country = ""
                
                formatted_destinations.append({
                    "airport_id": iata_code,
                    "name": destination.get('name', ''),
                    "name_zh": airport_name_zh,
                    "city": airport_city,
                    "country": airport_country,
                    "region": airport_country if airport_country else "國際"
                })

            current_app.logger.info(f"Successfully fetched {len(formatted_destinations)} destinations for {departure_airport_code}")
            
            return {
                "success": True,
                "message": f"成功獲取 {len(formatted_destinations)} 個目的地",
                "data": formatted_destinations,
                "meta": {
                    "total": len(formatted_destinations),
                    "source": "amadeus_airport_routes"
                }
            }, 200
            
        except Exception as e:
            current_app.logger.error(f"Error in AirportDestinations resource: {e}", exc_info=True)
            return {
                "success": False,
                "message": "伺服器內部發生錯誤",
                "error": str(e)
            }, 500 