"""
天氣模型
"""
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from datetime import datetime, timedelta
from .base import db, Base

class Weather(Base):
    """天氣數據模型"""
    __tablename__ = 'weather'
    
    weather_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    airport_id = db.Column(UUID(as_uuid=True), db.ForeignKey('airports.airport_id'), nullable=False)
    forecast_date = db.Column(db.Date, nullable=False)
    forecast_time = db.Column(db.Time)
    temperature = db.Column(db.Float)
    feels_like = db.Column(db.Float)
    humidity = db.Column(db.Integer)
    wind_speed = db.Column(db.Float)
    wind_direction = db.Column(db.String)
    weather_condition = db.Column(db.String)
    precipitation = db.Column(db.Float)
    visibility = db.Column(db.Float)
    pressure = db.Column(db.Float)
    detailed_forecast = db.Column(JSONB)
    data_source = db.Column(db.String)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Weather {self.airport_id} {self.forecast_date} {self.weather_condition}>"
    
    def to_dict(self):
        """轉換為字典"""
        return {
            'id': self.weather_id,
            'airport_id': str(self.airport_id),
            'forecast_date': self.forecast_date.isoformat() if self.forecast_date else None,
            'forecast_time': self.forecast_time.isoformat() if self.forecast_time else None,
            'temperature': self.temperature,
            'feels_like': self.feels_like,
            'humidity': self.humidity,
            'wind_speed': self.wind_speed,
            'wind_direction': self.wind_direction,
            'weather_condition': self.weather_condition,
            'precipitation': self.precipitation,
            'visibility': self.visibility,
            'pressure': self.pressure,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def get_forecast(cls, airport_id, date, is_test_data=False):
        """獲取特定機場和日期的天氣預報"""
        return cls.query.filter_by(
            airport_id=airport_id,
            forecast_date=date,
            is_test_data=is_test_data
        ).order_by(cls.forecast_time).all()
    
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