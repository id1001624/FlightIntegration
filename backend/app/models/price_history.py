"""
價格歷史模型
"""
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from datetime import datetime, timedelta
from .base import db, Base

class PriceHistory(Base):
    """價格歷史數據模型"""
    __tablename__ = 'price_history'
    
    history_id = db.Column(db.String, primary_key=True, default=lambda: str(uuid4()))
    flight_id = db.Column(db.String, db.ForeignKey('flights.flight_id'), nullable=False)
    ticket_price_id = db.Column(db.String, db.ForeignKey('ticket_prices.price_id'), nullable=False)
    cabin_info = db.Column(db.String, nullable=False)
    price = db.Column(db.Float, nullable=False)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_test_data = db.Column(db.Boolean, default=False)
    
    ticket_price_snapshot = db.relationship('TicketPrice', back_populates='price_history')
    
    def __repr__(self):
        return f"<PriceHistory {self.flight_id} {self.cabin_info} ${self.price} @ {self.recorded_at}>"
    
    @classmethod
    def get_price_trend(cls, flight_id, cabin_info, days=30, is_test_data=False):
        """
        獲取指定航班特定價格欄位的歷史價格趨勢
        
        Args:
            flight_id: 航班ID
            cabin_info: 價格欄位標識符 (e.g., 'economy_price')
            days: 查詢天數
            is_test_data: 是否為測試數據
            
        Returns:
            歷史價格列表
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        query = cls.query.filter(
            cls.flight_id == flight_id,
            cls.cabin_info == cabin_info,
            cls.recorded_at >= start_date
        )
        if is_test_data is not None:
            query = query.filter_by(is_test_data=is_test_data)
        return query.order_by(cls.recorded_at.asc()).all()
    
    @classmethod
    def get_price_comparison_data(cls, flight_id_1, flight_id_2, cabin_info='economy_price', days=30):
        """
        獲取兩個航班特定價格欄位的歷史價格數據以供比較
        
        Args:
            flight_id_1: 第一個航班ID
            flight_id_2: 第二個航班ID
            cabin_info: 價格欄位標識符 (e.g., 'economy_price')
            days: 查詢天數
            
        Returns:
            一個字典，包含兩個航班的歷史價格列表
        """
        history1 = cls.get_price_trend(flight_id_1, cabin_info, days)
        history2 = cls.get_price_trend(flight_id_2, cabin_info, days)
        return {
            'flight1': [{"date": h.recorded_at.strftime('%Y-%m-%d'), "price": h.price} for h in history1],
            'flight2': [{"date": h.recorded_at.strftime('%Y-%m-%d'), "price": h.price} for h in history2]
        }
    
    @classmethod
    def get_route_price_trend(cls, departure_airport_id, arrival_airport_id, 
                             class_type='經濟艙', days=30):
        """
        獲取特定路線的價格趨勢
        
        Args:
            departure_airport_id: 出發機場ID
            arrival_airport_id: 到達機場ID
            class_type: 艙位類型
            days: 查詢過去的天數
            
        Returns:
            按日期分組的平均價格字典
        """
        from .flight import Flight
        from sqlalchemy import func
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        results = db.session.query(
            func.date_trunc('day', cls.recorded_at).label('date'),
            func.avg(cls.price).label('avg_price')
        ).join(
            Flight, Flight.flight_id == cls.flight_id
        ).filter(
            Flight.departure_airport_id == departure_airport_id,
            Flight.arrival_airport_id == arrival_airport_id,
            cls.cabin_info == class_type,
            cls.recorded_at >= cutoff_date
        ).group_by(
            func.date_trunc('day', cls.recorded_at)
        ).order_by(
            'date'
        ).all()
        
        # 將結果轉換為字典
        trend = {}
        for date, avg_price in results:
            trend[date.strftime('%Y-%m-%d')] = float(avg_price)
            
        return trend 