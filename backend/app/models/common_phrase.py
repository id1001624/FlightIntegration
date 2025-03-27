"""
常用詞彙模型
"""
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from .base import db, Base

class CommonPhrase(Base):
    """常用詞彙數據模型"""
    __tablename__ = 'common_phrases'
    
    phrase_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    category = db.Column(db.String, nullable=False)
    language = db.Column(db.String, nullable=False)
    phrase = db.Column(db.Text, nullable=False)
    translation = db.Column(db.Text)
    usage_example = db.Column(db.Text)
    is_common = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f"<CommonPhrase {self.category} - {self.phrase[:20]}>"
    
    @classmethod
    def get_by_category(cls, category, language='zh-TW'):
        """獲取指定分類的詞彙"""
        return cls.query.filter_by(
            category=category,
            language=language
        ).all()
    
    @classmethod
    def get_common_phrases(cls, language='zh-TW', limit=10):
        """獲取常用詞彙"""
        return cls.query.filter_by(
            is_common=True,
            language=language
        ).limit(limit).all()
    
    @classmethod
    def search_phrases(cls, keyword, language='zh-TW'):
        """搜索詞彙"""
        return cls.query.filter(
            (cls.phrase.ilike(f'%{keyword}%') | 
            cls.translation.ilike(f'%{keyword}%')),
            cls.language == language
        ).all()
        
    @classmethod
    def get_travel_phrases(cls, dest_country, language='zh-TW'):
        """根據目的地國家獲取旅遊詞彙"""
        return cls.query.filter(
            cls.category.ilike('%travel%'),
            cls.language == language
        ).all() 