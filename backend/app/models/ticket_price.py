"""
機票價格模型
"""
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from datetime import datetime
from .base import db, Base

class TicketPrice(Base):
    """機票價格數據模型"""
    __tablename__ = 'ticket_prices'
    
    price_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    flight_id = db.Column(UUID(as_uuid=True), db.ForeignKey('flights.flight_id'), nullable=False)
    class_type = db.Column(db.String, nullable=False)
    base_price = db.Column(db.Numeric, nullable=False)
    available_seats = db.Column(db.Integer)
    price_updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('flight_id', 'class_type', name='uq_flight_class'),
    )
    
    def __repr__(self):
        return f"<TicketPrice {self.flight_id} {self.class_type} ${self.base_price}>"
    
    def update_price(self, new_price, available_seats=None):
        """
        更新價格並記錄歷史
        
        Args:
            new_price: 新價格
            available_seats: 可選，新的可用座位數
        """
        from .price_history import PriceHistory
        
        # 記錄歷史價格
        history = PriceHistory(
            flight_id=self.flight_id,
            class_type=self.class_type,
            price=self.base_price
        )
        db.session.add(history)
        
        # 更新價格和座位數
        self.base_price = new_price
        if available_seats is not None:
            self.available_seats = available_seats
        self.price_updated_at = datetime.utcnow()
        
        db.session.commit()
        return self
    
    @classmethod
    def get_by_flight_class(cls, flight_id, class_type):
        """獲取特定航班和艙位的價格"""
        return cls.query.filter_by(
            flight_id=flight_id,
            class_type=class_type
        ).first()
    
    @classmethod
    def get_lowest_price(cls, departure_airport_id, arrival_airport_id, date):
        """獲取特定路線在特定日期的最低價格"""
        from .flight import Flight
        
        # 設置日期範圍
        date_start = datetime.combine(date, datetime.min.time())
        date_end = datetime.combine(date, datetime.max.time())
        
        return db.session.query(
            Flight, cls.class_type, db.func.min(cls.base_price).label('min_price')
        ).join(
            Flight, Flight.flight_id == cls.flight_id
        ).filter(
            Flight.departure_airport_id == departure_airport_id,
            Flight.arrival_airport_id == arrival_airport_id,
            Flight.scheduled_departure >= date_start,
            Flight.scheduled_departure <= date_end
        ).group_by(
            Flight.flight_id, cls.class_type
        ).order_by(
            'min_price'
        ).first() 