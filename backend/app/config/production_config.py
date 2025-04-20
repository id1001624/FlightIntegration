# backend/config/production_config.py
from .base_config import BaseConfig

class ProductionConfig(BaseConfig):
    """生產環境配置"""
    DEBUG = False
    LOG_LEVEL = 'INFO'
    # 生產環境特定的配置
    # 例如，如果 BaseConfig 中的 CACHE_TYPE 默認是 SimpleCache，
    # 但生產環境強制使用 Redis，可以在這裡設置：
    # CACHE_TYPE = "RedisCache"
    # if not BaseConfig.CACHE_REDIS_URL:
    #     print("[ProductionConfig] 警告: 生產環境配置為使用 Redis 緩存，但 CACHE_REDIS_URL 未設置！") 