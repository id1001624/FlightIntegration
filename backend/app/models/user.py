"""
用戶模型
"""
from sqlalchemy.dialects.postgresql import UUID, JSONB
from uuid import uuid4
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from .base import db, Base

class User(Base):
    """用戶數據模型"""
    __tablename__ = 'users'
    
    user_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    line_user_id = db.Column(db.String, unique=True)
    email = db.Column(db.String, unique=True)
    password_hash = db.Column(db.String)
    full_name = db.Column(db.String)
    phone = db.Column(db.String)
    passport_number = db.Column(db.String)
    nationality = db.Column(db.String)
    date_of_birth = db.Column(db.Date)
    preferences = db.Column(JSONB, default={})
    last_login_time = db.Column(db.DateTime(timezone=True))
    
    # 關聯
    search_history = db.relationship('UserSearchHistory', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    queries = db.relationship('UserQuery', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<User {self.email or self.line_user_id}>"
    
    @property
    def password(self):
        """Password property that raises an error when accessed"""
        raise AttributeError('密碼不可讀取')
        
    @password.setter
    def password(self, password):
        """Sets password hash"""
        self.password_hash = generate_password_hash(password)
        
    def verify_password(self, password):
        """Verify password against stored hash"""
        if self.password_hash:
            return check_password_hash(self.password_hash, password)
        return False
    
    def update_login_time(self):
        """更新最後登入時間"""
        self.last_login_time = datetime.utcnow()
        db.session.commit()
    
    @classmethod
    def get_by_email(cls, email):
        """通過郵箱獲取用戶"""
        return cls.query.filter_by(email=email).first()
    
    @classmethod
    def get_by_line_id(cls, line_user_id):
        """通過LINE ID獲取用戶"""
        return cls.query.filter_by(line_user_id=line_user_id).first() 