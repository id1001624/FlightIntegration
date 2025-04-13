#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
測試獲取指定機場今天出發的航班
"""
import logging
import sys
import os
from datetime import datetime
import json
import argparse

print("開始執行航班測試腳本")

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_flights')

print("日誌配置完成")

# 導入API客戶端
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

print(f"當前目錄: {current_dir}")
print(f"系統路徑: {sys.path}")

try:
    # 優先使用相對路徑導入
    print("嘗試使用相對路徑導入API客戶端...")
    from app.clients.flightstats_client import FlightStatsApiClient
    from app.clients.tdx_client import TdxApiClient
    from app.scripts.sync_manager import ApiSyncManager
    print("使用相對路徑導入API客戶端成功")
except ImportError as e:
    print(f"相對路徑導入失敗: {str(e)}")
    logger.error(f"相對路徑導入失敗: {str(e)}")
    
    try:
        # 嘗試調整路徑後導入
        print("嘗試調整系統路徑後導入...")
        sys.path.append(os.path.join(current_dir, 'app'))
        print(f"添加路徑: {os.path.join(current_dir, 'app')}")
        
        from app.clients.flightstats_client import FlightStatsApiClient
        from app.clients.tdx_client import TdxApiClient
        from app.scripts.sync_manager import ApiSyncManager
        print("調整路徑後導入成功")
    except ImportError as e2:
        print(f"調整路徑導入失敗: {str(e2)}")
        logger.error(f"調整路徑導入失敗: {str(e2)}")
        
        try:
            # 嘗試使用舊的客戶端路徑
            print("嘗試使用舊版客戶端路徑...")
            from app.deprecated.flightstats_sync import FlightStatsApiClient
            from app.deprecated.tdx_sync import TdxApiClient
            from app.scripts.sync_manager import ApiSyncManager
            print("舊版API客戶端導入成功")
        except ImportError as e3:
            print(f"所有導入嘗試均失敗: {str(e3)}")
            logger.error(f"所有導入嘗試均失敗: {str(e3)}")
            sys.exit(1)

def test_get_flights(departure_code):
    """
    測試獲取指定機場當天出發的航班
    """
    print(f"開始執行test_get_flights函數，出發機場: {departure_code}")
    logger.info(f"=== 開始測試獲取{departure_code}機場今天出發的航班 ===")
    
    try:
        logger.info(f"使用 ApiSyncManager 獲取 {departure_code} 出發航班")
        sync_manager = ApiSyncManager()
        today_str = datetime.now().strftime('%Y-%m-%d')
        
        logger.info("獲取台灣各機場出發航班:")
        results = sync_manager.sync_taiwan_departures(today_str)
        
        if departure_code in results and results[departure_code]:
            flights = results[departure_code]
            logger.info(f"成功獲取 {len(flights)} 個{departure_code}航班")
            
            # 顯示前5個航班詳情
            for i, flight in enumerate(flights[:5]):
                logger.info(f"航班 {i+1}: {flight.get('flight_number', '')} "
                           f"目的地: {flight.get('arrival_airport', '')}")
                
            # 分析航空公司分布
            airline_counts = {}
            for flight in flights:
                airline = flight.get('airline_code', 'Unknown')
                if airline not in airline_counts:
                    airline_counts[airline] = 0
                airline_counts[airline] += 1
            
            logger.info("航空公司分布:")
            for airline, count in airline_counts.items():
                logger.info(f"  - {airline}: {count}航班")
                
            # 分析目的地分布
            dest_counts = {}
            for flight in flights:
                dest = flight.get('arrival_airport', 'Unknown')
                if dest not in dest_counts:
                    dest_counts[dest] = 0
                dest_counts[dest] += 1
            
            logger.info("目的地分布:")
            for dest, count in dest_counts.items():
                logger.info(f"  - {dest}: {count}航班")
        else:
            logger.warning(f"未獲取到{departure_code}航班資料，可能今天沒有排程航班")
            
            # 檢查其他機場是否有數據
            other_airports = [code for code in results.keys() if results[code]]
            if other_airports:
                logger.info(f"其他有航班的機場: {', '.join(other_airports)}")
                total_flights = sum(len(results[ap]) for ap in other_airports)
                logger.info(f"其他機場總計有 {total_flights} 個航班")
    except Exception as e:
        logger.error(f"API測試失敗: {str(e)}")
    
    logger.info("=== 測試完成 ===")

def main():
    """處理命令行參數並執行測試"""
    parser = argparse.ArgumentParser(description='測試獲取指定機場今天出發的航班')
    parser.add_argument('--departure', '-d', required=True, help='出發機場IATA代碼 (例如: TSA, TPE, KHH)')
    
    args = parser.parse_args()
    test_get_flights(args.departure)

if __name__ == "__main__":
    main()