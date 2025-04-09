"""
航空公司模型
"""
from .base import db, Base

class Airline(Base):
    """航空公司數據模型"""
    __tablename__ = 'airlines'
    
    airline_id = db.Column(db.String, primary_key=True)
    name_zh = db.Column(db.String, nullable=False)
    name_en = db.Column(db.String, nullable=False)
    website = db.Column(db.String)
    contact_phone = db.Column(db.String)
    is_domestic = db.Column(db.Boolean)
    
    # 關聯
    flights = db.relationship('Flight', backref='airline', lazy='dynamic')
    
    def __repr__(self):
        return f"<Airline {self.airline_id} - {self.name_zh}>"
    
    @classmethod
    def get_by_iata(cls, iata_code):
        """通過IATA代碼獲取航空公司"""
        return cls.query.filter_by(airline_id=iata_code).first()
    
    @classmethod
    def get_by_name(cls, name, lang='zh'):
        """通過名稱獲取航空公司"""
        if lang == 'zh':
            return cls.query.filter(cls.name_zh.ilike(f"%{name}%")).all()
        else:
            return cls.query.filter(cls.name_en.ilike(f"%{name}%")).all()
    
    @classmethod
    def get_domestic(cls):
        """獲取所有國內航空公司"""
        return cls.query.filter_by(is_domestic=True).all()
        
    @classmethod
    def get_international(cls):
        """獲取所有國際航空公司"""
        return cls.query.filter_by(is_domestic=False).all() 