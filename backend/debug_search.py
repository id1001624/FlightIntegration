#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
偵錯腳本: 測試航班搜索功能
"""
import asyncio
import os
import logging
from dotenv import load_dotenv
from app.services.search_service import SearchService
from app.database.db import get_db

# 設置日誌級別
logging.basicConfig(level=logging.INFO)

# 載入環境變數
load_dotenv()

async def test_search():
    """測試航班搜索功能"""
    print("開始查詢flights表的所有數據...")
    
    # 嘗試直接從數據庫搜索
    db = await get_db()
    try:
        # 查詢所有航班數據
        query = """
        SELECT 
            f.flight_id, 
            f.flight_number, 
            f.scheduled_departure, 
            f.scheduled_arrival, 
            f.status,
            f.departure_airport_id,
            f.arrival_airport_id,
            f.airline_id
        FROM 
            flights f
        LIMIT 20
        """
        
        flights = await db.fetch(query)
        print(f"找到 {len(flights)} 個航班 (僅顯示前20條):")
        for flight in flights:
            print(f"航班ID: {flight['flight_id']}")
            print(f"航班號: {flight['flight_number']}")
            print(f"出發地: {flight['departure_airport_id']} -> 目的地: {flight['arrival_airport_id']}")
            print(f"起飛時間: {flight['scheduled_departure']}")
            print(f"狀態: {flight['status']}")
            print("------------------------------")
        
        # 查詢總航班數
        count_query = "SELECT COUNT(*) FROM flights"
        count_result = await db.fetchrow(count_query)
        total_flights = count_result[0]
        print(f"flights表中總共有 {total_flights} 條記錄")
        
        # 查詢不同機場的航班數量
        airport_query = """
        SELECT 
            departure_airport_id, 
            COUNT(*) as flight_count
        FROM 
            flights
        GROUP BY 
            departure_airport_id
        ORDER BY 
            flight_count DESC
        LIMIT 10
        """
        
        airport_stats = await db.fetch(airport_query)
        print("\n各主要出發機場的航班數量:")
        for stat in airport_stats:
            print(f"機場: {stat['departure_airport_id']}, 航班數: {stat['flight_count']}")
        
        # 查詢不同航空公司的航班數量
        airline_query = """
        SELECT 
            airline_id, 
            COUNT(*) as flight_count
        FROM 
            flights
        GROUP BY 
            airline_id
        ORDER BY 
            flight_count DESC
        LIMIT 10
        """
        
        airline_stats = await db.fetch(airline_query)
        print("\n各主要航空公司的航班數量:")
        for stat in airline_stats:
            print(f"航空公司: {stat['airline_id']}, 航班數: {stat['flight_count']}")
        
        # 查詢特定航線的航班
        print("\n查詢台北(TPE)到峇里島(DPS)的航班:")
        specific_query = """
        SELECT 
            flight_id, 
            flight_number, 
            scheduled_departure, 
            status
        FROM 
            flights
        WHERE 
            departure_airport_id = 'TPE'
            AND arrival_airport_id = 'DPS'
            AND DATE(scheduled_departure) = '2025-04-07'
        """
        
        specific_flights = await db.fetch(specific_query)
        if specific_flights:
            for flight in specific_flights:
                print(f"航班號: {flight['flight_number']}")
                print(f"起飛時間: {flight['scheduled_departure']}")
                print(f"狀態: {flight['status']}")
                print("------------------------------")
        else:
            print("未找到符合條件的航班")
    
    except Exception as e:
        print(f"查詢時發生錯誤: {str(e)}")
    finally:
        # 關閉數據庫連接
        from app.database.db import release_db
        await release_db(db)

if __name__ == "__main__":
    asyncio.run(test_search())