"""
搜索服務模塊
處理航班搜索相關業務邏輯
"""
from datetime import datetime, date
from ..models import Flight, Airport, Airline, TicketPrice
from ..models.base import db
from sqlalchemy import func, and_, or_, exc
from flask import current_app
import traceback

class SearchService:
    """
    航班搜索服務
    處理航班搜索、過濾、排序的邏輯
    """
    
    @staticmethod
    def search_flights(departure_iata, arrival_iata, departure_date, 
                      return_date=None, airline_codes=None, price_min=None, 
                      price_max=None, class_type='經濟'):
        """
        搜索航班
        
        Args:
            departure_iata: 出發機場IATA代碼
            arrival_iata: 到達機場IATA代碼
            departure_date: 出發日期 (YYYY-MM-DD格式)
            return_date: 返回日期 (可選)
            airline_codes: 航空公司代碼列表 (可選)
            price_min: 最低價格 (可選)
            price_max: 最高價格 (可選)
            class_type: 艙等類型 (預設為經濟)
            
        Returns:
            dict: 包含去程和回程航班的結果
        """
        try:
            current_app.logger.info(f"搜索航班: 從 {departure_iata} 到 {arrival_iata}, 日期 {departure_date}, 艙等 {class_type}")
            result = {}
            
            # 轉換日期格式
            if isinstance(departure_date, str):
                current_app.logger.debug(f"轉換日期格式: {departure_date}")
                try:
                    departure_date = datetime.strptime(departure_date, '%Y-%m-%d').date()
                except ValueError as e:
                    current_app.logger.error(f"日期格式錯誤: {e}")
                    return {"error": "日期格式錯誤，請使用YYYY-MM-DD格式"}
            
            if return_date and isinstance(return_date, str):
                try:
                    return_date = datetime.strptime(return_date, '%Y-%m-%d').date()
                except ValueError as e:
                    current_app.logger.error(f"返回日期格式錯誤: {e}")
                    return {"error": "返回日期格式錯誤，請使用YYYY-MM-DD格式"}
            
            # 查詢出發和到達機場
            departure_airport = Airport.get_by_iata(departure_iata)
            arrival_airport = Airport.get_by_iata(arrival_iata)
            
            current_app.logger.debug(f"出發機場: {departure_airport}, 到達機場: {arrival_airport}")
            
            if not departure_airport or not arrival_airport:
                current_app.logger.error(f"找不到機場: {departure_iata} 或 {arrival_iata}")
                return {"error": "找不到指定的機場"}
            
            # 查詢去程航班
            try:
                outbound_flights = SearchService._query_flights(
                    departure_airport.airport_id, 
                    arrival_airport.airport_id, 
                    departure_date,
                    airline_codes,
                    price_min,
                    price_max,
                    class_type
                )
                
                # 格式化結果
                result['outbound_flights'] = SearchService._format_flights(outbound_flights)
                current_app.logger.info(f"找到 {len(result['outbound_flights'])} 個去程航班")
                
                # 如果有返回日期，查詢回程航班
                if return_date:
                    return_flights = SearchService._query_flights(
                        arrival_airport.airport_id,
                        departure_airport.airport_id,
                        return_date,
                        airline_codes,
                        price_min,
                        price_max,
                        class_type
                    )
                    result['return_flights'] = SearchService._format_flights(return_flights)
                    current_app.logger.info(f"找到 {len(result['return_flights'])} 個回程航班")
                
                return result
            except Exception as e:
                current_app.logger.error(f"搜索航班時出錯: {str(e)}")
                current_app.logger.error(traceback.format_exc())
                return {"error": "搜索航班時發生錯誤", "details": str(e)}
                
        except Exception as e:
            current_app.logger.error(f"處理航班搜索請求時出錯: {str(e)}")
            current_app.logger.error(traceback.format_exc())
            return {"error": "處理搜索請求時發生錯誤", "details": str(e)}
    
    @staticmethod
    def _query_flights(departure_airport_id, arrival_airport_id, flight_date, 
                      airline_codes=None, price_min=None, price_max=None, class_type='經濟'):
        """
        查詢符合條件的航班
        
        內部方法，用於構建並執行查詢
        """
        try:
            current_app.logger.debug(f"查詢航班: 從 {departure_airport_id} 到 {arrival_airport_id}, 日期 {flight_date}")
            
            # 首先檢查是否有符合條件的航班（不考慮價格）
            flight_query = db.session.query(Flight).filter(
                Flight.departure_airport_id == departure_airport_id,
                Flight.arrival_airport_id == arrival_airport_id,
                func.date(Flight.scheduled_departure) == flight_date
            )
            
            if airline_codes and len(airline_codes) > 0:
                flight_query = flight_query.join(
                    Airline, Flight.airline_id == Airline.airline_id
                ).filter(Airline.iata_code.in_(airline_codes))
            
            flights = flight_query.all()
            current_app.logger.debug(f"找到 {len(flights)} 個航班（不含價格）")
            
            if not flights:
                current_app.logger.info(f"沒有找到從 {departure_airport_id} 到 {arrival_airport_id} 在 {flight_date} 的航班")
                return []
            
            # 嘗試聯結價格表獲取完整數據
            try:
                # 基本查詢 - 聯結航班、價格和航空公司表
                query = db.session.query(
                    Flight, TicketPrice, Airline
                ).join(
                    TicketPrice, Flight.flight_id == TicketPrice.flight_id, isouter=True
                ).join(
                    Airline, Flight.airline_id == Airline.airline_id
                ).filter(
                    Flight.departure_airport_id == departure_airport_id,
                    Flight.arrival_airport_id == arrival_airport_id,
                    func.date(Flight.scheduled_departure) == flight_date
                )
                
                # 如果指定了艙等類型，加入條件（但使用左連接確保返回所有航班）
                if class_type:
                    query = query.filter(or_(TicketPrice.class_type == class_type, TicketPrice.class_type == None))
                
                # 如果指定了航空公司，添加過濾條件
                if airline_codes and len(airline_codes) > 0:
                    query = query.filter(Airline.iata_code.in_(airline_codes))
                
                # 價格過濾
                if price_min is not None:
                    query = query.filter(or_(TicketPrice.base_price >= price_min, TicketPrice.base_price == None))
                
                if price_max is not None:
                    query = query.filter(or_(TicketPrice.base_price <= price_max, TicketPrice.base_price == None))
                
                # 按起飛時間排序
                query = query.order_by(Flight.scheduled_departure)
                
                results = query.all()
                current_app.logger.debug(f"聯結價格表後找到 {len(results)} 個結果")
                
                # 如果沒有找到結果，返回只有航班和航空公司信息的數據
                if not results:
                    current_app.logger.warning("找到航班但沒有對應的價格數據，使用預設價格")
                    
                    # 手動組合航班和航空公司數據
                    fallback_results = []
                    for flight in flights:
                        airline = db.session.query(Airline).filter(Airline.airline_id == flight.airline_id).first()
                        # 創建一個模擬的TicketPrice對象
                        mock_price = type('MockTicketPrice', (), {
                            'class_type': class_type,
                            'base_price': 0,  # 預設為0
                            'available_seats': 0,  # 預設為0
                        })()
                        fallback_results.append((flight, mock_price, airline))
                    
                    return fallback_results
                
                return results
                
            except exc.SQLAlchemyError as e:
                current_app.logger.error(f"數據庫查詢錯誤: {str(e)}")
                current_app.logger.error(traceback.format_exc())
                # 如果聯結查詢失敗，返回空列表
                return []
                
        except Exception as e:
            current_app.logger.error(f"查詢航班時發生錯誤: {str(e)}")
            current_app.logger.error(traceback.format_exc())
            return []
    
    @staticmethod
    def _format_flights(flight_data):
        """
        格式化航班數據為API響應格式
        """
        try:
            result = []
            
            for item in flight_data:
                # 處理不同格式的數據
                if len(item) == 3:
                    flight, price, airline = item
                else:
                    current_app.logger.warning(f"無法處理的航班數據格式: {item}")
                    continue
                
                # 格式化價格
                if hasattr(price, 'base_price') and price.base_price is not None:
                    formatted_price = float(price.base_price)
                else:
                    formatted_price = None
                
                flight_data = {
                    'flight_id': str(flight.flight_id),
                    'flight_number': flight.flight_number,
                    'airline': {
                        'code': airline.iata_code if hasattr(airline, 'iata_code') else None,
                        'name': airline.name_zh if hasattr(airline, 'name_zh') else None
                    },
                    'departure': {
                        'airport_code': flight.departure_airport.iata_code if hasattr(flight, 'departure_airport') else None,
                        'airport_name': flight.departure_airport.name_zh if hasattr(flight, 'departure_airport') else None,
                        'time': flight.scheduled_departure.isoformat() if flight.scheduled_departure else None,
                        'city': flight.departure_airport.city if hasattr(flight, 'departure_airport') else None
                    },
                    'arrival': {
                        'airport_code': flight.arrival_airport.iata_code if hasattr(flight, 'arrival_airport') else None,
                        'airport_name': flight.arrival_airport.name_zh if hasattr(flight, 'arrival_airport') else None,
                        'time': flight.scheduled_arrival.isoformat() if flight.scheduled_arrival else None,
                        'city': flight.arrival_airport.city if hasattr(flight, 'arrival_airport') else None
                    },
                    'price': formatted_price,
                    'available_seats': price.available_seats if hasattr(price, 'available_seats') else None,
                    'class_type': price.class_type if hasattr(price, 'class_type') else None,
                    'status': flight.status if hasattr(flight, 'status') else None,
                    'duration': str(flight.duration) if (hasattr(flight, 'duration') and flight.duration) else None
                }
                
                result.append(flight_data)
            
            return result
        except Exception as e:
            current_app.logger.error(f"格式化航班數據時出錯: {str(e)}")
            current_app.logger.error(traceback.format_exc())
            return []
    
    @staticmethod
    def get_available_airlines():
        """
        獲取所有可用的航空公司
        
        Returns:
            list: 航空公司列表
        """
        # 使用直接SQL查詢避開country欄位
        airlines = db.session.query(
            Airline.airline_id,
            Airline.iata_code,
            Airline.name_zh,
            Airline.name_en,
            Airline.is_domestic
        ).all()
        
        return [{
            'code': airline.iata_code,
            'name': airline.name_zh or airline.name_en,
            'is_domestic': airline.is_domestic
        } for airline in airlines]
    
    @staticmethod
    def get_taiwan_airports():
        """
        獲取台灣所有機場
        
        Returns:
            list: 機場列表
        """
        # 使用直接SQL查詢避開created_at和updated_at欄位
        airports = db.session.query(
            Airport.airport_id,
            Airport.iata_code,
            Airport.name_zh,
            Airport.name_en,
            Airport.city,
            Airport.country
        ).filter(Airport.country == 'Taiwan').all()
        
        return [{
            'code': airport.iata_code,
            'name': f"{airport.name_zh or airport.name_en} ({airport.iata_code})",  # 中文名稱加IATA代碼
            'city': airport.city
        } for airport in airports]
    
    @staticmethod
    def get_available_destinations(departure_iata):
        """
        獲取從指定出發地可以到達的所有目的地
        
        Args:
            departure_iata: 出發機場IATA代碼
            
        Returns:
            list: 可到達的目的地機場列表
        """
        departure_airport = Airport.get_by_iata(departure_iata)
        
        if not departure_airport:
            return []
            
        # 查詢從該機場出發的所有目的地
        query = db.session.query(
            Airport
        ).join(
            Flight, Flight.arrival_airport_id == Airport.airport_id
        ).filter(
            Flight.departure_airport_id == departure_airport.airport_id
        ).distinct()
        
        destinations = query.all()
        
        return [{
            'code': airport.iata_code,
            'name': f"{airport.name_zh or airport.name_en} ({airport.iata_code})",  # 中文名稱加IATA代碼
            'city': airport.city,
            'country': airport.country
        } for airport in destinations] 