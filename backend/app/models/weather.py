"""
天氣模型
"""
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from datetime import datetime, timedelta
from .base import db, Base

class Weather(Base):
    """天氣數據模型"""
    __tablename__ = 'weather'
    
    weather_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    airport_id = db.Column(UUID(as_uuid=True), db.ForeignKey('airports.airport_id'), nullable=False)
    forecast_time = db.Column(db.DateTime, nullable=False)
    temperature = db.Column(db.Numeric)
    humidity = db.Column(db.Numeric)
    wind_speed = db.Column(db.Numeric)
    precipitation = db.Column(db.Numeric)
    visibility = db.Column(db.Integer)
    weather_condition = db.Column(db.String)
    source = db.Column(db.String)
    
    def __repr__(self):
        return f"<Weather {self.airport_id} {self.forecast_time.strftime('%Y-%m-%d %H:%M')} {self.weather_condition}>"
    
    @classmethod
    def get_current_weather(cls, airport_id):
        """
        獲取特定機場的當前天氣
        
        Args:
            airport_id: 機場ID
            
        Returns:
            最接近當前時間的天氣記錄
        """
        now = datetime.utcnow()
        
        return cls.query.filter(
            cls.airport_id == airport_id,
            cls.forecast_time <= now
        ).order_by(
            db.desc(cls.forecast_time)
        ).first()
    
    @classmethod
    def get_weather_forecast(cls, airport_id, days=5):
        """
        獲取特定機場的天氣預報
        
        Args:
            airport_id: 機場ID
            days: 預報天數（預設5天）
            
        Returns:
            未來指定天數的天氣預報列表
        """
        now = datetime.utcnow()
        end_date = now + timedelta(days=days)
        
        return cls.query.filter(
            cls.airport_id == airport_id,
            cls.forecast_time >= now,
            cls.forecast_time <= end_date
        ).order_by(
            cls.forecast_time
        ).all()
    
    @classmethod
    def check_flight_weather(cls, flight_id):
        """
        檢查特定航班的起飛和降落天氣
        
        Args:
            flight_id: 航班ID
            
        Returns:
            (起飛天氣, 降落天氣) 的元組
        """
        from .flight import Flight
        
        flight = Flight.query.get(flight_id)
        if not flight:
            return None, None
            
        # 獲取起飛機場的天氣
        departure_weather = cls.query.filter(
            cls.airport_id == flight.departure_airport_id,
            cls.forecast_time <= flight.scheduled_departure
        ).order_by(
            db.desc(cls.forecast_time)
        ).first()
        
        # 獲取降落機場的天氣
        arrival_weather = cls.query.filter(
            cls.airport_id == flight.arrival_airport_id,
            cls.forecast_time <= flight.scheduled_arrival
        ).order_by(
            db.desc(cls.forecast_time)
        ).first()
        
        return departure_weather, arrival_weather 