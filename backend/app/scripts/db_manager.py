#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
資料庫管理模組 - 處理API資料與資料庫之間的操作
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
logger = logging.getLogger('db_manager')

# 嘗試導入常量
try:
    from app.scripts.constants import TAIWAN_AIRPORTS, TARGET_AIRLINES
except ImportError:
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.append(current_dir)
        from constants import TAIWAN_AIRPORTS, TARGET_AIRLINES
    except ImportError:
        logger.warning("無法導入常量模組，使用預設值")
        TAIWAN_AIRPORTS = [
            'TPE', 'TSA', 'KHH', 'RMQ', 'TNN', 'CYI', 'HUN', 'TTT', 
            'KNH', 'MZG', 'LZN', 'MFK', 'KYD', 'GNI', 'WOT'
        ]
        TARGET_AIRLINES = [
            'AE', 'B7', 'BR', 'CI', 'CX', 'DA', 'IT', 'JL', 'JX', 'OZ'
        ]

# 嘗試導入其他必要模組
try:
    from .sync_manager import ApiSyncManager
    from app.clients.flightstats_client import FlightStatsApiClient
    from app.clients.tdx_client import TdxApiClient
except ImportError as e:
    logger.error(f"無法導入必要的客戶端模組: {str(e)}")
    try:
        # 嘗試使用不同的相對路徑導入方式
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.append(current_dir)
        from sync_manager import ApiSyncManager
        from app.clients.flightstats_client import FlightStatsApiClient
        from app.clients.tdx_client import TdxApiClient
    except ImportError as e2:
        logger.error(f"嘗試備用導入方式也失敗: {str(e2)}")
        ApiSyncManager = None
        FlightStatsApiClient = None
        TdxApiClient = None

# 匯入UUID模組
try:
    from uuid import UUID
except ImportError:
    logger.warning("無法匯入UUID模組，將使用字串作為替代")

