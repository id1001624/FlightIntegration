#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
偵錯腳本: 測試航班API
"""
import asyncio
import json
import requests
from pprint import pprint

API_BASE = "http://127.0.0.1:5000/api"

def test_search_api():
    """測試航班搜索API"""
    print("開始測試航班搜索API...")
    
    # 構建請求URL
    url = f"{API_BASE}/flights/search"
    params = {
        "departure": "TPE",
        "arrival": "DPS",
        "date": "2025-04-07",
        "class_type": "經濟"
    }
    
    # 發送請求
    try:
        response = requests.get(url, params=params)
        print(f"狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n搜索結果:")
            print(f"總航班數: {data['meta']['outbound_count']}")
            
            if data['outbound']:
                print("\n找到的航班:")
                for flight in data['outbound']:
                    print(f"航班號: {flight['flight_number']}")
                    print(f"航空公司: {flight['airline']['name']}")
                    print(f"出發時間: {flight['departure']['time']}")
                    print(f"到達時間: {flight['arrival']['time']}")
                    print(f"價格: {flight['price']['amount']} {flight['price']['currency']}")
                    print(f"艙位: {flight['price']['cabin_class']}")
                    print(f"可用座位: {flight['price']['available_seats']}")
                    print("------------------------------")
            else:
                print("未找到符合條件的航班")
                print("\n篩選條件:")
                print(json.dumps(data['filters'], indent=2, ensure_ascii=False))
        else:
            print(f"請求失敗: {response.text}")
    
    except Exception as e:
        print(f"測試過程中發生錯誤: {str(e)}")

if __name__ == "__main__":
    test_search_api() 