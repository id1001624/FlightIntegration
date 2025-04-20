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
from flask import Flask
from flask_cors import CORS
from flask_caching import Cache
from .models.base import db

# 導入配置類
from backend.config import DevelopmentConfig, ProductionConfig # <-- 改回絕對導入

# 初始化緩存
cache = Cache()

def create_app(config_name=None):
    """
    創建並初始化Flask應用
    
    Args:
        config_name: 配置名稱 ('development' 或 'production')。
                     如果為 None，則從 FLASK_ENV 環境變數讀取。
    
    Returns:
        flask.Flask: 初始化的Flask應用
    """
    app = Flask(__name__, instance_relative_config=False) # instance_relative_config=False 確保從對象加載
    
    # 確定配置名稱
    if not config_name:
        config_name = os.environ.get('FLASK_ENV', 'development')
    print(f"[create_app] 使用配置: {config_name}")

    # 根據名稱加載配置對象
    if config_name == 'production':
        app.config.from_object(ProductionConfig)
        print("[create_app] 已加載 ProductionConfig")
    else: # 默認為 development
        app.config.from_object(DevelopmentConfig)
        print("[create_app] 已加載 DevelopmentConfig")

    # --- Debug: 打印關鍵配置值 --- 
    print(f"[create_app] DEBUG: {app.config.get('DEBUG')}")
    print(f"[create_app] SQLALCHEMY_DATABASE_URI: {app.config.get('SQLALCHEMY_DATABASE_URI')}")
    print(f"[create_app] LINE_CHANNEL_SECRET: {'已設置' if app.config.get('LINE_CHANNEL_SECRET') else '未設置'}")
    # -------------------------------
    
    # 設置跨域 - 允許所有來源訪問
    # 注意：CORS 的配置可以考慮移到 config 文件中
    CORS(app, resources={r"/api/*": {"origins": "*", 
                                     "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                                     "allow_headers": ["Content-Type", "Authorization"]}})
    
    # 初始化數據庫
    # 檢查 DATABASE_URI 是否真的被設置了
    if not app.config.get('SQLALCHEMY_DATABASE_URI'):
        raise RuntimeError("資料庫 URI (SQLALCHEMY_DATABASE_URI) 未在配置中設置！請檢查 .env 文件和 config 文件。")
    try:
        db.init_app(app)
        print("[create_app] db.init_app(app) 執行成功。")
    except Exception as e:
        print(f"[create_app] db.init_app(app) 執行時發生錯誤: {e}")
        raise # 重新拋出異常
    
    # 初始化緩存
    # 緩存配置現在從 app.config 中讀取 (因為已通過 from_object 加載)
    cache_config = {
        "CACHE_TYPE": app.config.get("CACHE_TYPE", "SimpleCache"), 
        "CACHE_DEFAULT_TIMEOUT": app.config.get("CACHE_DEFAULT_TIMEOUT", 300)
    }
    if cache_config["CACHE_TYPE"] == "RedisCache":
        cache_config["CACHE_REDIS_URL"] = app.config.get("CACHE_REDIS_URL")
        if not cache_config["CACHE_REDIS_URL"]:
            app.logger.warning("Redis URL未配置，將回退到 SimpleCache")
            cache_config["CACHE_TYPE"] = "SimpleCache"
            
    cache.init_app(app, config=cache_config)
    app.logger.info(f"緩存已初始化，類型: {cache_config['CACHE_TYPE']}")
    
    # 配置日誌
    setup_logging(app)
    
    # 註冊藍圖
    register_blueprints(app)
    
    # 註冊錯誤處理
    register_error_handlers(app)
    
    # 註冊腳本命令
    from .scripts import register_script_commands
    register_script_commands(app)
    app.logger.info("自定義腳本命令已註冊。")
    
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
    from .controllers.airline_controller import airline_bp
    from .controllers.airport_controller import airport_bp
    from .controllers.flight_controller import flight_bp
    from .controllers.price_controller import ticket_price_bp
    from .controllers.line_webhook_controller import line_webhook_bp
    
    # 註冊藍圖
    app.register_blueprint(airline_bp, url_prefix='/api/airlines')
    app.register_blueprint(airport_bp, url_prefix='/api/airports')
    app.register_blueprint(flight_bp, url_prefix='/api/flights')
    app.register_blueprint(ticket_price_bp, url_prefix='/api/ticket-prices')
    app.register_blueprint(line_webhook_bp)

def register_error_handlers(app):
    """註冊錯誤處理器"""
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found'}, 404
    
    @app.errorhandler(500)
    def server_error(error):
        app.logger.error(error)
        return {'error': 'Internal server error'}, 500
