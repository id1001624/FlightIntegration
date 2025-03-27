"""
航空公司模型
"""
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from .base import db, Base

class Airline(Base):
    """航空公司數據模型"""
    __tablename__ = 'airlines'
    
    airline_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    iata_code = db.Column(db.String, unique=True)
    name_zh = db.Column(db.String, nullable=False)
    name_en = db.Column(db.String, nullable=False)
    country = db.Column(db.String, nullable=False)
    website = db.Column(db.String)
    contact_phone = db.Column(db.String)
    is_domestic = db.Column(db.Boolean, default=False)
    
    # 關聯
    flights = db.relationship('Flight', backref='airline', lazy='dynamic')
    
    def __repr__(self):
        return f"<Airline {self.iata_code} - {self.name_zh}>"
    
    @classmethod
    def get_by_iata(cls, iata_code):
        """通過IATA代碼獲取航空公司"""
        return cls.query.filter_by(iata_code=iata_code).first()
    
    @classmethod
    def get_by_country(cls, country):
        """獲取指定國家的所有航空公司"""
        return cls.query.filter_by(country=country).all()
    
    @classmethod
    def get_domestic(cls):
        """獲取所有國內航空公司"""
        return cls.query.filter_by(is_domestic=True).all()
        
    @classmethod
    def get_international(cls):
        """獲取所有國際航空公司"""
        return cls.query.filter_by(is_domestic=False).all() 