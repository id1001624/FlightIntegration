# backend/config/base_config.py
import os
# --- 移除導入時的 .env 加載 --- 
# from dotenv import load_dotenv, find_dotenv

# # 查找並加載 .env 文件
# dotenv_path = find_dotenv()
# if dotenv_path:
#     print(f"[BaseConfig] 找到 .env 文件: {dotenv_path}")
#     load_dotenv(dotenv_path=dotenv_path)
# else:
#     print("[BaseConfig] 警告: 未找到 .env 文件。")
# ------------------------------

class BaseConfig:
    """基礎配置類"""
    # 從環境變數獲取，提供默認值以防萬一
    SECRET_KEY = os.environ.get('SECRET_KEY', 'a_very_default_secret_key_for_dev')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 資料庫 URI - 必須在 .env 文件中設置
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI')
    # --- 移除類定義級別的檢查，將檢查移到應用創建時 --- 
    # if not SQLALCHEMY_DATABASE_URI:
    #     print("[BaseConfig] 嚴重錯誤: 環境變數 SQLALCHEMY_DATABASE_URI 未在 .env 文件中設置！")
        # 在實際應用中，這裡可能應該直接 raise RuntimeError
    # ----------------------------------------------

    # LINE Bot 配置 - 從環境變數讀取
    LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')
    LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')

    # 緩存配置 (可以放在這裡或特定環境配置中)
    CACHE_TYPE = os.environ.get("CACHE_TYPE", "SimpleCache") # 默認使用簡單內存緩存
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get("CACHE_DEFAULT_TIMEOUT", 300))
    CACHE_REDIS_URL = os.environ.get("CACHE_REDIS_URL") # 只有當 CACHE_TYPE 為 RedisCache 時才需要

    # 其他應用級別的配置可以在這裡添加
    # 例如：API密鑰、第三方服務URL等
    TDX_CLIENT_ID = os.environ.get('TDX_CLIENT_ID')
    TDX_CLIENT_SECRET = os.environ.get('TDX_CLIENT_SECRET')
    FLIGHTSTATS_API_ID = os.environ.get('FLIGHTSTATS_API_ID')
    FLIGHTSTATS_API_KEY = os.environ.get('FLIGHTSTATS_API_KEY')
    TDX_API_ID = os.environ.get('TDX_API_ID')
    TDX_API_KEY = os.environ.get('TDX_API_KEY')
