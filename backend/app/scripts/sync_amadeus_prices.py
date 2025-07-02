#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Amadeus 真實票價數據同步腳本
從 Amadeus Flight Offers Search API 獲取不同艙等的真實票價
"""
import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import aiohttp

# --- Logger 配置 ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('amadeus_prices_sync')

# --- 導入 ---
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from app import create_app
from app.models import TicketPrice, Flight
from app import db

class AmadeusPriceSync:
    """Amadeus 票價同步器"""
    
    def __init__(self):
        self.amadeus_api_key = os.getenv('AMADEUS_API_KEY')
        self.amadeus_api_secret = os.getenv('AMADEUS_API_SECRET')
        self.session = None
        self.access_token = None
        
        # 支持的艙等
        self.cabin_classes = ['ECONOMY', 'PREMIUM_ECONOMY', 'BUSINESS', 'FIRST']
        
        # 台灣國際機場
        self.taiwan_airports = ['TPE', 'TSA', 'KHH', 'RMQ', 'HUN']
        
    async def get_access_token(self):
        """獲取 Amadeus API 訪問令牌"""
        url = "https://test.api.amadeus.com/v1/security/oauth2/token"
        
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.amadeus_api_key,
            'client_secret': self.amadeus_api_secret
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        async with self.session.post(url, data=data, headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                self.access_token = result['access_token']
                logger.info("成功獲取 Amadeus API 訪問令牌")
                return True
            else:
                logger.error(f"獲取訪問令牌失敗：{response.status}")
                return False
    
    async def search_flight_offers(self, origin: str, destination: str, 
                                 departure_date: str, travel_class: str) -> List[Dict]:
        """
        調用 Amadeus Flight Offers Search API
        """
        url = "https://test.api.amadeus.com/v2/shopping/flight-offers"
        
        params = {
            'originLocationCode': origin,
            'destinationLocationCode': destination,
            'departureDate': departure_date,
            'adults': 1,
            'travelClass': travel_class,
            'max': 250,  # 最大結果數
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
                    return result.get('data', [])
                else:
                    logger.warning(f"API 調用失敗 {origin}->{destination} {travel_class}: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"API 調用異常 {origin}->{destination} {travel_class}: {e}")
            return []
    
    async def sync_prices_for_route(self, origin: str, destination: str, departure_date: str):
        """
        為特定航線的所有艙等同步票價
        """
        logger.info(f"開始同步航線 {origin} -> {destination} 於 {departure_date}")
        
        price_data = {}
        
        # 為每個艙等調用 API
        for cabin_class in self.cabin_classes:
            logger.info(f"  獲取 {cabin_class} 艙等價格...")
            offers = await self.search_flight_offers(origin, destination, departure_date, cabin_class)
            
            if offers:
                # 找到最低價格
                min_price = min(float(offer['price']['total']) for offer in offers if 'price' in offer)
                price_data[cabin_class.lower() + '_price'] = min_price
                logger.info(f"    {cabin_class}: {min_price} TWD ({len(offers)} 個選項)")
            else:
                logger.warning(f"    {cabin_class}: 無可用價格")
                
            # 避免API限制，添加延遲
            await asyncio.sleep(0.5)
        
        return price_data
    
    async def sync_all_routes(self):
        """
        同步所有台灣出發的國際航線票價
        """
        app = create_app()
        
        with app.app_context():
            # 獲取明天的日期（避免今天的航班已過期）
            tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            
            # 獲取數據庫中的目的地機場
            destinations_query = """
            SELECT DISTINCT arrival_airport_id as destination 
            FROM flights 
            WHERE departure_airport_id IN ('TPE', 'TSA', 'KHH', 'RMQ', 'HUN')
            AND arrival_airport_id NOT IN ('TPE', 'TSA', 'KHH', 'RMQ', 'HUN')
            """
            
            result = db.session.execute(destinations_query)
            destinations = [row[0] for row in result.fetchall()]
            
            logger.info(f"找到 {len(destinations)} 個國際目的地")
            
            total_routes = 0
            successful_routes = 0
            
            # 為每個台灣機場和目的地組合同步價格
            for origin in self.taiwan_airports:
                for destination in destinations:
                    total_routes += 1
                    
                    try:
                        price_data = await self.sync_prices_for_route(origin, destination, tomorrow)
                        
                        if price_data:
                            # 保存到數據庫（這裡需要找到對應的航班ID）
                            await self.save_price_data(origin, destination, tomorrow, price_data)
                            successful_routes += 1
                        
                    except Exception as e:
                        logger.error(f"同步航線 {origin}->{destination} 失敗: {e}")
                    
                    # 避免API限制
                    await asyncio.sleep(1)
            
            logger.info(f"同步完成：{successful_routes}/{total_routes} 條航線成功")
    
    async def save_price_data(self, origin: str, destination: str, 
                            departure_date: str, price_data: Dict):
        """
        保存價格數據到數據庫
        """
        # 查找對應的航班
        flights = Flight.query.filter(
            Flight.departure_airport_id == origin,
            Flight.arrival_airport_id == destination,
            Flight.scheduled_departure >= departure_date
        ).all()
        
        if not flights:
            logger.warning(f"未找到對應航班 {origin}->{destination}")
            return
        
        # 為每個航班創建或更新票價記錄
        for flight in flights:
            existing_price = TicketPrice.query.filter_by(flight_id=flight.flight_id).first()
            
            if existing_price:
                # 更新現有記錄
                for field, value in price_data.items():
                    setattr(existing_price, field, value)
                existing_price.price_updated_at = datetime.utcnow()
            else:
                # 創建新記錄
                new_price = TicketPrice(
                    flight_id=flight.flight_id,
                    **price_data,
                    is_test_data=False
                )
                db.session.add(new_price)
        
        try:
            db.session.commit()
            logger.info(f"保存價格數據成功 {origin}->{destination}")
        except Exception as e:
            db.session.rollback()
            logger.error(f"保存價格數據失敗 {origin}->{destination}: {e}")
    
    async def run(self):
        """運行同步流程"""
        if not self.amadeus_api_key or not self.amadeus_api_secret:
            logger.error("請設置 AMADEUS_API_KEY 和 AMADEUS_API_SECRET 環境變量")
            return
        
        self.session = aiohttp.ClientSession()
        
        try:
            # 獲取訪問令牌
            if not await self.get_access_token():
                return
            
            # 同步所有航線價格
            await self.sync_all_routes()
            
        finally:
            await self.session.close()

async def main():
    """主函數"""
    syncer = AmadeusPriceSync()
    await syncer.run()

if __name__ == "__main__":
    asyncio.run(main()) 