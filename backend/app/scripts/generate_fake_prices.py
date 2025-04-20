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
from dotenv import load_dotenv, find_dotenv

# --- 將 .env 加載移至頂部 --- 
dotenv_path = find_dotenv(filename='.env', raise_error_if_not_found=False, usecwd=True)
if dotenv_path:
    print(f"[generate_fake_prices.py] 找到並加載 .env 文件: {dotenv_path}")
    load_dotenv(dotenv_path=dotenv_path, override=True) # 添加 override=True
else:
    # 嘗試向上查找 backend/.env
    try:
        scripts_dir = os.path.dirname(__file__) # scripts/
        app_dir = os.path.dirname(scripts_dir) # app/
        backend_dir = os.path.dirname(app_dir) # backend/
        dotenv_path_alt = os.path.join(backend_dir, '.env')
        if os.path.exists(dotenv_path_alt):
            print(f"[generate_fake_prices.py] 在 backend 目錄找到並加載 .env 文件: {dotenv_path_alt}")
            load_dotenv(dotenv_path=dotenv_path_alt, override=True) # 添加 override=True
        else:
            print("[generate_fake_prices.py] 警告: 未在當前目錄或 backend 目錄找到 .env 文件。")
    except Exception as e:
        print(f"[generate_fake_prices.py] 查找備用 .env 時出錯: {e}")
# --------------------------

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
    db_url = os.getenv("SQLALCHEMY_DATABASE_URI")
    if not db_url:
        logger.error("未設置 SQLALCHEMY_DATABASE_URI 環境變數")
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
    """查找在 flights 表存在但在 ticket_prices 表中沒有任何記錄的航班"""
    # 使用 LEFT JOIN 查找在 flights 存在但在 ticket_prices 不存在的 flight_id
    query = """
    SELECT f.flight_id
    FROM flights f
    LEFT JOIN ticket_prices tp ON f.flight_id = tp.flight_id
    WHERE tp.flight_id IS NULL 
    LIMIT $1;
    """
    try:
        rows = await conn.fetch(query, limit)
        flight_ids = [row['flight_id'] for row in rows]
        # 修改日誌消息以反映新的查找邏輯
        logger.info(f"找到 {len(flight_ids)} 個在 flights 表存在但在 ticket_prices 表中沒有記錄的航班")
        return flight_ids
    except Exception as e:
        # 修改錯誤消息
        logger.error(f"查找缺少票價記錄的航班時出錯: {e}")
        return []

def generate_fake_price_data(flight_id):
    """為單個航班生成所有艙位的模擬票價數據"""
    prices = []
    now = datetime.now() # 使用本地時間或 UTC 取決於你的需求

    # 為基礎的經濟艙生成價格
    min_eco_price, max_eco_price = PRICE_RANGES["經濟"]
    economy_price = round(random.uniform(min_eco_price, max_eco_price), 2)
    base_price = economy_price # 為了兼容性，讓 base_price 等於 economy_price

    # 生成其他艙等價格，可能為 None
    business_price = round(economy_price * random.uniform(1.5, 3.0), 2) if random.random() > 0.2 else None
    first_price = round(economy_price * random.uniform(3.0, 5.0), 2) if random.random() > 0.5 else None

    # 對於每個艙位類型，生成一個記錄（因為當前模型仍依賴 class_type）
    for cabin in CABIN_CLASSES:
        # 生成可用座位數
        available_seats = random.randint(SEAT_RANGE[0], SEAT_RANGE[1])
        # 票價更新時間
        price_updated_at = now

        prices.append({
            'price_id': str(uuid.uuid4()),
            'flight_id': flight_id,
            'class_type': cabin, # 保留 class_type 以匹配當前模型
            'base_price': base_price, # 插入基礎價格（等於經濟艙）
            'economy_price': economy_price, # 插入經濟艙價格
            'business_price': business_price, # 插入商務艙價格 (可能為 None)
            'first_price': first_price, # 插入頭等艙價格 (可能為 None)
            'available_seats': available_seats,
            'price_updated_at': price_updated_at
        })
    return prices

async def insert_prices_batch(conn, prices_list):
    """批量插入票價數據"""
    if not prices_list:
        return 0

    # 修改 SQL 以包含所有價格欄位
    query = """
    INSERT INTO ticket_prices (
        price_id, flight_id, class_type, base_price,
        economy_price, business_price, first_price,
        available_seats, price_updated_at
    )
    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9) -- 使用 $1, $2... 佔位符
    ON CONFLICT (flight_id, class_type) DO UPDATE SET
        base_price = EXCLUDED.base_price,
        economy_price = EXCLUDED.economy_price,
        business_price = EXCLUDED.business_price,
        first_price = EXCLUDED.first_price,
        available_seats = EXCLUDED.available_seats,
        price_updated_at = EXCLUDED.price_updated_at;
    """

    try:
        # 將字典列表轉換為元組列表以供 executemany 使用
        data_tuples = [
            (
                p['price_id'],
                p['flight_id'],
                p['class_type'],
                p['base_price'],
                p['economy_price'],
                p['business_price'],
                p['first_price'],
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