"""
機場模型
"""
from datetime import datetime
from .base import db, Base

class Airport(Base):
    """機場數據模型"""
    __tablename__ = 'airports'
    
    airport_id = db.Column(db.String, primary_key=True)
    name_zh = db.Column(db.String, nullable=False)
    name_en = db.Column(db.String, nullable=False)
    city = db.Column(db.String, nullable=False)
    city_en = db.Column(db.String)
    country = db.Column(db.String, nullable=False)
    timezone = db.Column(db.String, nullable=False)
    contact_info = db.Column(db.String)
    website_url = db.Column(db.String)
    needs_manual_update = db.Column(db.Boolean, nullable=False, default=False, server_default='false')
    
    # 時間戳欄位
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 關聯
    departing_flights = db.relationship('Flight', foreign_keys='Flight.departure_airport_id', backref='departure_airport', lazy='dynamic')
    arriving_flights = db.relationship('Flight', foreign_keys='Flight.arrival_airport_id', backref='arrival_airport', lazy='dynamic')
    weather_data = db.relationship('Weather', backref='airport', lazy='dynamic')
    
    def __repr__(self):
        return f"<Airport {self.airport_id} - {self.name_zh}>"
    
    @classmethod
    def get_by_iata(cls, iata_code):
        """通過IATA代碼獲取機場"""
        return cls.query.filter_by(airport_id=iata_code).first()
    
    @classmethod
    def get_by_city(cls, city):
        """獲取指定城市的所有機場"""
        return cls.query.filter_by(city=city).all()
    
    @classmethod
    def get_by_country(cls, country):
        """獲取指定國家的所有機場"""
        return cls.query.filter_by(country=country).all()

class AirportDestination(Base):
    """機場目的地緩存表 - 用於快速查詢可用目的地，避免 API 延遲"""
    __tablename__ = 'airport_destinations'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    departure_airport_id = db.Column(db.String, db.ForeignKey('airports.airport_id'), nullable=False)
    destination_airport_id = db.Column(db.String, db.ForeignKey('airports.airport_id'), nullable=False)
    
    # 航線資訊
    is_active = db.Column(db.Boolean, nullable=False, default=True)  # 航線是否活躍
    last_flight_date = db.Column(db.Date)  # 最後一次有航班的日期
    flight_count_7days = db.Column(db.Integer, default=0)  # 過去7天的航班數量
    flight_count_30days = db.Column(db.Integer, default=0)  # 過去30天的航班數量
    
    # 時間戳欄位
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_synced_at = db.Column(db.DateTime)  # 最後同步時間
    
    # 關聯
    departure_airport = db.relationship('Airport', foreign_keys=[departure_airport_id], backref='destination_routes')
    destination_airport = db.relationship('Airport', foreign_keys=[destination_airport_id], backref='arrival_routes')
    
    # 複合唯一索引 - 確保同一出發地-目的地組合只有一條記錄
    __table_args__ = (
        db.UniqueConstraint('departure_airport_id', 'destination_airport_id', name='unique_route'),
        db.Index('idx_departure_airport', 'departure_airport_id'),
        db.Index('idx_destination_airport', 'destination_airport_id'),
        db.Index('idx_last_synced', 'last_synced_at'),
        db.Index('idx_active_routes', 'departure_airport_id', 'is_active'),
    )
    
    def __repr__(self):
        return f"<AirportDestination {self.departure_airport_id} -> {self.destination_airport_id}>"
    
    @classmethod
    def get_destinations_for_departure(cls, departure_airport_id, active_only=True):
        """獲取指定出發機場的所有目的地"""
        query = cls.query.filter_by(departure_airport_id=departure_airport_id)
        if active_only:
            query = query.filter_by(is_active=True)
        return query.all()
    
    @classmethod
    def get_popular_destinations(cls, departure_airport_id, limit=10):
        """獲取指定出發機場的熱門目的地（基於航班數量）"""
        return cls.query.filter_by(
            departure_airport_id=departure_airport_id, 
            is_active=True
        ).order_by(
            cls.flight_count_30days.desc()
        ).limit(limit).all()
    
    @classmethod
    def is_route_available(cls, departure_airport_id, destination_airport_id):
        """檢查指定航線是否可用"""
        route = cls.query.filter_by(
            departure_airport_id=departure_airport_id,
            destination_airport_id=destination_airport_id,
            is_active=True
        ).first()
        return route is not None 