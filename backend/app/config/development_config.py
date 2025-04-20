# backend/config/development_config.py
from .base_config import BaseConfig

class DevelopmentConfig(BaseConfig):
    """開發環境配置"""
    DEBUG = True
    SQLALCHEMY_ECHO = False # 可以設置為 True 來查看 SQLAlchemy 生成的 SQL
    LOG_LEVEL = 'DEBUG'
    # 開發環境可以覆蓋 BaseConfig 中的某些設置，如果需要的話
    # 例如，使用本地的 Redis 而不是生產環境的
    # CACHE_TYPE = "RedisCache"
    # CACHE_REDIS_URL = "redis://localhost:6379/0" 