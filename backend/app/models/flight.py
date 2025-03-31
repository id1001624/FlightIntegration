"""
航班模型
"""
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from datetime import datetime, timedelta
from .base import db, Base

class Flight(Base):
    """航班數據模型"""
    __tablename__ = 'flights'
    
    flight_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    flight_number = db.Column(db.String, nullable=False)
    airline_id = db.Column(UUID(as_uuid=True), db.ForeignKey('airlines.airline_id'), nullable=False)
    departure_airport_id = db.Column(UUID(as_uuid=True), db.ForeignKey('airports.airport_id'), nullable=False)
    arrival_airport_id = db.Column(UUID(as_uuid=True), db.ForeignKey('airports.airport_id'), nullable=False)
    scheduled_departure = db.Column(db.DateTime(timezone=True), nullable=False)
    scheduled_arrival = db.Column(db.DateTime(timezone=True), nullable=False)
    status = db.Column(db.String)
    
    # 只在Flight模型中添加時間戳欄位
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)
    
    # 關聯
    ticket_prices = db.relationship('TicketPrice', backref='flight', lazy='dynamic', cascade='all, delete-orphan')
    price_history = db.relationship('PriceHistory', backref='flight', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Flight {self.flight_number} {self.scheduled_departure.strftime('%Y-%m-%d %H:%M')}>"
    
    @property
    def duration(self):
        """計算航班持續時間"""
        if self.scheduled_departure and self.scheduled_arrival:
            return self.scheduled_arrival - self.scheduled_departure
        return None
    
    @property
    def is_domestic(self):
        """檢查是否為國內航班"""
        # 此處簡單判斷，可能需要根據實際情況調整
        return (self.departure_airport.country == 'Taiwan' or 
                self.arrival_airport.country == 'Taiwan')
                
    @classmethod
    def search_flights(cls, departure_airport_id, arrival_airport_id, 
                      departure_date, return_date=None, airline_id=None):
        """
        搜索符合條件的航班
        
        Args:
            departure_airport_id: 出發機場ID
            arrival_airport_id: 到達機場ID
            departure_date: 出發日期 (datetime.date)
            return_date: 返回日期 (datetime.date, 可選)
            airline_id: 航空公司ID (可選)
            
        Returns:
            outbound_flights: 去程航班
            return_flights: 回程航班 (如果指定了return_date)
        """
        # 設置日期範圍
        departure_start = datetime.combine(departure_date, datetime.min.time())
        departure_end = datetime.combine(departure_date, datetime.max.time())
        
        # 基本查詢
        query = cls.query.filter(
            cls.departure_airport_id == departure_airport_id,
            cls.arrival_airport_id == arrival_airport_id,
            cls.scheduled_departure >= departure_start,
            cls.scheduled_departure <= departure_end
        )
        
        # 如果指定了航空公司，添加過濾條件
        if airline_id:
            query = query.filter(cls.airline_id == airline_id)
        
        outbound_flights = query.order_by(cls.scheduled_departure).all()
        
        # 如果指定了返回日期，查詢返回航班
        if return_date:
            return_start = datetime.combine(return_date, datetime.min.time())
            return_end = datetime.combine(return_date, datetime.max.time())
            
            return_query = cls.query.filter(
                cls.departure_airport_id == arrival_airport_id,  # 注意這裡是相反的
                cls.arrival_airport_id == departure_airport_id,
                cls.scheduled_departure >= return_start,
                cls.scheduled_departure <= return_end
            )
            
            if airline_id:
                return_query = return_query.filter(cls.airline_id == airline_id)
                
            return_flights = return_query.order_by(cls.scheduled_departure).all()
            return outbound_flights, return_flights
        
        return outbound_flights 

    @classmethod
    def search(cls, departure_airport_id=None, arrival_airport_id=None, 
                departure_date=None, airline_id=None, is_test_data=False):
        """搜尋航班"""
        query = cls.query.filter_by(is_test_data=is_test_data)
        
        if departure_airport_id:
            query = query.filter_by(departure_airport_id=departure_airport_id)
        
        if arrival_airport_id:
            query = query.filter_by(arrival_airport_id=arrival_airport_id)
        
        if departure_date:
            # 格式化字符串為日期對象
            if isinstance(departure_date, str):
                departure_date = datetime.strptime(departure_date, '%Y-%m-%d').date()
            
            # 查詢指定日期的航班
            query = query.filter(db.func.date(cls.scheduled_departure) == departure_date)
        
        if airline_id:
            query = query.filter_by(airline_id=airline_id)
            
        return query.all() 