#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
資料庫同步工具 - 將FlightStats API資料同步到資料庫
"""
import os
import sys
import json
import logging
import psycopg2
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('database_sync')

# 嘗試導入 sync_manager (假設它已經在同一目錄)
try:
    from sync_manager import ApiSyncManager
except ImportError:
    # 嘗試相對導入
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.append(current_dir)
    try:
        from sync_manager import ApiSyncManager
    except ImportError as e:
        logger.error(f"無法導入 ApiSyncManager: {str(e)}")
        sys.exit(1)

# 嘗試導入 FlightStatsApiClient
try:
    from flightstats_sync import FlightStatsApiClient
except ImportError:
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.append(current_dir)
        from flightstats_sync import FlightStatsApiClient
    except ImportError as e:
        logger.error(f"無法導入 FlightStatsApiClient: {str(e)}")
        FlightStatsApiClient = None

class DatabaseSyncManager:
    """數據庫同步管理器 - 負責將API數據同步到數據庫"""
    
    def __init__(self, conn_str=None):
        """
        初始化數據庫同步管理器
        
        Args:
            conn_str: 數據庫連接字符串，若不提供則嘗試從環境變量讀取
        """
        self.conn_str = conn_str or self._get_conn_str_from_env()
        self.api_sync_manager = ApiSyncManager()
        if FlightStatsApiClient:
            try:
                self.flightstats_client = FlightStatsApiClient()
            except Exception as e:
                logger.error(f"初始化 FlightStatsApiClient 失敗: {str(e)}")
                self.flightstats_client = None
        else:
            self.flightstats_client = None
            
        # 加載機場和航空公司的中文映射
        self.airline_name_map = {}  # 航空公司代碼到中文名稱的映射
        self.airport_name_map = {}  # 機場代碼到中文名稱的映射
        self.load_translation_maps()
        
    def load_translation_maps(self):
        """從數據庫加載翻譯映射表"""
        try:
            conn = self.get_db_connection()
            with conn.cursor() as cursor:
                # 獲取航空公司映射
                cursor.execute("""
                    SELECT airline_id, name_zh FROM airlines 
                    WHERE name_zh IS NOT NULL AND name_zh != ''
                """)
                for row in cursor.fetchall():
                    self.airline_name_map[row[0]] = row[1]
                logger.info(f"已加載 {len(self.airline_name_map)} 個航空公司中文名稱映射")
                
                # 獲取機場映射
                cursor.execute("""
                    SELECT airport_id, name_zh FROM airports 
                    WHERE name_zh IS NOT NULL AND name_zh != ''
                """)
                for row in cursor.fetchall():
                    self.airport_name_map[row[0]] = row[1]
                logger.info(f"已加載 {len(self.airport_name_map)} 個機場中文名稱映射")
            conn.close()
        except Exception as e:
            logger.error(f"加載翻譯映射失敗: {str(e)}")
        
    def _get_conn_str_from_env(self):
        """從環境變量獲取數據庫連接字符串"""
        # 優先使用 DATABASE_URL 環境變數
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            logger.info("使用 DATABASE_URL 環境變數建立資料庫連接")
            return database_url
            
        # 嘗試從環境變量讀取數據庫配置
        db_host = os.getenv("DB_HOST")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME", "flight_integration")
        db_user = os.getenv("DB_USER")
        db_password = os.getenv("DB_PASSWORD")
        
        if not all([db_host, db_user, db_password]):
            logger.error("環境變量缺少數據庫連接信息")
            sys.exit(1)
        
        return f"host={db_host} port={db_port} dbname={db_name} user={db_user} password={db_password}"
    
    def get_db_connection(self):
        """獲取數據庫連接"""
        try:
            # 檢查連接字符串格式
            if self.conn_str.startswith('postgresql://'):
                # 這是 DATABASE_URL 格式的連接字符串
                conn = psycopg2.connect(self.conn_str)
            else:
                # 這是傳統 key=value 格式的連接字符串
                conn = psycopg2.connect(self.conn_str)
            return conn
        except Exception as e:
            logger.error(f"數據庫連接失敗: {str(e)}")
            raise
    
    def get_existing_airlines_airports(self):
        """
        獲取現有的航空公司和機場映射
        
        Returns:
            airlines_map: 航空公司IATA代碼到ID的映射 {iata_code: airline_id}
            airports_map: 機場IATA代碼到ID的映射 {iata_code: airport_id}
        """
        airlines_map = {}
        airports_map = {}
        
        conn = self.get_db_connection()
        try:
            with conn.cursor() as cursor:
                # 獲取航空公司映射
                cursor.execute("SELECT airline_id, airline_id as iata_code FROM airlines")
                for row in cursor.fetchall():
                    airlines_map[row[1]] = row[0]
                logger.debug(f"加載了 {len(airlines_map)} 個航空公司映射")
                
                # 獲取機場映射
                cursor.execute("SELECT airport_id, airport_id as iata_code FROM airports")
                for row in cursor.fetchall():
                    airports_map[row[1]] = row[0]
                logger.debug(f"加載了 {len(airports_map)} 個機場映射")
        except Exception as e:
            logger.error(f"獲取航空公司和機場映射時出錯: {str(e)}")
        finally:
            conn.close()
        
        return airlines_map, airports_map
    
    def translate_flight_data(self, flight_data: Dict) -> Dict:
        """
        將航班數據中的英文名稱翻譯為中文
        
        Args:
            flight_data: 原始航班數據
            
        Returns:
            翻譯後的航班數據
        """
        # 翻譯航空公司名稱
        airline_code = flight_data.get('airline_code')
        if airline_code and airline_code in self.airline_name_map:
            flight_data['airline_name'] = self.airline_name_map[airline_code]
        
        # 翻譯出發機場名稱
        departure_airport = flight_data.get('departure_airport')
        if departure_airport and departure_airport in self.airport_name_map:
            flight_data['departure_airport_name'] = self.airport_name_map[departure_airport]
        
        # 翻譯到達機場名稱
        arrival_airport = flight_data.get('arrival_airport')
        if arrival_airport and arrival_airport in self.airport_name_map:
            flight_data['arrival_airport_name'] = self.airport_name_map[arrival_airport]
        
        return flight_data
    
    def filter_flights_by_existing_data(self, 
                                        flights: List[Dict], 
                                        airlines_map: Dict[str, str], 
                                        airports_map: Dict[str, str]) -> List[Dict]:
        """
        過濾航班數據，只保留航空公司和機場都在資料庫中存在的航班，同時翻譯名稱
        
        Args:
            flights: 從API獲取的航班列表
            airlines_map: 航空公司IATA代碼到ID的映射
            airports_map: 機場IATA代碼到ID的映射
            
        Returns:
            過濾後的航班列表
        """
        filtered_flights = []
        
        for flight in flights:
            airline_code = flight.get('airline_code')
            departure_airport = flight.get('departure_airport')
            arrival_airport = flight.get('arrival_airport')
            
            # 翻譯航班數據中的名稱
            flight = self.translate_flight_data(flight)
            
            # 檢查航空公司和機場是否都存在
            if (airline_code in airlines_map and 
                departure_airport in airports_map and 
                arrival_airport in airports_map):
                # 添加ID信息到航班數據，方便後續處理
                flight['airline_id'] = airlines_map[airline_code]
                flight['departure_airport_id'] = airports_map[departure_airport]
                flight['arrival_airport_id'] = airports_map[arrival_airport]
                filtered_flights.append(flight)
                logger.debug(f"保留航班: {flight.get('flight_number')} ({departure_airport}->{arrival_airport})")
            else:
                missing = []
                if airline_code not in airlines_map:
                    missing.append(f"航空公司 {airline_code}")
                if departure_airport not in airports_map:
                    missing.append(f"出發機場 {departure_airport}")
                if arrival_airport not in airports_map:
                    missing.append(f"目的機場 {arrival_airport}")
                
                logger.debug(f"過濾掉航班: {flight.get('flight_number')} - 缺少: {', '.join(missing)}")
        
        logger.info(f"過濾前航班數: {len(flights)}, 過濾後: {len(filtered_flights)}")
        return filtered_flights
    
    def import_flights_to_database(self, flights: List[Dict]) -> Dict:
        """
        將航班資料導入資料庫
        
        Args:
            flights: 過濾後的航班列表，已包含airline_id, departure_airport_id, arrival_airport_id
            
        Returns:
            導入結果統計
        """
        import_count = 0
        update_count = 0
        error_count = 0
        skipped_count = 0
        
        conn = self.get_db_connection()
        try:
            with conn.cursor() as cursor:
                for flight in flights:
                    try:
                        # 確保航班號碼是正確格式 (carrier+flight_number)
                        flight_number = flight.get('flight_number', '')
                        airline_code = flight.get('airline_code', '')
                        
                        # 如果航班號碼不是以航空公司代碼開頭，重新格式化它
                        if not flight_number.startswith(airline_code):
                            flight_number = f"{airline_code}{flight_number}"
                            logger.debug(f"重新格式化航班號碼: {flight_number}")
                        
                        # 準備航班基本資料 - 只包含必要欄位
                        flight_data = {
                            'airline_id': flight.get('airline_id', ''),
                            'departure_airport_id': flight.get('departure_airport_id', ''),
                            'arrival_airport_id': flight.get('arrival_airport_id', ''),
                            'flight_number': flight_number,
                            'scheduled_departure': flight.get('departure_time'),
                            'scheduled_arrival': flight.get('arrival_time'),
                            'status': flight.get('status', '準時'),
                            'is_delayed': flight.get('is_delayed', False)
                        }
                        
                        # 檢查必要欄位是否存在
                        missing_fields = []
                        for field in ['airline_id', 'departure_airport_id', 'arrival_airport_id', 'scheduled_departure', 'scheduled_arrival']:
                            if not flight_data.get(field):
                                missing_fields.append(field)
                        
                        if missing_fields:
                            logger.warning(f"航班 {flight_number} 缺少必要欄位: {', '.join(missing_fields)}")
                            skipped_count += 1
                            continue
                        
                        # 檢查航班是否已存在
                        cursor.execute(
                            """
                            SELECT flight_id FROM flights 
                            WHERE flight_number = %s AND 
                                  DATE(scheduled_departure) = DATE(%s)
                            """,
                            (flight_data['flight_number'], flight_data['scheduled_departure'])
                        )
                        existing_flight = cursor.fetchone()
                        
                        if existing_flight:
                            # 更新現有航班
                            flight_id = existing_flight[0]
                            cursor.execute(
                                """
                                UPDATE flights SET 
                                    airline_id = %s,
                                    departure_airport_id = %s,
                                    arrival_airport_id = %s,
                                    scheduled_departure = %s,
                                    scheduled_arrival = %s,
                                    status = %s,
                                    is_delayed = %s,
                                    updated_at = NOW()
                                WHERE flight_id = %s
                                """,
                                (
                                    flight_data['airline_id'],
                                    flight_data['departure_airport_id'],
                                    flight_data['arrival_airport_id'],
                                    flight_data['scheduled_departure'],
                                    flight_data['scheduled_arrival'],
                                    flight_data['status'],
                                    flight_data['is_delayed'],
                                    flight_id
                                )
                            )
                            update_count += 1
                            logger.debug(f"已更新航班 {flight_data['flight_number']}, ID: {flight_id}")
                        else:
                            # 插入新航班
                            cursor.execute(
                                """
                                INSERT INTO flights (
                                    airline_id, departure_airport_id, arrival_airport_id,
                                    flight_number, scheduled_departure, scheduled_arrival,
                                    status, is_delayed, created_at, updated_at
                                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                                RETURNING flight_id
                                """,
                                (
                                    flight_data['airline_id'],
                                    flight_data['departure_airport_id'],
                                    flight_data['arrival_airport_id'],
                                    flight_data['flight_number'],
                                    flight_data['scheduled_departure'],
                                    flight_data['scheduled_arrival'],
                                    flight_data['status'],
                                    flight_data['is_delayed']
                                )
                            )
                            flight_id = cursor.fetchone()[0]
                            import_count += 1
                            logger.debug(f"已導入航班 {flight_data['flight_number']}, ID: {flight_id}")
                        
                    except Exception as e:
                        error_count += 1
                        logger.error(f"導入航班 {flight.get('flight_number')} 失敗: {str(e)}")
                        conn.rollback()
                        continue
                
                # 提交事務
                conn.commit()
            
            result = {
                "total": len(flights),
                "inserted": import_count,
                "updated": update_count,
                "skipped": skipped_count,
                "errors": error_count
            }
            logger.info(f"航班同步結果: 總數 {len(flights)}, 新增 {import_count}, 更新 {update_count}, 跳過 {skipped_count}, 錯誤 {error_count}")
            return result
        
        except Exception as e:
            logger.error(f"導入航班資料時發生錯誤: {str(e)}")
            conn.rollback()
            return {"total": len(flights), "inserted": 0, "updated": 0, "skipped": len(flights), "errors": 0, "error": str(e)}
        finally:
            conn.close()
            
    def _update_ticket_prices(self, cursor, flight_id, flight):
        """更新航班票價信息"""
        # 首先檢查是否有新的票價數據格式
        if 'prices' in flight and isinstance(flight['prices'], list):
            for price_info in flight['prices']:
                class_type = price_info.get('class_type', '經濟')
                price = price_info.get('price')
                available_seats = price_info.get('available_seats')
                
                # 跳過無效數據
                if price is None:
                    continue
                
                try:
                    self._update_single_ticket_price(cursor, flight_id, class_type, price, available_seats)
                except Exception as e:
                    logger.error(f"更新航班 {flight.get('flight_number')} 票價失敗: {str(e)}")
            return
                
        # 如果沒有新格式的票價數據，嘗試從舊格式中獲取
        price_fields = [
            ('經濟', 'economy_price', 'economy_seats'),
            ('商務', 'business_price', 'business_seats'),
            ('頭等', 'first_price', 'first_seats')
        ]
        
        for class_type, price_field, seats_field in price_fields:
            if price_field in flight and flight[price_field] is not None:
                # 獲取座位數，如果沒有特定艙位的座位數，則使用默認的available_seats
                available_seats = flight.get(seats_field, flight.get('available_seats', 0))
                try:
                    self._update_single_ticket_price(cursor, flight_id, class_type, flight[price_field], available_seats)
                except Exception as e:
                    logger.error(f"更新航班 {flight.get('flight_number')} 票價失敗: {str(e)}")
    
    def _update_single_ticket_price(self, cursor, flight_id, class_type, price, available_seats):
        """更新單個艙位的票價信息"""
        # 檢查是否已有該艙位價格
        cursor.execute(
            """
            SELECT price_id FROM ticket_prices 
            WHERE flight_id = %s AND class_type = %s
            """,
            (flight_id, class_type)
        )
        existing_price = cursor.fetchone()
        
        if existing_price:
            # 更新現有價格
            cursor.execute(
                """
                UPDATE ticket_prices SET 
                    base_price = %s,
                    available_seats = %s,
                    price_updated_at = NOW()
                WHERE flight_id = %s AND class_type = %s
                """,
                (price, available_seats, flight_id, class_type)
            )
        else:
            # 插入新價格
            cursor.execute(
                """
                INSERT INTO ticket_prices (
                    flight_id, class_type, base_price, available_seats, price_updated_at
                ) VALUES (%s, %s, %s, %s, NOW())
                """,
                (flight_id, class_type, price, available_seats)
            )
        logger.debug(f"已更新航班 ID {flight_id} 的 {class_type} 艙位價格: {price}")
    
    def sync_flights(self, departure, arrival, date=None, days=1):
        """
        同步航班資料到資料庫
        
        Args:
            departure: 出發機場 IATA 代碼
            arrival: 目的機場 IATA 代碼
            date: 起始日期（可選，默認為今天）
            days: 查詢天數（可選，默認為1）
            
        Returns:
            導入結果統計
        """
        # 1. 獲取現有的航空公司和機場映射
        airlines_map, airports_map = self.get_existing_airlines_airports()
        
        # 2. 從API獲取航班資料
        all_flights = []
        
        # 先嘗試從 FlightStats API 獲取數據（主要用於國際航班）
        if self.flightstats_client:
            try:
                # 使用 FlightStats API 獲取航班
                flightstats_flights = self.flightstats_client.get_flights(departure, arrival, date, days)
                if flightstats_flights:
                    logger.info(f"從 FlightStats API 獲取 {len(flightstats_flights)} 個航班")
                    all_flights.extend(flightstats_flights)
            except Exception as e:
                logger.error(f"從 FlightStats API 獲取航班失敗: {str(e)}")
        
        # 再從 TDX API 獲取數據（主要用於國內航班，如果 FlightStats 沒有數據）
        if not all_flights:
            tdx_flights = self.api_sync_manager.sync_flights(departure, arrival, date, days)
            if tdx_flights:
                logger.info(f"從 TDX API 獲取 {len(tdx_flights)} 個航班")
                all_flights.extend(tdx_flights)
        
        # 3. 過濾航班資料並翻譯名稱
        filtered_flights = self.filter_flights_by_existing_data(all_flights, airlines_map, airports_map)
        
        # 4. 導入資料庫
        if filtered_flights:
            result = self.import_flights_to_database(filtered_flights)
            logger.info(f"航班同步結果: {result}")
            return result
        else:
            logger.warning(f"沒有找到 {departure} -> {arrival} 航線的航班或過濾後沒有符合條件的航班")
            return {"total": 0, "inserted": 0, "updated": 0, "skipped": 0, "errors": 0, "message": "沒有符合條件的航班"}
    
    def sync_popular_routes(self, date=None, days=1):
        """
        同步熱門航線資料到資料庫
        
        Args:
            date: 起始日期（可選，默認為今天）
            days: 查詢天數（可選，默認為1）
            
        Returns:
            導入成功的航班數量
        """
        total_imported = 0
        
        # 先同步國內熱門航線
        for departure, arrival in self.api_sync_manager.POPULAR_DOMESTIC_ROUTES:
            logger.info(f"正在同步國內熱門航線: {departure} -> {arrival}")
            count = self.sync_flights(departure, arrival, date, days)
            total_imported += count
            logger.info(f"完成 {departure}->{arrival} 同步，導入 {count} 個航班")
        
        # 再同步國際熱門航線
        for departure, arrival in self.api_sync_manager.POPULAR_INTERNATIONAL_ROUTES:
            logger.info(f"正在同步國際熱門航線: {departure} -> {arrival}")
            count = self.sync_flights(departure, arrival, date, days)
            total_imported += count
            logger.info(f"完成 {departure}->{arrival} 同步，導入 {count} 個航班")
        
        logger.info(f"完成所有熱門航線同步，共導入 {total_imported} 個航班")
        return total_imported

    def sync_taiwan_flights(self, date=None, days=1):
        """
        同步所有台灣機場出發的航班資料
        
        Args:
            date: 起始日期（可選，默認為今天）
            days: 查詢天數（可選，默認為1）
            
        Returns:
            導入結果統計
        """
        if not self.flightstats_client:
            logger.error("FlightStats API 客戶端未初始化")
            return {"total": 0, "inserted": 0, "updated": 0, "skipped": 0, "errors": 0, "message": "FlightStats API 客戶端未初始化"}
        
        try:
            # 獲取現有的航空公司和機場映射
            airlines_map, airports_map = self.get_existing_airlines_airports()
            
            # 同步所有台灣機場的航班
            result = self.flightstats_client.sync_all_taiwan_flights(date)
            
            if result and result.get("status") == "success":
                flights = result.get("flights", [])
                logger.info(f"成功從 FlightStats API 獲取 {len(flights)} 個台灣出發的航班")
                
                # 過濾航班資料並翻譯名稱
                filtered_flights = self.filter_flights_by_existing_data(flights, airlines_map, airports_map)
                
                # 導入資料庫
                if filtered_flights:
                    result = self.import_flights_to_database(filtered_flights)
                    logger.info(f"台灣航班同步結果: {result}")
                    return result
                else:
                    logger.warning("沒有符合條件的航班可導入")
                    return {"total": 0, "inserted": 0, "updated": 0, "skipped": 0, "errors": 0, "message": "沒有符合條件的航班"}
            else:
                logger.error("同步台灣航班失敗")
                return {"total": 0, "inserted": 0, "updated": 0, "skipped": 0, "errors": 0, "message": "同步台灣航班失敗"}
        except Exception as e:
            logger.error(f"同步台灣航班時發生錯誤: {str(e)}")
            return {"total": 0, "inserted": 0, "updated": 0, "skipped": 0, "errors": 0, "error": str(e)}

    def sync_airports(self, airports: List[Dict]) -> Dict:
        """
        同步機場數據到數據庫
        
        Args:
            airports: 機場數據列表
            
        Returns:
            同步結果統計
        """
        if not airports:
            return {"total": 0, "inserted": 0, "updated": 0, "skipped": 0, "error": "沒有提供機場數據"}
        
        inserted = 0
        updated = 0
        skipped = 0
        errors = 0
        
        conn = self.get_db_connection()
        try:
            with conn.cursor() as cursor:
                for airport in airports:
                    try:
                        # 獲取必要信息
                        airport_id = airport.get('iata_code') or airport.get('iata')
                        if not airport_id:
                            logger.warning(f"跳過沒有IATA代碼的機場: {airport.get('name', 'Unknown')}")
                            skipped += 1
                            continue
                        
                        # 檢查機場是否已存在
                        cursor.execute(
                            "SELECT airport_id FROM airports WHERE airport_id = %s",
                            (airport_id,)
                        )
                        existing = cursor.fetchone()
                        
                        # 準備機場數據
                        name_zh = airport.get('name_zh', airport.get('name', ''))
                        name_en = airport.get('name_en', airport.get('name', ''))
                        city = airport.get('city', '')
                        city_en = airport.get('city_en', airport.get('city', ''))
                        country = airport.get('country', '')
                        timezone = airport.get('timezone', 'UTC')
                        contact_info = airport.get('contact_info', '')
                        website_url = airport.get('website', '')
                        
                        if existing:
                            # 更新現有機場
                            cursor.execute("""
                                UPDATE airports SET 
                                    name_zh = %s,
                                    name_en = %s,
                                    city = %s,
                                    city_en = %s,
                                    country = %s,
                                    timezone = %s,
                                    contact_info = %s,
                                    website_url = %s
                                WHERE airport_id = %s
                            """, (
                                name_zh, name_en, city, city_en, country,
                                timezone, contact_info, website_url, airport_id
                            ))
                            updated += 1
                            logger.debug(f"已更新機場: {airport_id} ({name_zh})")
                        else:
                            # 插入新機場
                            cursor.execute("""
                                INSERT INTO airports (
                                    airport_id, name_zh, name_en, city, city_en,
                                    country, timezone, contact_info, website_url
                                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """, (
                                airport_id, name_zh, name_en, city, city_en,
                                country, timezone, contact_info, website_url
                            ))
                            inserted += 1
                            logger.debug(f"已新增機場: {airport_id} ({name_zh})")
                    
                    except Exception as e:
                        errors += 1
                        logger.error(f"處理機場 {airport.get('iata_code', 'Unknown')} 時出錯: {str(e)}")
                        # 對單個機場的錯誤不影響整體事務
                        conn.rollback()
                
                # 提交事務
                conn.commit()
                
                # 重新加載翻譯映射
                self.load_translation_maps()
                
                result = {
                    "total": len(airports),
                    "inserted": inserted,
                    "updated": updated,
                    "skipped": skipped,
                    "errors": errors
                }
                logger.info(f"機場同步結果: 總數 {len(airports)}, 新增 {inserted}, 更新 {updated}, 跳過 {skipped}, 錯誤 {errors}")
                return result
                
        except Exception as e:
            logger.error(f"同步機場數據時發生錯誤: {str(e)}")
            conn.rollback()
            return {"total": len(airports), "inserted": 0, "updated": 0, "skipped": 0, "errors": len(airports), "error": str(e)}
        finally:
            conn.close()
    
    def sync_airlines(self, airlines: List[Dict]) -> Dict:
        """
        同步航空公司數據到數據庫
        
        Args:
            airlines: 航空公司數據列表
            
        Returns:
            同步結果統計
        """
        if not airlines:
            return {"total": 0, "inserted": 0, "updated": 0, "skipped": 0, "error": "沒有提供航空公司數據"}
        
        inserted = 0
        updated = 0
        skipped = 0
        errors = 0
        
        conn = self.get_db_connection()
        try:
            with conn.cursor() as cursor:
                for airline in airlines:
                    try:
                        # 獲取必要信息
                        airline_id = airline.get('iata_code') or airline.get('iata')
                        if not airline_id:
                            logger.warning(f"跳過沒有IATA代碼的航空公司: {airline.get('name', 'Unknown')}")
                            skipped += 1
                            continue
                        
                        # 檢查航空公司是否已存在
                        cursor.execute(
                            "SELECT airline_id FROM airlines WHERE airline_id = %s",
                            (airline_id,)
                        )
                        existing = cursor.fetchone()
                        
                        # 準備航空公司數據
                        name_zh = airline.get('name_zh', airline.get('name', ''))
                        name_en = airline.get('name_en', airline.get('name', ''))
                        website = airline.get('website', '')
                        contact_phone = airline.get('contact_phone', '')
                        is_domestic = airline.get('is_domestic', False)
                        
                        if existing:
                            # 更新現有航空公司
                            cursor.execute("""
                                UPDATE airlines SET 
                                    name_zh = %s,
                                    name_en = %s,
                                    website = %s,
                                    contact_phone = %s,
                                    is_domestic = %s
                                WHERE airline_id = %s
                            """, (
                                name_zh, name_en, website, contact_phone, is_domestic, airline_id
                            ))
                            updated += 1
                            logger.debug(f"已更新航空公司: {airline_id} ({name_zh})")
                        else:
                            # 插入新航空公司
                            cursor.execute("""
                                INSERT INTO airlines (
                                    airline_id, name_zh, name_en, website,
                                    contact_phone, is_domestic
                                ) VALUES (%s, %s, %s, %s, %s, %s)
                            """, (
                                airline_id, name_zh, name_en, website,
                                contact_phone, is_domestic
                            ))
                            inserted += 1
                            logger.debug(f"已新增航空公司: {airline_id} ({name_zh})")
                    
                    except Exception as e:
                        errors += 1
                        logger.error(f"處理航空公司 {airline.get('iata_code', 'Unknown')} 時出錯: {str(e)}")
                        # 對單個航空公司的錯誤不影響整體事務
                        conn.rollback()
                
                # 提交事務
                conn.commit()
                
                # 重新加載翻譯映射
                self.load_translation_maps()
                
                result = {
                    "total": len(airlines),
                    "inserted": inserted,
                    "updated": updated,
                    "skipped": skipped,
                    "errors": errors
                }
                logger.info(f"航空公司同步結果: 總數 {len(airlines)}, 新增 {inserted}, 更新 {updated}, 跳過 {skipped}, 錯誤 {errors}")
                return result
                
        except Exception as e:
            logger.error(f"同步航空公司數據時發生錯誤: {str(e)}")
            conn.rollback()
            return {"total": len(airlines), "inserted": 0, "updated": 0, "skipped": 0, "errors": len(airlines), "error": str(e)}
        finally:
            conn.close()


def main():
    """主函數，處理命令行參數並執行相應操作"""
    import argparse
    from datetime import datetime
    
    parser = argparse.ArgumentParser(description='航班資料庫同步工具')
    parser.add_argument('--conn', help='數據庫連接字符串（若未提供則從環境變量獲取）')
    
    subparsers = parser.add_subparsers(dest='command', help='指令')
    
    # 航班同步指令
    flights_parser = subparsers.add_parser('flights', help='同步特定航線的航班資料到資料庫')
    flights_parser.add_argument('--departure', '-d', required=True, help='出發機場 IATA 代碼')
    flights_parser.add_argument('--arrival', '-a', required=True, help='目的機場 IATA 代碼')
    flights_parser.add_argument('--date', default=datetime.now().strftime('%Y-%m-%d'), 
                               help='查詢日期（YYYY-MM-DD 格式），預設為今天')
    flights_parser.add_argument('--days', type=int, default=1, help='查詢天數，預設為 1')
    
    # 熱門航線同步指令
    popular_parser = subparsers.add_parser('popular', help='同步熱門航線資料到資料庫')
    popular_parser.add_argument('--date', default=datetime.now().strftime('%Y-%m-%d'), 
                               help='查詢日期（YYYY-MM-DD 格式），預設為今天')
    popular_parser.add_argument('--days', type=int, default=1, help='查詢天數，預設為 1')
    
    # 台灣機場航班同步指令
    taiwan_parser = subparsers.add_parser('taiwan', help='同步所有台灣機場出發的航班資料到資料庫')
    taiwan_parser.add_argument('--date', default=datetime.now().strftime('%Y-%m-%d'), 
                               help='查詢日期（YYYY-MM-DD 格式），預設為今天')
    taiwan_parser.add_argument('--days', type=int, default=1, help='查詢天數，預設為 1')
    
    args = parser.parse_args()
    
    # 初始化資料庫同步管理器
    db_sync = DatabaseSyncManager(args.conn)
    
    # 根據指令執行相應操作
    if args.command == 'flights':
        logger.info(f"正在同步 {args.departure} -> {args.arrival} 航班到資料庫（{args.date} 起 {args.days} 天）")
        count = db_sync.sync_flights(args.departure, args.arrival, args.date, args.days)
        logger.info(f"完成航班同步，成功導入 {count} 個航班到資料庫")
    
    elif args.command == 'popular':
        logger.info(f"正在同步熱門航線到資料庫（{args.date} 起 {args.days} 天）")
        count = db_sync.sync_popular_routes(args.date, args.days)
        logger.info(f"完成熱門航線同步，成功導入 {count} 個航班到資料庫")
    
    elif args.command == 'taiwan':
        logger.info(f"正在同步台灣機場出發航班到資料庫（{args.date} 起 {args.days} 天）")
        count = db_sync.sync_taiwan_flights(args.date, args.days)
        logger.info(f"完成台灣機場航班同步，成功導入 {count} 個航班到資料庫")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main() 