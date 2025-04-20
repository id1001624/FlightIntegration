#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
資料庫連接管理模組
支持 SQLAlchemy 和 asyncpg 連接方式
"""

import os
import logging
from typing import AsyncGenerator, Optional
# import urllib.parse # 不再需要解析

# --- 移除頂層環境變數讀取 ---
# DATABASE_URL = os.environ.get("SQLALCHEMY_DATABASE_URI") 

# 從模型基礎導入 SQLAlchemy db 對象
from ..models.base import db as sqlalchemy_db 

# 用於 FastAPI 異步支持
import asyncpg
from asyncpg.pool import Pool

# 配置日誌
logger = logging.getLogger("database")

# --- 移除頂層 DB_URL 設置和解析 ---
# DB_URL = DATABASE_URL or "postgresql://postgres@localhost:5432/flight_integration"
# parsed_url = urllib.parse.urlparse(DB_URL)
# DB_HOST = parsed_url.hostname or "localhost"
# DB_PORT = parsed_url.port or 5432
# DB_NAME = parsed_url.path[1:] if parsed_url.path else "flight_integration"
# DB_USER = parsed_url.username or "postgres"
# DB_PASSWORD = parsed_url.password or ""
# DB_SSL = "sslmode=require" in DB_URL
# ------------------------------------

# 異步數據庫連接池
_asyncpg_pool: Optional[Pool] = None

def get_db_url():
    """動態獲取資料庫URL"""
    # 優先使用 SQLALCHEMY_DATABASE_URI，若無則使用 DATABASE_URL
    db_connection_url = os.environ.get('SQLALCHEMY_DATABASE_URI') or os.environ.get('DATABASE_URL')
    if not db_connection_url:
        logger.warning("環境變數 SQLALCHEMY_DATABASE_URI 和 DATABASE_URL 均未設置，返回 None")
    return db_connection_url

def init_sqlalchemy(app):
    """初始化 SQLAlchemy"""
    db_connection_url = get_db_url()
    if not db_connection_url:
         raise RuntimeError("無法初始化 SQLAlchemy：未找到資料庫連接 URL 環境變數。")
         
    # 設置數據庫URL
    app.config['SQLALCHEMY_DATABASE_URI'] = db_connection_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 初始化 SQLAlchemy 並與 app 綁定
    sqlalchemy_db.init_app(app)
    
    logger.info("SQLAlchemy 數據庫連接已初始化")
    return sqlalchemy_db

async def init_asyncpg_pool() -> Pool:
    """初始化 asyncpg 連接池 (動態讀取 URL)"""
    global _asyncpg_pool
    
    if _asyncpg_pool is None:
        # --- 在函數內部動態讀取環境變數 ---
        db_connection_url = get_db_url() # 使用輔助函數獲取 URL
        if not db_connection_url:
             # 如果沒有獲取到 URL，則無法創建連接池
             error_msg = "無法創建 asyncpg 連接池：環境變數 SQLALCHEMY_DATABASE_URI 或 DATABASE_URL 未設置。"
             logger.error(error_msg)
             raise RuntimeError(error_msg)
        # ------------------------------------
             
        try:
            # 直接使用獲取到的完整連接字串
            _asyncpg_pool = await asyncpg.create_pool(
                dsn=db_connection_url, # 將獲取的 URL 傳遞給 dsn 參數
                min_size=5,
                max_size=20
            )
            logger.info("asyncpg 數據庫連接池初始化成功")
        except Exception as e:
            logger.error(f"asyncpg 數據庫連接池初始化失敗: {str(e)}")
            raise
    
    return _asyncpg_pool

async def get_pool() -> Pool:
    """獲取初始化的 asyncpg 連接池"""
    # Ensures pool is initialized and returns it
    return await init_asyncpg_pool()

async def close_asyncpg_pool():
    """關閉 asyncpg 連接池"""
    global _asyncpg_pool
    
    if _asyncpg_pool:
        await _asyncpg_pool.close()
        _asyncpg_pool = None
        logger.info("asyncpg 數據庫連接池已關閉")

# 提供兼容舊代碼的 SQLAlchemy 直接訪問方式
db = sqlalchemy_db

# 提供在 FastAPI 啟動時初始化數據庫連接的函數
async def setup_db(app):
    """設置數據庫連接（同時適用於 Flask 和 FastAPI）"""
    # 初始化 asyncpg 連接池
    await init_asyncpg_pool()
    
    # 如果是 Flask 應用，也初始化 SQLAlchemy
    if hasattr(app, 'config'):
        init_sqlalchemy(app)
    
    # 在應用關閉時關閉連接池
    async def cleanup():
        await close_asyncpg_pool()
    
    if hasattr(app, 'on_event'):
        # FastAPI
        app.on_event("shutdown")(cleanup)
    else:
        # Flask
        @app.teardown_appcontext
        def teardown(exception=None):
            pass  # SQLAlchemy 會自動處理 