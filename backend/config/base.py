"""
基礎配置模組 - 所有環境共用的配置項
"""
import os

# 安全配置
SECRET_KEY = os.environ.get('SECRET_KEY', 'development_key')

# 資料庫配置
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://neondb_owner:npg_v5X1mjPwFJgo@ep-blue-pond-a1mf0ja3-pooler.ap-southeast-1.aws.neon.tech/flight_integration?sslmode=require')
SQLALCHEMY_TRACK_MODIFICATIONS = False

# API設定
TDX_CLIENT_ID = os.environ.get('TDX_CLIENT_ID', 'n1116440-eff4950c-7994-47de')
TDX_CLIENT_SECRET = os.environ.get('TDX_CLIENT_SECRET', 'efc87a00-3930-4be2-bca9-37f3b8f46d1d')
FLIGHTSTATS_APP_ID = os.environ.get('FLIGHTSTATS_APP_ID', 'cb5c8184')
FLIGHTSTATS_APP_KEY = os.environ.get('FLIGHTSTATS_APP_KEY', '82304b41352d18995b0e7440a977cc1b')

# 緩存設定
CACHE_TYPE = "SimpleCache"
CACHE_DEFAULT_TIMEOUT = 300

# 日誌設定
LOG_LEVEL = 'INFO' 