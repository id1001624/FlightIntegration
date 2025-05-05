#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
航班數據同步腳本 - 合併了TDX和FlightStats的API調用和數據庫同步功能
可直接運行此腳本完成所有API調用和數據庫更新
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime, timedelta
import psycopg2
import time
from dotenv import load_dotenv, find_dotenv
from collections import defaultdict

# --- 在導入應用模塊前加載 .env 文件 ---
dotenv_path = find_dotenv(filename='.env', raise_error_if_not_found=False, usecwd=True)
# 嘗試從 backend 目錄查找 .env (如果腳本在 scripts 中執行或從根目錄以 -m 執行)
if not dotenv_path:
    try:
        # 判斷當前是否以 -m 模式從根目錄執行
        # 如果是，當前工作目錄應為 FlightIntegration
        # 如果直接執行，工作目錄可能不同
        cwd = os.getcwd()
        # 假設項目根目錄名為 FlightIntegration
        if os.path.basename(cwd) == 'FlightIntegration': 
            backend_path = os.path.join(cwd, 'backend')
        else:
            # 嘗試從腳本位置向上查找 backend
            scripts_dir = os.path.dirname(__file__)
            app_dir = os.path.dirname(scripts_dir)
            backend_path = os.path.dirname(app_dir)
            
        dotenv_path_alt = os.path.join(backend_path, '.env')
        if os.path.exists(dotenv_path_alt):
            dotenv_path = dotenv_path_alt
    except Exception:
        pass # 忽略查找過程中的錯誤

if dotenv_path and os.path.exists(dotenv_path):
    print(f"[sync_flight_data] 找到並加載 .env 文件: {dotenv_path}")
    load_dotenv(dotenv_path=dotenv_path, override=True) 
else:
    print("[sync_flight_data] 警告: 未找到 .env 文件於預期位置，將依賴系統環境變數。")
# --------------------------------------

# -- 路徑計算更新 --
# current_dir: backend/app/scripts/
current_dir = os.path.dirname(os.path.abspath(__file__))
# app_dir: backend/app/
app_dir = os.path.dirname(current_dir)
# backend_dir: backend/
backend_dir = os.path.dirname(app_dir)
# project_root_dir: (專案根目錄)
project_root_dir = os.path.dirname(backend_dir)

# 將 backend 目錄添加到 sys.path，以便導入 app.*
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# -- 日誌路徑更新 --
# logs_dir: backend/logs/
logs_dir = os.path.join(backend_dir, 'logs')
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

# 配置日誌 - 使用完整的handler設置而非basicConfig
log_file = os.path.join(logs_dir, 'app.log')

# 創建logger
logger = logging.getLogger('sync_flight_data')
logger.setLevel(logging.INFO)

# 防止日誌重複
logger.handlers = []

# 創建文件處理器
file_handler = logging.FileHandler(log_file, 'a', encoding='utf-8')
file_handler.setLevel(logging.INFO)

# 創建控制台處理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# 創建格式化器
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# 添加處理器到logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# -- 模塊導入更新 --
# 優先使用絕對導入 (從 app 開始)，保留相對導入作為備用
try:
    logger.info("嘗試使用絕對路徑導入 (app.scripts.*)...")
    from app.scripts.sync_manager import ApiSyncManager
    from app.scripts.db_manager import DbManager
    from app.scripts.constants import TAIWAN_AIRPORTS, TARGET_AIRLINES
    logger.info("成功使用絕對路徑導入模塊")
except ImportError as e1:
    logger.warning(f"絕對導入失敗: {e1}。嘗試使用相對路徑導入...")
    try:
        from .sync_manager import ApiSyncManager
        from .db_manager import DbManager
        from .constants import TAIWAN_AIRPORTS, TARGET_AIRLINES
        logger.info("成功使用相對路徑導入客戶端")
    except ImportError as e2:
        logger.error(f"相對導入也失敗: {e2}", exc_info=True)
        logger.critical("無法導入必要模組，請檢查 sync_manager.py 和 db_manager.py 是否存在於 scripts 目錄下，程序退出")
        sys.exit(1)


