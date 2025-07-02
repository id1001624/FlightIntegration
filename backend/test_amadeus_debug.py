import asyncio
import sys
import json
sys.path.append('.')

from app import create_app
from app.services.amadeus_service import amadeus_service

async def test_different_airports():
    """測試不同的機場組合"""
    print("=== 測試不同機場組合 ===")
    
    # Amadeus Test API 通常支持的機場組合
    test_routes = [
        ('LHR', 'JFK', '2025-03-15'),  # 倫敦 - 紐約
        ('SYD', 'BKK', '2025-03-15'),  # 雪梨 - 曼谷  
        ('MAD', 'BCN', '2025-03-15'),  # 馬德里 - 巴塞隆納
        ('TPE', 'BKK', '2025-03-15'),  # 台北 - 曼谷
        ('HKG', 'NRT', '2025-03-15'),  # 香港 - 東京
        ('TPE', 'HKG', '2025-03-15'),  # 台北 - 香港
    ]
    
    for origin, destination, date in test_routes:
        print(f"\n--- 測試路線: {origin} -> {destination} on {date} ---")
        try:
            result = await amadeus_service.search_flight_offers(
                origin=origin,
                destination=destination,
                departure_date=date,
                adults=1,
                max_results=5
            )
            
            if isinstance(result, dict):
                if 'error' in result:
                    print(f"❌ {origin}->{destination}: API錯誤 - {result['error']}")
                    if 'details' in result:
                        print(f"   詳情: {result['details']}")
                elif 'data' in result:
                    print(f"✅ {origin}->{destination}: 成功獲取 {len(result['data'])} 個航班")
                else:
                    print(f"⚠️ {origin}->{destination}: 意外響應格式")
            else:
                print(f"⚠️ {origin}->{destination}: API返回 {type(result)}")
                
        except Exception as e:
            print(f"❌ {origin}->{destination}: 測試失敗 - {str(e)}")
            
        # 避免API調用過於頻繁
        await asyncio.sleep(1)

async def test_api_error_details():
    """獲取API錯誤的詳細信息"""
    print("\n=== 獲取 TPE->NRT 錯誤詳情 ===")
    
    try:
        # 嘗試獲取原始錯誤響應
        session = await amadeus_service._get_session()
        token = await amadeus_service._get_access_token()
        
        url = f"{amadeus_service.base_url}/v2/shopping/flight-offers"
        headers = {"Authorization": f"Bearer {token}"}
        params = {
            "originLocationCode": 'TPE',
            "destinationLocationCode": 'NRT',
            "departureDate": '2025-02-15',
            "adults": 1,
            "nonStop": "false",
            "currencyCode": "TWD",
            "max": 10
        }
        
        async with session.get(url, headers=headers, params=params) as response:
            print(f"響應狀態: {response.status}")
            print(f"響應頭: {dict(response.headers)}")
            
            try:
                error_data = await response.json()
                print(f"錯誤響應內容: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except Exception as e:
                error_text = await response.text()
                print(f"錯誤響應文本: {error_text}")
                
    except Exception as e:
        print(f"獲取錯誤詳情失敗: {str(e)}")

async def test_supported_destinations():
    """測試 TPE 支持的目的地"""
    print("\n=== 測試 TPE 支持的目的地 ===")
    
    try:
        result = await amadeus_service.search_flight_destinations('TPE')
        
        if isinstance(result, dict):
            if 'error' in result:
                print(f"❌ 查詢 TPE 目的地失敗: {result['error']}")
                if 'details' in result:
                    print(f"   詳情: {result['details']}")
            elif 'data' in result:
                destinations = result['data']
                print(f"✅ TPE 支持 {len(destinations)} 個目的地")
                
                # 顯示前10個目的地
                for i, dest in enumerate(destinations[:10]):
                    code = dest.get('destination', dest.get('iataCode', 'N/A'))
                    price = dest.get('price', {}).get('total', 'N/A')
                    print(f"   {i+1}. {code} - 價格: {price}")
                    
                # 檢查是否包含 NRT
                nrt_found = any(dest.get('destination') == 'NRT' or dest.get('iataCode') == 'NRT' 
                               for dest in destinations)
                print(f"   包含 NRT: {'是' if nrt_found else '否'}")
            else:
                print(f"⚠️ 意外響應格式: {result}")
        else:
            print(f"⚠️ API返回 {type(result)}")
            
    except Exception as e:
        print(f"查詢目的地失敗: {str(e)}")

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
    
    with app.app_context():
        try:
            # 測試1: 獲取TPE->NRT錯誤詳情
            await test_api_error_details()
            
            # 測試2: 查詢TPE支持的目的地
            await test_supported_destinations()
            
            # 測試3: 嘗試不同的機場組合
            await test_different_airports()
            
        finally:
            await cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 