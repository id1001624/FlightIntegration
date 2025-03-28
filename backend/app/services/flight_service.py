import requests
import json
from datetime import datetime, timedelta
import os
from flask import current_app
from sqlalchemy import and_, or_, desc, func
import uuid

from app.models import db, Flight, Airport, Airline, TicketPrice, PriceHistory, Weather, FlightPrediction
from app.services.tdx_service import TDXService

class FlightService:
    """航班服務類，處理航班查詢、票價分析等功能"""
    
    def __init__(self, test_mode=False):
        self.test_mode = test_mode
        self.tdx_service = TDXService(test_mode=test_mode)
        
        # Cirium FlightStats API配置
        self.flightstats_app_id = "cb5c8184"
        self.flightstats_app_key = "82304b41352d18995b0e7440a977cc1b"
        self.flightstats_base_url = "https://api.flightstats.com/flex"
    
    def search_flights(self, params):
        """搜索航班"""
        # 提取參數
        departure_airport = params.get('departure_airport')
        arrival_airport = params.get('arrival_airport')
        departure_date = params.get('departure_date')
        return_date = params.get('return_date')
        airline_code = params.get('airline_code')
        min_price = params.get('min_price')
        max_price = params.get('max_price')
        sort_by = params.get('sort_by', 'departure_time')
        sort_order = params.get('sort_order', 'asc')
        is_direct_only = params.get('is_direct_only', False)
        
        # 檢查必填參數
        if not all([departure_airport, arrival_airport, departure_date]):
            return {'success': False, 'message': '請提供出發機場、目的地機場和出發日期'}
        
        try:
            # 轉換日期格式
            dep_date = datetime.strptime(departure_date, '%Y-%m-%d')
            ret_date = None
            if return_date:
                ret_date = datetime.strptime(return_date, '%Y-%m-%d')
            
            # 查詢機場ID
            dep_airport = Airport.query.filter_by(iata_code=departure_airport).first()
            arr_airport = Airport.query.filter_by(iata_code=arrival_airport).first()
            
            if not dep_airport or not arr_airport:
                return {'success': False, 'message': '無法找到指定的機場'}
            
            # 構建基本查詢條件
            outbound_conditions = [
                Flight.departure_airport_id == dep_airport.id,
                Flight.arrival_airport_id == arr_airport.id,
                func.date(Flight.scheduled_departure_time) == dep_date.date(),
                Flight.is_test_data == self.test_mode
            ]
            
            # 處理其他篩選條件
            if airline_code:
                airline = Airline.query.filter_by(iata_code=airline_code).first()
                if airline:
                    outbound_conditions.append(Flight.airline_id == airline.id)
            
            if is_direct_only:
                outbound_conditions.append(Flight.is_direct_flight == True)
            
            # 設定排序
            order_by = Flight.scheduled_departure_time
            if sort_by == 'departure_time':
                order_by = Flight.scheduled_departure_time
            elif sort_by == 'arrival_time':
                order_by = Flight.scheduled_arrival_time
            elif sort_by == 'price':
                # 票價排序需要特殊處理
                pass
                
            if sort_order == 'desc':
                order_by = desc(order_by)
            
            # 執行查詢
            outbound_flights = Flight.query.filter(and_(*outbound_conditions)).order_by(order_by).all()
            
            # 格式化去程航班結果
            result_data = []
            for flight in outbound_flights:
                flight_data = flight.to_dict()
                flight_data['trip_type'] = 'outbound'
                
                # 獲取票價資訊
                ticket_price = TicketPrice.query.filter_by(
                    flight_id=flight.id,
                    is_test_data=self.test_mode
                ).order_by(desc(TicketPrice.created_at)).first()
                
                if ticket_price:
                    flight_data['ticket_price'] = ticket_price.to_dict()
                
                result_data.append(flight_data)
            
            # 處理回程航班
            if return_date:
                inbound_conditions = [
                    Flight.departure_airport_id == arr_airport.id,
                    Flight.arrival_airport_id == dep_airport.id,
                    func.date(Flight.scheduled_departure_time) == ret_date.date(),
                    Flight.is_test_data == self.test_mode
                ]
                
                if airline_code:
                    airline = Airline.query.filter_by(iata_code=airline_code).first()
                    if airline:
                        inbound_conditions.append(Flight.airline_id == airline.id)
                
                if is_direct_only:
                    inbound_conditions.append(Flight.is_direct_flight == True)
                
                # 執行回程查詢
                inbound_flights = Flight.query.filter(and_(*inbound_conditions)).order_by(order_by).all()
                
                # 格式化回程航班結果
                for flight in inbound_flights:
                    flight_data = flight.to_dict()
                    flight_data['trip_type'] = 'inbound'
                    
                    # 獲取票價資訊
                    ticket_price = TicketPrice.query.filter_by(
                        flight_id=flight.id,
                        is_test_data=self.test_mode
                    ).order_by(desc(TicketPrice.created_at)).first()
                    
                    if ticket_price:
                        flight_data['ticket_price'] = ticket_price.to_dict()
                    
                    result_data.append(flight_data)
            
            return {'success': True, 'data': result_data}
            
        except Exception as e:
            current_app.logger.error(f"搜索航班時發生錯誤: {e}")
            return {'success': False, 'message': f'搜索航班時發生錯誤: {str(e)}'}
    
    def get_flight_details(self, flight_id):
        """獲取特定航班的詳細資訊"""
        try:
            flight = Flight.query.filter_by(flight_id=flight_id, is_test_data=self.test_mode).first()
            
            if not flight:
                return {'success': False, 'message': '找不到指定航班'}
            
            result = flight.to_dict()
            
            # 添加票價資訊
            ticket_price = TicketPrice.query.filter_by(
                flight_id=flight.id,
                is_test_data=self.test_mode
            ).order_by(desc(TicketPrice.created_at)).first()
            
            if ticket_price:
                result['ticket_price'] = ticket_price.to_dict()
            
            # 添加航班預測資訊（如果有）
            prediction = FlightPrediction.query.filter_by(
                flight_id=flight.id,
                is_test_data=self.test_mode
            ).order_by(desc(FlightPrediction.created_at)).first()
            
            if prediction:
                result['prediction'] = prediction.to_dict()
            
            # 添加目的地天氣資訊（如果有）
            arrival_airport = Airport.query.get(flight.arrival_airport_id)
            if arrival_airport:
                weather = Weather.query.filter_by(
                    airport_id=arrival_airport.id,
                    forecast_date=flight.scheduled_arrival_time.date(),
                    is_test_data=self.test_mode
                ).first()
                
                if weather:
                    result['destination_weather'] = weather.to_dict()
            
            return {'success': True, 'data': result}
            
        except Exception as e:
            current_app.logger.error(f"獲取航班詳細資訊時發生錯誤: {e}")
            return {'success': False, 'message': f'獲取航班詳細資訊時發生錯誤: {str(e)}'}
    
    def update_flight_status(self, force_update=False):
        """更新航班狀態
        
        參數:
            force_update: 是否強制更新所有航班狀態，即使未到達更新時間
        """
        try:
            # 取得今天的日期
            today = datetime.now().date()
            
            # 查詢今日所有航班
            flights = Flight.query.filter(
                func.date(Flight.scheduled_departure_time) == today,
                Flight.is_test_data == self.test_mode
            ).all()
            
            updated_count = 0
            for flight in flights:
                # 檢查是否需要更新（出發前6小時內或已延誤的航班每30分鐘更新一次）
                current_time = datetime.now()
                time_diff = flight.scheduled_departure_time - current_time
                should_update = force_update
                
                if not should_update:
                    if flight.status == 'D':  # Delayed
                        # 上次更新時間超過30分鐘才更新
                        if flight.updated_at and (current_time - flight.updated_at).seconds > 1800:
                            should_update = True
                    elif time_diff.total_seconds() <= 21600:  # 6小時內
                        # 上次更新時間超過30分鐘才更新
                        if flight.updated_at and (current_time - flight.updated_at).seconds > 1800:
                            should_update = True
                
                if should_update:
                    # 從TDX API獲取最新狀態
                    airline = Airline.query.get(flight.airline_id)
                    if not airline:
                        continue
                    
                    # 如果是測試模式，模擬狀態更新
                    if self.test_mode:
                        import random
                        statuses = ['A', 'D', 'C']  # A:正常, D:延誤, C:取消
                        weights = [0.7, 0.2, 0.1]  # 70%正常, 20%延誤, 10%取消
                        new_status = random.choices(statuses, weights=weights, k=1)[0]
                        
                        flight.status = new_status
                        if new_status == 'A':
                            flight.status_description = '正常'
                        elif new_status == 'D':
                            delay_minutes = random.randint(15, 180)
                            flight.status_description = f'延誤 {delay_minutes} 分鐘'
                            # 更新預計出發時間
                            if flight.actual_departure_time is None and flight.scheduled_departure_time > current_time:
                                flight.estimated_departure_time = flight.scheduled_departure_time + timedelta(minutes=delay_minutes)
                        elif new_status == 'C':
                            flight.status_description = '取消'
                        
                        updated_count += 1
                    else:
                        # 從實際API獲取航班狀態
                        dep_airport = Airport.query.get(flight.departure_airport_id)
                        if not dep_airport:
                            continue
                        
                        # 調用TDX API查詢航班狀態
                        api_result = self.tdx_service.get_flight_info(
                            airline.iata_code,
                            flight.flight_number,
                            flight.scheduled_departure_time.strftime('%Y-%m-%d')
                        )
                        
                        if api_result['success'] and api_result['data']:
                            flight_data = api_result['data']
                            flight.status = flight_data.get('FlightStatusCode', flight.status)
                            flight.status_description = flight_data.get('FlightStatus', flight.status_description)
                            
                            # 處理實際/預計時間
                            actual_dep_time = flight_data.get('ActualDepartureTime')
                            if actual_dep_time:
                                flight.actual_departure_time = datetime.strptime(actual_dep_time, '%Y-%m-%dT%H:%M:%S')
                            
                            actual_arr_time = flight_data.get('ActualArrivalTime')
                            if actual_arr_time:
                                flight.actual_arrival_time = datetime.strptime(actual_arr_time, '%Y-%m-%dT%H:%M:%S')
                            
                            updated_count += 1
            
            # 提交所有更新
            db.session.commit()
            
            return {'success': True, 'message': f'已更新 {updated_count} 筆航班狀態'}
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"更新航班狀態時發生錯誤: {e}")
            return {'success': False, 'message': f'更新航班狀態時發生錯誤: {str(e)}'}
    
    def analyze_price_trend(self, flight_id, class_type='經濟'):
        """分析航班票價趨勢並提供購買建議"""
        try:
            flight = Flight.query.filter_by(flight_id=flight_id, is_test_data=self.test_mode).first()
            
            if not flight:
                return {'success': False, 'message': '找不到指定航班'}
            
            # 獲取該航班的歷史票價
            price_history = PriceHistory.query.filter_by(
                flight_id=flight.id,
                class_type=class_type,
                is_test_data=self.test_mode
            ).order_by(PriceHistory.recorded_date).all()
            
            if len(price_history) < 3:
                return {'success': False, 'message': '歷史價格數據不足，無法進行分析'}
            
            # 計算價格趨勢
            prices = [p.price for p in price_history]
            latest_price = prices[-1]
            avg_price = sum(prices) / len(prices)
            max_price = max(prices)
            min_price = min(prices)
            
            # 簡單趨勢分析
            if len(prices) >= 5:
                recent_trend = prices[-5:]
                if recent_trend[0] < recent_trend[-1]:
                    trend = "上升"
                elif recent_trend[0] > recent_trend[-1]:
                    trend = "下降"
                else:
                    trend = "穩定"
            else:
                trend = "資料不足"
            
            # 購買建議
            recommendation = "考慮購買"
            if latest_price < avg_price * 0.9:
                recommendation = "現在是購買的好時機"
            elif latest_price > avg_price * 1.1:
                recommendation = "建議等待價格下降"
            
            # 如果是上升趨勢且接近歷史低價，建議盡快購買
            if trend == "上升" and latest_price < (avg_price * 0.95):
                recommendation = "價格有上升趨勢，建議盡快購買"
            
            # 如果是下降趨勢且不是特別便宜，可以等等看
            if trend == "下降" and latest_price > (min_price * 1.1):
                recommendation = "價格有下降趨勢，可再等待看看"
            
            # 整理分析結果
            result = {
                'flight_number': flight.flight_number,
                'airline': Airline.query.get(flight.airline_id).name_zh,
                'class_type': class_type,
                'current_price': latest_price,
                'average_price': avg_price,
                'max_price': max_price,
                'min_price': min_price,
                'price_trend': trend,
                'recommendation': recommendation,
                'price_history': [p.to_dict() for p in price_history]
            }
            
            return {'success': True, 'data': result}
            
        except Exception as e:
            current_app.logger.error(f"分析票價趨勢時發生錯誤: {e}")
            return {'success': False, 'message': f'分析票價趨勢時發生錯誤: {str(e)}'}
    
    def fetch_ticket_prices(self, flight_id=None, use_api=True):
        """獲取機票價格資訊
        
        參數:
            flight_id: 指定航班ID，若不提供則獲取所有近期航班
            use_api: 是否使用外部API獲取價格，設為False將使用模擬數據
        """
        try:
            # 決定要查詢哪些航班
            query = Flight.query.filter_by(is_test_data=self.test_mode)
            if flight_id:
                query = query.filter_by(flight_id=flight_id)
            else:
                # 只查詢未來7天的航班
                today = datetime.now().date()
                next_week = today + timedelta(days=7)
                query = query.filter(
                    func.date(Flight.scheduled_departure_time) >= today,
                    func.date(Flight.scheduled_departure_time) <= next_week
                )
            
            flights = query.all()
            updated_count = 0
            
            for flight in flights:
                # 如果使用模擬數據或是測試模式
                if not use_api or self.test_mode:
                    self._generate_mock_ticket_prices(flight)
                    updated_count += 1
                    continue
                
                # 使用實際API獲取價格
                airline = Airline.query.get(flight.airline_id)
                dep_airport = Airport.query.get(flight.departure_airport_id)
                arr_airport = Airport.query.get(flight.arrival_airport_id)
                
                if not all([airline, dep_airport, arr_airport]):
                    continue
                
                # 這裡需要調用實際的機票價格API
                # 由於Cirium FlightStats API本身不提供票價資訊
                # 這裡需要使用其他第三方API如Skyscanner等
                # 暫時用模擬數據代替
                self._generate_mock_ticket_prices(flight)
                updated_count += 1
            
            # 提交所有更新
            db.session.commit()
            
            return {'success': True, 'message': f'已更新 {updated_count} 筆航班票價資訊'}
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"獲取機票價格時發生錯誤: {e}")
            return {'success': False, 'message': f'獲取機票價格時發生錯誤: {str(e)}'}
    
    def _generate_mock_ticket_prices(self, flight):
        """產生模擬票價資料（測試用）"""
        import random
        
        # 檢查是否已經有今天的票價記錄
        today = datetime.now().date()
        existing_price = TicketPrice.query.filter_by(
            flight_id=flight.id,
            is_test_data=self.test_mode
        ).filter(func.date(TicketPrice.created_at) == today).first()
        
        if existing_price:
            return
        
        # 基礎票價 - 根據飛行距離和航空公司確定
        dep_airport = Airport.query.get(flight.departure_airport_id)
        arr_airport = Airport.query.get(flight.arrival_airport_id)
        
        # 計算飛行距離（簡化版）
        # 實際應用中應使用更準確的地理距離計算
        distance = 1000  # 預設值
        if dep_airport and arr_airport and dep_airport.latitude and arr_airport.latitude:
            from math import radians, cos, sin, asin, sqrt
            
            def haversine(lon1, lat1, lon2, lat2):
                # 將經緯度轉換為弧度
                lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
                
                # haversine公式
                dlon = lon2 - lon1 
                dlat = lat2 - lat1 
                a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                c = 2 * asin(sqrt(a)) 
                r = 6371  # 地球半徑，單位為公里
                return c * r
            
            distance = haversine(
                dep_airport.longitude, dep_airport.latitude,
                arr_airport.longitude, arr_airport.latitude
            )
        
        # 根據距離確定基礎票價
        base_price = distance * 0.1  # 簡單估算
        
        # 根據航空公司調整
        airline = Airline.query.get(flight.airline_id)
        if airline:
            if airline.iata_code in ['CI', 'BR']:  # 中華或長榮
                base_price *= 1.2
            elif airline.iata_code in ['AE', 'B7']:  # 華信或立榮
                base_price *= 0.9
        
        # 三種艙等
        economy_price = base_price
        business_price = base_price * 2.5
        first_price = base_price * 4
        
        # 添加隨機波動
        economy_price *= random.uniform(0.85, 1.15)
        business_price *= random.uniform(0.9, 1.1)
        first_price *= random.uniform(0.95, 1.05)
        
        # 創建票價記錄
        ticket_price = TicketPrice(
            flight_id=flight.id,
            economy_price=round(economy_price),
            business_price=round(business_price),
            first_price=round(first_price),
            currency='TWD',
            is_test_data=self.test_mode
        )
        db.session.add(ticket_price)
        
        # 同時更新價格歷史記錄
        for class_type, price in [
            ('經濟', economy_price),
            ('商務', business_price),
            ('頭等', first_price)
        ]:
            price_history = PriceHistory(
                flight_id=flight.id,
                price=round(price),
                class_type=class_type,
                currency='TWD',
                recorded_date=today,
                is_test_data=self.test_mode
            )
            db.session.add(price_history)
    
    def predict_flight_delays(self, airport_code=None, date=None):
        """預測航班延誤情況
        
        參數:
            airport_code: 機場IATA代碼，若不提供則預測所有機場
            date: 日期，格式為YYYY-MM-DD，若不提供則預測今天
        """
        try:
            # 確定要預測的日期
            if date:
                target_date = datetime.strptime(date, '%Y-%m-%d').date()
            else:
                target_date = datetime.now().date()
            
            # 構建查詢條件
            query = Flight.query.filter(
                func.date(Flight.scheduled_departure_time) == target_date,
                Flight.is_test_data == self.test_mode
            )
            
            # 如果指定了機場，只預測該機場出發的航班
            if airport_code:
                airport = Airport.query.filter_by(iata_code=airport_code).first()
                if not airport:
                    return {'success': False, 'message': '找不到指定機場'}
                
                query = query.filter(Flight.departure_airport_id == airport.id)
            
            flights = query.all()
            prediction_count = 0
            
            for flight in flights:
                # 檢查今天是否已有預測
                existing_prediction = FlightPrediction.query.filter_by(
                    flight_id=flight.id,
                    is_test_data=self.test_mode
                ).filter(func.date(FlightPrediction.created_at) == target_date).first()
                
                if existing_prediction:
                    continue
                
                # 在測試模式下生成模擬的預測結果
                if self.test_mode:
                    self._generate_mock_predictions(flight)
                    prediction_count += 1
                    continue
                
                # 實際預測邏輯 - 這裡需要整合Cirium FlightStats API的延誤指數
                # 或使用機器學習模型進行預測
                # 暫時使用模擬預測
                self._generate_mock_predictions(flight)
                prediction_count += 1
            
            # 提交所有更新
            db.session.commit()
            
            return {'success': True, 'message': f'已預測 {prediction_count} 筆航班延誤情況'}
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"預測航班延誤時發生錯誤: {e}")
            return {'success': False, 'message': f'預測航班延誤時發生錯誤: {str(e)}'}
    
    def _generate_mock_predictions(self, flight):
        """產生模擬航班延誤預測（測試用）"""
        import random
        
        # 各種影響因素
        factors = {
            'weather': random.uniform(0, 0.5),  # 天氣影響
            'airline_history': random.uniform(0, 0.3),  # 航空公司歷史表現
            'airport_congestion': random.uniform(0, 0.4),  # 機場擁堵
            'maintenance': random.uniform(0, 0.2),  # 維護問題
            'seasonal_factor': random.uniform(0, 0.2)  # 季節性因素
        }
        
        # 計算總延誤機率
        delay_probability = min(
            0.95,  # 最大延誤機率上限
            sum(factors.values()) / 2  # 簡單加權平均
        )
        
        # 如果已知航班已延誤，則設定延誤機率為1
        if flight.status == 'D':  # Delayed
            delay_probability = 1.0
        
        # 預測延誤時間
        predicted_delay_minutes = 0
        if delay_probability > 0.3:  # 只有當延誤機率較高時才預測延誤時間
            # 延誤時間與延誤機率成正比
            predicted_delay_minutes = int(delay_probability * 180)  # 最多預測3小時延誤
        
        # 創建預測記錄
        prediction = FlightPrediction(
            flight_id=flight.id,
            delay_probability=round(delay_probability, 2),
            predicted_delay_minutes=predicted_delay_minutes,
            factors=json.dumps(factors),
            algorithm_version='mock-v1.0',
            is_test_data=self.test_mode
        )
        db.session.add(prediction)