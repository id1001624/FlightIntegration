"""
預測服務模組 - 處理航班延誤預測功能
"""
import logging
import json
import random
from datetime import datetime, timedelta
from flask import current_app
from sqlalchemy import func

from app.models import db, Flight, Airline, Airport, FlightPrediction, Weather

# 設置日誌
logger = logging.getLogger(__name__)

class PredictionService:
    """
    預測服務類 - 處理航班延誤預測功能
    """
    
    def __init__(self, test_mode=False):
        """
        初始化預測服務
        
        Args:
            test_mode (bool): 是否為測試模式
        """
        self.test_mode = test_mode
    
    def predict_flight_delays(self, airport_code=None, date=None):
        """
        預測航班延誤情況
        
        Args:
            airport_code (str, optional): 機場IATA代碼，若不提供則預測所有機場
            date (str, optional): 日期，格式為YYYY-MM-DD，若不提供則預測今天
            
        Returns:
            dict: 預測結果
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
                    return {
                        'success': False,
                        'message': '找不到指定機場'
                    }
                
                query = query.filter(Flight.departure_airport_id == airport.id)
            
            flights = query.all()
            
            if not flights:
                return {
                    'success': False,
                    'message': f'找不到{target_date.strftime("%Y-%m-%d")}的航班'
                }
            
            prediction_count = 0
            results = []
            
            for flight in flights:
                # 檢查今天是否已有預測
                existing_prediction = FlightPrediction.query.filter_by(
                    flight_id=flight.id,
                    is_test_data=self.test_mode
                ).filter(func.date(FlightPrediction.created_at) == target_date).first()
                
                if existing_prediction:
                    results.append({
                        'flight_number': flight.flight_number,
                        'prediction': existing_prediction.to_dict()
                    })
                    continue
                
                # 生成預測
                prediction = self._generate_prediction(flight)
                prediction_count += 1
                
                # 添加到結果列表
                results.append({
                    'flight_number': flight.flight_number,
                    'prediction': prediction.to_dict()
                })
            
            # 提交所有更新
            db.session.commit()
            
            return {
                'success': True,
                'message': f'已預測 {prediction_count} 筆航班延誤情況',
                'data': results
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"預測航班延誤時發生錯誤: {e}")
            return {
                'success': False,
                'message': f'預測航班延誤時發生錯誤: {str(e)}'
            }
    
    def _generate_prediction(self, flight):
        """
        為航班生成延誤預測
        
        Args:
            flight (Flight): 航班對象
            
        Returns:
            FlightPrediction: 預測對象
        """
        # 獲取相關數據
        airport = Airport.query.get(flight.departure_airport_id)
        airline = Airline.query.get(flight.airline_id)
        
        # 獲取天氣數據（如果有）
        weather_data = None
        if airport:
            weather = Weather.query.filter_by(
                airport_id=airport.id,
                forecast_date=flight.scheduled_departure_time.date(),
                is_test_data=self.test_mode
            ).first()
            
            if weather:
                weather_data = weather.to_dict()
        
        # 各種影響因素
        factors = {
            'weather': random.uniform(0, 0.5),  # 天氣影響
            'airline_history': random.uniform(0, 0.3),  # 航空公司歷史表現
            'airport_congestion': random.uniform(0, 0.4),  # 機場擁堵
            'maintenance': random.uniform(0, 0.2),  # 維護問題
            'seasonal_factor': random.uniform(0, 0.2)  # 季節性因素
        }
        
        # 如果有天氣數據，根據天氣調整延誤概率
        if weather_data:
            # 如果天氣不佳，增加延誤機率
            if 'rain' in weather_data.get('weather_condition', '').lower():
                factors['weather'] = random.uniform(0.3, 0.7)
            if 'storm' in weather_data.get('weather_condition', '').lower():
                factors['weather'] = random.uniform(0.6, 0.9)
            
            # 根據風速調整
            wind_speed = weather_data.get('wind_speed', 0)
            if wind_speed > 30:  # 假設風速超過30km/h為大風
                factors['weather'] = max(factors['weather'], random.uniform(0.5, 0.8))
        
        # 根據航空公司調整
        if airline:
            if airline.iata_code in ['CI', 'BR']:  # 假設這些航空公司較準時
                factors['airline_history'] = random.uniform(0, 0.2)
        
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
            algorithm_version='model-v1.0',
            is_test_data=self.test_mode
        )
        db.session.add(prediction)
        
        return prediction
    
    def get_historical_delay_stats(self, airline_code=None, airport_code=None, days=30):
        """
        獲取歷史延誤統計數據
        
        Args:
            airline_code (str, optional): 航空公司IATA代碼
            airport_code (str, optional): 機場IATA代碼
            days (int, optional): 統計的天數範圍
            
        Returns:
            dict: 統計結果
        """
        try:
            # 計算起始日期
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            # 構建基本查詢
            query = Flight.query.filter(
                func.date(Flight.scheduled_departure_time) >= start_date,
                func.date(Flight.scheduled_departure_time) <= end_date,
                Flight.is_test_data == self.test_mode
            )
            
            # 篩選條件
            if airline_code:
                airline = Airline.query.filter_by(iata_code=airline_code).first()
                if airline:
                    query = query.filter(Flight.airline_id == airline.id)
            
            if airport_code:
                airport = Airport.query.filter_by(iata_code=airport_code).first()
                if airport:
                    query = query.filter(Flight.departure_airport_id == airport.id)
            
            # 執行查詢
            flights = query.all()
            
            if not flights:
                return {
                    'success': False,
                    'message': '未找到符合條件的航班'
                }
            
            # 計算延誤統計數據
            total_flights = len(flights)
            delayed_flights = sum(1 for f in flights if f.status == 'D')
            cancelled_flights = sum(1 for f in flights if f.status == 'C')
            normal_flights = total_flights - delayed_flights - cancelled_flights
            
            delay_rate = delayed_flights / total_flights if total_flights > 0 else 0
            cancel_rate = cancelled_flights / total_flights if total_flights > 0 else 0
            
            # 統計不同延誤時間段的數量
            delay_stats = {
                '0-15分鐘': 0,
                '15-30分鐘': 0,
                '30-60分鐘': 0,
                '1-2小時': 0,
                '2小時以上': 0
            }
            
            for flight in flights:
                if flight.status == 'D' and flight.actual_departure_time:
                    delay_minutes = (flight.actual_departure_time - flight.scheduled_departure_time).total_seconds() / 60
                    
                    if delay_minutes <= 15:
                        delay_stats['0-15分鐘'] += 1
                    elif delay_minutes <= 30:
                        delay_stats['15-30分鐘'] += 1
                    elif delay_minutes <= 60:
                        delay_stats['30-60分鐘'] += 1
                    elif delay_minutes <= 120:
                        delay_stats['1-2小時'] += 1
                    else:
                        delay_stats['2小時以上'] += 1
            
            return {
                'success': True,
                'data': {
                    'total_flights': total_flights,
                    'normal_flights': normal_flights,
                    'delayed_flights': delayed_flights,
                    'cancelled_flights': cancelled_flights,
                    'delay_rate': round(delay_rate * 100, 2),
                    'cancel_rate': round(cancel_rate * 100, 2),
                    'delay_distribution': delay_stats
                }
            }
            
        except Exception as e:
            logger.error(f"獲取延誤統計時發生錯誤: {e}")
            return {
                'success': False,
                'message': f'獲取延誤統計時發生錯誤: {str(e)}'
            }