class FlightDataSyncTool:
    """航班數據同步工具，整合API調用和數據庫同步功能"""
    
    def __init__(self):
        """初始化同步工具"""
        # 檢查環境變數是否設置
        required_vars = []
        
        # 首先嘗試從.env加載環境變數
        self._load_env_from_dotenv()
        
        # 檢查是否有資料庫連接 URI (使用 SQLALCHEMY_DATABASE_URI)
        has_db_uri = bool(os.getenv('SQLALCHEMY_DATABASE_URI'))
        
        # 如果沒有完整的 URI，才需要檢查單獨的資料庫環境變數
        if not has_db_uri:
            required_vars.extend(['DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT', 'DB_NAME'])
        
        # 檢查 API 相關環境變數
        required_vars.extend([
            'TDX_CLIENT_ID', 'TDX_CLIENT_SECRET',
            'FLIGHTSTATS_APP_ID', 'FLIGHTSTATS_APP_KEY'
        ])
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            logger.error(f"加載後仍缺少以下環境變數: {', '.join(missing_vars)}")
            logger.error("請確保.env文件中包含所有必要的環境變數 (應位於 backend/ 或專案根目錄)")
            sys.exit(1)
        
        # 初始化API同步管理器
        try:
            self.api_manager = ApiSyncManager()
            logger.info("API同步管理器初始化成功")
        except Exception as e:
            logger.error(f"API同步管理器初始化失敗: {str(e)}")
            sys.exit(1)
        
        # 初始化數據庫同步管理器
        try:
            self.db_manager = DbManager()
            logger.info("數據庫同步管理器初始化成功")
        except Exception as e:
            logger.error(f"數據庫同步管理器初始化失敗: {str(e)}")
            sys.exit(1)
    
    def _load_env_from_dotenv(self):
        """從.env文件加載環境變數"""
        try:
            # -- .env 搜索路徑更新 --
            # 優先 backend 目錄，其次是專案根目錄
            dotenv_paths = [
                os.path.join(backend_dir, '.env'),
                os.path.join(project_root_dir, '.env')
            ]
            
            for dotenv_path in dotenv_paths:
                if os.path.exists(dotenv_path):
                    logger.info(f"從 {dotenv_path} 加載環境變數")
                    with open(dotenv_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            # 跳過註釋和空行
                            if not line or line.startswith('#'):
                                continue
                            
                            # 解析環境變數
                            if '=' in line:
                                key, value = line.split('=', 1)
                                # 去除引號
                                value = value.strip('\'"')
                                # 設置環境變數
                                os.environ[key.strip()] = value
                    
                    logger.info("環境變數加載完成")
                    return
            
            logger.warning(f"未在 {backend_dir} 或 {project_root_dir} 找到 .env 文件")
        except Exception as e:
            logger.error(f"加載環境變數時發生錯誤: {str(e)}")
    
    def test_api_connectivity(self):
        """測試API連接狀態"""
        logger.info("測試API連接狀態...")
        
        # 測試TDX API
        tdx_status = "失敗"
        tdx_error = None
        if hasattr(self.api_manager, 'tdx_api') and self.api_manager.tdx_api:
            try:
                # 修正：測試獲取訪問令牌
                token = self.api_manager.tdx_api.get_access_token()
                if token:
                    tdx_status = "成功"
                else:
                    tdx_error = "無法獲取 TDX 訪問令牌"
            except Exception as e:
                tdx_error = str(e)
        else:
            tdx_error = "TDX API客戶端未初始化"
        
        # 測試FlightStats API
        fs_status = "失敗"
        fs_error = None
        if hasattr(self.api_manager, 'flightstats_api') and self.api_manager.flightstats_api:
            try:
                # 使用 get_flights 方法進行基本連接測試
                # 使用一個常見航線和接近的日期
                test_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
                # 調用 get_flights 查詢常見航線（如 TPE-HKG）
                self.api_manager.flightstats_api.get_flights('TPE', 'HKG', test_date)
                # 如果上面沒拋異常，視為連接成功
                fs_status = "成功"
            except Exception as e:
                # 如果有異常，記錄錯誤，狀態保持"失敗"
                fs_error = str(e)
        else:
            fs_error = "FlightStats API客戶端未初始化"
        
        # 輸出結果
        print("\n=== API連接狀態 ===")
        print(f"TDX API: {tdx_status}")
        if tdx_error:
            print(f"  錯誤: {tdx_error}")
        
        print(f"FlightStats API: {fs_status}")
        if fs_error:
            print(f"  錯誤: {fs_error}")
        
        return tdx_status == "成功" or fs_status == "成功"
    
    def test_database_connectivity(self):
        """測試數據庫連接狀態"""
        logger.info("測試數據庫連接狀態...")
        
        db_status = "失敗"
        db_error = None
        
        try:
            # 優先使用 DATABASE_URL 環境變數
            conn_str = os.getenv("DATABASE_URL")
            if not conn_str:
                # 如果 DATABASE_URL 不存在，則構建連接字符串
                db_user = os.getenv('DB_USER')
                db_password = os.getenv('DB_PASSWORD')
                db_host = os.getenv('DB_HOST')
                db_port = os.getenv('DB_PORT', '5432')
                db_name = os.getenv('DB_NAME', 'flight_integration')
                
                if not all([db_user, db_password, db_host]):
                    raise ValueError("缺少資料庫連接所需的基本環境變數")
                
                conn_str = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
            
            conn = psycopg2.connect(conn_str)
            if conn:
                db_status = "成功"
                # 執行簡單查詢測試
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
                conn.close()
        except Exception as e:
            db_error = str(e)
        
        # 輸出結果
        print("\n=== 數據庫連接狀態 ===")
        print(f"PostgreSQL: {db_status}")
        if db_error:
            print(f"  錯誤: {db_error}")
        
        return db_status == "成功"
    
    def sync_flights_route(self, departure, arrival, date_str, days=1, limit=0):
        """同步特定航線的航班"""
        try:
            logger.info(f"開始同步航線 {departure}-{arrival} 的航班數據")
            
            # 強制轉換為大寫（確保搜索匹配）
            departure = departure.strip().upper()
            arrival = arrival.strip().upper()

            # 獲取航班數據
            flights_data = self.api_manager.sync_flights(departure, arrival, date_str, days)
            
            if not flights_data:
                logger.warning(f"未找到航線 {departure}-{arrival} 的航班數據")
                return 0
            
            # 限制處理的航班數量（如果需要）
            if limit > 0 and len(flights_data) > limit:
                flights_data = flights_data[:limit]
                logger.info(f"將航班數據限制為 {limit} 條")
            
            # 將航班數據同步到數據庫
            self.db_manager.import_flights_to_database(flights_data)
            added = len(flights_data) # 假設 import 成功就是新增
            updated = 0
            skipped = 0
            
            logger.info(f"航線 {departure}-{arrival} 同步完成: 新增 {added}, 更新 {updated}, 跳過 {skipped}")
            
            # 返回成功處理的航班數量
            return added + updated
        except Exception as e:
            logger.error(f"同步航線 {departure}-{arrival} 時發生錯誤: {str(e)}")
            return 0
    
    def sync_flights_only(self):
        """同步所有已知航線的所有未來航班數據"""
        logger.info("開始僅同步航班數據 (所有已知航線的所有未來排程)")
        
        all_future_flights = []
        # --- 導入並使用 ALL_ROUTES_TUPLES --- 
        try:
            # 從 constants 導入所有航線元組
            from app.scripts.constants import ALL_ROUTES_TUPLES 
            all_routes = set(ALL_ROUTES_TUPLES) # 使用所有已知航線
            logger.info(f"將同步 {len(all_routes)} 條唯一已知航線的所有未來航班數據")
        except ImportError:
            logger.error("無法從 constants 導入 ALL_ROUTES_TUPLES，同步中止")
            return # 提前返回，避免後續錯誤
        # --- 結束修改 --- 
        
        # 循環獲取 flights_for_route 的邏輯不變
        total_flights_fetched = 0 # <-- 新增：初始化總獲取計數器
        airline_counts = defaultdict(int) # <-- 新增：初始化航空公司計數器
        departure_airport_counts = defaultdict(int) # <-- 新增：初始化出發機場計數器

        for dep, arr in all_routes:
            logger.debug(f"獲取航線 {dep}->{arr} 的所有未來數據")
            try:
                flights_for_route = self.api_manager.sync_future_flights(dep, arr)
                if flights_for_route:
                    current_route_count = len(flights_for_route)
                    total_flights_fetched += current_route_count # <-- 新增：累加航班數
                    all_future_flights.extend(flights_for_route)
                    logger.debug(f"航線 {dep}->{arr} 獲取了 {current_route_count} 筆未來航班數據")
                    
                    # --- 新增：統計當前航線的航班 --- 
                    for flight in flights_for_route:
                        if isinstance(flight, dict):
                            airline = flight.get('airline_id')
                            dep_airport = flight.get('departure_airport_id')
                            if airline:
                                airline_counts[airline] += 1
                            if dep_airport:
                                departure_airport_counts[dep_airport] += 1
                    # --- 結束統計 --- 
                            
            except Exception as e:
                logger.error(f"同步航線 {dep}->{arr} 的未來數據時出錯: {e}", exc_info=True)
            
            time.sleep(self.api_manager.request_delay if self.api_manager else 0.5)

        # --- 新增：數據庫導入前的匯總日誌 --- 
        if all_future_flights:
            logger.info(f"所有航線共獲取 {total_flights_fetched} 條未來航班記錄 (去重前)。")
            
            logger.info("--- 按航空公司統計 (去重前) ---")
            if airline_counts:
                # 按航班數量降序排序
                sorted_airlines = sorted(airline_counts.items(), key=lambda item: item[1], reverse=True)
                for airline, count in sorted_airlines:
                    logger.info(f"  {airline}: {count} 個航班")
            else:
                logger.info("  未能統計到任何航空公司的航班。")
                
            logger.info("--- 按出發機場統計 (去重前) ---")
            if departure_airport_counts:
                # 按航班數量降序排序
                sorted_airports = sorted(departure_airport_counts.items(), key=lambda item: item[1], reverse=True)
                for airport, count in sorted_airports:
                    logger.info(f"  {airport}: {count} 個出發航班")
            else:
                logger.info("  未能統計到任何出發機場的航班。")
                
            # --- 原有的導入日誌 --- 
            logger.info(f"準備將獲取的 {len(all_future_flights)} 條未來航班數據同步到數據庫 (去重後)")
            self.db_manager.import_flights_to_database(all_future_flights)
            logger.info("未來航班數據已同步到數據庫")
        else:
            logger.info("未獲取到任何未來航班數據，無需同步到數據庫")
        # --- 結束新增 ---

def main():
    """主函數，處理命令行參數並執行相應操作"""
    parser = argparse.ArgumentParser(description='航班資料同步工具')
    subparsers = parser.add_subparsers(dest='command', help='指令')
    
    # 測試連接指令
    test_parser = subparsers.add_parser('test', help='測試API和數據庫連接')
    
    # 航班同步指令 - 使 date 和 days 可選
    flights_parser = subparsers.add_parser('flights', help='同步特定航線的航班資料。預設獲取所有未來航班。')
    flights_parser.add_argument('--departure', '-d', required=True, help='出發機場 IATA 代碼')
    flights_parser.add_argument('--arrival', '-a', required=True, help='目的機場 IATA 代碼')
    # 修改 date: default=None, nargs='?' 使其完全可選
    flights_parser.add_argument('--date', default=None, nargs='?', help='指定查詢日期（YYYY-MM-DD 格式）。若不提供，則獲取所有未來航班。預設為 None。') 
    # 修改 days: 只有在指定 date 時才有意義
    flights_parser.add_argument('--days', type=int, default=1, help='查詢天數 (僅在提供 --date 時有效)，預設為 1') 
    flights_parser.add_argument('--limit', type=int, default=0, help='限制航班數量 (主要影響指定日期查詢)，預設為0(不限制)')
    
    flights_only_parser = subparsers.add_parser('flights-only', help='僅同步所有熱門航線的未來航班資料')
    
    popular_parser = subparsers.add_parser('popular', help='同步所有熱門航線的未來航班數據 (會寫入數據庫)')
    
    args = parser.parse_args()
    
    sync_tool = FlightDataSyncTool()
    
    if args.command == 'test':
        sync_tool.test_api_connectivity()
        sync_tool.test_database_connectivity()
    
    elif args.command == 'flights':
        # --- 修改 flights 指令處理 --- 
        if args.date:
            logger.info(f"執行特定日期航班同步: {args.departure}->{args.arrival}, Date: {args.date}, Days: {args.days}")
            sync_tool.sync_flights_route(args.departure, args.arrival, args.date, args.days, args.limit)
        else:
            logger.info(f"執行未來航班同步: {args.departure}->{args.arrival}")
            future_flights = sync_tool.api_manager.sync_future_flights(args.departure, args.arrival)
            if future_flights:
                if args.limit > 0 and len(future_flights) > args.limit:
                    future_flights = future_flights[:args.limit]
                    logger.info(f"將未來航班數據限制為 {args.limit} 條")
                logger.info(f"準備將 {len(future_flights)} 條未來航班 ({args.departure}->{args.arrival}) 同步到數據庫")
                sync_tool.db_manager.import_flights_to_database(future_flights)
            else:
                logger.warning(f"未找到航線 {args.departure}->{args.arrival} 的未來航班數據")
        # --- 結束修改 --- 
            
    elif args.command == 'flights-only':
        sync_tool.sync_flights_only()
    
    elif args.command == 'popular':
        # popular 指令現在直接觸發熱門航線的未來數據同步和導入
        logger.info("執行熱門航線未來航班同步...")
        sync_tool.sync_flights_only()
        logger.info("熱門航線未來航班同步完成")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()