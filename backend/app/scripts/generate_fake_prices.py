#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
生成模擬機票價格數據腳本
"""

import asyncio
import asyncpg
import random
import uuid
from datetime import datetime
import logging
import os
import sys
from dotenv import load_dotenv

# 配置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- 配置 ---
CABIN_CLASSES = ["經濟", "商務", "頭等"]
PRICE_RANGES = {
    "經濟": (1500, 8000),  # 基礎價格範圍 (TWD)
    "商務": (5000, 20000),
    "頭等": (15000, 50000),
}
SEAT_RANGE = (5, 50) # 可用座位數範圍
BATCH_SIZE = 100 # 一次處理多少航班

# --- 資料庫連接 ---
async def get_db_connection():
    """獲取資料庫連接"""
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        logger.error("未設置 DATABASE_URL 環境變數")
        sys.exit(1)
        
    try:
        conn = await asyncpg.connect(db_url)
        logger.info("成功連接到資料庫")
        return conn
    except Exception as e:
        logger.error(f"連接資料庫失敗: {e}")
        sys.exit(1)

async def release_db_connection(conn):
    """釋放資料庫連接"""
    if conn:
        await conn.close()
        logger.info("資料庫連接已關閉")

# --- 主要邏輯 ---
async def find_flights_without_prices(conn, limit=BATCH_SIZE):
    """查找缺少票價記錄的航班"""
    query = """
    SELECT f.flight_id
    FROM flights f
    LEFT JOIN ticket_prices tp ON f.flight_id = tp.flight_id
    WHERE tp.price_id IS NULL
    LIMIT $1;
    """
    try:
        rows = await conn.fetch(query, limit)
        return [row['flight_id'] for row in rows]
    except Exception as e:
        logger.error(f"查找缺少票價的航班時出錯: {e}")
        return []

def generate_fake_price_data(flight_id):
    """為單個航班生成所有艙位的模擬票價數據"""
    prices_data = []
    now = datetime.now() # 使用本地時間或 UTC 取決於你的需求

    for cabin in CABIN_CLASSES:
        min_price, max_price = PRICE_RANGES[cabin]
        base_price = round(random.uniform(min_price, max_price), 2)
        available_seats = random.randint(SEAT_RANGE[0], SEAT_RANGE[1])
        
        prices_data.append({
            'price_id': uuid.uuid4(),
            'flight_id': flight_id,
            'class_type': cabin,
            'base_price': base_price,
            'available_seats': available_seats,
            'price_updated_at': now
        })
    return prices_data

async def insert_prices_batch(conn, prices_list):
    """批量插入票價數據"""
    if not prices_list:
        return 0
        
    query = """
    INSERT INTO ticket_prices (price_id, flight_id, class_type, base_price, available_seats, price_updated_at)
    VALUES ($1, $2, $3, $4, $5, $6)
    ON CONFLICT (flight_id, class_type) DO NOTHING; 
    """
    # ON CONFLICT 確保如果特定航班和艙位的價格已存在，則跳過插入，避免錯誤
    
    try:
        # 將字典列表轉換為元組列表以供 executemany 使用
        data_tuples = [
            (
                p['price_id'], 
                p['flight_id'], 
                p['class_type'], 
                p['base_price'], 
                p['available_seats'], 
                p['price_updated_at']
            ) for p in prices_list
        ]
        status = await conn.executemany(query, data_tuples)
        # executemany 不直接返回插入的行數，我們返回嘗試插入的記錄數
        logger.debug(f"批量插入狀態: {status}")
        return len(prices_list)
    except Exception as e:
        logger.error(f"批量插入票價時出錯: {e}")
        # 可以考慮更細緻的錯誤處理，例如記錄失敗的 flight_id
        return 0

async def main():
    """腳本主函數"""
    conn = None
    total_flights_processed = 0
    total_prices_inserted = 0
    
    try:
        conn = await get_db_connection()
        
        while True:
            logger.info(f"正在查找下一批 ({BATCH_SIZE}) 個缺少票價的航班...")
            flight_ids = await find_flights_without_prices(conn, BATCH_SIZE)
            
            if not flight_ids:
                logger.info("沒有更多缺少票價的航班了。")
                break
                
            logger.info(f"找到 {len(flight_ids)} 個航班，正在生成票價...")
            
            all_prices_to_insert = []
            for flight_id in flight_ids:
                fake_prices = generate_fake_price_data(flight_id)
                all_prices_to_insert.extend(fake_prices)
                
            logger.info(f"準備插入 {len(all_prices_to_insert)} 條票價記錄...")
            inserted_count = await insert_prices_batch(conn, all_prices_to_insert)
            logger.info(f"成功插入 {inserted_count} 條票價記錄。")
            
            total_flights_processed += len(flight_ids)
            total_prices_inserted += inserted_count
            
            # 如果找到的航班數少於批次大小，說明這是最後一批
            if len(flight_ids) < BATCH_SIZE:
                logger.info("已處理完所有找到的航班。")
                break
                
            # 短暫休眠避免過度請求資料庫 (可選)
            # await asyncio.sleep(0.1) 
            
    except Exception as e:
        logger.error(f"生成票價過程中發生未預期錯誤: {e}", exc_info=True)
    finally:
        await release_db_connection(conn)
        logger.info(f"腳本執行完畢。總共處理了 {total_flights_processed} 個航班，插入了 {total_prices_inserted} 條票價記錄。")

if __name__ == "__main__":
    asyncio.run(main()) 