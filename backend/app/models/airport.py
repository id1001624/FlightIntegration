"""
機場模型
"""
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from .base import db, Base

class Airport(Base):
    """機場數據模型"""
    __tablename__ = 'airports'
    
    airport_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    iata_code = db.Column(db.String, unique=True)
    name_zh = db.Column(db.String, nullable=False)
    name_en = db.Column(db.String, nullable=False)
    city = db.Column(db.String, nullable=False)
    city_en = db.Column(db.String)
    country = db.Column(db.String, nullable=False)
    timezone = db.Column(db.String, nullable=False)
    contact_info = db.Column(db.String)
    website_url = db.Column(db.String)
    
    # 關聯
    departing_flights = db.relationship('Flight', foreign_keys='Flight.departure_airport_id', backref='departure_airport', lazy='dynamic')
    arriving_flights = db.relationship('Flight', foreign_keys='Flight.arrival_airport_id', backref='arrival_airport', lazy='dynamic')
    weather_data = db.relationship('Weather', backref='airport', lazy='dynamic')
    
    def __repr__(self):
        return f"<Airport {self.iata_code} - {self.name_zh}>"
    
    @classmethod
    def get_by_iata(cls, iata_code):
        """通過IATA代碼獲取機場"""
        return cls.query.filter_by(iata_code=iata_code).first()
    
    @classmethod
    def get_by_city(cls, city):
        """獲取指定城市的所有機場"""
        return cls.query.filter_by(city=city).all()
    
    @classmethod
    def get_by_country(cls, country):
        """獲取指定國家的所有機場"""
        return cls.query.filter_by(country=country).all() 