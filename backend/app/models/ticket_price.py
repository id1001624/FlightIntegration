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
    class_type = db.Column(db.String(20), nullable=False)
    base_price = db.Column(db.Numeric, nullable=False)
    economy_price = db.Column(db.Numeric, nullable=True)
    business_price = db.Column(db.Numeric, nullable=True)
    first_price = db.Column(db.Numeric, nullable=True)
    available_seats = db.Column(db.Integer)
    price_updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_test_data = db.Column(db.Boolean, default=False, nullable=False)
    
    __table_args__ = (
        db.UniqueConstraint('flight_id', 'class_type', name='uq_flight_class'),
    )
    
    def __repr__(self):
        return f"<TicketPrice {self.flight_id} {self.class_type} Eco:{self.economy_price} Biz:{self.business_price} Fst:{self.first_price}>"
    
    def update_price(self, economy_price=None, business_price=None, first_price=None, available_seats=None):
        """
        更新價格並記錄歷史
        
        Args:
            economy_price: 新的經濟艙價格
            business_price: 新的商務艙價格
            first_price: 新的頭等艙價格
            available_seats: 可選，新的可用座位數
        """
        from .price_history import PriceHistory
        
        # 記錄歷史價格 (根據 class_type 記錄對應的舊價格)
        old_price = None
        if self.class_type == '經濟':
            old_price = self.economy_price
        elif self.class_type == '商務':
            old_price = self.business_price
        elif self.class_type == '頭等':
            old_price = self.first_price
            
        if old_price is not None:
            history = PriceHistory(
                flight_id=self.flight_id,
                class_type=self.class_type,
                price=old_price # 記錄變更前的價格
            )
            db.session.add(history)
            
        # 更新價格
        if economy_price is not None:
            self.economy_price = economy_price
        if business_price is not None:
            self.business_price = business_price
        if first_price is not None:
            self.first_price = first_price
            
        if available_seats is not None:
            self.available_seats = available_seats
            
        self.price_updated_at = datetime.utcnow()
        
        db.session.commit()
        return self
    
    @classmethod
    def get_by_flight_class(cls, flight_id, class_type):
        """獲取特定航班和艙位的價格記錄"""
        return cls.query.filter_by(
            flight_id=flight_id,
            class_type=class_type
        ).first()
    
    @classmethod
    def get_lowest_price(cls, departure_airport_id, arrival_airport_id, date, class_type='經濟'):
        """獲取特定路線在特定日期的指定艙位最低價格"""
        from .flight import Flight
        
        # 設置日期範圍
        date_start = datetime.combine(date, datetime.min.time())
        date_end = datetime.combine(date, datetime.max.time())
        
        # 根據艙等選擇價格欄位
        price_column = cls.economy_price
        if class_type == '商務':
            price_column = cls.business_price
        elif class_type == '頭等':
            price_column = cls.first_price
            
        return db.session.query(
            Flight, db.func.min(price_column).label('min_price')
        ).join(
            Flight, Flight.flight_id == cls.flight_id
        ).filter(
            Flight.departure_airport_id == departure_airport_id,
            Flight.arrival_airport_id == arrival_airport_id,
            Flight.scheduled_departure >= date_start,
            Flight.scheduled_departure <= date_end,
            cls.class_type == class_type, # 確保只比較同一艙等
            price_column.isnot(None) # 確保價格存在
        ).group_by(
            Flight.flight_id
        ).order_by(
            'min_price'
        ).first()

    @classmethod
    def get_latest_price(cls, flight_id, class_type=None, is_test_data=False):
        """獲取最新票價記錄"""
        query = cls.query.filter_by(flight_id=flight_id, is_test_data=is_test_data)
        
        if class_type:
            query = query.filter_by(class_type=class_type)
            
        return query.order_by(cls.price_updated_at.desc()).first() 