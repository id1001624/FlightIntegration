#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
實時價格服務 - 整合 Amadeus API 和智能緩存
負責處理航班價格的實時查詢、緩存管理和數據適配
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple

from ..services.amadeus_service import amadeus_service
from ..adapters.amadeus_offers_adapter import adapt_flight_offers
from ..models.ticket_price import TicketPrice
from app import db

logger = logging.getLogger(__name__)

class RealtimePriceService:
    """實時價格服務類"""
    
    def __init__(self):
        self.cache_duration_hours = 4  # 默認緩存 4 小時
        self.max_api_calls_per_search = 4  # 每次搜索最多調用 4 個艙等的 API
    
    async def search_flight_prices(self, origin: str, destination: str, 
                                 departure_date: str, cabin_preference: Optional[str] = None,
                                 use_cache: bool = True) -> Dict:
        """
        搜索航班價格 - 主要入口方法
        
        Args:
            origin: 出發機場 IATA 代碼
            destination: 到達機場 IATA 代碼  
            departure_date: 出發日期 (YYYY-MM-DD)
            cabin_preference: 艙等偏好 (ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST)
            use_cache: 是否使用緩存
            
        Returns:
            Dict: 包含航班和價格信息的字典
        """
        try:
            # 1. 檢查緩存
            if use_cache:
                cached_result = await self._get_cached_prices(origin, destination, departure_date)
                if cached_result:
                    logger.info(f"使用緩存數據：{origin}->{destination} on {departure_date}")
                    return {
                        "success": True,
                        "data": cached_result,
                        "source": "cache",
                        "message": "從緩存獲取價格數據"
                    }
            
            # 2. 調用 Amadeus API 獲取實時數據
            api_result = await self._fetch_realtime_prices(origin, destination, departure_date, cabin_preference)
            
            if not api_result["success"]:
                return api_result
            
            # 3. 保存到緩存（異步，不阻塞響應）
            if use_cache and api_result["data"]:
                asyncio.create_task(self._save_to_cache(origin, destination, departure_date, api_result["data"]))
            
            return api_result
            
        except Exception as e:
            logger.error(f"搜索航班價格時發生錯誤：{e}", exc_info=True)
            return {
                "success": False,
                "message": "搜索航班價格時發生內部錯誤",
                "error": str(e)
            }
    
    async def _get_cached_prices(self, origin: str, destination: str, departure_date: str) -> Optional[List[Dict]]:
        """從緩存中獲取價格數據"""
        try:
            departure_dt = datetime.strptime(departure_date, '%Y-%m-%d')
            
            # 查詢未過期的緩存記錄
            cached_records = TicketPrice.query.filter(
                TicketPrice.origin_airport_code == origin,
                TicketPrice.destination_airport_code == destination,
                TicketPrice.departure_date >= departure_dt,
                TicketPrice.is_cached == True,
                TicketPrice.cache_expires_at > datetime.utcnow()
            ).all()
            
            if not cached_records:
                return None
            
            # 轉換為前端期望的格式
            cached_flights = []
            for record in cached_records:
                if record.amadeus_offer_id:  # 確保有 Amadeus offer ID
                    flight_data = {
                        "flight_id": record.amadeus_offer_id,
                        "id": record.amadeus_offer_id,
                        "departure": {
                            "code": record.origin_airport_code,
                            "time": record.departure_date.isoformat()
                        },
                        "arrival": {
                            "code": record.destination_airport_code
                        },
                        "price": {
                            "amount": record.total_price or record.economy_price,
                            "currency": record.currency,
                            "cabin_class": record.cabin_class
                        },
                        "cabin_class": record.cabin_class,
                        "cached": True,
                        "cache_expires": record.cache_expires_at.isoformat()
                    }
                    cached_flights.append(flight_data)
            
            return cached_flights if cached_flights else None
            
        except Exception as e:
            logger.error(f"獲取緩存價格時發生錯誤：{e}")
            return None
    
    async def _fetch_realtime_prices(self, origin: str, destination: str, 
                                   departure_date: str, cabin_preference: Optional[str] = None) -> Dict:
        """從 Amadeus API 獲取實時價格"""
        try:
            # 如果指定了艙等偏好，只查詢該艙等
            if cabin_preference:
                cabin_classes = [cabin_preference.upper()]
            else:
                # 否則查詢所有艙等
                cabin_classes = ['ECONOMY', 'PREMIUM_ECONOMY', 'BUSINESS', 'FIRST']
            
            all_offers = []
            
            # 並行查詢多個艙等（如果需要）
            if len(cabin_classes) > 1:
                tasks = []
                for cabin_class in cabin_classes:
                    # 注意：amadeus_service.search_flight_offers 沒有 travel_class 參數
                    # 只能查詢默認艙等，這裡需要修改 amadeus_service 或使用其他方法
                    task = amadeus_service.search_flight_offers(
                        origin=origin,
                        destination=destination, 
                        departure_date=departure_date,
                        max_results=50
                    )
                    tasks.append(task)
                
                # 等待所有 API 調用完成
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # 合併結果
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        logger.warning(f"艙等 {cabin_classes[i]} 查詢失敗：{result}")
                        continue
                    
                    if result and isinstance(result, dict) and 'data' in result:
                        all_offers.extend(result['data'])
            else:
                # 單一艙等查詢
                result = await amadeus_service.search_flight_offers(
                    origin=origin,
                    destination=destination,
                    departure_date=departure_date,
                    max_results=100
                )
                
                if result and isinstance(result, dict) and 'data' in result:
                    all_offers = result['data']
            
            if not all_offers:
                return {
                    "success": True,
                    "data": [],
                    "source": "amadeus_api",
                    "message": "未找到符合條件的航班"
                }
            
            # 使用現有的適配器處理數據
            adapted_offers = await adapt_flight_offers({'data': all_offers})
            
            return {
                "success": True,
                "data": adapted_offers,
                "source": "amadeus_api",
                "message": f"成功獲取 {len(adapted_offers)} 個航班報價"
            }
            
        except Exception as e:
            logger.error(f"從 Amadeus API 獲取價格時發生錯誤：{e}")
            return {
                "success": False,
                "message": "無法從 API 獲取實時價格數據",
                "error": str(e)
            }
    
    async def _save_to_cache(self, origin: str, destination: str, departure_date: str, offers: List[Dict]):
        """將搜索結果保存到緩存"""
        try:
            departure_dt = datetime.strptime(departure_date, '%Y-%m-%d')
            
            # 為每個 offer 創建或更新緩存記錄
            for offer in offers[:10]:  # 限制緩存數量
                price_data = {
                    'economy_price': None,
                    'premium_economy_price': None,
                    'business_price': None,
                    'first_price': None,
                    'total_price': None,
                    'currency': 'TWD',
                    'cabin_class': offer.get('cabin_class', 'ECONOMY')
                }
                
                # 根據艙等設置對應價格
                cabin_class = offer.get('cabin_class', 'ECONOMY').upper()
                price_amount = float(offer.get('price', {}).get('amount', 0))
                
                if cabin_class == 'ECONOMY':
                    price_data['economy_price'] = price_amount
                elif cabin_class == 'PREMIUM_ECONOMY':
                    price_data['premium_economy_price'] = price_amount
                elif cabin_class == 'BUSINESS':
                    price_data['business_price'] = price_amount
                elif cabin_class == 'FIRST':
                    price_data['first_price'] = price_amount
                
                price_data['total_price'] = price_amount
                price_data['currency'] = offer.get('price', {}).get('currency', 'TWD')
                
                # 保存到數據庫
                TicketPrice.save_search_result(
                    origin_code=origin,
                    destination_code=destination,
                    departure_date=departure_dt,
                    price_data=price_data,
                    amadeus_offer_id=offer.get('id'),
                    cache_hours=self.cache_duration_hours
                )
            
            logger.info(f"成功緩存 {len(offers[:10])} 個航班報價")
            
        except Exception as e:
            logger.error(f"保存緩存時發生錯誤：{e}")
    
    async def get_price_history(self, origin: str, destination: str, 
                              days_back: int = 30) -> Dict:
        """獲取指定路線的價格歷史趨勢"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days_back)
            
            history_records = TicketPrice.query.filter(
                TicketPrice.origin_airport_code == origin,
                TicketPrice.destination_airport_code == destination,
                TicketPrice.price_updated_at >= start_date
            ).order_by(TicketPrice.price_updated_at.desc()).all()
            
            if not history_records:
                return {
                    "success": False,
                    "message": "沒有找到價格歷史數據"
                }
            
            # 組織歷史數據
            price_history = []
            for record in history_records:
                history_item = {
                    "date": record.price_updated_at.strftime('%Y-%m-%d'),
                    "economy_price": record.economy_price,
                    "premium_economy_price": record.premium_economy_price,
                    "business_price": record.business_price,
                    "first_price": record.first_price,
                    "lowest_price": record.get_lowest_price_for_flight(record.price_id)
                }
                price_history.append(history_item)
            
            return {
                "success": True,
                "data": price_history,
                "meta": {
                    "route": f"{origin}->{destination}",
                    "days_back": days_back,
                    "total_records": len(price_history)
                }
            }
            
        except Exception as e:
            logger.error(f"獲取價格歷史時發生錯誤：{e}")
            return {
                "success": False,
                "message": "獲取價格歷史時發生內部錯誤",
                "error": str(e)
            }
    
    async def clear_expired_cache(self):
        """清理過期的緩存數據"""
        try:
            expired_count = TicketPrice.query.filter(
                TicketPrice.is_cached == True,
                TicketPrice.cache_expires_at < datetime.utcnow()
            ).delete()
            
            db.session.commit()
            logger.info(f"清理了 {expired_count} 條過期緩存記錄")
            return expired_count
            
        except Exception as e:
            logger.error(f"清理過期緩存時發生錯誤：{e}")
            db.session.rollback()
            return 0

# 創建服務實例
realtime_price_service = RealtimePriceService() 