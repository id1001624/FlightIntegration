import asyncio
import sys
sys.path.append('.')
from app.services.realtime_price_service import realtime_price_service

async def test_realtime_price_service():
    """測試實時價格服務基本功能"""
    print("=== 開始測試實時價格服務 ===")
    
    try:
        result = await realtime_price_service.search_flight_prices(
            origin='TPE',
            destination='NRT', 
            departure_date='2025-01-15',
            cabin_preference='ECONOMY'
        )
        
        print('=== 實時價格服務測試結果 ===')
        print(f'結果類型: {type(result)}')
        
        if isinstance(result, dict):
            print(f'查詢成功: {result.get("success", False)}')
            
            data = result.get("data", {})
            flights = data.get("flights", [])
            
            print(f'結果數量: {len(flights)}')
            print(f'總價格選項: {data.get("total_results", 0)}')
            print(f'查詢來源: {data.get("source", "未知")}')
            
            if "message" in result:
                print(f'訊息: {result["message"]}')
                
            # 顯示第一個航班的詳細信息
            if flights:
                first_flight = flights[0]
                print("\n=== 第一個航班詳細信息 ===")
                print(f'航班號: {first_flight.get("flight_number", "N/A")}')
                print(f'出發時間: {first_flight.get("departure_time", "N/A")}')
                print(f'到達時間: {first_flight.get("arrival_time", "N/A")}')
                print(f'航空公司: {first_flight.get("airline_name", "N/A")}')
                print(f'經濟艙價格: {first_flight.get("economy_price", "N/A")}')
                print(f'商務艙價格: {first_flight.get("business_price", "N/A")}')
        else:
            print(f'結果: {result}')
            
    except Exception as e:
        print(f'測試失敗: {str(e)}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_realtime_price_service()) 