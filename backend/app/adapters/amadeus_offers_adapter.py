"""
This adapter is responsible for converting the raw flight offer search response 
from the Amadeus API into a standardized format that the application can use internally.
"""

import logging
from ..services.airport_service import airport_service
from ..services.airline_service import airline_service

logger = logging.getLogger(__name__)

async def _get_airline_name(carrier_code, dictionaries):
    """從本地資料庫或 Amadeus 字典中獲取航空公司名稱。"""
    airline = await airline_service.get_airline_by_code(carrier_code)
    if airline and airline.get('name_zh'):
        return airline['name_zh']
    return dictionaries.get('carriers', {}).get(carrier_code, carrier_code)

async def _get_airport_name(iata_code, dictionaries):
    """從本地資料庫或 Amadeus 字典中獲取機場名稱。"""
    airport = await airport_service.get_airport_by_iata(iata_code)
    if airport and airport.get('name_zh'):
        return airport['name_zh']
    # Amadeus 的機場資料在 `locations` key 裡面
    return dictionaries.get('locations', {}).get(iata_code, {}).get('detailedName', iata_code)

async def adapt_flight_offers(raw_offers_response):
    """
    Adapts the raw Amadeus Flight Offers Search API response.
    This version reads from the local database for chinese names, with fallback to Amadeus's data.
    It does NOT write to the database.

    Args:
        raw_offers_response (dict): The raw JSON response from Amadeus API.

    Returns:
        list: A list of standardized flight offer dictionaries.
    """
    if not isinstance(raw_offers_response, dict) or 'data' not in raw_offers_response:
        logger.error("Invalid raw_offers_response format: 'data' key missing or not a dict.")
        return []

    processed_offers = []
    flight_data = raw_offers_response.get('data', [])
    dictionaries = raw_offers_response.get('dictionaries', {})

    for offer in flight_data:
        try:
            # 建立標準化的 offer 結構
            standardized_offer = {
                "id": offer.get('id'),
                "price": offer.get('price', {}).get('total'),
                "currency": offer.get('price', {}).get('currency'),
                "itineraries": []
            }

            # 遍歷 offer 中的每一個行程 (itinerary)
            for itinerary in offer.get('itineraries', []):
                standardized_itinerary = {
                    "duration": itinerary.get('duration'),
                    "segments": []
                }

                # 遍歷行程中的每一個航段 (segment)
                for segment in itinerary.get('segments', []):
                    
                    carrier_code = segment.get('carrierCode')
                    dep_iata = segment.get('departure', {}).get('iataCode')
                    arr_iata = segment.get('arrival', {}).get('iataCode')

                    # --- 策略 B: 唯讀查詢，找不到則備用 ---
                    airline_name = await _get_airline_name(carrier_code, dictionaries)
                    dep_airport_name = await _get_airport_name(dep_iata, dictionaries)
                    arr_airport_name = await _get_airport_name(arr_iata, dictionaries)
                    # --- 結束 ---

                    standardized_segment = {
                        "departure_airport": dep_iata,
                        "departure_airport_name": dep_airport_name,
                        "departure_time": segment.get('departure', {}).get('at'),
                        "arrival_airport": arr_iata,
                        "arrival_airport_name": arr_airport_name,
                        "arrival_time": segment.get('arrival', {}).get('at'),
                        "airline_code": carrier_code,
                        "airline_name": airline_name,
                        "flight_number": segment.get('number'),
                        "duration": segment.get('duration'),
                    }
                    standardized_itinerary['segments'].append(standardized_segment)
                
                standardized_offer['itineraries'].append(standardized_itinerary)
            
            processed_offers.append(standardized_offer)

        except (KeyError, TypeError) as e:
            logger.error(f"處理航班 offer 時出錯: {e}. Offer ID: {offer.get('id')}")
            continue

    return processed_offers 