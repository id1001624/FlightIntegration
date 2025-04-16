#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
測試 FlightStatsApiClient 的 get_flights 方法
"""
import os
import sys
import json
import logging
from datetime import datetime
from dotenv import load_dotenv

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backend/logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('flightstats_test')

# 確定 .env 檔案的路徑
script_dir = os.path.dirname(__file__)
backend_dir = os.path.abspath(os.path.join(script_dir, '..'))  # backend 目錄
dotenv_path = os.path.join(backend_dir, '.env')  # backend/.env 路徑

print(f"嘗試從 {dotenv_path} 加載 .env 文件...")
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)
    print(".env 文件加載成功")
else:
    print(f"警告: 未找到 .env 文件於 {dotenv_path}, 請確保文件存在於專案根目錄")

# 添加應用路徑
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 導入要測試的模組
try:
    from app.clients.flightstats_client import FlightStatsApiClient
    print("成功導入 FlightStatsApiClient")
except ImportError as e:
    logger.error(f"無法導入 FlightStatsApiClient: {e}")
    sys.exit(1)

# 添加 UUID 轉換函數
def serialize_for_json(flight_data):
    """
    將航班數據中的 UUID 轉換為字符串，以便進行 JSON 序列化
    """
    serialized_data = {}
    for key, value in flight_data.items():
        # 檢查值是否為 UUID 類型
        if str(type(value)).find('uuid.UUID') != -1:
            serialized_data[key] = str(value)
        else:
            serialized_data[key] = value
    return serialized_data

def main():
    """測試 FlightStatsApiClient 的 get_flights 方法"""
    try:
        # 初始化客戶端
        client = FlightStatsApiClient()
        logger.info("成功初始化 FlightStatsApiClient")
        
        # 設定測試參數
        dep_airport = 'TPE'
        arr_airport = 'HKG'
        date = '2025-04-16'
        
        logger.info(f"開始測試 get_flights 方法 ({dep_airport}->{arr_airport}, {date})")
        
        # 調用 get_flights 方法
        flights = client.get_flights(dep_airport, arr_airport, date)
        
        if not flights:
            logger.warning(f"未找到從 {dep_airport} 到 {arr_airport} 在 {date} 的航班")
            return
        
        logger.info(f"成功獲取 {len(flights)} 個航班")
        
        # 限制只輸出 5 筆資料
        max_flights = min(5, len(flights))
        
        for i in range(max_flights):
            flight = flights[i]
            # 將 UUID 轉換為字符串以便進行 JSON 序列化
            serialized_flight = serialize_for_json(flight)
            logger.info(f"航班 {i+1}: {json.dumps(serialized_flight, ensure_ascii=False, indent=2)}")
            
            # 驗證關鍵字段存在
            if 'flight_number' not in flight:
                logger.error(f"航班 {i+1} 缺少 flight_number 字段")
            if 'airline_id' not in flight:
                logger.error(f"航班 {i+1} 缺少 airline_id 字段")
            if 'departure_airport_id' not in flight:
                logger.error(f"航班 {i+1} 缺少 departure_airport_id 字段")
            if 'arrival_airport_id' not in flight:
                logger.error(f"航班 {i+1} 缺少 arrival_airport_id 字段")
            if 'scheduled_departure' not in flight:
                logger.error(f"航班 {i+1} 缺少 scheduled_departure 字段")
            if 'scheduled_arrival' not in flight:
                logger.error(f"航班 {i+1} 缺少 scheduled_arrival 字段")
            
        logger.info("測試完成")
        
    except Exception as e:
        logger.error(f"測試過程中發生錯誤: {e}", exc_info=True)

if __name__ == "__main__":
    main() 