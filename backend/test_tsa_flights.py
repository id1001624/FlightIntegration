#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
測試獲取TSA (台北松山機場) 今天出發的航班
"""
import logging
import sys
import os
from datetime import datetime
import json

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_tsa')

# 導入API客戶端
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

try:
    # 嘗試導入API客戶端
    from app.scripts.flightstats_sync import FlightStatsApiClient
    from app.scripts.tdx_sync import TdxApiClient
    from app.scripts.sync_manager import ApiSyncManager
except ImportError as e:
    logger.error(f"導入API客戶端失敗: {str(e)}")
    logger.info("嘗試使用相對路徑導入...")
    try:
        sys.path.append(os.path.join(current_dir, 'app', 'scripts'))
        from app.scripts.flightstats_sync import FlightStatsApiClient
        from app.scripts.tdx_sync import TdxApiClient
        from app.scripts.sync_manager import ApiSyncManager
    except ImportError as e:
        logger.error(f"導入API客戶端失敗: {str(e)}")
        sys.exit(1)

def test_get_tsa_flights():
    """
    測試獲取TSA機場當天出發的航班
    """
    logger.info("=== 開始測試獲取TSA機場今天出發的航班 ===")
    
    # 測試1: 使用 FlightStats API
    try:
        logger.info("測試1: 使用 FlightStats API 獲取 TSA 出發航班")
        fs_client = FlightStatsApiClient()
        today = datetime.now()
        
        # 請求所有航班
        logger.info("獲取所有航空公司的航班:")
        flights = fs_client.get_airport_departures(
            airport_code="TSA", 
            date=today
        )
        
        if flights:
            logger.info(f"成功獲取 {len(flights)} 個航班")
            for i, flight in enumerate(flights[:5]):  # 只顯示前5個航班
                logger.info(f"航班 {i+1}: {flight.get('airlineCode', '')} {flight.get('flightNumber', '')} "
                           f"目的地: {flight.get('destinationAirportCode', '')}")
                
            # 分析航空公司分布
            airline_counts = {}
            for flight in flights:
                airline = flight.get('airlineCode', 'Unknown')
                if airline not in airline_counts:
                    airline_counts[airline] = 0
                airline_counts[airline] += 1
            
            logger.info("航空公司分布:")
            for airline, count in airline_counts.items():
                logger.info(f"  - {airline}: {count}航班")
            
            # 檢查目標航空公司
            target_airlines = ['BR', 'JL', 'JX', 'IT', 'CX', 'DA', 'CI', 'OZ', 'AE', 'B7']
            target_flights = [f for f in flights if f.get('airlineCode') in target_airlines]
            logger.info(f"目標航空公司航班數: {len(target_flights)}/{len(flights)}")
        else:
            logger.warning("未獲取到航班資料")
            logger.info("可能的原因:")
            logger.info("1. TSA機場今天可能確實沒有航班")
            logger.info("2. API金鑰可能無效或過期")
            logger.info("3. API連接可能出現問題")
            logger.info("4. 日期範圍可能不在API支援範圍內")
    except Exception as e:
        logger.error(f"FlightStats API測試失敗: {str(e)}")
    
    # 測試2: 使用 TDX API
    try:
        logger.info("\n測試2: 使用 TDX API 獲取 TSA 出發航班")
        tdx_client = TdxApiClient()
        today_str = datetime.now().strftime('%Y-%m-%d')
        
        logger.info("獲取FIDS航班資訊:")
        tdx_flights = tdx_client.get_fids_flights("TSA", today_str)
        
        if tdx_flights:
            logger.info(f"成功獲取 {len(tdx_flights)} 個航班")
            for i, flight in enumerate(tdx_flights[:5]):  # 只顯示前5個航班
                logger.info(f"航班 {i+1}: {flight.get('AirlineID', '')} {flight.get('FlightNumber', '')} "
                           f"目的地: {flight.get('ArrivalAirportID', '')}")
                
            # 分析航空公司分布
            airline_counts = {}
            for flight in tdx_flights:
                airline = flight.get('AirlineID', 'Unknown')
                if airline not in airline_counts:
                    airline_counts[airline] = 0
                airline_counts[airline] += 1
            
            logger.info("航空公司分布:")
            for airline, count in airline_counts.items():
                logger.info(f"  - {airline}: {count}航班")
            
            # 檢查目標航空公司
            target_airlines = ['BR', 'JL', 'JX', 'IT', 'CX', 'DA', 'CI', 'OZ', 'AE', 'B7']
            target_flights = [f for f in tdx_flights if f.get('AirlineID') in target_airlines]
            logger.info(f"目標航空公司航班數: {len(target_flights)}/{len(tdx_flights)}")
        else:
            logger.warning("未獲取到航班資料")
            logger.info("可能的原因:")
            logger.info("1. TDX API可能無法獲取TSA機場數據")
            logger.info("2. API金鑰可能無效或過期")
            logger.info("3. API連接可能出現問題")
            logger.info("4. 今天TSA機場可能確實沒有航班")
    except Exception as e:
        logger.error(f"TDX API測試失敗: {str(e)}")
    
    # 測試3: 使用 Sync Manager (整合方案)
    try:
        logger.info("\n測試3: 使用 ApiSyncManager 獲取 TSA 出發航班")
        sync_manager = ApiSyncManager()
        today_str = datetime.now().strftime('%Y-%m-%d')
        
        logger.info("獲取TSA機場出發航班:")
        results = sync_manager.sync_taiwan_departures(today_str)
        
        if "TSA" in results and results["TSA"]:
            tsa_flights = results["TSA"]
            logger.info(f"成功獲取 {len(tsa_flights)} 個TSA航班")
            for i, flight in enumerate(tsa_flights[:5]):  # 只顯示前5個航班
                logger.info(f"航班 {i+1}: {flight.get('flight_number', '')} "
                           f"目的地: {flight.get('arrival_airport', '')}")
                
            # 分析航空公司分布
            airline_counts = {}
            for flight in tsa_flights:
                airline = flight.get('airline_code', 'Unknown')
                if airline not in airline_counts:
                    airline_counts[airline] = 0
                airline_counts[airline] += 1
            
            logger.info("航空公司分布:")
            for airline, count in airline_counts.items():
                logger.info(f"  - {airline}: {count}航班")
        else:
            logger.warning("未獲取到TSA航班資料")
            logger.info("可能的原因:")
            logger.info("1. 同步管理器可能只返回目標航空公司的航班")
            logger.info("2. 今天TSA機場可能確實沒有目標航空公司的航班")
            logger.info("3. 兩個API來源都可能無法獲取資料")
    except Exception as e:
        logger.error(f"Sync Manager測試失敗: {str(e)}")
    
    logger.info("=== 測試完成 ===")

if __name__ == "__main__":
    test_get_tsa_flights()