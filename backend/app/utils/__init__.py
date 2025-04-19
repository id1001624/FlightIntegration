"""
工具包初始化文件

導入常用的工具類或函數到包命名空間中，方便外部訪問。
"""

# from .api_client import APIClient # <-- 舊的錯誤拼寫
from .api_client import ApiClient # <-- 確保是 ApiClient
from .cache_manager import CacheManager
# from .date_utils import DateUtils # <-- 移除不存在的類導入
from .date_utils import parse_datetime, format_datetime, get_date_range # <-- 導入實際的函數
# from app.utils.token_manager import TokenManager # <-- 舊的絕對導入
from .token_manager import TokenManager # <-- 改為相對導入
# from app.utils.mock_data_generator import MockDataGenerator # <-- 舊的絕對導入
# from app.utils.rate_limiter import RateLimiter # <-- 舊的絕對導入
from .mock_data_generator import MockDataGenerator # <-- 改為相對導入
from .rate_limiter import RateLimiter # <-- 改為相對導入

# 可以選擇性地定義一個 __all__ 列表
__all__ = [
    'ApiClient', # <-- 確保是 ApiClient
    'CacheManager',
    # 'DateUtils', # <-- 移除
    'parse_datetime', # <-- 添加函數名
    'format_datetime', # <-- 添加函數名
    'get_date_range', # <-- 添加函數名
    'TokenManager',
    'MockDataGenerator',
    'RateLimiter'
]