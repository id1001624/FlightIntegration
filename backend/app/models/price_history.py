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
    
    history_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    flight_id = db.Column(UUID(as_uuid=True), db.ForeignKey('flights.flight_id'), nullable=False)
    class_type = db.Column(db.String, nullable=False)
    price = db.Column(db.Numeric, nullable=False)
    recorded_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f"<PriceHistory {self.flight_id} {self.class_type} ${self.price} @ {self.recorded_at}>"
    
    @classmethod
    def get_price_trend(cls, flight_id, class_type, days=30, is_test_data=False):
        """
        獲取特定航班和艙位的價格趨勢
        
        Args:
            flight_id: 航班ID
            class_type: 艙位類型
            days: 查詢過去的天數
            is_test_data: 是否為測試數據
            
        Returns:
            價格歷史記錄列表，按時間排序
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        return cls.query.filter(
            cls.flight_id == flight_id,
            cls.class_type == class_type,
            cls.is_test_data == is_test_data,
            cls.recorded_at >= cutoff_date
        ).order_by(cls.recorded_at).all()
    
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
            cls.class_type == class_type,
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