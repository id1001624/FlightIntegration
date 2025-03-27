"""
用戶查詢模型
"""
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from datetime import datetime
from .base import db, Base

class UserQuery(Base):
    """用戶查詢數據模型"""
    __tablename__ = 'user_queries'
    
    query_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.user_id'))
    platform = db.Column(db.String, nullable=False)  # 'web', 'line', 'mobile'
    query_type = db.Column(db.String, nullable=False)  # 'flight', 'airport', 'airline', 'weather'
    query_content = db.Column(db.Text, nullable=False)
    query_time = db.Column(db.DateTime, default=datetime.utcnow)
    response_content = db.Column(db.Text)
    was_helpful = db.Column(db.Boolean)
    
    def __repr__(self):
        return f"<UserQuery {self.query_type} - {self.query_content[:20]}>"
    
    @classmethod
    def get_by_user(cls, user_id, limit=10):
        """獲取用戶的查詢歷史"""
        return cls.query.filter_by(user_id=user_id).order_by(db.desc(cls.query_time)).limit(limit).all()
    
    @classmethod
    def get_popular_queries(cls, days=30, limit=10):
        """獲取熱門查詢"""
        from sqlalchemy import func
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        return db.session.query(
            cls.query_content,
            func.count().label('count')
        ).filter(
            cls.query_time >= cutoff_date
        ).group_by(
            cls.query_content
        ).order_by(
            db.desc('count')
        ).limit(limit).all()
    
    @classmethod
    def get_by_platform(cls, platform, limit=10):
        """獲取指定平台的查詢"""
        return cls.query.filter_by(platform=platform).order_by(db.desc(cls.query_time)).limit(limit).all()
    
    @classmethod
    def get_by_query_type(cls, query_type, limit=10):
        """獲取指定類型的查詢"""
        return cls.query.filter_by(query_type=query_type).order_by(db.desc(cls.query_time)).limit(limit).all()
    
    def mark_helpful(self, helpful=True):
        """標記查詢是否有幫助"""
        self.was_helpful = helpful
        db.session.commit()
        return self 