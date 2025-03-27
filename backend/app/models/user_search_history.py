"""
用戶搜索歷史模型
"""
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from datetime import datetime
from .base import db, Base

class UserSearchHistory(Base):
    """用戶搜索歷史數據模型"""
    __tablename__ = 'user_search_history'
    
    search_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.user_id'))
    departure_airport_id = db.Column(UUID(as_uuid=True), db.ForeignKey('airports.airport_id'), nullable=False)
    arrival_airport_id = db.Column(UUID(as_uuid=True), db.ForeignKey('airports.airport_id'), nullable=False)
    departure_date = db.Column(db.Date, nullable=False)
    return_date = db.Column(db.Date)
    adults = db.Column(db.Integer, default=1)
    children = db.Column(db.Integer, default=0)
    infants = db.Column(db.Integer, default=0)
    class_type = db.Column(db.String, default='經濟')
    search_time = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 關聯
    departure_airport = db.relationship('Airport', foreign_keys=[departure_airport_id])
    arrival_airport = db.relationship('Airport', foreign_keys=[arrival_airport_id])
    
    def __repr__(self):
        return f"<UserSearchHistory {self.departure_airport_id} to {self.arrival_airport_id} on {self.departure_date}>"
    
    @classmethod
    def get_by_user(cls, user_id, limit=10):
        """獲取用戶的搜索歷史"""
        return cls.query.filter_by(user_id=user_id).order_by(db.desc(cls.search_time)).limit(limit).all()
    
    @classmethod
    def get_popular_routes(cls, days=30, limit=5):
        """獲取熱門路線"""
        from sqlalchemy import func
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        return db.session.query(
            cls.departure_airport_id,
            cls.arrival_airport_id,
            func.count().label('count')
        ).filter(
            cls.search_time >= cutoff_date
        ).group_by(
            cls.departure_airport_id,
            cls.arrival_airport_id
        ).order_by(
            db.desc('count')
        ).limit(limit).all()
        
    @classmethod
    def get_similar_searches(cls, departure_airport_id, arrival_airport_id, limit=5):
        """獲取類似的搜索"""
        return cls.query.filter_by(
            departure_airport_id=departure_airport_id,
            arrival_airport_id=arrival_airport_id
        ).order_by(
            db.desc(cls.search_time)
        ).limit(limit).all() 