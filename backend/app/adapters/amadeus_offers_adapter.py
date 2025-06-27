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

async def _get_airline_details(carrier_code, dictionaries):
    """獲取完整的航空公司詳細信息，包括 logo_path"""
    airline = await airline_service.get_airline_by_code(carrier_code)
    if airline:
        return {
            'code': carrier_code,
            'name': airline.get('name', carrier_code),
            'name_zh': airline.get('name_zh', airline.get('name', carrier_code)),
            'logo_path': airline.get('logo_path', '')
        }
    
    # 如果本地資料庫沒有，使用 Amadeus 字典的資料
    amadeus_name = dictionaries.get('carriers', {}).get(carrier_code, carrier_code)
    return {
        'code': carrier_code,
        'name': amadeus_name,
        'name_zh': amadeus_name,
        'logo_path': ''
    }

async def _get_airport_name(iata_code, dictionaries):
    """從本地資料庫或 Amadeus 字典中獲取機場名稱。"""
    airport = await airport_service.get_airport_by_iata(iata_code)
    if airport and airport.get('name_zh'):
        return airport['name_zh']
    # Amadeus 的機場資料在 `locations` key 裡面
    return dictionaries.get('locations', {}).get(iata_code, {}).get('detailedName', iata_code)

def _extract_cabin_class(traveler_pricings):
    """從 Amadeus travelerPricings 中提取艙等信息，返回前端期待的格式"""
    if not traveler_pricings or not isinstance(traveler_pricings, list):
        return 'Economy'  # 默認經濟艙
    
    # 取第一個旅客的票價詳情
    first_traveler = traveler_pricings[0]
    fare_details = first_traveler.get('fareDetailsBySegment', [])
    
    if fare_details and len(fare_details) > 0:
        # 從第一個航段的票價詳情中獲取艙等
        amadeus_cabin = fare_details[0].get('cabin', 'ECONOMY')
        # 轉換為前端期待的格式
        cabin_mapping = {
            'ECONOMY': 'Economy',
            'PREMIUM_ECONOMY': 'Premium Economy',
            'BUSINESS': 'Business', 
            'FIRST': 'First'
        }
        return cabin_mapping.get(amadeus_cabin, 'Economy')
    
    return 'Economy'

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
            # 從 offer 中提取艙等信息
            traveler_pricings = offer.get('travelerPricings', [])
            cabin_class = _extract_cabin_class(traveler_pricings)
            cabin_class_zh = _map_cabin_to_chinese(cabin_class)
            
            # 獲取第一個行程的第一個航段作為主要航班信息
            # Amadeus 通常返回直飛或轉機航班，我們取第一段作為主要顯示
            itineraries = offer.get('itineraries', [])
            if not itineraries:
                continue
                
            first_itinerary = itineraries[0]
            segments = first_itinerary.get('segments', [])
            if not segments:
                continue
                
            first_segment = segments[0]
            last_segment = segments[-1]  # 最後一段用於到達信息
            
            # 提取航空公司和機場信息
            carrier_code = first_segment.get('carrierCode')
            dep_iata = first_segment.get('departure', {}).get('iataCode')
            arr_iata = last_segment.get('arrival', {}).get('iataCode')
            
            # 獲取詳細信息
            airline_detail = await _get_airline_details(carrier_code, dictionaries)
            dep_airport_name = await _get_airport_name(dep_iata, dictionaries)
            arr_airport_name = await _get_airport_name(arr_iata, dictionaries)
            
            # 計算總飛行時間（分鐘）
            duration_minutes = _parse_duration_to_minutes(first_itinerary.get('duration'))
            
            # 建立前端期待的扁平化結構
            price_info = offer.get('price', {})
            standardized_offer = {
                # 基本航班信息
                "flight_id": offer.get('id'),  # 前端期待的 flight_id
                "id": offer.get('id'),  # 保留原始 id
                "flight_number": first_segment.get('number'),
                
                # 航空公司信息
                "airline": airline_detail,
                
                # 起降信息 - 前端期待的結構
                "departure": {
                    "time": first_segment.get('departure', {}).get('at'),
                    "code": dep_iata,
                    "name": dep_airport_name,
                    "airport": dep_airport_name
                },
                "arrival": {
                    "time": last_segment.get('arrival', {}).get('at'),
                    "code": arr_iata, 
                    "name": arr_airport_name,
                    "airport": arr_airport_name
                },
                
                # 時間信息（向下相容）
                "scheduled_departure": first_segment.get('departure', {}).get('at'),
                "scheduled_arrival": last_segment.get('arrival', {}).get('at'),
                "duration_minutes": duration_minutes,
                
                # 價格信息
                "price": {
                    "amount": price_info.get('total'),
                    "currency": price_info.get('currency'),
                    "isAvailable": True,  # Amadeus 返回的 offers 都是可用的
                    "cabin_class": cabin_class
                },
                
                # 艙等信息
                "cabin_class": cabin_class,
                "cabin_class_zh": cabin_class_zh,
                
                # 保留完整的行程信息供詳細頁面使用
                "itineraries": []
            }
            
            # 收集所有航空公司信息
            airlines_in_offer = set()
            
            # 處理完整的行程信息
            for itinerary in itineraries:
                standardized_itinerary = {
                    "duration": itinerary.get('duration'),
                    "segments": []
                }

                # 遍歷行程中的每一個航段 (segment)
                for segment in itinerary.get('segments', []):
                    
                    segment_carrier_code = segment.get('carrierCode')
                    segment_dep_iata = segment.get('departure', {}).get('iataCode')
                    segment_arr_iata = segment.get('arrival', {}).get('iataCode')

                    # 收集航空公司代碼
                    if segment_carrier_code:
                        airlines_in_offer.add(segment_carrier_code)

                    # 獲取航空公司和機場名稱
                    segment_airline_name = await _get_airline_name(segment_carrier_code, dictionaries)
                    segment_dep_airport_name = await _get_airport_name(segment_dep_iata, dictionaries)
                    segment_arr_airport_name = await _get_airport_name(segment_arr_iata, dictionaries)

                    standardized_segment = {
                        "departure_airport": segment_dep_iata,
                        "departure_airport_name": segment_dep_airport_name,
                        "departure_time": segment.get('departure', {}).get('at'),
                        "arrival_airport": segment_arr_iata,
                        "arrival_airport_name": segment_arr_airport_name,
                        "arrival_time": segment.get('arrival', {}).get('at'),
                        "airline_code": segment_carrier_code,
                        "airline_name": segment_airline_name,
                        "flight_number": segment.get('number'),
                        "duration": segment.get('duration'),
                        "cabin_class": cabin_class,
                        "cabin_class_zh": cabin_class_zh,
                    }
                    standardized_itinerary['segments'].append(standardized_segment)
                
                standardized_offer['itineraries'].append(standardized_itinerary)
            
            # 為這個 offer 添加所有航空公司詳細信息
            airlines_details = []
            for airline_code in airlines_in_offer:
                airline_detail_full = await _get_airline_details(airline_code, dictionaries)
                airlines_details.append(airline_detail_full)
            
            standardized_offer['airlines'] = airlines_details
            
            processed_offers.append(standardized_offer)

        except (KeyError, TypeError) as e:
            logger.error(f"處理航班 offer 時出錯: {e}. Offer ID: {offer.get('id')}")
            continue

    return processed_offers

def _parse_duration_to_minutes(iso_duration):
    """將 ISO 8601 持續時間格式 (PT2H30M) 轉換為分鐘數"""
    if not iso_duration:
        return 0
        
    try:
        # 移除 'PT' 前綴
        duration_str = iso_duration.replace('PT', '')
        
        hours = 0
        minutes = 0
        
        # 解析小時
        if 'H' in duration_str:
            hours_str = duration_str.split('H')[0]
            hours = int(hours_str)
            duration_str = duration_str.split('H')[1] if 'H' in duration_str else ''
        
        # 解析分鐘
        if 'M' in duration_str:
            minutes_str = duration_str.split('M')[0]
            minutes = int(minutes_str)
        
        return hours * 60 + minutes
        
    except (ValueError, IndexError) as e:
        logger.warning(f"無法解析持續時間格式: {iso_duration}, 錯誤: {e}")
        return 0 