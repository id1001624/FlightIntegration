import asyncio
import sys
from datetime import datetime, timedelta
sys.path.append('.')

from app import create_app
from app.services.realtime_price_service import realtime_price_service
from app.services.amadeus_service import amadeus_service

def get_future_date(days_ahead=10):
    """獲取未來的日期"""
    future_date = datetime.now() + timedelta(days=days_ahead)
    return future_date.strftime('%Y-%m-%d')

async def test_amadeus_api_with_correct_date():
    """使用正確日期測試 Amadeus API"""
    print("=== 使用正確日期測試 Amadeus API ===")
    
    future_date = get_future_date(15)  # 15天後
    print(f"使用日期: {future_date}")
    
    try:
        result = await amadeus_service.search_flight_offers(
            origin='TPE',
            destination='NRT',
            departure_date=future_date,
            adults=1,
            max_results=10
        )
        
        print(f"API 調用結果類型: {type(result)}")
        
        if isinstance(result, dict):
            if 'error' in result:
                print(f"❌ API錯誤: {result['error']}")
                if 'details' in result:
                    print(f"   詳情: {result['details']}")
            elif 'data' in result:
                offers = result['data']
                print(f"✅ 成功獲取 {len(offers)} 個航班報價")
                
                if offers:
                    print("\n=== 第一個航班報價詳情 ===")
                    first_offer = offers[0]
                    print(f"報價ID: {first_offer.get('id', 'N/A')}")
                    
                    # 顯示行程詳情
                    itineraries = first_offer.get('itineraries', [])
                    if itineraries:
                        first_itinerary = itineraries[0]
                        segments = first_itinerary.get('segments', [])
                        if segments:
                            first_segment = segments[0]
                            print(f"航班號: {first_segment.get('carrierCode', '')}{first_segment.get('number', '')}")
                            print(f"出發: {first_segment.get('departure', {}).get('iataCode', '')}")
                            print(f"到達: {first_segment.get('arrival', {}).get('iataCode', '')}")
                    
                    # 顯示價格
                    price = first_offer.get('price', {})
                    print(f"總價: {price.get('total', 'N/A')} {price.get('currency', '')}")
                    
            else:
                print(f"⚠️ 意外的API響應格式: {result}")
        else:
            print(f"⚠️ API 返回: {result}")
            
    except Exception as e:
        print(f"❌ 直接API測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()

async def test_realtime_price_service_with_correct_date():
    """使用正確日期測試實時價格服務"""
    print("\n=== 使用正確日期測試實時價格服務 ===")
    
    future_date = get_future_date(15)  # 15天後
    print(f"使用日期: {future_date}")
    
    try:
        # 測試 1: 不使用緩存
        print("\n--- 測試 1: 不使用緩存 ---")
        result1 = await realtime_price_service.search_flight_prices(
            origin='TPE',
            destination='NRT', 
            departure_date=future_date,
            cabin_preference='ECONOMY',
            use_cache=False
        )
        
        print(f'查詢成功: {result1.get("success", False)}')
        print(f'查詢來源: {result1.get("source", "未知")}')
        print(f'訊息: {result1.get("message", "N/A")}')
        
        if result1.get("success"):
            data = result1.get("data", [])
            print(f'結果數量: {len(data)}')
            
            if data:
                print(f'第一個航班: {data[0].get("flight_number", "N/A") if isinstance(data[0], dict) else "數據格式檢查"}')
        else:
            print(f'錯誤: {result1.get("error", "無錯誤信息")}')
        
        # 測試 2: 使用緩存
        if result1.get("success"):
            print("\n--- 測試 2: 使用緩存 ---")
            result2 = await realtime_price_service.search_flight_prices(
                origin='TPE',
                destination='NRT', 
                departure_date=future_date,
                cabin_preference='ECONOMY',
                use_cache=True
            )
            
            print(f'第二次查詢來源: {result2.get("source", "未知")}')
            
            # 等待一下再測試緩存
            await asyncio.sleep(2)
            
            result3 = await realtime_price_service.search_flight_prices(
                origin='TPE',
                destination='NRT', 
                departure_date=future_date,
                cabin_preference='ECONOMY',
                use_cache=True
            )
            
            print(f'第三次查詢來源: {result3.get("source", "未知")}')
            
            if result2.get("source") == "amadeus_api" and result3.get("source") == "cache":
                print("✅ 緩存機制工作正常！")
            elif result3.get("source") == "cache":
                print("✅ 緩存機制工作正常！（可能已有緩存）")
            else:
                print("⚠️ 緩存機制可能有問題")
                print(f"   預期: amadeus_api -> cache")
                print(f"   實際: {result2.get('source')} -> {result3.get('source')}")
                
    except Exception as e:
        print(f'❌ 實時價格服務測試失敗: {str(e)}')
        import traceback
        traceback.print_exc()

async def test_different_routes():
    """測試不同路線"""
    print("\n=== 測試不同路線 ===")
    
    future_date = get_future_date(20)  # 20天後
    
    test_routes = [
        ('TPE', 'HKG', '台北 -> 香港'),
        ('TPE', 'BKK', '台北 -> 曼谷'),
        ('HKG', 'NRT', '香港 -> 東京'),
    ]
    
    for origin, destination, description in test_routes:
        print(f"\n--- 測試路線: {description} ({origin}->{destination}) ---")
        
        try:
            result = await amadeus_service.search_flight_offers(
                origin=origin,
                destination=destination,
                departure_date=future_date,
                adults=1,
                max_results=5
            )
            
            if isinstance(result, dict) and 'data' in result:
                print(f"✅ {description}: 成功獲取 {len(result['data'])} 個航班")
            elif isinstance(result, dict) and 'error' in result:
                print(f"❌ {description}: {result['error']}")
            else:
                print(f"⚠️ {description}: 意外響應格式")
                
        except Exception as e:
            print(f"❌ {description}: 測試失敗 - {str(e)}")
            
        await asyncio.sleep(1)  # 避免API調用過於頻繁

async def cleanup():
    """清理資源"""
    try:
        await amadeus_service.close_session()
        print("\n已關閉 Amadeus API session")
    except Exception as e:
        print(f"清理資源時發生錯誤: {e}")

async def main():
    """主測試函數"""
    app = create_app('development')
    
    print(f"測試開始時間: {datetime.now()}")
    
    with app.app_context():
        try:
            # 測試1: 直接API調用（使用正確日期）
            await test_amadeus_api_with_correct_date()
            
            # 測試2: 實時價格服務（使用正確日期）
            await test_realtime_price_service_with_correct_date()
            
            # 測試3: 不同路線測試
            await test_different_routes()
            
        finally:
            await cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 