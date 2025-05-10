#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
資料庫連接管理模組
支持 SQLAlchemy 和 asyncpg 連接方式
"""

import os
import logging
from typing import AsyncGenerator, Optional
import asyncio 

# 從模型基礎導入 SQLAlchemy db 對象
from ..models.base import db as sqlalchemy_db 

# 用於 FastAPI 異步支持
import asyncpg
from asyncpg.pool import Pool

# 配置日誌
logger = logging.getLogger("database")

# 異步數據庫連接池
# _asyncpg_pool: Optional[Pool] = None # 移除全局變數
# _pool_lock = asyncio.Lock()  # 移除鎖

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
    """創建並返回一個新的 asyncpg 連接池 (不再共享全局池)"""
    # global _asyncpg_pool # 移除 global
    
    # 移除鎖的使用
    # async with _pool_lock:
    #     if _asyncpg_pool is None:
    
    # --- 在函數內部動態讀取環境變數 ---
    db_connection_url = get_db_url() # 使用輔助函數獲取 URL
    if not db_connection_url:
         # 如果沒有獲取到 URL，則無法創建連接池
         error_msg = "無法創建 asyncpg 連接池：環境變數 SQLALCHEMY_DATABASE_URI 或 DATABASE_URL 未設置。"
         logger.error(error_msg)
         raise RuntimeError(error_msg)
    # ------------------------------------
         
    try:
        # 直接使用獲取到的完整連接字串創建 *新* 連接池
        pool = await asyncpg.create_pool(
            dsn=db_connection_url, # 將獲取的 URL 傳遞給 dsn 參數
            min_size=2,  # 減少每次創建的最小連接數
            max_size=5,  # 減少每次創建的最大連接數
            # 移除不活動超時，因為池是短暫的
            # max_inactive_connection_lifetime=300.0  
            command_timeout=60.0 # 添加命令超時
        )
        logger.info("為當前請求創建了一個新的 asyncpg 連接池")
        return pool # 直接返回新創建的池
    except Exception as e:
        logger.error(f"創建新的 asyncpg 連接池失敗: {str(e)}")
        raise
    
    # return _asyncpg_pool # 不再返回全局池

async def get_pool() -> Pool:
    """獲取 asyncpg 連接池 (現在每次都創建新的)"""
    # 確保連接池已初始化並返回
    return await init_asyncpg_pool()

async def close_asyncpg_pool():
    """關閉 asyncpg 連接池 (不再需要全局關閉)"""
    # global _asyncpg_pool # 移除 global
    
    # 這個函數現在意義不大，因為池是按需創建的
    # 如果需要關閉傳入的特定池，需要修改接口
    # if _asyncpg_pool:
    #     await _asyncpg_pool.close()
    #     _asyncpg_pool = None
    #     logger.info("asyncpg 數據庫連接池已關閉")
    logger.warning("close_asyncpg_pool 不再管理全局池，此調用無效果。")
    pass # 保留函數定義以避免導入錯誤，但使其無操作

# 提供兼容舊代碼的 SQLAlchemy 直接訪問方式
db = sqlalchemy_db

# 提供在 FastAPI 啟動時初始化數據庫連接的函數
async def setup_db(app):
    """設置數據庫連接（同時適用於 Flask 和 FastAPI）"""
    # 初始化 asyncpg 連接池 (不再需要在啟動時預創建全局池)
    # await init_asyncpg_pool() 
    logger.info("數據庫設置：asyncpg 連接池將按需創建。")
    
    # 如果是 Flask 應用，也初始化 SQLAlchemy
    if hasattr(app, 'config'):
        init_sqlalchemy(app)
    
    # 在應用關閉時關閉連接池 (不再需要全局關閉)
    # async def cleanup():
    #     await close_asyncpg_pool()
    
    # if hasattr(app, 'on_event'):
    #     # FastAPI
    #     app.on_event("shutdown")(cleanup)
    # else:
    #     # Flask
    #     @app.teardown_appcontext
    #     def teardown(exception=None):
    #         pass  # SQLAlchemy 會自動處理 