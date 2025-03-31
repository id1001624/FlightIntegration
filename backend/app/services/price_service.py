"""
票價服務模塊
處理機票價格相關的業務邏輯
"""
from datetime import datetime, timedelta
from ..models import TicketPrice, Flight, Airline, PriceHistory
from ..models.base import db
from sqlalchemy import func, desc
from flask import current_app

class PriceService:
    """
    票價服務
    處理票價查詢、分析和統計的邏輯
    """
    
    @staticmethod
    def get_price_by_flight(flight_id, class_type=None):
        """
        獲取航班的票價信息
        
        Args:
            flight_id: 航班ID
            class_type: 艙等類型（可選）
            
        Returns:
            list: 票價列表
        """
        query = TicketPrice.query.filter_by(flight_id=flight_id)
        
        if class_type:
            query = query.filter_by(class_type=class_type)
            
        prices = query.all()
        
        return [{
            'class_type': price.class_type,
            'price': float(price.base_price),
            'available_seats': price.available_seats,
            'updated_at': price.price_updated_at.isoformat() if price.price_updated_at else None
        } for price in prices]
    
    @staticmethod
    def get_lowest_prices(departure_iata, arrival_iata, start_date, end_date=None):
        """
        獲取指定日期範圍內的最低票價
        
        Args:
            departure_iata: 出發機場IATA代碼
            arrival_iata: 到達機場IATA代碼
            start_date: 開始日期
            end_date: 結束日期（可選，默認為開始日期後30天）
            
        Returns:
            dict: 日期和最低票價的映射
        """
        from ..models import Airport
        
        # 處理日期格式
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            
        if not end_date:
            end_date = start_date + timedelta(days=30)
        elif isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
        # 查詢機場ID
        departure_airport = Airport.get_by_iata(departure_iata)
        arrival_airport = Airport.get_by_iata(arrival_iata)
        
        if not departure_airport or not arrival_airport:
            return {"error": "找不到指定的機場"}
            
        # 構建SQL查詢
        results = db.session.query(
            func.date(Flight.scheduled_departure).label('flight_date'),
            func.min(TicketPrice.base_price).label('min_price')
        ).join(
            TicketPrice, Flight.flight_id == TicketPrice.flight_id
        ).filter(
            Flight.departure_airport_id == departure_airport.airport_id,
            Flight.arrival_airport_id == arrival_airport.airport_id,
            func.date(Flight.scheduled_departure) >= start_date,
            func.date(Flight.scheduled_departure) <= end_date,
            TicketPrice.class_type == '經濟艙'  # 預設查詢經濟艙
        ).group_by(
            func.date(Flight.scheduled_departure)
        ).order_by(
            'flight_date'
        ).all()
        
        # 格式化結果
        price_map = {}
        for date_obj, price in results:
            price_map[date_obj.isoformat()] = float(price)
            
        return price_map
    
    @staticmethod
    def get_price_history(flight_id, class_type='經濟艙', days=30):
        """
        獲取航班的歷史票價
        
        Args:
            flight_id: 航班ID
            class_type: 艙等類型
            days: 歷史天數
            
        Returns:
            list: 歷史票價列表
        """
        # 計算時間範圍
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # 查詢歷史票價
        history = PriceHistory.query.filter(
            PriceHistory.flight_id == flight_id,
            PriceHistory.class_type == class_type,
            PriceHistory.created_at >= start_date,
            PriceHistory.created_at <= end_date
        ).order_by(
            PriceHistory.created_at
        ).all()
        
        # 格式化結果
        return [{
            'date': record.created_at.isoformat(),
            'price': float(record.price)
        } for record in history]
    
    @staticmethod
    def analyze_price_trend(flight_id, class_type='經濟艙'):
        """
        分析票價趨勢並提供購買建議
        
        Args:
            flight_id: 航班ID
            class_type: 艙等類型
            
        Returns:
            dict: 分析結果
        """
        # 獲取歷史票價
        history = PriceService.get_price_history(flight_id, class_type, days=60)
        
        if not history:
            return {
                "trend": "無法分析",
                "recommendation": "無足夠數據進行分析"
            }
            
        # 計算簡單趨勢
        prices = [item['price'] for item in history]
        
        if len(prices) < 3:
            return {
                "trend": "數據不足",
                "recommendation": "數據點不足，建議等待更多價格數據"
            }
            
        # 計算最近幾次價格變化趨勢
        recent_changes = []
        for i in range(len(prices) - 1):
            change = prices[i+1] - prices[i]
            recent_changes.append(change)
            
        # 計算平均變化
        avg_change = sum(recent_changes) / len(recent_changes)
        
        # 當前價格與最低價格的比較
        current_price = prices[-1]
        min_price = min(prices)
        max_price = max(prices)
        
        price_range = max_price - min_price
        if price_range == 0:
            price_position = 0.5  # 如果價格沒有變化，設為中間位置
        else:
            price_position = (current_price - min_price) / price_range
            
        # 根據分析結果提供建議
        if avg_change > 0:
            trend = "上漲"
            if price_position < 0.3:
                recommendation = "價格趨勢上漲，但當前價格接近歷史最低點，建議購買"
            else:
                recommendation = "價格呈上漲趨勢，建議等待價格回落"
        elif avg_change < 0:
            trend = "下跌"
            if price_position > 0.7:
                recommendation = "價格趨勢下跌，但當前價格仍然較高，建議等待"
            else:
                recommendation = "價格呈下跌趨勢，接近低點，可以考慮購買"
        else:
            trend = "穩定"
            if price_position < 0.4:
                recommendation = "價格穩定且接近歷史低點，適合購買"
            elif price_position > 0.8:
                recommendation = "價格穩定但接近歷史高點，建議等待"
            else:
                recommendation = "價格穩定在中間水平，可以考慮購買"
                
        return {
            "trend": trend,
            "recommendation": recommendation,
            "current_price": current_price,
            "min_price": min_price,
            "max_price": max_price,
            "avg_change": avg_change
        } 