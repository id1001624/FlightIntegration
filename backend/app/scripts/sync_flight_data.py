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
# 使用相對導入
try:
    logger.info("嘗試使用相對路徑導入...")
    from .sync_manager import ApiSyncManager
    from .db_manager import DbManager
    logger.info("成功使用相對路徑導入客戶端")
except ImportError as e:
    logger.error(f"導入模塊失敗: {e}", exc_info=True)
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
        
        # 檢查是否有 DATABASE_URL
        has_database_url = bool(os.getenv('DATABASE_URL'))
        
        # 如果沒有 DATABASE_URL，則需要檢查單獨的資料庫環境變數
        if not has_database_url:
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
    
    def sync_airlines(self):
        """同步航空公司數據"""
        logger.info("開始同步航空公司數據...")
        
        # 從API獲取航空公司數據
        airlines = self.api_manager.sync_airlines()
        
        if not airlines:
            logger.warning("未獲取到航空公司數據")
            return
        
        logger.info(f"從API獲取了 {len(airlines)} 個航空公司")
        
        # 同步到資料庫
        result = self.db_manager.sync_airlines(airlines)
        
        # 輸出結果
        print("\n=== 航空公司同步結果 ===")
        print(f"總數: {result.get('total', 0)}")
        print(f"新增: {result.get('inserted', 0)}")
        print(f"更新: {result.get('updated', 0)}")
        print(f"跳過: {result.get('skipped', 0)}")
    
    def sync_airports(self):
        """同步機場數據"""
        logger.info("開始同步機場數據...")
        
        # 從API獲取機場數據
        airports = self.api_manager.sync_airports()
        
        if not airports:
            logger.warning("未獲取到機場數據")
            return
        
        logger.info(f"從API獲取了 {len(airports)} 個機場")
        
        # 同步到資料庫
        result = self.db_manager.sync_airports(airports)
        
        # 輸出結果
        print("\n=== 機場同步結果 ===")
        print(f"總數: {result.get('total', 0)}")
        print(f"新增: {result.get('inserted', 0)}")
        print(f"更新: {result.get('updated', 0)}")
        print(f"跳過: {result.get('skipped', 0)}")
    
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
    
    def sync_flights_only(self, date_str, days=1):
        """僅同步航班數據 (基於熱門航線)，不包括機場和航空公司"""
        logger.info(f"開始僅同步航班數據 (基於熱門航線), 日期: {date_str}, 天數: {days}")

        # 調用 sync_manager 的 sync_popular_routes 來獲取航班數據
        all_flights_dict = {}
        try:
            # sync_popular_routes 返回的是字典 {route_tuple: [flights]} 
            popular_routes_data = self.api_manager.sync_popular_routes(date_str, days)
            logger.info(f"已從 ApiSyncManager 的 sync_popular_routes 獲取 {len(popular_routes_data)} 條航線的數據")

            # 合併所有航班列表
            all_flights = []
            for route, flights in popular_routes_data.items():
                if flights:
                    all_flights.extend(flights)
            
            logger.info(f"合併後共獲取 {len(all_flights)} 條航班數據")

        except Exception as e:
            logger.error(f"調用 sync_popular_routes 時出錯: {str(e)}", exc_info=True)
            all_flights = [] # 出錯時設為空列表

        if not all_flights:
             logger.warning(f"基於熱門航線，日期 {date_str} (及後續 {days-1} 天) 未找到任何航班數據可同步")
             return [] # 返回空列表表示沒有數據

        logger.info(f"準備將 {len(all_flights)} 條航班數據同步到數據庫")
        try:
            # 調用 db_manager 的 import_flights_to_database
            self.db_manager.import_flights_to_database(all_flights)
            logger.info(f"成功將 {len(all_flights)} 條航班數據同步到數據庫")
            return all_flights # 返回成功同步的航班列表
        except Exception as e:
            logger.error(f"數據庫同步航班時出錯: {str(e)}", exc_info=True)
            return [] # 同步失敗也返回空列表
    
    def sync_all(self, date_str, days=1):
        """同步所有數據 (航空公司, 機場, 熱門航線航班)"""
        print("\n=== 開始全面數據同步 ===\n")
        
        # 測試連接狀態
        api_ok = self.test_api_connectivity()
        db_ok = self.test_database_connectivity()
        
        if not api_ok or not db_ok:
            logger.error("連接測試失敗，無法進行同步")
            return
        
        # 同步航空公司數據
        self.sync_airlines()
        
        # 同步機場數據
        self.sync_airports()
        
        # 同步熱門航線的航班數據
        # 注意：這裡調用 sync_popular_routes，它會從 API 獲取數據，但不直接同步到 DB
        # 我們需要獲取其返回的航班數據，然後調用 DB manager 進行同步
        logger.info(f"開始同步熱門航線航班, 日期: {date_str}, 天數: {days}")
        all_popular_flights = []
        try:
            popular_routes_data = self.api_manager.sync_popular_routes(date_str, days)
            for route, flights in popular_routes_data.items():
                if flights:
                    all_popular_flights.extend(flights)
            logger.info(f"從 sync_popular_routes 獲取 {len(all_popular_flights)} 條熱門航線航班數據")

            if all_popular_flights:
                 logger.info(f"準備將 {len(all_popular_flights)} 條熱門航線航班同步到數據庫")
                 self.db_manager.import_flights_to_database(all_popular_flights)
                 logger.info(f"成功將 {len(all_popular_flights)} 條熱門航線航班同步到數據庫")
            else:
                logger.warning("未從 sync_popular_routes 獲取到任何航班數據進行同步")

        except Exception as e:
             logger.error(f"在 sync_all 中處理熱門航線時出錯: {str(e)}", exc_info=True)

        print("\n=== 全面數據同步完成 ===")

