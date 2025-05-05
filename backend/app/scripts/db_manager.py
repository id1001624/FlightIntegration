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

# *** 導入 date_utils ***
from ..utils.date_utils import parse_datetime, format_datetime

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
except ImportError as e:
    logger.error(f"無法導入必要的客戶端模組: {str(e)}")
    try:
        # 嘗試使用不同的相對路徑導入方式
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.append(current_dir)
        from sync_manager import ApiSyncManager
        from app.clients.flightstats_client import FlightStatsApiClient
    except ImportError as e2:
        logger.error(f"嘗試備用導入方式也失敗: {str(e2)}")
        ApiSyncManager = None
        FlightStatsApiClient = None

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
        # 優先使用 SQLALCHEMY_DATABASE_URI 環境變數
        database_uri = os.environ.get("SQLALCHEMY_DATABASE_URI")
        if database_uri:
            logger.info("使用 SQLALCHEMY_DATABASE_URI 環境變數建立資料庫連接")
            return database_uri

        # 如果 SQLALCHEMY_DATABASE_URI 不存在，則記錄錯誤並退出
        # 因為這是預期的主要配置方式
        logger.error("環境變數 SQLALCHEMY_DATABASE_URI 未設置！")
        sys.exit(1)
    
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
    
    def import_flights_to_database(self, flights: List[Dict]) -> List[Dict]:
        """
        將格式化後的航班數據導入數據庫，處理重複數據，並返回包含穩定DB flight_id 的列表

        Args:
            flights: 從ApiSyncManager傳來的航班列表 (不包含 flight_id)

        Returns:
            處理後的航班列表，每個字典包含從數據庫獲取的穩定 flight_id
            或者在失敗時返回空列表
        """
        if not flights:
            logger.warning("沒有提供航班數據進行導入")
            return []

        conn = None
        processed_flights_with_id = [] # 新增：用於存儲帶 flight_id 的處理後航班
        update_count = 0
        insert_count = 0
        error_count = 0
        skipped_count = 0 # 新增：初始化 skipped_count

        try:
            conn = self.get_db_connection()
            with conn.cursor() as cursor:
                logger.info(f"準備將 {len(flights)} 筆航班數據導入數據庫...")

                # 使用集合來跟踪處理過的航班鍵，避免重複處理
                processed_flight_keys: Set[str] = set()

                for flight in flights:
                    try:
                        # 創建唯一鍵，例如：航班號 + 出發時間日期部分
                        scheduled_departure = flight.get('scheduled_departure')
                        if not scheduled_departure:
                            logger.warning(f"跳過航班，缺少 scheduled_departure: {flight.get('flight_number')}")
                            continue
                        
                        # 確保 scheduled_departure 是 datetime 對象
                        if isinstance(scheduled_departure, str):
                            departure_dt = parse_datetime(scheduled_departure) # 假設 parse_datetime 返回 datetime
                            if not departure_dt:
                                 logger.warning(f"無法解析 scheduled_departure: {scheduled_departure}, 跳過航班: {flight.get('flight_number')}")
                                 continue
                            departure_date_str = departure_dt.strftime('%Y-%m-%d')
                        elif isinstance(scheduled_departure, datetime):
                            departure_date_str = scheduled_departure.strftime('%Y-%m-%d')
                            departure_dt = scheduled_departure # 直接使用 datetime 對象
                        else:
                             logger.warning(f"未知的 scheduled_departure 類型: {type(scheduled_departure)}, 跳過航班: {flight.get('flight_number')}")
                             continue
                            
                        flight_key = f"{flight.get('flight_number', '')}-{departure_date_str}"
                        
                        # 如果這個鍵已經處理過，跳過
                        if flight_key in processed_flight_keys:
                            continue
                        
                        # 添加到已處理集合
                        processed_flight_keys.add(flight_key)
                        
                        # 提取其他欄位，使用 .get() 並提供默認值 None
                        airline_id = flight.get('airline_id')
                        flight_number = flight.get('flight_number')
                        departure_airport_id = flight.get('departure_airport_id')
                        arrival_airport_id = flight.get('arrival_airport_id')
                        scheduled_arrival = flight.get('scheduled_arrival')
                        # 新增：獲取 aircraft
                        aircraft = flight.get('aircraft') 
                        # 航廈可能為 None
                        departure_terminal = flight.get('departure_terminal')
                        arrival_terminal = flight.get('arrival_terminal')
                        
                        # 檢查必要的 ID 是否存在
                        if not all([airline_id, flight_number, departure_airport_id, arrival_airport_id]):
                            logger.warning(f"跳過航班，缺少必要的 ID 資訊: {flight}")
                            continue

                        # 查找現有航班
                        cursor.execute("""
                            SELECT flight_id FROM flights 
                            WHERE flight_number = %s AND departure_airport_id = %s AND arrival_airport_id = %s AND scheduled_departure = %s
                        """, (flight_number, departure_airport_id, arrival_airport_id, departure_dt))
                        existing_flight = cursor.fetchone()
                        
                        # 生成UUID
                        flight_id_str = str(uuid.uuid4())

                        # 獲取價格信息 (假設在 flight 字典中) - 修正縮排
                        price_economy = flight.get('price_economy')
                        price_business = flight.get('price_business')
                        price_first = flight.get('price_first')

                        if existing_flight:
                            # 更新現有航班 (只更新特定字段，例如 aircraft, terminal)
                            flight_id_str = str(existing_flight[0]) # 使用現有的UUID
                            update_parts = []
                            update_values = []
                            # 如果提供了 aircraft，則更新
                            if aircraft is not None:
                                update_parts.append("aircraft = %s")
                                update_values.append(aircraft)
                            # 如果提供了 departure_terminal，則更新 (即使是 None)
                            if 'departure_terminal' in flight:
                                update_parts.append("departure_terminal = %s")
                                update_values.append(departure_terminal)
                             # 如果提供了 arrival_terminal，則更新 (即使是 None)
                            if 'arrival_terminal' in flight:
                                update_parts.append("arrival_terminal = %s")
                                update_values.append(arrival_terminal)
                            # 如果 scheduled_arrival 提供了，也更新
                            if scheduled_arrival is not None:
                                 update_parts.append("scheduled_arrival = %s")
                                 update_values.append(scheduled_arrival)
                            
                            if update_parts:
                                update_sql = f"UPDATE flights SET {', '.join(update_parts)}, updated_at = NOW() WHERE flight_id = %s"
                                update_values.append(flight_id_str)
                                cursor.execute(update_sql, tuple(update_values))
                                update_count += 1 # 統一使用 update_count
                                logger.debug(f"更新航班: {flight_number} ({flight_id_str})")
                            else:
                                skipped_count += 1 # 沒有需要更新的字段
                                
                            # 更新或添加票價信息
                            self._update_flight_prices(cursor, flight_id_str, price_economy, price_business, price_first)
                        else:
                            # 插入新航班
                            insert_sql = """
                            INSERT INTO flights (
                                flight_id, flight_number, airline_id, 
                                departure_airport_id, arrival_airport_id, 
                                scheduled_departure, scheduled_arrival, 
                                aircraft, departure_terminal, arrival_terminal, 
                                created_at, updated_at
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                            """
                            cursor.execute(insert_sql, (
                                flight_id_str, flight_number, airline_id, 
                                departure_airport_id, arrival_airport_id, 
                                departure_dt, scheduled_arrival, 
                                aircraft, departure_terminal, arrival_terminal
                            ))
                            insert_count += 1 # 統一使用 insert_count
                            logger.debug(f"插入新航班: {flight_number} ({flight_id_str})")
                            
                            # 添加票價信息
                            self._add_flight_prices(cursor, flight_id_str, price_economy, price_business, price_first)
                            
                        # 將成功處理的數據（更新或插入）添加到列表，並包含 flight_id
                        processed_flight_data = flight.copy() # 複製原始數據
                        processed_flight_data['flight_id'] = flight_id_str # 添加/確保 flight_id 存在
                        processed_flights_with_id.append(processed_flight_data) 

                    except Exception as e:
                        conn.rollback() # 回滾當前事務中的單個錯誤
                        logger.error(f"處理單個航班數據時出錯: {flight}, 錯誤: {str(e)}")
                        error_count += 1 # 增加錯誤計數
                        continue # 繼續處理下一個航班
                        
                # 提交所有成功的更改
                conn.commit()
                logger.info(f"航班數據導入完成。新增: {insert_count}, 更新: {update_count}, 跳過: {skipped_count}, 錯誤: {error_count}")
                
        except Exception as e:
            logger.error(f"導入航班數據到數據庫時發生嚴重錯誤: {str(e)}")
            if conn:
                conn.rollback()
            return [] # 返回空列表表示失敗
        finally:
            if conn:
                conn.close()
                
        return processed_flights_with_id # 返回包含穩定 DB flight_id 的列表

    def _add_flight_prices(self, cursor, flight_id_str: str, price_economy, price_business, price_first):
        """為新航班添加不同艙等的票價"""
        if price_economy is None and price_business is None and price_first is None:
            logger.debug(f"航班 {flight_id_str} 沒有提供任何價格信息，跳過添加票價")
            return # 如果沒有價格信息，不執行插入

        # 使用UUID物件而非字串來生成 price_id
        price_id = uuid.uuid4()

        # 插入經濟艙價格記錄
        cursor.execute("""
            INSERT INTO ticket_prices (
                price_id, flight_id, class_type, economy_price, business_price, first_price, available_seats, is_test_data
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            str(price_id), flight_id_str, '經濟', price_economy, price_business, price_first, 
            50, False  # 預設50個座位，非測試資料
        ))
        logger.debug(f"為航班 {flight_id_str} 添加了票價: 經濟:{price_economy}, 商務:{price_business}, 頭等:{price_first}")

    def _update_flight_prices(self, cursor, flight_id_str: str, price_economy, price_business, price_first):
        """更新航班票價，接收字串格式的 flight_id"""
        if price_economy is None and price_business is None and price_first is None:
             logger.debug(f"航班 {flight_id_str} 沒有提供任何價格信息，跳過更新票價")
             return # 如果沒有價格信息，不執行更新

        # 檢查是否已經有票價記錄
        cursor.execute("""
            SELECT price_id FROM ticket_prices
            WHERE flight_id = %s
            LIMIT 1
        """, (flight_id_str,))

        existing = cursor.fetchone()

        if existing:
            # 更新現有票價
            cursor.execute("""
                UPDATE ticket_prices SET
                    economy_price = %s,
                    business_price = %s,
                    first_price = %s,
                    price_updated_at = NOW()
                WHERE price_id = %s
            """, (
                price_economy, price_business, price_first,
                existing[0]
            ))
            logger.debug(f"更新航班 {flight_id_str} 的票價: 經濟:{price_economy}, 商務:{price_business}, 頭等:{price_first}")
        else:
            # 添加新票價
            self._add_flight_prices(cursor, flight_id_str, price_economy, price_business, price_first)
    
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