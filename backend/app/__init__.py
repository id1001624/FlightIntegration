"""
應用初始化模塊
"""
from flask import Flask
from flask_cors import CORS
from flask_caching import Cache
from .models.base import db
import os
import logging
from logging.handlers import RotatingFileHandler

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
    
    return app

def setup_logging(app):
    """設置日誌配置"""
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO'))
    
    handler = RotatingFileHandler(
        os.path.join(log_dir, 'app.log'),
        maxBytes=10000000,  # 10MB
        backupCount=5
    )
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    handler.setLevel(log_level)
    
    app.logger.addHandler(handler)
    app.logger.setLevel(log_level)
    
    # 同時輸出到控制台
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    app.logger.addHandler(console_handler)

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
