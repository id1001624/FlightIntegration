"""
航班預測模型
"""
from sqlalchemy.dialects.postgresql import UUID, JSONB
from uuid import uuid4
from datetime import datetime
from .base import db, Base

class FlightPrediction(Base):
    """航班預測數據模型"""
    __tablename__ = 'flight_predictions'
    
    prediction_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    flight_id = db.Column(UUID(as_uuid=True), db.ForeignKey('flights.flight_id'), nullable=False)
    predicted_status = db.Column(db.String, nullable=False)
    delay_probability = db.Column(db.Numeric)
    estimated_delay_minutes = db.Column(db.Integer)
    confidence_level = db.Column(db.Numeric)
    prediction_factors = db.Column(JSONB)
    
    # 關聯
    flight = db.relationship('Flight', backref='predictions')
    
    def __repr__(self):
        return f"<FlightPrediction {self.flight_id} - {self.predicted_status}>"
    
    @classmethod
    def get_latest_for_flight(cls, flight_id):
        """獲取航班的最新預測"""
        return cls.query.filter_by(
            flight_id=flight_id
        ).order_by(
            db.desc(cls.created_at)
        ).first()
        
    @classmethod
    def get_high_risk_flights(cls, probability_threshold=0.7, limit=10):
        """獲取高風險航班（延誤或取消概率高）"""
        return cls.query.filter(
            cls.delay_probability >= probability_threshold
        ).order_by(
            db.desc(cls.delay_probability)
        ).limit(limit).all()
    
    @classmethod
    def get_by_status(cls, status, limit=10):
        """獲取特定預測狀態的航班"""
        return cls.query.filter_by(
            predicted_status=status
        ).order_by(
            db.desc(cls.confidence_level)
        ).limit(limit).all()
    
    @property
    def is_high_risk(self):
        """檢查是否為高風險航班"""
        return self.delay_probability and self.delay_probability >= 0.7
    
    @property
    def formatted_factors(self):
        """獲取格式化的預測因素"""
        if not self.prediction_factors:
            return {}
        
        # 假設prediction_factors是一個包含預測因素的JSON
        return {
            factor: {
                'weight': details.get('weight', 0),
                'description': details.get('description', '')
            }
            for factor, details in self.prediction_factors.items()
        } 