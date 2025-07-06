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
import json

from ..services.amadeus_service import amadeus_service
from ..adapters.amadeus_offers_adapter import adapt_flight_offers
from ..models.ticket_price import TicketPrice
from app import db
from ..services.airline_service import airline_service
from ..services.airport_service import airport_service

logger = logging.getLogger(__name__)

def _get_airline_logo_path(airline_code: str) -> str:
    """獲取航空公司Logo路徑"""
    if not airline_code or airline_code == 'N/A':
        return ""
    
    # 基於文件系統中的Logo文件
    logo_filename = f"{airline_code.upper()}.png"
    logo_path = f"/app/static/images/logos/{logo_filename}"
    
    # 檢查Logo是否存在（這裡假設常見的航空公司都有Logo）
    common_airlines = ['CI', 'BR', 'JL', 'NH', 'KE', 'OZ', 'CX', 'SQ', 'TG', 'VJ', 
                       'MU', 'MF', 'AK', 'TR', 'GK', 'JX', 'IT', 'B7', 'TW', 'DA',
                       'NX', 'HX', 'HB', 'SL', '3U', 'AE']
    
    if airline_code.upper() in common_airlines:
        return logo_path
    else:
        return ""  # 默認無Logo

def _parse_datetime(time_str: str) -> Optional[datetime]:
    """解析 ISO 格式的日期時間字符串"""
    if not time_str:
        return None
    try:
        # 如果字符串包含時區信息，移除它進行簡單解析
        if 'T' in time_str and '+' in time_str:
            time_str = time_str.split('+')[0]
        elif 'T' in time_str and 'Z' in time_str:
            time_str = time_str.replace('Z', '')
        
        # 支持常見的ISO格式
        if '.' in time_str:
            return datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%S.%f')
        else:
            return datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%S')
    except (ValueError, AttributeError) as e:
        logger.warning(f"無法解析時間格式: {time_str}, 錯誤: {e}")
        return None

def _map_cabin_to_chinese(cabin):
    """將艙等代碼映射為中文"""
    cabin_mapping = {
        # 新格式
        'Economy': '經濟艙',
        'Premium Economy': '優質經濟艙', 
        'Business': '商務艙',
        'First': '頭等艙',
        # 向下相容舊格式
        'ECONOMY': '經濟艙',
        'PREMIUM_ECONOMY': '優質經濟艙', 
        'BUSINESS': '商務艙',
        'FIRST': '頭等艙'
    }
    return cabin_mapping.get(cabin, '經濟艙')

