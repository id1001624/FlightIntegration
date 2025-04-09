#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
數據同步服務模組 - 負責從外部API同步數據到本地數據庫
"""

import logging
import os
import json
import uuid
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta

import asyncio
import httpx
from fastapi import Depends

# 使用新的數據庫模組
from app.database.db import get_db, db

from app.models.airline import Airline
from app.models.airport import Airport
from app.models.flight import Flight
from app.models.weather import Weather

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('data_sync_service')

# 導入API同步管理器
try:
    from app.scripts.sync_manager import ApiSyncManager
except ImportError:
    logger.warning("無法直接導入ApiSyncManager，可能需要手動導入腳本路徑")
    import sys
    import os
    # 嘗試導入腳本目錄
    script_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scripts')
    if script_dir not in sys.path:
        sys.path.append(script_dir)
    try:
        from app.scripts.sync_manager import ApiSyncManager
    except ImportError as e:
        logger.error(f"無法導入ApiSyncManager: {str(e)}")

class DataSyncService:
    """數據同步服務 - 負責從外部API同步數據到本地數據庫"""
    
    # 台灣機場列表
    TAIWAN_AIRPORTS = ['TPE', 'TSA', 'RMQ', 'KHH', 'TNN', 'CYI', 'HUN', 'TTT', 'KNH', 'MZG', 'LZN', 'MFK', 'KYD', 'GNI', 'WOT', 'CMJ']
    
    # 目標航空公司列表
    TARGET_AIRLINES = ['AE', 'B7', 'BR', 'CI', 'CX', 'DA', 'IT', 'JL', 'JX', 'OZ']
    
    def __init__(self, pool=None):
        """
        初始化數據同步服務
        
        Args:
            pool: 資料庫連接池，若不提供則自動建立
        """
        self.pool = pool
        self.api_base_url = os.getenv("API_BASE_URL", "https://flightstats-api.example.com")
        self.api_key = os.getenv("API_KEY", "")
        self.api_timeout = int(os.getenv("API_TIMEOUT", "30"))
        
        # 中文名稱映射
        self.airline_name_map = {}  # 航空公司代碼到中文名稱的映射
        self.airport_name_map = {}  # 機場代碼到中文名稱的映射
        
        # API同步管理器
        try:
            self.sync_manager = ApiSyncManager()
            logger.info("已初始化API同步管理器")
        except Exception as e:
            self.sync_manager = None
            logger.error(f"初始化API同步管理器失敗: {str(e)}")
    
    async def get_pool(self):
        """獲取或創建連接池，優先使用傳入的連接池"""
        if self.pool is None:
            # 使用 db.py 中的方法初始化連接池
            from app.database.db import init_asyncpg_pool
            self.pool = await init_asyncpg_pool()
        return self.pool
    
    async def close_pool(self):
        """關閉連接池"""
        if self.pool:
            # 如果是通過 db.py 創建的連接池，不需要在這裡關閉
            # 因為 db.py 會在應用關閉時處理
            pass
    
    async def load_translation_maps(self):
        """加載中文名稱映射"""
        if self.airline_name_map and self.airport_name_map:
            return  # 已經加載過，直接返回
            
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            # 加載航空公司映射
            rows = await conn.fetch("""
                SELECT iata_code, name_zh FROM airlines 
                WHERE name_zh IS NOT NULL AND name_zh != ''
            """)
            self.airline_name_map = {row['iata_code']: row['name_zh'] for row in rows}
            logger.info(f"已加載 {len(self.airline_name_map)} 個航空公司中文名稱映射")
            
            # 加載機場映射
            rows = await conn.fetch("""
                SELECT iata_code, name_zh FROM airports 
                WHERE name_zh IS NOT NULL AND name_zh != ''
            """)
            self.airport_name_map = {row['iata_code']: row['name_zh'] for row in rows}
            logger.info(f"已加載 {len(self.airport_name_map)} 個機場中文名稱映射")
    
    async def translate_flight_data(self, flight_data: Dict) -> Dict:
        """
        將航班數據中的英文名稱翻譯為中文
        
        Args:
            flight_data: 原始航班數據
            
        Returns:
            翻譯後的航班數據
        """
        # 確保已加載映射表
        await self.load_translation_maps()
        
        # 翻譯航空公司名稱
        airline_code = flight_data.get('airline_code')
        if airline_code and airline_code in self.airline_name_map:
            flight_data['airline_name_zh'] = self.airline_name_map[airline_code]
        
        # 翻譯出發機場名稱
        departure_airport = flight_data.get('departure_airport')
        if departure_airport and departure_airport in self.airport_name_map:
            flight_data['departure_airport_name_zh'] = self.airport_name_map[departure_airport]
        
        # 翻譯到達機場名稱
        arrival_airport = flight_data.get('arrival_airport')
        if arrival_airport and arrival_airport in self.airport_name_map:
            flight_data['arrival_airport_name_zh'] = self.airport_name_map[arrival_airport]
        
        return flight_data
    
    async def sync_airlines(self, source="api"):
        """
        同步航空公司數據
        
        Args:
            source: 數據來源，可選 'api'（從外部API獲取）或 'file'（從本地文件獲取）
        
        Returns:
            同步結果摘要
        """
        logger.info(f"開始同步航空公司數據，來源: {source}")
        
        # 從來源獲取航空公司數據
        airlines_data = []
        if source == "api":
            airlines_data = await self._fetch_airlines_from_api()
        elif source == "file":
            airlines_data = self._read_airlines_from_file()
        else:
            raise ValueError(f"不支持的數據來源: {source}")
        
        if not airlines_data:
            logger.warning("未獲取到航空公司數據")
            return {"status": "error", "message": "未獲取到航空公司數據", "count": 0}
        
        # 獲取數據庫連接池
        pool = await self.get_pool()
        
        # 同步到數據庫
        new_count = 0
        update_count = 0
        
        async with pool.acquire() as conn:
            # 獲取現有的航空公司
            existing_airlines = {}
            rows = await conn.fetch("SELECT airline_id, iata_code FROM airlines")
            for row in rows:
                # 映射 iata_code 到 airline_id
                existing_airlines[row['iata_code']] = row['airline_id']
            
            # 處理每個航空公司
            for airline in airlines_data:
                iata_code = airline.get('iata_code')
                
                # 如果沒有 IATA 代碼，跳過
                if not iata_code:
                    continue
                
                # 準備插入或更新的資料
                airline_data = {
                    'name': airline.get('name', ''),
                    'name_zh': airline.get('name_zh', airline.get('name', '')),  # 如果有中文名稱就使用，否則使用英文名稱
                    'alias': airline.get('alias', ''),
                    'iata_code': iata_code,
                    'icao_code': airline.get('icao_code', ''),
                    'callsign': airline.get('callsign', ''),
                    'country': airline.get('country', ''),
                    'is_active': airline.get('is_active', True),
                    'logo_url': airline.get('logo_url', ''),
                    'website': airline.get('website', '')
                }
                
                # 檢查是否已存在
                if iata_code in existing_airlines:
                    # 更新現有航空公司
                    await conn.execute("""
                        UPDATE airlines SET
                            name = $1, name_zh = $2, alias = $3, icao_code = $4, callsign = $5,
                            country = $6, is_active = $7, logo_url = $8, website = $9,
                            updated_at = NOW()
                        WHERE airline_id = $10
                    """, 
                    airline_data['name'], airline_data['name_zh'], airline_data['alias'], airline_data['icao_code'],
                    airline_data['callsign'], airline_data['country'], airline_data['is_active'],
                    airline_data['logo_url'], airline_data['website'], iata_code)
                    update_count += 1
                else:
                    # 新增航空公司，使用 IATA 代碼作為主鍵
                    await conn.execute("""
                        INSERT INTO airlines (
                            airline_id, name, name_zh, alias, iata_code, icao_code, callsign,
                            country, is_active, logo_url, website, created_at, updated_at
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW(), NOW())
                    """, 
                    iata_code, airline_data['name'], airline_data['name_zh'], airline_data['alias'], 
                    airline_data['iata_code'], airline_data['icao_code'], airline_data['callsign'],
                    airline_data['country'], airline_data['is_active'], airline_data['logo_url'], 
                    airline_data['website'])
                    new_count += 1
        
            return {
                "status": "success",
                "message": f"成功同步航空公司數據: 新增 {new_count} 個，更新 {update_count} 個",
                "new_count": new_count,
                "update_count": update_count,
                "total_count": new_count + update_count
            }
    
    async def sync_airports(self, source="api"):
        """
        同步機場數據
        
        Args:
            source: 數據來源，可選 'api'（從外部API獲取）或 'file'（從本地文件獲取）
        
        Returns:
            同步結果摘要
        """
        logger.info(f"開始同步機場數據，來源: {source}")
        
        # 從來源獲取機場數據
        airports_data = []
        if source == "api":
            airports_data = await self._fetch_airports_from_api()
        elif source == "file":
            airports_data = self._read_airports_from_file()
        else:
            raise ValueError(f"不支持的數據來源: {source}")
        
        if not airports_data:
            logger.warning("未獲取到機場數據")
            return {"status": "error", "message": "未獲取到機場數據", "count": 0}
        
        # 獲取數據庫連接池
        pool = await self.get_pool()
        
        # 同步到數據庫
        new_count = 0
        update_count = 0
        
        async with pool.acquire() as conn:
            # 獲取現有的機場
            existing_airports = {}
            rows = await conn.fetch("SELECT airport_id, iata_code FROM airports")
            for row in rows:
                existing_airports[row['iata_code']] = row['airport_id']
            
            # 處理每個機場
            for airport in airports_data:
                iata_code = airport.get('iata_code')
                
                # 如果沒有 IATA 代碼，跳過
                if not iata_code:
                    continue
                
                # 準備插入或更新的資料
                airport_data = {
                    'name': airport.get('name', ''),
                    'name_zh': airport.get('name_zh', airport.get('name', '')),  # 如果有中文名稱就使用，否則使用英文名稱
                    'city': airport.get('city', ''),
                    'city_zh': airport.get('city_zh', airport.get('city', '')),
                    'country': airport.get('country', ''),
                    'country_zh': airport.get('country_zh', airport.get('country', '')),
                    'iata_code': iata_code,
                    'icao_code': airport.get('icao_code', ''),
                    'latitude': airport.get('latitude'),
                    'longitude': airport.get('longitude'),
                    'timezone': airport.get('timezone', ''),
                    'is_active': airport.get('is_active', True),
                    'website': airport.get('website', '')
                }
                
                # 檢查是否已存在
                if iata_code in existing_airports:
                    # 更新現有機場
                    await conn.execute("""
                        UPDATE airports SET
                            name = $1, name_zh = $2, city = $3, city_zh = $4, country = $5, country_zh = $6,
                            icao_code = $7, latitude = $8, longitude = $9, timezone = $10,
                            is_active = $11, website = $12, updated_at = NOW()
                        WHERE airport_id = $13
                    """, 
                    airport_data['name'], airport_data['name_zh'], airport_data['city'], airport_data['city_zh'],
                    airport_data['country'], airport_data['country_zh'], airport_data['icao_code'],
                    airport_data['latitude'], airport_data['longitude'], airport_data['timezone'],
                    airport_data['is_active'], airport_data['website'], iata_code)
                    update_count += 1
                else:
                    # 新增機場，使用 IATA 代碼作為主鍵
                    await conn.execute("""
                        INSERT INTO airports (
                            airport_id, name, name_zh, city, city_zh, country, country_zh,
                            iata_code, icao_code, latitude, longitude, timezone,
                            is_active, website, created_at, updated_at
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, NOW(), NOW())
                    """, 
                    iata_code, airport_data['name'], airport_data['name_zh'], airport_data['city'],
                    airport_data['city_zh'], airport_data['country'], airport_data['country_zh'],
                    iata_code, airport_data['icao_code'], airport_data['latitude'],
                    airport_data['longitude'], airport_data['timezone'], airport_data['is_active'],
                    airport_data['website'])
                    new_count += 1
                    
            # 更新中文名稱映射
            await self.load_translation_maps()
        
        logger.info(f"機場同步完成: {new_count} 個新增, {update_count} 個更新")
        return {
                "status": "success",
            "message": f"機場同步完成: {new_count} 個新增, {update_count} 個更新",
            "new_count": new_count,
            "update_count": update_count,
            "total_count": new_count + update_count
        }
    
    async def sync_flights(self, departures: List[str], arrivals: List[str], dates: List[str] = None):
        """
        同步航班數據
        
        Args:
            departures: 出發機場IATA代碼列表
            arrivals: 到達機場IATA代碼列表
            dates: 航班日期列表，若不提供則使用今明兩天
            
        Returns:
            同步結果摘要
        """
        logger.info(f"開始同步航班數據: {len(departures)} 個出發地, {len(arrivals)} 個目的地")
        
        # 如果沒有提供日期，使用今明兩天
        if not dates:
            today = datetime.now()
            tomorrow = today + timedelta(days=1)
            dates = [today.strftime('%Y-%m-%d'), tomorrow.strftime('%Y-%m-%d')]
        
        # 獲取數據庫連接池
        pool = await self.get_pool()
        
        # 同步到數據庫
        new_count = 0
        update_count = 0
        total_routes = len(departures) * len(arrivals) * len(dates)
        
        async with pool.acquire() as conn:
            for departure in departures:
                for arrival in arrivals:
                    for date in dates:
                        logger.info(f"同步航班: {departure} -> {arrival} on {date}")
                        
                        # 從API獲取航班數據
                        flights_data = await self._fetch_flights_from_api(departure, arrival, date)
                        
                        if not flights_data:
                            logger.warning(f"未獲取到航班數據: {departure} -> {arrival} on {date}")
                            continue
                        
                        # 處理每個航班
                        for flight in flights_data:
                            try:
                                # 獲取必要字段
                                airline_code = flight.get('airline_code')
                                flight_number = flight.get('flight_number')
                                scheduled_departure = flight.get('scheduled_departure')
                                scheduled_arrival = flight.get('scheduled_arrival')
                                
                                # 如果缺少必要信息，跳過
                                if not all([airline_code, flight_number, scheduled_departure, scheduled_arrival]):
                                    continue
                                
                                # 查詢對應的航空公司和機場ID
                                airline_id = await conn.fetchval(
                                    "SELECT airline_id FROM airlines WHERE iata_code = $1",
                                    airline_code
                                )
                                
                                departure_airport_id = await conn.fetchval(
                                    "SELECT airport_id FROM airports WHERE iata_code = $1",
                                    departure
                                )
                                
                                arrival_airport_id = await conn.fetchval(
                                    "SELECT airport_id FROM airports WHERE iata_code = $1",
                                    arrival
                                )
                                
                                # 如果找不到對應的航空公司或機場，跳過
                                if not all([airline_id, departure_airport_id, arrival_airport_id]):
                                    logger.warning(f"找不到航班相關信息: {airline_code}/{departure}/{arrival}")
                                    continue
                                
                                # 檢查航班是否已存在
                                existing_flight = await conn.fetchrow("""
                                    SELECT flight_id FROM flights 
                                    WHERE airline_id = $1 AND 
                                        flight_number = $2 AND 
                                        DATE(scheduled_departure) = DATE($3)
                                """, airline_id, flight_number, scheduled_departure)
                                
                                # 準備航班數據
                                flight_data = {
                                    'airline_id': airline_id,
                                    'departure_airport_id': departure_airport_id,
                                    'arrival_airport_id': arrival_airport_id,
                                    'flight_number': flight_number,
                                    'scheduled_departure': scheduled_departure,
                                    'scheduled_arrival': scheduled_arrival,
                                    'status': flight.get('status', 'scheduled'),
                                    'departure_terminal': flight.get('departure_terminal', ''),
                                    'departure_gate': flight.get('departure_gate', ''),
                                    'arrival_terminal': flight.get('arrival_terminal', ''),
                                    'arrival_gate': flight.get('arrival_gate', ''),
                                    'aircraft_type': flight.get('aircraft_type', ''),
                                    'duration_minutes': flight.get('duration_minutes', 0)
                                }
                                
                                if existing_flight:
                                    # 更新現有航班
                                    flight_id = existing_flight['flight_id']
                                    await conn.execute("""
                                        UPDATE flights SET
                                            airline_id = $1,
                                            departure_airport_id = $2,
                                            arrival_airport_id = $3,
                                            scheduled_departure = $4,
                                            scheduled_arrival = $5,
                                            status = $6,
                                            departure_terminal = $7,
                                            departure_gate = $8,
                                            arrival_terminal = $9,
                                            arrival_gate = $10,
                                            aircraft_type = $11,
                                            duration_minutes = $12,
                                            updated_at = NOW()
                                        WHERE flight_id = $13
                                    """, 
                                    flight_data['airline_id'], flight_data['departure_airport_id'],
                                    flight_data['arrival_airport_id'], flight_data['scheduled_departure'],
                                    flight_data['scheduled_arrival'], flight_data['status'],
                                    flight_data['departure_terminal'], flight_data['departure_gate'],
                                    flight_data['arrival_terminal'], flight_data['arrival_gate'],
                                    flight_data['aircraft_type'], flight_data['duration_minutes'],
                                    flight_id)
                                    update_count += 1
                                else:
                                    # 插入新航班
                                    flight_id = await conn.fetchval("""
                                        INSERT INTO flights (
                                            airline_id, departure_airport_id, arrival_airport_id,
                                            flight_number, scheduled_departure, scheduled_arrival,
                                            status, departure_terminal, departure_gate,
                                            arrival_terminal, arrival_gate, aircraft_type,
                                            duration_minutes, created_at, updated_at
                                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, NOW(), NOW())
                                        RETURNING flight_id
                                    """, 
                                    flight_data['airline_id'], flight_data['departure_airport_id'],
                                    flight_data['arrival_airport_id'], flight_data['flight_number'],
                                    flight_data['scheduled_departure'], flight_data['scheduled_arrival'],
                                    flight_data['status'], flight_data['departure_terminal'],
                                    flight_data['departure_gate'], flight_data['arrival_terminal'],
                                    flight_data['arrival_gate'], flight_data['aircraft_type'],
                                    flight_data['duration_minutes'])
                                    new_count += 1
                                
                                # 處理票價信息
                                await self._sync_ticket_prices(conn, flight_id, flight)
                                
                            except Exception as e:
                                logger.error(f"同步航班時出錯: {str(e)}")
        
        logger.info(f"航班同步完成: {new_count} 個新增, {update_count} 個更新")
        return {
                "status": "success",
            "message": f"航班同步完成: {new_count} 個新增, {update_count} 個更新",
            "new_count": new_count,
            "update_count": update_count,
            "total_count": new_count + update_count,
            "routes_processed": total_routes
        }

    async def sync_popular_routes(self, days=7):
        """
        同步熱門航線的航班數據
        
        Args:
            days: 同步未來幾天的數據
            
        Returns:
            同步結果摘要
        """
        # 獲取熱門航線的來源和目的地
        # 這裡可以從配置文件或者數據庫中讀取熱門航線
        popular_departures = ['TPE', 'TSA', 'KHH']  # 台北、台北松山、高雄
        popular_destinations = [
            'HKG', 'NRT', 'KIX', 'ICN', 'PVG', 'PEK', 'CAN', 'SIN', 'BKK', 'MNL'
        ]  # 香港、東京成田、大阪、首爾、上海浦東、北京、廣州、新加坡、曼谷、馬尼拉
        
        # 生成未來幾天的日期
        dates = []
        for i in range(days):
            date = (datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d')
            dates.append(date)
        
        # 同步航班數據
        return await self.sync_flights(popular_departures, popular_destinations, dates)
    
    async def sync_single_airport(self, iata_code):
        """
        同步單個機場的數據
        
        Args:
            iata_code: 機場IATA代碼
            
        Returns:
            同步結果
        """
        logger.info(f"開始同步機場 {iata_code} 的數據")
        
        # 從API獲取機場數據
        airport_data = await self._fetch_airport_from_api(iata_code)
        
        if not airport_data:
            logger.warning(f"未獲取到機場 {iata_code} 的數據")
            return {"status": "error", "message": f"未獲取到機場 {iata_code} 的數據"}
        
        # 獲取數據庫連接池
        pool = await self.get_pool()
        
        # 同步到數據庫
        async with pool.acquire() as conn:
            # 檢查機場是否已存在
            existing_airport = await conn.fetchrow(
                "SELECT airport_id FROM airports WHERE iata_code = $1",
                iata_code
            )
            
            # 準備機場數據
            airport = {
                'name': airport_data.get('name', ''),
                'city': airport_data.get('city', ''),
                'country': airport_data.get('country', ''),
                'iata_code': iata_code,
                'icao_code': airport_data.get('icao_code', ''),
                'latitude': airport_data.get('latitude', 0),
                'longitude': airport_data.get('longitude', 0),
                'altitude': airport_data.get('altitude', 0),
                'timezone': airport_data.get('timezone', ''),
                'is_active': airport_data.get('is_active', True)
            }
            
            if existing_airport:
                # 更新現有機場
                await conn.execute("""
                    UPDATE airports SET
                        name = $1, city = $2, country = $3, icao_code = $4,
                        latitude = $5, longitude = $6, altitude = $7, timezone = $8,
                        is_active = $9, updated_at = NOW()
                    WHERE airport_id = $10
                """, 
                airport['name'], airport['city'], airport['country'],
                airport['icao_code'], airport['latitude'], airport['longitude'],
                airport['altitude'], airport['timezone'], airport['is_active'],
                iata_code)
                logger.info(f"已更新機場: {iata_code}")
                return {"status": "success", "message": f"已更新機場: {iata_code}", "action": "update"}
            else:
                # 新增機場
                await conn.execute("""
                    INSERT INTO airports (
                        airport_id, name, city, country, iata_code, icao_code,
                        latitude, longitude, altitude, timezone, is_active,
                        created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW(), NOW())
                """, 
                iata_code, airport['name'], airport['city'], airport['country'],
                iata_code, airport['icao_code'], airport['latitude'],
                airport['longitude'], airport['altitude'], airport['timezone'],
                airport['is_active'])
                logger.info(f"已新增機場: {iata_code}")
                return {"status": "success", "message": f"已新增機場: {iata_code}", "action": "insert"}
    
    async def _sync_ticket_prices(self, conn, flight_id, flight):
        """
        同步航班票價
        
        Args:
            conn: 數據庫連接
            flight_id: 航班ID
            flight: 航班數據
        """
        # 檢查是否有票價數據
        if 'prices' not in flight:
            return
        
        for price_info in flight['prices']:
            class_type = price_info.get('class_type', '經濟')
            price = price_info.get('price')
            available_seats = price_info.get('available_seats', 0)
            
            # 跳過無效數據
            if price is None:
                continue
            
            # 檢查是否已有該艙位價格
            existing_price = await conn.fetchrow(
                "SELECT price_id FROM ticket_prices WHERE flight_id = $1 AND class_type = $2",
                flight_id, class_type
            )
            
            if existing_price:
                # 更新現有價格
                await conn.execute("""
                    UPDATE ticket_prices SET
                        base_price = $1,
                        available_seats = $2,
                        price_updated_at = NOW()
                    WHERE flight_id = $3 AND class_type = $4
                """, price, available_seats, flight_id, class_type)
            else:
                # 插入新價格
                await conn.execute("""
                    INSERT INTO ticket_prices (
                        flight_id, class_type, base_price, available_seats, price_updated_at
                    ) VALUES ($1, $2, $3, $4, NOW())
                """, flight_id, class_type, price, available_seats)
    
    async def _fetch_airlines_from_api(self):
        """從API獲取航空公司數據"""
        # 這裡是示範代碼，實際應該使用真實的API請求
        url = f"{self.api_base_url}/airlines"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        try:
            async with httpx.AsyncClient(timeout=self.api_timeout) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return response.json().get('data', [])
        except Exception as e:
            logger.error(f"從API獲取航空公司數據失敗: {str(e)}")
            return []
    
    def _read_airlines_from_file(self):
        """從本地文件讀取航空公司數據"""
        try:
            with open('data/airlines.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"從文件讀取航空公司數據失敗: {str(e)}")
            return []
    
    async def _fetch_airports_from_api(self):
        """從API獲取機場數據"""
        # 這裡是示範代碼，實際應該使用真實的API請求
        url = f"{self.api_base_url}/airports"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        try:
            async with httpx.AsyncClient(timeout=self.api_timeout) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return response.json().get('data', [])
        except Exception as e:
            logger.error(f"從API獲取機場數據失敗: {str(e)}")
            return []
    
    def _read_airports_from_file(self):
        """從本地文件讀取機場數據"""
        try:
            with open('data/airports.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"從文件讀取機場數據失敗: {str(e)}")
            return []
    
    async def _fetch_airport_from_api(self, iata_code):
        """從API獲取單個機場數據"""
        url = f"{self.api_base_url}/airports/{iata_code}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        try:
            async with httpx.AsyncClient(timeout=self.api_timeout) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return response.json().get('data', {})
        except Exception as e:
            logger.error(f"從API獲取機場 {iata_code} 數據失敗: {str(e)}")
            return {}
    
    async def _fetch_flights_from_api(self, departure, arrival, date):
        """從API獲取航班數據"""
        url = f"{self.api_base_url}/flights?departure={departure}&arrival={arrival}&date={date}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        try:
            async with httpx.AsyncClient(timeout=self.api_timeout) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return response.json().get('data', [])
        except Exception as e:
            logger.error(f"從API獲取航班數據失敗 ({departure}->{arrival} on {date}): {str(e)}")
            return []
            
    async def sync_taiwan_flights(self, date_str, days=1):
        """
        同步從台灣出發的航班數據
        
        Args:
            date_str: 起始日期，YYYY-MM-DD 格式
            days: 查詢天數
            
        Returns:
            同步結果摘要
        """
        logger.info(f"開始同步從台灣出發的航班數據，日期: {date_str}，天數: {days}")
        
        if not self.sync_manager:
            logger.error("API同步管理器未初始化，無法進行同步")
            return {"status": "error", "message": "API同步管理器未初始化", "count": 0}
        
        # 獲取從台灣出發的航班
        try:
            flight_data = self.sync_manager.sync_taiwan_departures(date_str, days)
            
            # 計算獲取的航班總數
            total_flights = sum(len(flights) for flights in flight_data.values())
            
            if total_flights == 0:
                logger.warning("未獲取到任何航班數據")
                return {"status": "warning", "message": "未獲取到任何航班數據", "count": 0}
                
            logger.info(f"從API獲取了 {total_flights} 個航班")
            
            # 將數據寫入數據庫
            # 使用數據庫連接池
            pool = await self.get_pool()
            
            # 處理每個機場的航班
            airport_stats = {}
            total_imported = 0
            
            for departure_airport, flights in flight_data.items():
                # 篩選目標航空公司的航班
                target_flights = [f for f in flights if f.get('airline_code') in self.TARGET_AIRLINES]
                
                # 翻譯航班數據
                translated_flights = []
                for flight in target_flights:
                    translated_flight = await self.translate_flight_data(flight)
                    translated_flights.append(translated_flight)
                
                # 導入到數據庫
                imported_count = await self._import_flights_to_db(pool, translated_flights)
                airport_stats[departure_airport] = {
                    "total": len(flights),
                    "target_airlines": len(target_flights),
                    "imported": imported_count
                }
                total_imported += imported_count
            
            return {
                "status": "success",
                "message": f"成功從台灣機場獲取並同步 {total_imported} 個航班",
                "total_flights": total_flights,
                "imported_flights": total_imported,
                "airport_stats": airport_stats
            }
            
        except Exception as e:
            logger.error(f"同步台灣航班時出錯: {str(e)}")
            return {"status": "error", "message": f"同步出錯: {str(e)}", "count": 0}
    
    async def _import_flights_to_db(self, pool, flights):
        """
        將航班數據導入到數據庫
        
        Args:
            pool: 數據庫連接池
            flights: 航班數據列表
            
        Returns:
            導入的航班數量
        """
        if not flights:
            return 0
            
        # 獲取現有的航空公司和機場映射
        airline_mapping, airport_mapping = await self._get_existing_airlines_airports(pool)
        
        # 篩選可以導入的航班（航空公司和機場必須已存在於數據庫中）
        valid_flights = []
        for flight in flights:
            airline_code = flight.get('airline_code')
            departure_airport = flight.get('departure_airport')
            arrival_airport = flight.get('arrival_airport')
            
            if (airline_code in airline_mapping and 
                departure_airport in airport_mapping and 
                arrival_airport in airport_mapping):
                
                flight['airline_id'] = airline_mapping[airline_code]
                flight['departure_airport_id'] = airport_mapping[departure_airport]
                flight['arrival_airport_id'] = airport_mapping[arrival_airport]
                valid_flights.append(flight)
            else:
                logger.warning(f"航班 {flight.get('flight_number')} 的航空公司或機場不存在於數據庫中，跳過導入")
        
        # 如果沒有有效航班，直接返回
        if not valid_flights:
            return 0
        
        # 導入有效航班
        imported_count = 0
        async with pool.acquire() as conn:
            async with conn.transaction():
                for flight in valid_flights:
                    try:
                        # 使用 flight_id 作為唯一標識
                        flight_id = flight.get('flight_id')
                        if not flight_id:
                            # 如果沒有提供flight_id，生成一個
                            flight_id = f"{flight['flight_number']}_{flight['departure_time'].split('T')[0]}"
                        
                        # 檢查航班是否已存在
                        existing = await conn.fetchval(
                            "SELECT flight_id FROM flights WHERE flight_id = $1", 
                            flight_id
                        )
                        
                        if existing:
                            # 更新現有航班
                            await conn.execute("""
                                UPDATE flights SET
                                    flight_number = $1,
                                    airline_id = $2,
                                    departure_airport_id = $3,
                                    arrival_airport_id = $4,
                                    scheduled_departure = $5,
                                    scheduled_arrival = $6,
                                    status = $7,
                                    updated_at = NOW()
                                WHERE flight_id = $8
                            """,
                            flight['flight_number'],
                            flight['airline_id'],
                            flight['departure_airport_id'],
                            flight['arrival_airport_id'],
                            flight['departure_time'],
                            flight['arrival_time'],
                            flight.get('status', 'scheduled'),
                            flight_id
                            )
                        else:
                            # 插入新航班
                            await conn.execute("""
                                INSERT INTO flights (
                                    flight_id, flight_number, airline_id,
                                    departure_airport_id, arrival_airport_id,
                                    scheduled_departure, scheduled_arrival,
                                    status, created_at, updated_at
                                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW(), NOW())
                            """,
                            flight_id,
                            flight['flight_number'],
                            flight['airline_id'],
                            flight['departure_airport_id'],
                            flight['arrival_airport_id'],
                            flight['departure_time'],
                            flight['arrival_time'],
                            flight.get('status', 'scheduled')
                            )
                        
                        # 更新票價信息
                        await self._update_ticket_prices(conn, flight_id, flight)
                        
                        imported_count += 1
                    except Exception as e:
                        logger.error(f"導入航班 {flight.get('flight_number')} 時出錯: {str(e)}")
                        # 繼續處理其他航班，不中斷整個事務
        
        return imported_count
    
    async def _get_existing_airlines_airports(self, pool):
        """
        獲取現有的航空公司和機場映射
        
        Args:
            pool: 數據庫連接池
            
        Returns:
            (airline_mapping, airport_mapping) 元組，
            分別將IATA代碼映射到數據庫ID
        """
        airline_mapping = {}
        airport_mapping = {}
        
        async with pool.acquire() as conn:
            # 獲取航空公司映射
            airlines = await conn.fetch("SELECT airline_id, iata_code FROM airlines")
            for airline in airlines:
                airline_mapping[airline['iata_code']] = airline['airline_id']
            
            # 獲取機場映射
            airports = await conn.fetch("SELECT airport_id, iata_code FROM airports")
            for airport in airports:
                airport_mapping[airport['iata_code']] = airport['airport_id']
        
        return airline_mapping, airport_mapping
    
    async def _update_ticket_prices(self, conn, flight_id, flight):
        """
        更新航班票價信息
        
        Args:
            conn: 數據庫連接
            flight_id: 航班ID
            flight: 航班數據
        """
        # 檢查是否有票價信息
        if not any(key in flight for key in ['economy_price', 'business_price', 'first_price']):
            return  # 沒有票價信息，不更新
        
        # 清除已有的票價記錄
        await conn.execute(
            "DELETE FROM ticket_prices WHERE flight_id = $1",
            flight_id
        )
        
        # 插入經濟艙票價
        if 'economy_price' in flight:
            await conn.execute("""
                INSERT INTO ticket_prices (
                    flight_id, class_type, base_price, available_seats, price_updated_at
                ) VALUES ($1, 'economy', $2, $3, NOW())
            """,
            flight_id,
            flight['economy_price'],
            flight.get('available_seats', 100)  # 默認100個座位
            )
        
        # 插入商務艙票價
        if 'business_price' in flight:
            await conn.execute("""
                INSERT INTO ticket_prices (
                    flight_id, class_type, base_price, available_seats, price_updated_at
                ) VALUES ($1, 'business', $2, $3, NOW())
            """,
            flight_id,
            flight['business_price'],
            flight.get('available_seats_business', 20)  # 默認20個座位
            )
        
        # 插入頭等艙票價
        if 'first_price' in flight:
            await conn.execute("""
                INSERT INTO ticket_prices (
                    flight_id, class_type, base_price, available_seats, price_updated_at
                ) VALUES ($1, 'first', $2, $3, NOW())
            """,
            flight_id,
            flight['first_price'],
            flight.get('available_seats_first', 10)  # 默認10個座位
            ) 