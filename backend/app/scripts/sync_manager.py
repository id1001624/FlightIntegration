#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Amadeus 數據同步管理器
"""
import asyncio
import logging
import argparse
import sys
from typing import List, Dict

# --- Logger 配置 ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('sync_manager')

# --- 導入 ---
# 確保腳本可以作為模塊運行，並能找到上層包
try:
    from ..services.amadeus_service import amadeus_service
    from ..services.airport_service import airport_service
    from ..services.airline_service import airline_service
    from .constants import TAIWAN_AIRPORTS, AIRLINE_CODES
except ImportError as e:
    logger.error(f"無法導入必要的模組。請確保以 'python -m backend.app.scripts.sync_manager' 方式運行。錯誤: {e}")
    sys.exit(1)

class AmadeusSyncManager:
    """與 Amadeus API 協作，同步機場和航空公司數據。"""

    async def sync_airlines_from_iata_codes(self, airline_codes: List[str]):
        """
        根據提供的航空公司 IATA 代碼列表，從 Amadeus 獲取詳細資訊並存入資料庫。
        """
        logger.info(f"準備從 Amadeus 同步 {len(airline_codes)} 家航空公司的數據...")
        # 這裡的 amadeus_service.get_airline_details 預計是一個異步函數
        airlines_data = await amadeus_service.get_airlines_by_codes(airline_codes)
        
        if not airlines_data:
            logger.warning("從 Amadeus 未獲取到任何航空公司數據。")
            return

        logger.info(f"從 Amadeus 成功獲取 {len(airlines_data)} 家航空公司的數據。")
        
        # 這裡的 airline_service.save_airlines 預計是一個異步函數
        saved_count = await airline_service.bulk_save_airlines(airlines_data)
        logger.info(f"成功儲存或更新了 {saved_count} 家航空公司的數據到資料庫。")

    async def sync_airports_from_iata_codes(self, airport_codes: List[str]):
        """
        根據提供的機場 IATA 代碼列表，從 Amadeus 獲取機場資訊並存入資料庫。
        (此功能為示意，因為 Amadeus API 可能沒有直接通過 IATA code 批量獲取機場資訊的端點，
        通常機場數據是靜態的或通過其他方式獲取。此處我們假設有一個服務可以做到)
        """
        logger.info(f"準備同步 {len(airport_codes)} 個機場的數據...")
        # 假設 airport_service 有一個方法可以處理這件事
        # 在我們的案例中，機場資料是相對靜態的，可能已經在資料庫中
        # 這裡的重點是確保我們的 airport_service 有能力處理數據的更新
        
        # 模擬從某個服務獲取數據
        airports_data = []
        for code in airport_codes:
            # 這裡應該是調用 amadeus_service 的一個方法
            # 為了演示，我們先創建一些假數據
             airports_data.append({
                "iata_code": code,
                "name_zh": f"機場-{code}", # 實際應從API獲取
                "name_en": f"Airport-{code}",
                "country": "N/A",
                "city": "N/A"
            })

        saved_count = await airport_service.bulk_save_airports(airports_data)
        logger.info(f"成功儲存了 {saved_count} 個機場的數據。")


async def main():
    """主函數，處理命令行參數並執行異步操作"""
    parser = argparse.ArgumentParser(description='Amadeus 數據同步工具')
    parser.add_argument('--sync-airlines', action='store_true', help='同步所有已知的航空公司數據')
    parser.add_argument('--sync-airports', action='store_true', help='同步所有已知的機場數據')
    
    args = parser.parse_args()
    
    manager = AmadeusSyncManager()
    
    if not any(vars(args).values()):
        parser.print_help()
        sys.exit(0)

    try:
        tasks = []
        if args.sync_airlines:
            logger.info("檢測到 --sync-airlines 參數。")
            # 我們從 AIRLINE_CODES 常量中獲取需要同步的航空公司列表
            task = manager.sync_airlines_from_iata_codes(AIRLINE_CODES)
            tasks.append(task)
            
        if args.sync_airports:
            logger.info("檢測到 --sync-airports 參數。")
            # 我們從 TAIWAN_AIRPORTS 常量中獲取機場列表
            task = manager.sync_airports_from_iata_codes(TAIWAN_AIRPORTS)
            tasks.append(task)

        if tasks:
            logger.info(f"準備執行 {len(tasks)} 個同步任務...")
            await asyncio.gather(*tasks)
            logger.info("所有同步任務已完成。")
    finally:
        # 確保 aiohttp session 被關閉
        logger.info("正在關閉 aiohttp session...")
        await amadeus_service.close_session()

if __name__ == "__main__":
    # 使用 asyncio.run() 來執行異步的 main 函數
    asyncio.run(main()) 