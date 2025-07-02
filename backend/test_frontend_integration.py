#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
前後端整合測試
測試前端調用的API端點是否正確工作
"""
import asyncio
import sys
import aiohttp
from datetime import datetime, timedelta
sys.path.append('.')

from app import create_app

def get_future_date(days_ahead=10):
    """獲取未來的日期"""
    future_date = datetime.now() + timedelta(days=days_ahead)
    return future_date.strftime('%Y-%m-%d')

async def test_frontend_api_endpoint():
    """測試前端調用的 /api/flights/search 端點"""
    print("=== 測試前端API端點整合 ===\n")
    
    # 測試參數 (與前端調用相同的格式)
    future_date = get_future_date(15)
    test_params = {
        'departure_code': 'TPE',
        'arrival_code': 'NRT', 
        'date_str': future_date,
        'passengers': 1,
        'max_results': 10
    }
    
    print(f"測試參數: {test_params}")
    print(f"模擬前端調用: GET /api/flights/search")
    print("-" * 50)
    
    # 創建 Flask 應用上下文
    app = create_app()
    
    with app.app_context():
        # 導入並測試航班控制器
        from app.controllers.flight_controller import search_flights
        from unittest.mock import MagicMock
        
        # 模擬 request.args
        mock_request = MagicMock()
        mock_request.args = test_params
        
        # 替換 request 對象
        import app.controllers.flight_controller as fc
        original_request = fc.request
        fc.request = mock_request
        
        try:
            # 調用搜索方法
            result = await search_flights()
            
            print("API 調用結果:")
            print(f"狀態碼: {result[1] if isinstance(result, tuple) else '200'}")
            
            if isinstance(result, tuple):
                response_data, status_code = result
            else:
                response_data = result
                status_code = 200
            
            print(f"響應類型: {type(response_data)}")
            
            if isinstance(response_data, dict):
                print(f"成功: {response_data.get('success', 'N/A')}")
                print(f"訊息: {response_data.get('message', 'N/A')}")
                
                data = response_data.get('data', [])
                print(f"航班數量: {len(data) if isinstance(data, list) else 'N/A'}")
                
                if isinstance(data, list) and data:
                    print(f"第一個航班範例: {data[0] if data else 'N/A'}")
            
        except Exception as e:
            print(f"測試過程中發生錯誤: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # 恢復原始 request 對象
            fc.request = original_request

async def test_cache_behavior():
    """測試緩存行為"""
    print("\n=== 測試緩存行為 ===\n")
    
    # 創建HTTP客戶端測試實際的HTTP端點
    base_url = "http://localhost:5000"
    future_date = get_future_date(15)
    
    params = {
        'departure_code': 'TPE',
        'arrival_code': 'HKG',
        'date_str': future_date,
        'passengers': 1,
        'max_results': 5
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            print("第一次調用 (應該從 Amadeus API 獲取):")
            async with session.get(f"{base_url}/api/flights/search", params=params) as response:
                if response.status == 200:
                    result1 = await response.json()
                    print(f"成功: {result1.get('success')}")
                    print(f"數據來源: 預期為 amadeus_api")
                    print(f"航班數量: {len(result1.get('data', []))}")
                else:
                    print(f"HTTP錯誤: {response.status}")
            
            print("\n第二次調用 (應該從緩存獲取):")
            async with session.get(f"{base_url}/api/flights/search", params=params) as response:
                if response.status == 200:
                    result2 = await response.json()
                    print(f"成功: {result2.get('success')}")
                    print(f"數據來源: 預期為 cache")
                    print(f"航班數量: {len(result2.get('data', []))}")
                else:
                    print(f"HTTP錯誤: {response.status}")
                    
    except aiohttp.ClientConnectorError:
        print("⚠️ 無法連接到後端服務 (http://localhost:5000)")
        print("請確保後端服務正在運行: python run.py")
    except Exception as e:
        print(f"HTTP測試過程中發生錯誤: {e}")

async def main():
    """主測試函數"""
    print("🚀 開始前後端整合測試\n")
    
    # 測試1: 直接API調用
    await test_frontend_api_endpoint()
    
    # 測試2: HTTP緩存行為
    await test_cache_behavior()
    
    print("\n✅ 整合測試完成!")
    print("\n📝 前端測試說明:")
    print("1. 打開瀏覽器訪問 http://localhost:3000 (或相應前端地址)")
    print("2. 執行航班搜索: TPE -> NRT, 日期: 未來15天")
    print("3. 觀察 Network 標籤中的API調用: 應該調用 /api/flights/search")
    print("4. 重複相同搜索測試緩存功能")

if __name__ == "__main__":
    asyncio.run(main()) 