class DbManager:
    """數據庫管理器 - 負責管理API數據與資料庫之間的操作"""
    
    def __init__(self, conn_str=None):
        """
        初始化數據庫管理器
        
        Args:
            conn_str: 數據庫連接字符串，若不提供則嘗試從環境變量讀取
        """
        self.conn_str = conn_str or self._get_conn_str_from_env()
        
        # 初始化API客戶端
        self.api_sync_manager = ApiSyncManager() if ApiSyncManager else None
        
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
        
    def _get_conn_str_from_env(self):
        """從環境變量獲取數據庫連接字符串"""
        # 優先使用 DATABASE_URL 環境變數
        database_url = os.environ.get("DATABASE_URL")
        if database_url:
            logger.info("使用 DATABASE_URL 環境變數建立資料庫連接")
            return database_url
            
        # 嘗試從環境變量讀取數據庫配置
        db_host = os.environ.get("DB_HOST")
        db_port = os.environ.get("DB_PORT", "5432")
        db_name = os.environ.get("DB_NAME", "flight_integration")
        db_user = os.environ.get("DB_USER")
        db_password = os.environ.get("DB_PASSWORD")
        
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
        
        # 計數器以記錄過濾原因
        airline_missing_count = 0
        departure_missing_count = 0
        arrival_missing_count = 0
        
        for flight in flights:
            airline_code = flight.get('airline_code')
            departure_airport = flight.get('departure_airport')
            arrival_airport = flight.get('arrival_airport')
            
            # 翻譯航班數據中的名稱
            flight = self.translate_flight_data(flight)
            
            # 詳細記錄正在處理的航班
            logger.debug(f"處理航班: {flight.get('flight_number')} - {departure_airport} -> {arrival_airport}")
            
            # 放寬過濾條件：只要航空公司和出發機場存在，就保留航班
            if airline_code in airlines_map and departure_airport in airports_map:
                # 添加ID信息到航班數據
                flight['airline_id'] = airlines_map[airline_code]
                flight['departure_airport_id'] = airports_map[departure_airport]
                
                # 如果到達機場不存在，使用代碼作為ID
                if arrival_airport in airports_map:
                    flight['arrival_airport_id'] = airports_map[arrival_airport]
                else:
                    flight['arrival_airport_id'] = arrival_airport
                    arrival_missing_count += 1
                    logger.warning(f"使用到達機場代碼 {arrival_airport} 作為ID，因為在資料庫中找不到此機場")
                
                filtered_flights.append(flight)
            else:
                missing = []
                if airline_code not in airlines_map:
                    missing.append(f"航空公司 {airline_code}")
                    airline_missing_count += 1
                if departure_airport not in airports_map:
                    missing.append(f"出發機場 {departure_airport}")
                    departure_missing_count += 1
                
                logger.warning(f"跳過航班 {flight.get('flight_number')}，因為缺少: {', '.join(missing)}")
        
        # 記錄過濾統計
        logger.info(f"航班過濾結果: 總數 {len(flights)}, 保留 {len(filtered_flights)}")
        logger.info(f"過濾原因統計: 缺少航空公司 {airline_missing_count}, 缺少出發機場 {departure_missing_count}, 缺少到達機場(但已納入) {arrival_missing_count}")
        
        return filtered_flights
    
    def import_flights_to_database(self, flights: List[Dict]) -> Dict:
        """
        將航班數據導入到數據庫
        
        Args:
            flights: 航班數據列表
            
        Returns:
            導入結果統計
        """
        if not flights:
            return {"total": 0, "inserted": 0, "updated": 0, "skipped": 0, "errors": 0}
        
        inserted = 0
        updated = 0
        skipped = 0
        errors = 0
        
        conn = self.get_db_connection()
        try:
            with conn.cursor() as cursor:
                for flight in flights:
                    try:
                        # 檢查必要欄位
                        flight_number = flight.get('flight_number')
                        airline_id = flight.get('airline_id')
                        departure_airport_id = flight.get('departure_airport_id')
                        arrival_airport_id = flight.get('arrival_airport_id')
                        scheduled_departure = flight.get('scheduled_departure')
                        scheduled_arrival = flight.get('scheduled_arrival')
                        
                        # 檢查並詳細記錄缺少的字段
                        missing_fields = []
                        if not flight_number:
                            missing_fields.append('flight_number')
                        if not airline_id:
                            missing_fields.append('airline_id')
                        if not departure_airport_id:
                            missing_fields.append('departure_airport_id')
                        if not arrival_airport_id:
                            missing_fields.append('arrival_airport_id')
                        if not scheduled_departure:
                            missing_fields.append('scheduled_departure')
                        if not scheduled_arrival:
                            missing_fields.append('scheduled_arrival')
                        
                        if missing_fields:
                            # 輸出更詳細的錯誤信息
                            logger.warning(f"跳過航班 {flight.get('flight_number', '未知')}, 缺少必要欄位: {', '.join(missing_fields)}")
                            # 打印部分航班數據以進行診斷
                            logger.debug(f"航班數據片段: {self._debug_flight_data(flight)}")
                            skipped += 1
                            continue
                        
                        # 創建或更新航班
                        cursor.execute("""
                            SELECT flight_id FROM flights
                            WHERE flight_number = %s AND scheduled_departure::date = %s::date
                        """, (flight_number, scheduled_departure))
                        existing = cursor.fetchone()
                        
                        # 生成唯一航班ID - 使用UUID物件而非字串
                        if not existing:
                            flight_id = uuid.uuid4()
                        else:
                            # 如果現有ID是字串，轉換為UUID物件
                            try:
                                flight_id = existing[0] if isinstance(existing[0], uuid.UUID) else uuid.UUID(existing[0])
                            except (ValueError, TypeError):
                                logger.warning(f"現有flight_id格式不正確: {existing[0]}，將生成新ID")
                                flight_id = uuid.uuid4()
                        
                        # 準備數據
                        status = flight.get('status', '')
                        actual_departure = flight.get('actual_departure')
                        actual_arrival = flight.get('actual_arrival')
                        terminal_departure = flight.get('terminal_departure', '')
                        terminal_arrival = flight.get('terminal_arrival', '')
                        gate_departure = flight.get('gate_departure', '')
                        gate_arrival = flight.get('gate_arrival', '')
                        baggage_claim = flight.get('baggage_claim', '')
                        data_source = flight.get('data_source', 'API')
                        updated_at = datetime.now().isoformat()
                        price_economy = flight.get('price_economy')
                        price_business = flight.get('price_business')
                        price_first = flight.get('price_first')
                        
                        if existing:
                            # 更新現有航班
                            cursor.execute("""
                                UPDATE flights SET 
                                    airline_id = %s,
                                    departure_airport_id = %s,
                                    arrival_airport_id = %s,
                                    scheduled_departure = %s,
                                    scheduled_arrival = %s,
                                    actual_departure = %s,
                                    actual_arrival = %s,
                                    status = %s,
                                    terminal_departure = %s,
                                    terminal_arrival = %s,
                                    gate_departure = %s,
                                    gate_arrival = %s,
                                    baggage_claim = %s,
                                    data_source = %s,
                                    updated_at = %s
                                WHERE flight_id = %s
                            """, (
                                airline_id, departure_airport_id, arrival_airport_id, 
                                scheduled_departure, scheduled_arrival, actual_departure, actual_arrival,
                                status, terminal_departure, terminal_arrival, gate_departure, gate_arrival,
                                baggage_claim, data_source, updated_at, flight_id
                            ))
                            updated += 1
                            logger.debug(f"已更新航班: {flight_number} ({flight_id})")
                            
                            # 如果有票價資訊，更新票價
                            if any([price_economy, price_business, price_first]):
                                self._update_flight_prices(cursor, flight_id, price_economy, price_business, price_first)
                        else:
                            # 插入新航班
                            cursor.execute("""
                                INSERT INTO flights (
                                    flight_id, flight_number, airline_id, departure_airport_id,
                                    arrival_airport_id, scheduled_departure, scheduled_arrival,
                                    actual_departure, actual_arrival, status,
                                    terminal_departure, terminal_arrival, gate_departure,
                                    gate_arrival, baggage_claim, data_source, created_at, updated_at
                                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """, (
                                flight_id, flight_number, airline_id, departure_airport_id,
                                arrival_airport_id, scheduled_departure, scheduled_arrival,
                                actual_departure, actual_arrival, status,
                                terminal_departure, terminal_arrival, gate_departure,
                                gate_arrival, baggage_claim, data_source, updated_at, updated_at
                            ))
                            inserted += 1
                            logger.debug(f"已新增航班: {flight_number} ({flight_id})")
                            
                            # 如果有票價資訊，新增票價
                            if any([price_economy, price_business, price_first]):
                                self._add_flight_prices(cursor, flight_id, price_economy, price_business, price_first)
                        
                    except Exception as e:
                        errors += 1
                        logger.error(f"處理航班 {flight.get('flight_number', 'Unknown')} 時出錯: {str(e)}")
                        # 單個航班處理錯誤不影響整體事務
                        conn.rollback()
                
                # 提交事務
                conn.commit()
                
                result = {
                    "total": len(flights),
                    "inserted": inserted,
                    "updated": updated,
                    "skipped": skipped,
                    "errors": errors
                }
                logger.info(f"航班導入結果: 總數 {len(flights)}, 新增 {inserted}, 更新 {updated}, 跳過 {skipped}, 錯誤 {errors}")
                return result
                
        except Exception as e:
            logger.error(f"導入航班數據時發生錯誤: {str(e)}")
            conn.rollback()
            return {"total": len(flights), "inserted": 0, "updated": 0, "skipped": 0, "errors": len(flights), "error": str(e)}
        finally:
            conn.close()
    
    def _add_flight_prices(self, cursor, flight_id, price_economy, price_business, price_first):
        """添加航班票價"""
        # 使用UUID物件而非字串
        price_id = uuid.uuid4()
        created_at = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO ticket_prices (
                price_id, flight_id, economy_price, business_price,
                first_price, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            price_id, flight_id, price_economy, price_business,
            price_first, created_at
        ))
    
    def _update_flight_prices(self, cursor, flight_id, price_economy, price_business, price_first):
        """更新航班票價"""
        created_at = datetime.now().isoformat()
        
        # 檢查是否已經有票價記錄
        cursor.execute("""
            SELECT price_id FROM ticket_prices
            WHERE flight_id = %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (flight_id,))
        
        existing = cursor.fetchone()
        
        if existing:
            # 更新現有票價
            cursor.execute("""
                UPDATE ticket_prices SET
                    economy_price = %s,
                    business_price = %s,
                    first_price = %s
                WHERE price_id = %s
            """, (
                price_economy, price_business, price_first, existing[0]
            ))
        else:
            # 添加新票價
            self._add_flight_prices(cursor, flight_id, price_economy, price_business, price_first) 
    
    def _debug_flight_data(self, flight: Dict) -> Dict:
        """
        返回一個精簡版的航班數據用於調試目的
        
        Args:
            flight: 完整航班數據
            
        Returns:
            包含關鍵字段的精簡版航班數據
        """
        # 創建一個新的字典，只包含關鍵字段
        debug_data = {}
        key_fields = [
            'flight_number', 'airline_code', 'airline_id', 
            'departure_airport', 'departure_airport_id',
            'arrival_airport', 'arrival_airport_id',
            'scheduled_departure', 'scheduled_arrival',
            'data_source'
        ]
        
        for field in key_fields:
            if field in flight:
                debug_data[field] = flight[field]
        
        # 如果數據量太大，可以增加更多關鍵字段
        return debug_data
    
    def debug_print_flight_data(self, flights: List[Dict], sample_size: int = 1) -> None:
        """
        打印航班數據樣本以幫助調試
        
        Args:
            flights: 航班數據列表
            sample_size: 要打印的樣本數量
        """
        if not flights:
            logger.info("沒有航班數據可供調試")
            return
        
        for i, flight in enumerate(flights[:sample_size]):
            logger.info(f"航班樣本 {i+1}:")
            logger.info(json.dumps(flight, ensure_ascii=False, indent=2, default=str)) 