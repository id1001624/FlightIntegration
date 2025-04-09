#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
資料庫連接管理模組
支持 SQLAlchemy 和 asyncpg 連接方式
"""

import os
import logging
from typing import AsyncGenerator, Optional
import urllib.parse

# 從 models/base.py 導入 SQLAlchemy 實例
# 注意：這裡不直接初始化 SQLAlchemy，而是使用已經在 base.py 中初始化的實例
from app.models.base import db as sqlalchemy_db

# 用於 FastAPI 異步支持
import asyncpg
from asyncpg.pool import Pool

# 配置日誌
logger = logging.getLogger("database")

# 數據庫連接設置
DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres@localhost:5432/flight_integration")

# 解析數據庫 URL
parsed_url = urllib.parse.urlparse(DB_URL)
DB_HOST = parsed_url.hostname or "localhost"
DB_PORT = parsed_url.port or 5432
DB_NAME = parsed_url.path[1:] if parsed_url.path else "flight_integration"
DB_USER = parsed_url.username or "postgres"
DB_PASSWORD = parsed_url.password or ""
DB_SSL = "sslmode=require" in DB_URL

# 異步數據庫連接池
_asyncpg_pool: Optional[Pool] = None

def get_db_url():
    """獲取數據庫URL"""
    return DB_URL

def init_sqlalchemy(app):
    """初始化 SQLAlchemy"""
    # 設置數據庫URL
    app.config['SQLALCHEMY_DATABASE_URI'] = get_db_url()
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 初始化 SQLAlchemy 並與 app 綁定
    sqlalchemy_db.init_app(app)
    
    logger.info("SQLAlchemy 數據庫連接已初始化")
    return sqlalchemy_db

async def init_asyncpg_pool() -> Pool:
    """初始化 asyncpg 連接池"""
    global _asyncpg_pool
    
    if _asyncpg_pool is None:
        try:
            # 直接使用完整連接字串，不嘗試解析
            _asyncpg_pool = await asyncpg.create_pool(
                DB_URL,
                min_size=5,
                max_size=20
            )
            logger.info("asyncpg 數據庫連接池初始化成功")
        except Exception as e:
            logger.error(f"asyncpg 數據庫連接池初始化失敗: {str(e)}")
            raise
    
    return _asyncpg_pool

async def get_db():
    """
    獲取 asyncpg 數據庫連接
    
    Returns:
        Connection: 異步數據庫連接
    """
    pool = await init_asyncpg_pool()
    return await pool.acquire()

async def release_db(conn):
    """
    釋放數據庫連接
    
    Args:
        conn: 要釋放的連接
    """
    if conn:
        pool = await init_asyncpg_pool()
        await pool.release(conn)

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