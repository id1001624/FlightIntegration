import logging
from ..services.airport_service import AirportService

logger = logging.getLogger(__name__)

async def adapt_flight_destinations(amadeus_data):
    """
    將 Amadeus 的 flight-destinations API 回應轉換為前端所需的格式。
    這個適配器還會查詢本地資料庫以豐富機場資訊。
    """
    adapted_results = []
    if not amadeus_data or 'data' not in amadeus_data:
        return []

    for item in amadeus_data['data']:
        try:
            # 1. 從 Amadeus 獲取基礎數據
            origin_code = item.get('origin')
            destination_code = item.get('destination')
            price_data = item.get('price', {})
            
            # 2. 查詢本地資料庫以豐富機場資訊 (使用異步函式)
            departure_airport = await AirportService.get_airport_by_id(origin_code)
            arrival_airport = await AirportService.get_airport_by_id(destination_code)

            # 如果在我們的資料庫中找不到機場，就跳過這筆資料
            if not departure_airport or not arrival_airport:
                logger.warning(f"Skipping destination {origin_code}->{destination_code} because airport info not found in local DB.")
                continue

            # 3. 組裝成前端期望的格式
            adapted_item = {
                "flight_id": f"amadeus_{origin_code}_{destination_code}", # 暫時用組合字串當作唯一ID
                "flight_number": "N/A", # 目前的 API 沒有提供
                "aircraft": "N/A",
                "duration_minutes": None,
                "available_seats": None,
                "price_updated_at": item.get('lastTicketingDate'), # 使用 Amadeus 的欄位

                # 嵌套 Departure 機場資訊
                "departure": {
                    "code": departure_airport['airport_id'],
                    "name": departure_airport['name_zh'],
                    "city": departure_airport['city'],
                    "country": departure_airport['country'],
                    "logo_path": None # 這個可能需要另外的邏輯
                },
                
                # 嵌套 Arrival 機場資訊
                "arrival": {
                    "code": arrival_airport['airport_id'],
                    "name": arrival_airport['name_zh'],
                    "city": arrival_airport['city'],
                    "country": arrival_airport['country'],
                    "logo_path": None
                },
                
                # 嵌套價格資訊
                "price": {
                    "amount": float(price_data.get('total', 0.0)),
                    "currency": "EUR", # Amadeus Self-Service API 通常返回 EUR
                    "cabin_class": "Economy", # 假設為經濟艙
                    "isAvailable": True
                },

                # 由於此API不提供航空公司資訊，暫時留空或設為默認值
                "airline": None 
            }
            adapted_results.append(adapted_item)
        except (KeyError, TypeError, ValueError) as e:
            logger.error(f"Error adapting Amadeus item: {item}. Error: {e}")
            continue
            
    return adapted_results 