import asyncio
import sys
import os
sys.path.append('.')

# 設置Flask應用上下文
from app import create_app
from app.services.realtime_price_service import realtime_price_service
from app.services.amadeus_service import amadeus_service

async def test_amadeus_api_directly():
    """直接測試 Amadeus API 調用"""
    print("=== 直接測試 Amadeus API ===")
    
    try:
        result = await amadeus_service.search_flight_offers(
            origin='TPE',
            destination='NRT',
            departure_date='2025-02-15',  # 使用更遠的未來日期
            adults=1,
            max_results=10
        )
        
        print(f"API 調用結果類型: {type(result)}")
        
        if isinstance(result, dict):
            if 'error' in result:
                print(f"API 錯誤: {result['error']}")
                print(f"錯誤詳情: {result.get('details', 'N/A')}")
            elif 'data' in result:
                print(f"成功獲取 {len(result['data'])} 個航班報價")
                if result['data']:
                    print(f"第一個報價ID: {result['data'][0].get('id', 'N/A')}")
            else:
                print(f"意外的API響應格式: {result}")
        else:
            print(f"API 返回: {result}")
            
    except Exception as e:
        print(f"直接API測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()

async def test_realtime_price_service():
    """測試實時價格服務基本功能"""
    print("\n=== 測試實時價格服務 ===")
    
    try:
        result = await realtime_price_service.search_flight_prices(
            origin='TPE',
            destination='NRT', 
            departure_date='2025-02-15',  # 使用更遠的未來日期
            cabin_preference='ECONOMY',
            use_cache=False  # 先不使用緩存進行測試
        )
        
        print('=== 實時價格服務測試結果 ===')
        print(f'結果類型: {type(result)}')
        
        if isinstance(result, dict):
            print(f'查詢成功: {result.get("success", False)}')
            
            data = result.get("data", {})
            
            if isinstance(data, list):
                flights = data
            else:
                flights = data.get("flights", []) if isinstance(data, dict) else []
            
            print(f'結果數量: {len(flights)}')
            print(f'查詢來源: {result.get("source", "未知")}')
            
            if "message" in result:
                print(f'訊息: {result["message"]}')
                
            if "error" in result:
                print(f'錯誤: {result["error"]}')
                
            # 顯示第一個航班的詳細信息
            if flights:
                first_flight = flights[0]
                print("\n=== 第一個航班詳細信息 ===")
                print(f'航班數據: {first_flight}')
        else:
            print(f'結果: {result}')
            
    except Exception as e:
        print(f'測試失敗: {str(e)}')
        import traceback
        traceback.print_exc()

async def test_cache_mechanism():
    """測試緩存機制"""
    print("\n=== 測試緩存機制 ===")
    
    try:
        # 第一次查詢（會調用API）
        print("第一次查詢（應該調用API）...")
        result1 = await realtime_price_service.search_flight_prices(
            origin='TPE',
            destination='NRT', 
            departure_date='2025-02-15',
            cabin_preference='ECONOMY',
            use_cache=True
        )
        
        print(f'第一次查詢來源: {result1.get("source", "未知")}')
        
        # 稍等一下
        await asyncio.sleep(2)
        
        # 第二次查詢（應該使用緩存）
        print("第二次查詢（應該使用緩存）...")
        result2 = await realtime_price_service.search_flight_prices(
            origin='TPE',
            destination='NRT', 
            departure_date='2025-02-15',
            cabin_preference='ECONOMY',
            use_cache=True
        )
        
        print(f'第二次查詢來源: {result2.get("source", "未知")}')
        
        if result1.get("source") == "amadeus_api" and result2.get("source") == "cache":
            print("✅ 緩存機制工作正常！")
        else:
            print("⚠️ 緩存機制可能有問題")
            
    except Exception as e:
        print(f'緩存測試失敗: {str(e)}')

async def cleanup():
    """清理資源"""
    try:
        await amadeus_service.close_session()
        print("已關閉 Amadeus API session")
    except Exception as e:
        print(f"清理資源時發生錯誤: {e}")

async def main():
    """主測試函數"""
    app = create_app('development')
    
    with app.app_context():
        try:
            # 測試1: 直接API調用
            await test_amadeus_api_directly()
            
            # 測試2: 實時價格服務
            await test_realtime_price_service()
            
            # 測試3: 緩存機制（只有當前面測試成功時）
            # await test_cache_mechanism()
            
        finally:
            # 清理資源
            await cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 