"""
票價服務模組 - 處理機票價格相關功能
"""
import logging
import json
from datetime import datetime, timedelta
from flask import current_app
from sqlalchemy import func, desc
import random
import math

from app.models import db, Flight, Airline, Airport, TicketPrice, PriceHistory

# 設置日誌
logger = logging.getLogger(__name__)

class PriceService:
    """
    票價服務類 - 處理票價分析與獲取
    """
    
    def __init__(self, test_mode=False):
        """
        初始化票價服務
        
        Args:
            test_mode (bool): 是否為測試模式
        """
        self.test_mode = test_mode
    
    def analyze_price_trend(self, flight_id, class_type='經濟'):
        """
        分析航班票價趨勢並提供購買建議
        
        Args:
            flight_id (str): 航班ID
            class_type (str): 艙等類型 (經濟、商務、頭等)
            
        Returns:
            dict: 分析結果
        """
        try:
            flight = Flight.query.filter_by(flight_id=flight_id, is_test_data=self.test_mode).first()
            
            if not flight:
                return {
                    'success': False,
                    'message': '找不到指定航班'
                }
            
            # 獲取該航班的歷史票價
            price_history = PriceHistory.query.filter_by(
                flight_id=flight.id,
                class_type=class_type,
                is_test_data=self.test_mode
            ).order_by(PriceHistory.recorded_date).all()
            
            if len(price_history) < 3:
                return {
                    'success': False,
                    'message': '歷史價格數據不足，無法進行分析'
                }
            
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
            airline = Airline.query.get(flight.airline_id)
            result = {
                'flight_number': flight.flight_number,
                'airline': airline.name_zh if airline else 'Unknown',
                'class_type': class_type,
                'current_price': latest_price,
                'average_price': round(avg_price, 2),
                'max_price': max_price,
                'min_price': min_price,
                'price_trend': trend,
                'recommendation': recommendation,
                'price_history': [p.to_dict() for p in price_history]
            }
            
            return {
                'success': True,
                'data': result
            }
            
        except Exception as e:
            logger.error(f"分析票價趨勢時發生錯誤: {e}")
            return {
                'success': False,
                'message': f'分析票價趨勢時發生錯誤: {str(e)}'
            }
    
    def fetch_ticket_prices(self, flight_id=None, use_api=True):
        """
        獲取機票價格資訊
        
        Args:
            flight_id (str, optional): 指定航班ID，若不提供則獲取所有近期航班
            use_api (bool, optional): 是否使用外部API獲取價格
            
        Returns:
            dict: 操作結果
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
                    self.generate_mock_ticket_prices(flight)
                    updated_count += 1
                    continue
                
                # 使用實際API獲取價格
                airline = Airline.query.get(flight.airline_id)
                dep_airport = Airport.query.get(flight.departure_airport_id)
                arr_airport = Airport.query.get(flight.arrival_airport_id)
                
                if not all([airline, dep_airport, arr_airport]):
                    continue
                
                # 這裡需要調用實際的機票價格API
                # 暫時用模擬數據代替
                self.generate_mock_ticket_prices(flight)
                updated_count += 1
            
            # 提交所有更新
            db.session.commit()
            
            return {
                'success': True,
                'message': f'已更新 {updated_count} 筆航班票價資訊'
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"獲取機票價格時發生錯誤: {e}")
            return {
                'success': False,
                'message': f'獲取機票價格時發生錯誤: {str(e)}'
            }
    
    def generate_mock_ticket_prices(self, flight):
        """
        生成模擬票價數據（測試用）
        
        Args:
            flight (Flight): 航班對象
        """
        # 檢查是否已經有今天的票價記錄
        today = datetime.now().date()
        existing_price = TicketPrice.query.filter_by(
            flight_id=flight.id,
            is_test_data=self.test_mode
        ).filter(func.date(TicketPrice.created_at) == today).first()
        
        if existing_price:
            return
        
        # 基於飛行距離和航空公司計算基礎票價
        dep_airport = Airport.query.get(flight.departure_airport_id)
        arr_airport = Airport.query.get(flight.arrival_airport_id)
        
        # 計算飛行距離
        distance = 1000  # 預設距離
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
        
        # 创建票價記錄
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