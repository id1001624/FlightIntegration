#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
測試 Amadeus API 艙等功能
驗證不同艙等是否返回不同的價格
"""
import asyncio
import aiohttp
import os
import json
from datetime import datetime, timedelta

class AmadeusAPITester:
    """Amadeus API 艙等測試器"""
    
    def __init__(self):
        self.api_key = os.getenv('AMADEUS_API_KEY')
        self.api_secret = os.getenv('AMADEUS_API_SECRET')
        self.session = None
        self.access_token = None
        
        # 要測試的艙等
        self.cabin_classes = ['ECONOMY', 'PREMIUM_ECONOMY', 'BUSINESS', 'FIRST']
        
    async def get_access_token(self):
        """獲取訪問令牌"""
        url = "https://test.api.amadeus.com/v1/security/oauth2/token"
        
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.api_key,
            'client_secret': self.api_secret
        }
        
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        
        async with self.session.post(url, data=data, headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                self.access_token = result['access_token']
                print("✅ 成功獲取訪問令牌")
                return True
            else:
                print(f"❌ 獲取訪問令牌失敗：{response.status}")
                error_text = await response.text()
                print(f"錯誤詳情：{error_text}")
                return False
    
    async def test_cabin_class(self, travel_class: str):
        """測試特定艙等"""
        url = "https://test.api.amadeus.com/v2/shopping/flight-offers"
        
        # 使用明天的日期
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        params = {
            'originLocationCode': 'TPE',
            'destinationLocationCode': 'NRT',  # 台北到東京
            'departureDate': tomorrow,
            'adults': 1,
            'travelClass': travel_class,
            'max': 10,  # 限制結果數量以便觀察
            'currencyCode': 'TWD'
        }
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            async with self.session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    offers = result.get('data', [])
                    
                    if offers:
                        prices = [float(offer['price']['total']) for offer in offers if 'price' in offer]
                        min_price = min(prices) if prices else None
                        max_price = max(prices) if prices else None
                        avg_price = sum(prices) / len(prices) if prices else None
                        
                        print(f"🛫 {travel_class}:")
                        print(f"   結果數量: {len(offers)}")
                        print(f"   價格範圍: {min_price:.0f} - {max_price:.0f} TWD")
                        print(f"   平均價格: {avg_price:.0f} TWD")
                        
                        return {
                            'class': travel_class,
                            'count': len(offers),
                            'min_price': min_price,
                            'max_price': max_price,
                            'avg_price': avg_price,
                            'offers': offers[:3]  # 只保留前3個作為樣本
                        }
                    else:
                        print(f"❌ {travel_class}: 沒有找到航班")
                        return {'class': travel_class, 'count': 0}
                        
                else:
                    print(f"❌ {travel_class}: API 調用失敗 {response.status}")
                    error_text = await response.text()
                    print(f"   錯誤詳情：{error_text}")
                    return {'class': travel_class, 'error': response.status}
                    
        except Exception as e:
            print(f"❌ {travel_class}: 異常 {e}")
            return {'class': travel_class, 'exception': str(e)}
    
    async def run_test(self):
        """運行完整測試"""
        if not self.api_key or not self.api_secret:
            print("❌ 請設置環境變量：")
            print("   AMADEUS_API_KEY=your_api_key")
            print("   AMADEUS_API_SECRET=your_api_secret")
            return
        
        self.session = aiohttp.ClientSession()
        
        try:
            print("🧪 開始測試 Amadeus API 艙等功能")
            print("=" * 50)
            
            # 獲取令牌
            if not await self.get_access_token():
                return
            
            print("\n📊 測試航線：台北 (TPE) → 東京 (NRT)")
            print("=" * 50)
            
            # 測試每個艙等
            results = []
            for cabin_class in self.cabin_classes:
                result = await self.test_cabin_class(cabin_class)
                results.append(result)
                await asyncio.sleep(1)  # 避免API限制
            
            # 分析結果
            print("\n📈 結果分析")
            print("=" * 50)
            
            valid_results = [r for r in results if 'min_price' in r and r['min_price']]
            
            if len(valid_results) > 1:
                prices = [r['min_price'] for r in valid_results]
                if len(set(prices)) > 1:
                    print("✅ 不同艙等返回不同價格 - API 功能正常！")
                else:
                    print("⚠️  所有艙等返回相同價格 - 可能是測試數據限制")
                
                print("\n艙等價格比較：")
                for result in valid_results:
                    print(f"   {result['class']}: {result['min_price']:.0f} TWD")
            else:
                print("❌ 測試失敗：沒有足夠的有效結果進行比較")
            
            # 保存詳細結果到文件
            with open('amadeus_test_results.json', 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"\n💾 詳細結果已保存到 amadeus_test_results.json")
            
        finally:
            await self.session.close()

async def main():
    """主函數"""
    tester = AmadeusAPITester()
    await tester.run_test()

if __name__ == "__main__":
    print("🚀 Amadeus API 艙等功能測試")
    print("請確保已設置正確的 API 憑證")
    print()
    
    asyncio.run(main()) 