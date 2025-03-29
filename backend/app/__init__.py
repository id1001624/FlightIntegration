"""
主應用模組 - 負責初始化Flask應用及組件
"""
import os
import logging
from flask import Flask, jsonify
from flask_cors import CORS

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app(config_name=None):
    """
    創建Flask應用
    
    Args:
        config_name (str, optional): 配置名稱，例如'development', 'production'
        
    Returns:
        Flask: Flask應用實例
    """
    app = Flask(__name__)
    
    # 加載配置
    configure_app(app, config_name)
    
    # 跨域支持
    CORS(app)
    
    # 初始化資料庫
    from app.models.base import db
    db.init_app(app)
    
    # 註冊藍圖
    register_blueprints(app)
    
    # 註冊錯誤處理
    register_error_handlers(app)
    
    # 註冊命令
    register_commands(app)
    
    return app

def configure_app(app, config_name=None):
    """
    配置應用
    
    Args:
        app (Flask): Flask應用實例
        config_name (str, optional): 配置名稱
    """
    # 加載基本配置
    app.config.from_object('config.base')
    
    # 根據環境加載配置
    if not config_name:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    try:
        app.config.from_object(f'config.{config_name}')
    except ImportError:
        app.config.from_object('config.development')
    
    # 加載環境變量配置
    app.config.from_envvar('APP_CONFIG', silent=True)
    
    # 設置測試模式
    app.config['TEST_MODE'] = os.environ.get('TEST_MODE', 'False').lower() == 'true'
    
    # 設置不要绕過緩存
    app.config['BYPASS_CACHE'] = os.environ.get('BYPASS_CACHE', 'False').lower() == 'true'
    
    # 從環境變量獲取資料庫連接字符串
    db_uri = os.environ.get('DATABASE_URL')
    if db_uri:
        # 適配 Heroku 的 postgres 連接字符串
        if db_uri.startswith('postgres://'):
            db_uri = db_uri.replace('postgres://', 'postgresql://', 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    
    # 確保設置了密鑰
    if not app.config.get('SECRET_KEY'):
        app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key')
    
    logger.info(f"應用配置加載完成，環境: {config_name}, 測試模式: {app.config['TEST_MODE']}")

def register_blueprints(app):
    """
    註冊藍圖
    
    Args:
        app (Flask): Flask應用實例
    """
    from app.controllers import flight_bp, airport_bp, admin_bp, auth_bp, user_bp, weather_bp
    
    # 註冊藍圖
    app.register_blueprint(flight_bp)
    app.register_blueprint(airport_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(weather_bp)
    
    logger.info("藍圖註冊完成")

def register_error_handlers(app):
    """
    註冊錯誤處理器
    
    Args:
        app (Flask): Flask應用實例
    """
    from app.utils.api_helper import api_response
    
    @app.errorhandler(404)
    def not_found(error):
        return api_response(False, message="資源未找到", status_code=404)
    
    @app.errorhandler(500)
    def internal_server_error(error):
        return api_response(False, message="伺服器內部錯誤", status_code=500)
    
    @app.errorhandler(400)
    def bad_request(error):
        return api_response(False, message=str(error), status_code=400)
    
    logger.info("錯誤處理器註冊完成")

def register_commands(app):
    """
    註冊自定義命令
    
    Args:
        app (Flask): Flask應用實例
    """
    @app.cli.command("init-db")
    def init_db():
        """初始化資料庫"""
        from app.models.base import db
        db.create_all()
        print("資料庫初始化完成")
    
    @app.cli.command("seed-db")
    def seed_db():
        """填充初始資料"""
        from app.models.base import db
        from app.services import data_sync_service
        
        # 同步機場和航空公司資料
        print("正在同步機場資料...")
        data_sync_service.sync_airports()
        
        print("正在同步航空公司資料...")
        data_sync_service.sync_airlines()
        
        print("資料填充完成")
    
    logger.info("命令註冊完成")