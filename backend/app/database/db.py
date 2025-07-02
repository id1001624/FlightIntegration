#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
資料庫連接管理模組
專注於 asyncpg 連接方式
"""

import os
import logging
from typing import Optional
import asyncpg
from asyncpg.pool import Pool
from flask import g

# 配置日誌
logger = logging.getLogger("database")

# 全局變量來保存連接池
_pool: Optional[Pool] = None

def get_db_url():
    """動態獲取資料庫URL"""
    db_connection_url = os.environ.get('SQLALCHEMY_DATABASE_URI') or os.environ.get('DATABASE_URL')
    if not db_connection_url:
        logger.warning("環境變數 SQLALCHEMY_DATABASE_URI 和 DATABASE_URL 均未設置，返回 None")
    return db_connection_url

async def init_asyncpg_pool():
    """創建並返回一個共享的 asyncpg 連接池"""
    global _pool
    if _pool is not None:
        # 連接池已存在是正常情況，不再打印日誌
        return _pool

    db_connection_url = get_db_url()
    if not db_connection_url:
         error_msg = "無法創建 asyncpg 連接池：環境變數 SQLALCHEMY_DATABASE_URI 或 DATABASE_URL 未設置。"
         logger.error(error_msg)
         raise RuntimeError(error_msg)
         
    try:
        _pool = await asyncpg.create_pool(
            dsn=db_connection_url,
            min_size=2,
            max_size=10, # 稍微增加池大小
            command_timeout=60.0
        )
        logger.info("成功創建並初始化了共享的 asyncpg 連接池。")
        return _pool
    except Exception as e:
        logger.error(f"創建共享的 asyncpg 連接池失敗: {str(e)}")
        raise

async def get_pool() -> Pool:
    """獲取共享的 asyncpg 連接池"""
    global _pool
    if _pool is None:
        logger.warning("連接池尚未初始化，現在進行初始化...")
        await init_asyncpg_pool()
    return _pool

async def close_asyncpg_pool():
    """關閉共享的 asyncpg 連接池"""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        logger.info("已成功關閉共享的 asyncpg 連接池。")

def setup_db(app):
    """在應用程式啟動時初始化數據庫連接池，並在關閉時註冊關閉函數。"""
    
    @app.before_first_request
    async def create_pool():
        """在第一個請求之前創建連接池。"""
        # 使用 g 來確保在應用上下文中只創建一次
        if 'asyncpg_pool' not in g:
            g.asyncpg_pool = await init_asyncpg_pool()

    @app.teardown_appcontext
    async def close_pool(exception=None):
        """在應用程式上下文結束時關閉連接池。"""
        # 注意: teardown 函數需要是同步的，但我們的關閉是異步的
        # 這裡我們不主動關閉，讓它在應用生命週期結束時自然關閉
        # 如果需要強制關閉，需要更複雜的 atexit 或 signal 處理
        pass
        
    logger.info("數據庫設置：asyncpg 連接池將在第一個請求時被創建。")
    