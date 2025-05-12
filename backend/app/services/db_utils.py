#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
資料庫操作工具模組 - 提供通用的資料庫操作輔助函數
"""

import logging
import asyncpg
from ..database.db import init_asyncpg_pool
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

async def execute_db_operation(operation_func, *args, **kwargs):
    """
    執行資料庫操作的通用模式，處理連接獲取和釋放
    
    Args:
        operation_func: 接受連接和其他參數的非同步函數
        *args, **kwargs: 傳遞給 operation_func 的參數
        
    Returns:
        operation_func 的返回值，或出錯時返回 None
    """
    pool = None
    conn = None
    try:
        pool = await init_asyncpg_pool()
        conn = await pool.acquire()
        return await operation_func(conn, *args, **kwargs)
    except Exception as e:
        operation_name = operation_func.__name__ if hasattr(operation_func, "__name__") else "匿名操作"
        logger.error(f"執行資料庫操作 '{operation_name}' 時發生錯誤: {e}", exc_info=True)
        return None
    finally:
        if conn and pool:
            try:
                await pool.release(conn)
            except (RuntimeError, asyncpg.exceptions.InterfaceError) as e:
                logger.warning(f"釋放連接時發生可忽略的異常: {e}")
            except Exception as e:
                logger.error(f"釋放連接時發生未預期的異常: {e}", exc_info=True)

async def execute_query(conn, query, *params, fetch_one=False, return_none_on_empty=False):
    """
    執行 SQL 查詢並返回結果
    
    Args:
        conn: 資料庫連接
        query: SQL 查詢字符串
        *params: 查詢參數
        fetch_one: 是否只獲取一條記錄
        return_none_on_empty: 若結果為空時是否返回 None
        
    Returns:
        查詢結果列表或單條記錄
    """
    try:
        if fetch_one:
            result = await conn.fetchrow(query, *params)
            if result:
                return dict(result)
            return None if return_none_on_empty else {}
        else:
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"執行查詢時發生錯誤: {e}\nSQL: {query}\nParams: {params}", exc_info=True)
        raise

def normalize_cabin_class(cabin_class: str) -> str:
    """
    標準化艙等名稱
    """
    # 中文名稱到英文名稱的映射
    cabin_mapping = {
        '經濟': 'economy',
        '經濟艙': 'economy',
        '商務': 'business',
        '商務艙': 'business',
        '頭等': 'first', 
        '頭等艙': 'first'
    }
    
    # 如果是中文名稱，轉換為英文
    if cabin_class in cabin_mapping:
        return cabin_mapping[cabin_class]
    
    # 如果已經是英文或是其他格式，直接返回 (英文格式應為 economy, business, first)
    return cabin_class

def get_price_field_by_cabin_class(cabin_class: str) -> str:
    """
    根據艙等獲取對應的價格欄位名稱
    """
    cabin_class = normalize_cabin_class(cabin_class)
    
    field_mapping = {
        'economy': 'economy_price',
        'business': 'business_price',
        'first': 'first_price'
    }
    
    # 如果已經是欄位名稱，則直接返回
    if cabin_class in ['economy_price', 'business_price', 'first_price']:
        return cabin_class
    
    # 否則查找映射
    return field_mapping.get(cabin_class, 'economy_price')

def get_display_name_by_cabin_field(cabin_field: str) -> str:
    """
    根據價格欄位名稱獲取顯示名稱
    """
    display_mapping = {
        'economy_price': '經濟艙',
        'business_price': '商務艙',
        'first_price': '頭等艙'
    }
    
    return display_mapping.get(cabin_field, '經濟艙') 