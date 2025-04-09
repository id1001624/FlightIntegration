"""
應用初始化模塊
"""
import os
import logging
from logging.handlers import RotatingFileHandler
import asyncio
from flask.json import jsonify
from werkzeug.exceptions import HTTPException
from asgiref.wsgi import WsgiToAsgi

# 加載環境變量
from dotenv import load_dotenv
load_dotenv()

from flask import Flask
from flask_cors import CORS
from flask_caching import Cache
from .models.base import db

# 初始化緩存
cache = Cache()

def create_app(config_name=None):
    """
    創建並初始化Flask應用
    
    Args:
        config_name: 配置名稱，用於選擇不同的配置環境
    
    Returns:
        flask.Flask: 初始化的Flask應用
    """
    app = Flask(__name__)
    
    # 配置應用
    if not config_name:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    if config_name == 'production':
        app.config.from_object('config.production')
    else:
        app.config.from_object('config.base')
    
    # 設置跨域 - 允許所有來源訪問
    CORS(app, resources={r"/api/*": {"origins": "*", 
                                     "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                                     "allow_headers": ["Content-Type", "Authorization"]}})
    
    # 初始化數據庫
    db.init_app(app)
    
    # 初始化緩存
    cache.init_app(app)
    
    # 配置日誌
    setup_logging(app)
    
    # 註冊藍圖
    register_blueprints(app)
    
    # 註冊錯誤處理
    register_error_handlers(app)
    
    # 支持異步路由函數
    app.before_request_funcs.setdefault(None, []).append(setup_async_context)
    
    return app

def setup_async_context():
    """設置異步上下文"""
    try:
        # 嘗試獲取或創建事件循環
        loop = asyncio.get_event_loop()
    except RuntimeError:
        # 沒有事件循環，創建一個新的
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

def setup_logging(app):
    """設置日誌配置"""
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO'))
    
    # 確保所有日誌處理器都使用UTF-8編碼
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'app.log'),
        maxBytes=10000000,  # 10MB
        backupCount=5,
        encoding='utf-8',  # 添加UTF-8編碼參數
        mode='a'           # 確保使用追加模式
    )
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)
    
    # 清除現有處理器
    for handler in app.logger.handlers[:]:
        app.logger.removeHandler(handler)
        
    # 添加新處理器
    app.logger.addHandler(file_handler)
    app.logger.setLevel(log_level)
    
    # 同時輸出到控制台
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    app.logger.addHandler(console_handler)
    
    # 設置根記錄器
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # 清除根記錄器現有處理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        
    # 將相同的處理器添加到根記錄器
    root_file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'app.log'),
        maxBytes=10000000,
        backupCount=5,
        encoding='utf-8',
        mode='a'
    )
    root_file_handler.setFormatter(formatter)
    root_file_handler.setLevel(log_level)
    root_logger.addHandler(root_file_handler)
    
    root_console_handler = logging.StreamHandler()
    root_console_handler.setFormatter(formatter)
    root_console_handler.setLevel(log_level)
    root_logger.addHandler(root_console_handler)

def register_blueprints(app):
    """註冊所有藍圖"""
    # 導入藍圖
    from .controllers.airline import airline_bp
    from .controllers.airport import airport_bp
    from .controllers.flight import flight_bp
    from .controllers.ticket_price import ticket_price_bp
    
    # 註冊藍圖
    app.register_blueprint(airline_bp, url_prefix='/api/airlines')
    app.register_blueprint(airport_bp, url_prefix='/api/airports')
    app.register_blueprint(flight_bp, url_prefix='/api/flights')
    app.register_blueprint(ticket_price_bp, url_prefix='/api/ticket-prices')

def register_error_handlers(app):
    """註冊錯誤處理器"""
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found'}, 404
    
    @app.errorhandler(500)
    def server_error(error):
        app.logger.error(error)
        return {'error': 'Internal server error'}, 500