class RealtimePriceService:
    """實時價格服務類"""
    
    def __init__(self):
        self.cache_duration_hours = 4  # 默認緩存 4 小時
        self.max_api_calls_per_search = 4  # 每次搜索最多調用 4 個艙等的 API
    
    async def search_flight_prices(self, origin: str, destination: str, departure_date: str, 
                                   cabin_preference: Optional[str] = None, use_cache: bool = True) -> Dict:
        """搜索航班價格 - 臨時禁用緩存避免事務錯誤"""
        
        logger.info(f"開始搜索航班價格：{origin} -> {destination}, 日期: {departure_date}, 艙等: {cabin_preference}")
        
        try:
            # 臨時禁用緩存功能，直接返回空結果讓controller回退到靜態查詢
            logger.info("臨時禁用實時價格緩存，回退到靜態航班數據")
                    return {
                "success": False,
                "data": [],
                "message": "實時價格服務暫時禁用，使用靜態數據",
                "source": "disabled_cache"
            }
            
        except Exception as e:
            logger.error(f"搜索航班價格時發生錯誤：{e}")
            return {
                "success": False,
                "data": [],
                "message": f"搜索失敗：{str(e)}",
                "source": "error"
            }
    
    async def _get_cached_prices(self, origin: str, destination: str, departure_date: str, cabin_class: Optional[str] = None) -> Optional[List[Dict]]:
        """從緩存中獲取價格數據 - 完整航班信息版本"""
        try:
            departure_dt = datetime.strptime(departure_date, '%Y-%m-%d')
            
            # 緩存應該區分艙等 - 如果指定了艙等，只返回該艙等的航班
            cached_records = TicketPrice.query.filter(
                TicketPrice.origin_airport_code == origin,
                TicketPrice.destination_airport_code == destination,
                TicketPrice.departure_date == departure_dt,
                TicketPrice.is_cached == True,
                TicketPrice.cache_expires_at > datetime.utcnow()
            )
            
            # 如果指定了艙等，添加艙等篩選
            if cabin_class:
                cached_records = cached_records.filter(TicketPrice.cabin_class == cabin_class)
            
            cached_records = cached_records.all()
            
            if not cached_records:
                logger.info(f"沒有找到有效的緩存數據：{origin}->{destination} on {departure_date} (艙等: {cabin_class or '全部'})")
                return None
            
            logger.info(f"找到 {len(cached_records)} 條緩存記錄")
            
            # 轉換為前端期望的格式
            cached_flights = []
            for record in cached_records:
                if record.amadeus_offer_id:  # 確保有 Amadeus offer ID
                    # 獲取機場信息
                    dep_airport = await airport_service.get_airport_by_iata(record.origin_airport_code)
                    arr_airport = await airport_service.get_airport_by_iata(record.destination_airport_code)
                    
                    # 使用緩存中的完整航班信息
                    flight_data = {
                        "flight_id": record.amadeus_offer_id,
                        "id": record.amadeus_offer_id,
                        "flight_number": getattr(record, 'flight_number', 'N/A'),
                        
                        # 航空公司信息 - 使用緩存的完整信息
                        "airline": {
                            "code": getattr(record, 'airline_code', 'N/A'),
                            "name": getattr(record, 'airline_name', '未知航空'),
                            "name_zh": getattr(record, 'airline_name_zh', getattr(record, 'airline_name', '未知航空')),
                            "logo_path": _get_airline_logo_path(getattr(record, 'airline_code', 'N/A'))
                        },
                        
                        "departure": {
                            "code": record.origin_airport_code,
                            "time": getattr(record, 'departure_time').isoformat() if getattr(record, 'departure_time', None) else f"{record.departure_date.strftime('%Y-%m-%d')}T08:00:00",
                            "name": dep_airport.get('name_zh', dep_airport.get('name', '未知機場')) if dep_airport else '未知機場',
                            "airport": dep_airport.get('name_zh', dep_airport.get('name', '未知機場')) if dep_airport else '未知機場'
                        },
                        "arrival": {
                            "code": record.destination_airport_code,
                            "time": getattr(record, 'arrival_time').isoformat() if getattr(record, 'arrival_time', None) else f"{record.departure_date.strftime('%Y-%m-%d')}T11:00:00",
                            "name": arr_airport.get('name_zh', arr_airport.get('name', '未知機場')) if arr_airport else '未知機場',
                            "airport": arr_airport.get('name_zh', arr_airport.get('name', '未知機場')) if arr_airport else '未知機場'
                        },
                        "price": {
                            "amount": record.total_price or record.economy_price,
                            "currency": record.currency,
                            "cabin_class": record.cabin_class,
                            "isAvailable": True
                        },
                        "cabin_class": record.cabin_class,
                        "cabin_class_zh": _map_cabin_to_chinese(record.cabin_class),
                        "duration": getattr(record, 'duration', 'N/A'),
                        "cached": True,
                        "cache_expires": record.cache_expires_at.isoformat(),
                        "search_rank": getattr(record, 'search_rank', 1)
                    }
                    cached_flights.append(flight_data)
            
            # 按搜索排名排序
            cached_flights.sort(key=lambda x: x.get('search_rank', 999))
            
            # 返回緩存數據 - 注意：這裡返回所有艙等的數據，後續會在主搜尋邏輯中按艙等篩選
            logger.info(f"從緩存返回 {len(cached_flights)} 個完整航班信息")
            return cached_flights if cached_flights else None
            
        except Exception as e:
            logger.error(f"獲取緩存價格時發生錯誤：{e}")
            return None
    
    async def _fetch_realtime_prices(self, origin: str, destination: str, 
                                   departure_date: str, cabin_preference: Optional[str] = None) -> Dict:
        """從 Amadeus API 獲取實時價格"""
        try:
            # 設置合理的超時時間和結果數量限制
            max_results = 10  # 減少結果數量以避免超時
            api_timeout = 45  # 45秒超時
            
            logger.info(f"開始查詢 Amadeus API：{origin}->{destination} on {departure_date}")
                
            # 使用 asyncio.wait_for 設置總體超時
            result = await asyncio.wait_for(
                amadeus_service.search_flight_offers(
                    origin=origin,
                    destination=destination,
                    departure_date=departure_date,
                    max_results=max_results
                ),
                timeout=api_timeout
                )
                
            all_offers = []
                if result and isinstance(result, dict) and 'data' in result:
                    all_offers = result['data']
                logger.info(f"Amadeus API 返回 {len(all_offers)} 個航班報價")
            else:
                logger.warning(f"Amadeus API 未返回有效數據：{result}")
            
            # 如果指定了艙等偏好，過濾結果
            if cabin_preference and all_offers:
                cabin_preference_upper = cabin_preference.upper()
                logger.info(f"按艙等 {cabin_preference_upper} 過濾結果")
            
            if not all_offers:
                return {
                    "success": True,
                    "data": [],
                    "source": "amadeus_api",
                    "message": "未找到符合條件的航班"
                }
            
            # 使用現有的適配器處理數據，增加超時時間並分批處理
            try:
                # 增加適配器超時時間
                adapter_timeout = 45  # 增加到45秒
                
                # 分批處理以避免超時
                if len(all_offers) > 5:
                    # 分批處理大量數據
                    batch_size = 5
                    adapted_offers = []
                    
                    for i in range(0, len(all_offers), batch_size):
                        batch = all_offers[i:i + batch_size]
                        batch_result = await asyncio.wait_for(
                            adapt_flight_offers({'data': batch}),
                            timeout=adapter_timeout
                        )
                        if batch_result:
                            adapted_offers.extend(batch_result)
                        
                        # 短暫延遲以避免過載
                        await asyncio.sleep(0.01)
                else:
                    # 少量數據直接處理
                    adapted_offers = await asyncio.wait_for(
                        adapt_flight_offers({'data': all_offers}),
                        timeout=adapter_timeout
                    )
                
                logger.info(f"成功適配 {len(adapted_offers)} 個航班報價")
            
            except asyncio.TimeoutError:
                logger.error("適配航班數據時超時")
                return {
                    "success": False,
                    "message": "處理航班數據時超時",
                    "error": "適配器超時"
                }
            
            return {
                "success": True,
                "data": adapted_offers,
                "source": "amadeus_api",
                "message": f"成功獲取 {len(adapted_offers)} 個航班報價"
            }
            
        except asyncio.TimeoutError:
            logger.error("適配航班數據時超時")
            return {
                "success": False,
                "message": "處理航班數據時超時",
                "error": "適配器超時"
            }
        except Exception as e:
            logger.error(f"從 Amadeus API 獲取價格時發生錯誤：{e}")
            return {
                "success": False,
                "message": "無法從 API 獲取實時價格數據",
                "error": str(e)
            }
        finally:
            # 確保清理資源
            try:
                await amadeus_service.close_session()
            except Exception as cleanup_error:
                logger.warning(f"清理 Amadeus 服務時發生錯誤：{cleanup_error}")
    
    async def _save_to_cache(self, origin: str, destination: str, departure_date: str, offers: List[Dict], cabin_preference: Optional[str] = None):
        """將搜索結果保存到緩存 - 修復事務管理"""
        try:
            departure_dt = datetime.strptime(departure_date, '%Y-%m-%d')
            
            # 生成緩存鍵（包含艙等信息）
            cache_key = f"{origin}_{destination}_{departure_date}_{cabin_preference or 'ALL'}"
            
            # 保存高優先級結果到緩存
            priority_flights = offers[:max(5, len(offers) // 3)]  # 取前5個或前1/3
            cache_objects = []
            
            for index, flight in enumerate(priority_flights):
                # 確保獲取Amadeus Offer ID
                amadeus_offer_id = flight.get("id") or flight.get("flight_id")
                if not amadeus_offer_id:
                    continue
                
                # 確定艙等 - 優先使用搜索時指定的艙等，否則使用航班數據中的艙等
                flight_cabin_class = cabin_preference or flight.get("cabin_class") or flight.get("price", {}).get("cabin_class") or "ECONOMY"
                    
                cache_obj = TicketPrice(
                    amadeus_offer_id=amadeus_offer_id,
                    origin_airport_code=origin,
                    destination_airport_code=destination,
                    departure_date=departure_dt,
                    
                    # 價格信息
                    total_price=flight.get("price", {}).get("amount"),
                    currency=flight.get("price", {}).get("currency", "TWD"),
                    cabin_class=flight_cabin_class,  # 使用確定的艙等
                    
                    # 新增：完整航班信息
                    airline_code=flight.get("airline", {}).get("code"),
                    airline_name=flight.get("airline", {}).get("name"),
                    airline_name_zh=flight.get("airline", {}).get("name_zh"),
                    flight_number=flight.get("flight_number"),
                    duration=flight.get("duration"),
                    
                    # 時間信息（解析 ISO 格式）
                    departure_time=_parse_datetime(flight.get("departure", {}).get("time")),
                    arrival_time=_parse_datetime(flight.get("arrival", {}).get("time")),
                    
                    # 緩存控制
                    cache_priority=index,  # 搜索排名
                    search_rank=index + 1,
                    is_cached=True,
                    cache_expires_at=datetime.utcnow() + timedelta(hours=1),
                    search_key=cache_key
                )
                cache_objects.append(cache_obj)
            
            if cache_objects:
                # 使用獨立的事務保存緩存
                try:
                    db.session.add_all(cache_objects)
                    db.session.commit()
                    logger.info(f"成功緩存 {len(cache_objects)} 個航班報價（艙等: {cabin_preference or 'ALL'}）")
                except Exception as commit_error:
                    logger.error(f"緩存提交時發生錯誤：{commit_error}")
                    db.session.rollback()
                    raise
            else:
                logger.warning("沒有有效的航班數據可緩存")
            
        except Exception as e:
            logger.error(f"保存緩存時發生錯誤：{e}")
            try:
                db.session.rollback()
            except Exception as rollback_error:
                logger.error(f"回滾事務時發生錯誤：{rollback_error}")
    
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