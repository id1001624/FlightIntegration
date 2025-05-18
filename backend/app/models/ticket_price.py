"""
機票價格模型
"""
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from datetime import datetime
from .base import db, Base
from typing import Optional
from sqlalchemy.orm.attributes import get_history
from .flight import Flight

class TicketPrice(Base):
    """機票價格數據模型"""
    __tablename__ = 'ticket_prices'
    
    price_id = db.Column(db.String, primary_key=True, default=lambda: str(uuid4()))
    flight_id = db.Column(db.String, db.ForeignKey('flights.flight_id'), nullable=False)
    economy_price = db.Column(db.Float, nullable=True)
    business_price = db.Column(db.Float, nullable=True)
    first_price = db.Column(db.Float, nullable=True)
    available_seats = db.Column(db.Integer, nullable=True)
    price_updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_test_data = db.Column(db.Boolean, default=False)
    
    flight = db.relationship('Flight', back_populates='ticket_prices')
    price_history = db.relationship('PriceHistory', back_populates='ticket_price_snapshot', cascade='all, delete-orphan')
    
    __table_args__ = (
        db.UniqueConstraint('flight_id', name='uq_flight_price_entry'),
    )
    
    def __repr__(self):
        return f"<TicketPrice {self.flight_id} Eco:{self.economy_price} Biz:{self.business_price} Fst:{self.first_price}>"
    
    @staticmethod
    def before_flush(session, flush_context, instances):
        from .price_history import PriceHistory
        for instance in session.dirty:
            if isinstance(instance, TicketPrice) and session.is_modified(instance):
                changes = get_history(instance, 'economy_price')
                if changes.has_changes():
                    instance.record_price_change(session, 'economy_price', changes.deleted[0] if changes.deleted else None)
                
                changes_business = get_history(instance, 'business_price')
                if changes_business.has_changes():
                    instance.record_price_change(session, 'business_price', changes_business.deleted[0] if changes_business.deleted else None)

                changes_first = get_history(instance, 'first_price')
                if changes_first.has_changes():
                    instance.record_price_change(session, 'first_price', changes_first.deleted[0] if changes_first.deleted else None)

    def record_price_change(self, session, cabin_identifier: str, old_price: Optional[float]):
        """記錄特定艙等的價格變動。 cabin_identifier 是 'economy_price', 'business_price', or 'first_price'."""
        from .price_history import PriceHistory
        new_price = getattr(self, cabin_identifier)
        if old_price is not None and new_price != old_price:
            history_entry = PriceHistory(
                flight_id=self.flight_id,
                ticket_price_id=self.price_id,
                cabin_info=cabin_identifier,
                price=new_price,
                recorded_at=datetime.utcnow(),
                is_test_data=self.is_test_data
            )
            session.add(history_entry)

    @classmethod
    def get_by_flight_id(cls, flight_id):
        return cls.query.filter_by(flight_id=flight_id).first()
    
    @classmethod
    def get_lowest_price_for_flight(cls, flight_id: str) -> Optional[float]:
        """獲取指定航班的最低可用票價 (從三個艙等中選取)"""
        price_entry = cls.query.filter_by(flight_id=flight_id).first()
        if not price_entry:
            return None
        
        prices = []
        if price_entry.economy_price is not None:
            prices.append(price_entry.economy_price)
        if price_entry.business_price is not None:
            prices.append(price_entry.business_price)
        if price_entry.first_price is not None:
            prices.append(price_entry.first_price)
            
        return min(prices) if prices else None

    @classmethod
    def get_lowest_price(cls, departure_airport_id, arrival_airport_id, date, cabin_preference: Optional[str] = None):
        """獲取指定航線和日期的最低票價，可選艙等偏好"""
        query = db.session.query(cls).join(Flight).filter(
            Flight.departure_airport_id == departure_airport_id,
            Flight.arrival_airport_id == arrival_airport_id,
            db.func.date(Flight.scheduled_departure) == date
        )

        flights_prices = query.all()
        if not flights_prices:
            return None

        lowest_overall_price = float('inf')
        
        for price_entry in flights_prices:
            current_flight_prices = []
            if cabin_preference == 'economy' or cabin_preference is None:
                if price_entry.economy_price is not None: current_flight_prices.append(price_entry.economy_price)
            if cabin_preference == 'business' or cabin_preference is None:
                if price_entry.business_price is not None: current_flight_prices.append(price_entry.business_price)
            if cabin_preference == 'first' or cabin_preference is None:
                if price_entry.first_price is not None: current_flight_prices.append(price_entry.first_price)
            
            if current_flight_prices:
                lowest_overall_price = min(lowest_overall_price, min(current_flight_prices))

        return lowest_overall_price if lowest_overall_price != float('inf') else None

    @classmethod
    def get_latest_price(cls, flight_id, is_test_data=False):
        """獲取最新的票價記錄 (現在一個 flight_id 只有一筆)"""
        query = cls.query.filter_by(flight_id=flight_id)
        if is_test_data is not None:
            query = query.filter_by(is_test_data=is_test_data)
        return query.order_by(cls.price_updated_at.desc()).first() 