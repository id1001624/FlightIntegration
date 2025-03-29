"""
生產環境配置模組
"""
from config.base import *

# 生產模式配置
DEBUG = False

# 測試模式 (是否使用模擬數據)
TEST_MODE = False  # 生產環境使用真實數據

# 緩存配置
BYPASS_CACHE = False

# 日誌配置
LOG_LEVEL = 'INFO' 