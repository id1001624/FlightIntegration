import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

class Config:
    """應用配置類"""
    # 密鑰配置 - 用於加密 session 等安全功能
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'wLUj3cXI6CtgHnP9mYs5A2qZfvR0DOhE'
    
    # SQL Server 資料庫連接設定 - 使用環境變數
    SQLALCHEMY_DATABASE_URI = (
        f'mssql+pyodbc://{os.environ.get("DB_USER", "adminfid")}:'
        f'{os.environ.get("DB_PASSWORD", "Flight_admin123@")}'
        f'@{os.environ.get("DB_SERVER", "140.131.114.241")}/'
        f'{os.environ.get("DB_NAME", "FlightIntegration_DB")}'
        '?driver=SQL+Server'
    )
    
    # 關閉 SQLAlchemy 的修改追蹤系統，減少記憶體使用
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 調試模式 - 本地開發使用
    DEBUG = os.getenv('FLASK_DEBUG', '1') == '1'
    
    # 其他實際使用的配置
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # 增大到 8MB
    
    # API 請求速率限制
    RATE_LIMIT = 150  # 增加到每分鐘 150 次