def main():
    """主函數，處理命令行參數並執行相應操作"""
    parser = argparse.ArgumentParser(description='航班資料同步工具')
    subparsers = parser.add_subparsers(dest='command', help='指令')
    
    # 測試連接指令
    test_parser = subparsers.add_parser('test', help='測試API和數據庫連接')
    
    # 航空公司同步指令
    airlines_parser = subparsers.add_parser('airlines', help='同步航空公司資料')
    
    # 機場同步指令
    airports_parser = subparsers.add_parser('airports', help='同步機場資料')
    
    # 航班同步指令
    flights_parser = subparsers.add_parser('flights', help='同步航班資料')
    flights_parser.add_argument('--departure', '-d', required=True, help='出發機場 IATA 代碼')
    flights_parser.add_argument('--arrival', '-a', required=True, help='目的機場 IATA 代碼')
    flights_parser.add_argument('--date', default=datetime.now().strftime('%Y-%m-%d'), help='查詢日期（YYYY-MM-DD 格式），預設為今天')
    flights_parser.add_argument('--days', type=int, default=1, help='查詢天數，預設為 1')
    flights_parser.add_argument('--limit', type=int, default=0, help='限制航班數量，預設為0(不限制)')
    
    # 全部同步指令
    all_parser = subparsers.add_parser('all', help='同步所有數據')
    all_parser.add_argument('--date', default=datetime.now().strftime('%Y-%m-%d'), help='查詢日期（YYYY-MM-DD 格式），預設為今天')
    all_parser.add_argument('--days', type=int, default=1, help='查詢天數，預設為 1')
    
    # 僅航班同步指令（不更新航空公司和機場資料）
    flights_only_parser = subparsers.add_parser('flights-only', help='僅同步航班資料（不更新航空公司和機場資料）')
    flights_only_parser.add_argument('--date', default=datetime.now().strftime('%Y-%m-%d'), help='查詢日期（YYYY-MM-DD 格式），預設為今天')
    flights_only_parser.add_argument('--days', type=int, default=1, help='查詢天數，預設為 1')
    
    # 熱門航線同步指令
    popular_parser = subparsers.add_parser('popular', help='同步熱門航線數據')
    popular_parser.add_argument('--date', default=datetime.now().strftime('%Y-%m-%d'), help='查詢日期（YYYY-MM-DD 格式），預設為今天')
    popular_parser.add_argument('--days', type=int, default=1, help='查詢天數，預設為 1')
    popular_parser.add_argument('--limit', type=int, default=0, help='每條航線的最大處理航班數量 (0表示不限制)')
    
    args = parser.parse_args()
    
    # 初始化同步工具
    sync_tool = FlightDataSyncTool()
    
    # 根據指令執行相應操作
    if args.command == 'test':
        sync_tool.test_api_connectivity()
        sync_tool.test_database_connectivity()
    
    elif args.command == 'airlines':
        sync_tool.sync_airlines()
    
    elif args.command == 'airports':
        sync_tool.sync_airports()
    
    elif args.command == 'flights':
        sync_tool.sync_flights_route(args.departure, args.arrival, args.date, args.days, args.limit)
    
    elif args.command == 'all':
        sync_tool.sync_all(args.date, args.days)
    
    elif args.command == 'flights-only':
        sync_tool.sync_flights_only(args.date, args.days)
    
    elif args.command == 'popular':
        sync_tool.sync_all(args.date, args.days) # 注意：popular 指令現在也調用 sync_all
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()