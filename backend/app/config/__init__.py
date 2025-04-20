# backend/config/__init__.py
"""
配置包初始化文件

將主要的配置類導入到包命名空間中，方便外部導入。
例如，可以直接使用 from backend.config import DevelopmentConfig
"""
from .base_config import BaseConfig
from .development_config import DevelopmentConfig
from .production_config import ProductionConfig

# 可以選擇性地定義一個 __all__ 列表，明確指定允許從 'from backend.config import *' 導入的名稱
__all__ = ['BaseConfig', 'DevelopmentConfig', 'ProductionConfig'] 