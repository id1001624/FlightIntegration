"""
基礎模型定義
包含所有模型共用的基礎類和方法
"""
from datetime import datetime
from uuid import uuid4
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import UUID, JSONB

db = SQLAlchemy()

class Base(db.Model):
    """所有模型的基礎類"""
    __abstract__ = True
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def save(self):
        """保存當前實例到數據庫"""
        db.session.add(self)
        db.session.commit()
        return self
    
    def delete(self):
        """從數據庫中刪除當前實例"""
        db.session.delete(self)
        db.session.commit()
        return self
        
    @classmethod
    def get_by_id(cls, id):
        """通過ID獲取實例"""
        return cls.query.get(id)
    
    @classmethod
    def get_all(cls):
        """獲取所有實例"""
        return cls.query.all() 