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

# 添加應用程式路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.join(current_dir, 'backend')
if app_dir not in sys.path:
    sys.path.append(app_dir)

# 確保logs目錄存在
logs_dir = os.path.join(current_dir, 'logs')
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

# 導入相關模組
try:
    from app.scripts.sync_manager import ApiSyncManager
    from app.scripts.database_sync import DatabaseSyncManager
except ImportError as e:
    logger.error(f"無法導入必要模組: {str(e)}")
    logger.info("請確保您在專案根目錄執行此腳本")
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
            logger.error("請確保.env文件中包含所有必要的環境變數")
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
            self.db_manager = DatabaseSyncManager()
            logger.info("數據庫同步管理器初始化成功")
        except Exception as e:
            logger.error(f"數據庫同步管理器初始化失敗: {str(e)}")
            sys.exit(1)
    
    def _load_env_from_dotenv(self):
        """從.env文件加載環境變數"""
        try:
            # 嘗試從當前目錄和backend目錄查找.env文件
            dotenv_paths = [
                os.path.join(current_dir, '.env'),
                os.path.join(app_dir, '.env')
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
                                value = value.strip('"\'')
                                # 設置環境變數
                                os.environ[key.strip()] = value
                    
                    logger.info("環境變數加載完成")
                    return
            
            logger.warning("未找到.env文件")
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
                # 簡單測試獲取機場資訊
                airports = self.api_manager.tdx_api.get_airports()
                if airports:
                    tdx_status = "成功"
                else:
                    tdx_error = "獲取機場資訊失敗"
            except Exception as e:
                tdx_error = str(e)
        else:
            tdx_error = "TDX API客戶端未初始化"
        
        # 測試FlightStats API
        fs_status = "失敗"
        fs_error = None
        if hasattr(self.api_manager, 'flightstats_api') and self.api_manager.flightstats_api:
            try:
                # 測試獲取機場信息
                airport = self.api_manager.flightstats_api.get_airport('TPE')
                if airport:
                    fs_status = "成功"
                else:
                    fs_error = "獲取機場信息失敗"
            except Exception as e:
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
        """同步特定航線的航班數據"""
        logger.info(f"開始同步 {departure} -> {arrival} 航線的航班數據...")
        
        # 首先確保航空公司和機場資料已同步 - 只同步一次
        logger.info("確保基礎資料已同步...")
        try:
            # 只載入一次基礎資料
            airlines = self.api_manager.sync_airlines()
            if airlines and len(airlines) > 0:
                self.db_manager.sync_airlines(airlines)
                logger.info(f"成功同步 {len(airlines)} 個航空公司資料")
                
            airports = self.api_manager.sync_airports()
            if airports and len(airports) > 0:
                self.db_manager.sync_airports(airports)
                logger.info(f"成功同步 {len(airports)} 個機場資料")
                
            # 獲取航空公司和機場映射
            airlines_map, airports_map = self.db_manager.get_existing_airlines_airports()
            logger.info(f"已載入 {len(airlines_map)} 個航空公司映射和 {len(airports_map)} 個機場映射")
        except Exception as e:
            logger.error(f"同步基礎資料時出錯: {str(e)}")
            print(f"同步基礎資料時出錯: {str(e)}")
            return {"total": 0, "inserted": 0, "updated": 0, "skipped": 0, "errors": 1, "message": f"同步基礎資料時出錯: {str(e)}"}
        
        # 從API獲取航班數據，使用更短的超時時間
        logger.info(f"開始獲取 {departure} -> {arrival} 航線的航班數據...")
        try:
            flights = self.api_manager.sync_flights(departure, arrival, date_str, days)
            
            if not flights:
                logger.warning(f"未獲取到 {departure} -> {arrival} 航線的航班數據")
                return {"total": 0, "inserted": 0, "updated": 0, "skipped": 0, "errors": 0, "message": "未獲取到航班數據"}
            
            # 如果設置了limit並且大於0，則限制航班數量
            if limit > 0 and len(flights) > limit:
                logger.info(f"應用限制，從 {len(flights)} 個航班中選取 {limit} 個")
                flights = flights[:limit]
            
            logger.info(f"從API獲取了 {len(flights)} 個航班")
        except Exception as e:
            logger.error(f"獲取航班數據時出錯: {str(e)}")
            print(f"獲取航班數據時出錯: {str(e)}")
            return {"total": 0, "inserted": 0, "updated": 0, "skipped": 0, "errors": 1, "message": f"獲取航班數據時出錯: {str(e)}"}
        
        try:
            # 過濾航班數據
            filtered_flights = self.db_manager.filter_flights_by_existing_data(flights, airlines_map, airports_map)
            logger.info(f"過濾後保留 {len(filtered_flights)} 個航班數據")
            
            if not filtered_flights:
                logger.warning(f"過濾後沒有可用的航班數據")
                result = {"total": 0, "inserted": 0, "updated": 0, "skipped": 0, "errors": 0, "message": "過濾後沒有可用的航班數據"}
            else:
                # 直接導入到數據庫，不再呼叫sync_flights方法（該方法會重複獲取數據）
                result = self.db_manager.import_flights_to_database(filtered_flights)
                
            # 輸出結果
            print(f"\n=== {departure} -> {arrival} 航線同步結果 ===")
            print(f"總數: {result.get('total', 0)}")
            print(f"新增: {result.get('inserted', 0)}")
            print(f"更新: {result.get('updated', 0)}")
            print(f"跳過: {result.get('skipped', 0)}")
            
            return result
        except Exception as e:
            logger.error(f"同步航班數據到資料庫時出錯: {str(e)}")
            print(f"同步航班數據到資料庫時出錯: {str(e)}")
            return {"total": 0, "inserted": 0, "updated": 0, "skipped": 0, "errors": 1, "message": f"同步航班數據到資料庫時出錯: {str(e)}"}
    
    def sync_taiwan_flights(self, date_str, days=1):
        """同步從台灣出發的航班數據"""
        logger.info(f"開始同步從台灣出發的航班數據，日期: {date_str}，天數: {days}...")
        
        # 從API獲取航班數據
        taiwan_flights = self.api_manager.sync_taiwan_departures(date_str, days)
        
        if not taiwan_flights:
            logger.warning("未獲取到從台灣出發的航班數據")
            return {"total": 0, "inserted": 0, "updated": 0, "skipped": 0, "errors": 0, "message": "未獲取到航班數據"}
        
        # 計算總航班數
        total_flights = sum(len(flights) for flights in taiwan_flights.values())
        logger.info(f"從API獲取了 {total_flights} 個從台灣出發的航班")
        
        # 首先確保航空公司和機場資料已同步
        logger.info("確保航空公司和機場資料已同步...")
        airlines = self.api_manager.sync_airlines()
        if airlines:
            self.db_manager.sync_airlines(airlines)
            
        airports = self.api_manager.sync_airports()
        if airports:
            self.db_manager.sync_airports(airports)
        
        # 獲取航空公司和機場映射
        airlines_map, airports_map = self.db_manager.get_existing_airlines_airports()
        
        # 合併所有航班數據
        all_flights = []
        for airport, flights in taiwan_flights.items():
            all_flights.extend(flights)
        
        # 過濾航班數據
        filtered_flights = self.db_manager.filter_flights_by_existing_data(all_flights, airlines_map, airports_map)
        logger.info(f"過濾後保留 {len(filtered_flights)} 個航班數據")
        
        if not filtered_flights:
            logger.warning("過濾後沒有可用的航班數據")
            result = {"total": 0, "inserted": 0, "updated": 0, "skipped": 0, "errors": 0, "message": "過濾後沒有可用的航班數據"}
        else:
            # 直接導入到數據庫
            result = self.db_manager.import_flights_to_database(filtered_flights)
        
        # 輸出結果
        print("\n=== 台灣出發航班同步結果 ===")
        print(f"總數: {result.get('total', 0)}")
        print(f"新增: {result.get('inserted', 0)}")
        print(f"更新: {result.get('updated', 0)}")
        print(f"跳過: {result.get('skipped', 0)}")
        
        # 輸出各機場統計
        print("\n各機場統計:")
        for airport, flights in taiwan_flights.items():
            print(f"  {airport}: {len(flights)} 個航班")
            
        return result
    
    def sync_flights_only(self, date_str, days=1):
        """僅同步航班數據（不更新航空公司和機場資料）"""
        print("\n=== 開始僅同步航班數據 ===\n")
        
        # 測試連接狀態
        api_ok = self.test_api_connectivity()
        db_ok = self.test_database_connectivity()
        
        if not api_ok or not db_ok:
            logger.error("連接測試失敗，無法進行同步")
            return
        
        # 直接獲取航空公司和機場映射，不執行同步
        logger.info("獲取現有航空公司和機場映射...")
        airlines_map, airports_map = self.db_manager.get_existing_airlines_airports()
        logger.info(f"已載入 {len(airlines_map)} 個航空公司映射和 {len(airports_map)} 個機場映射")
        
        # 從API獲取航班數據
        logger.info(f"開始同步從台灣出發的航班數據，日期: {date_str}，天數: {days}...")
        taiwan_flights = self.api_manager.sync_taiwan_departures(date_str, days)
        
        if not taiwan_flights:
            logger.warning("未獲取到從台灣出發的航班數據")
            return {"total": 0, "inserted": 0, "updated": 0, "skipped": 0, "errors": 0, "message": "未獲取到航班數據"}
        
        # 計算總航班數
        total_flights = sum(len(flights) for flights in taiwan_flights.values())
        logger.info(f"從API獲取了 {total_flights} 個從台灣出發的航班")
        
        # 合併所有航班數據
        all_flights = []
        for airport, flights in taiwan_flights.items():
            all_flights.extend(flights)
        
        # 過濾航班數據
        filtered_flights = self.db_manager.filter_flights_by_existing_data(all_flights, airlines_map, airports_map)
        logger.info(f"過濾後保留 {len(filtered_flights)} 個航班數據")
        
        if not filtered_flights:
            logger.warning("過濾後沒有可用的航班數據")
            result = {"total": 0, "inserted": 0, "updated": 0, "skipped": 0, "errors": 0, "message": "過濾後沒有可用的航班數據"}
        else:
            # 直接導入到數據庫
            result = self.db_manager.import_flights_to_database(filtered_flights)
        
        # 輸出結果
        print("\n=== 台灣出發航班同步結果 ===")
        print(f"總數: {result.get('total', 0)}")
        print(f"新增: {result.get('inserted', 0)}")
        print(f"更新: {result.get('updated', 0)}")
        print(f"跳過: {result.get('skipped', 0)}")
        
        # 輸出各機場統計
        print("\n各機場統計:")
        for airport, flights in taiwan_flights.items():
            print(f"  {airport}: {len(flights)} 個航班")
            
        print("\n=== 航班數據同步完成 ===")
        return result
    
    def sync_all(self, date_str, days=1):
        """同步所有數據"""
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
        
        # 同步台灣出發的航班數據
        self.sync_taiwan_flights(date_str, days)
        
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
    
    # 台灣出發航班同步指令
    taiwan_parser = subparsers.add_parser('taiwan', help='同步從台灣出發的航班資料')
    taiwan_parser.add_argument('--date', default=datetime.now().strftime('%Y-%m-%d'), help='查詢日期（YYYY-MM-DD 格式），預設為今天')
    taiwan_parser.add_argument('--days', type=int, default=1, help='查詢天數，預設為 1')
    
    # 全部同步指令
    all_parser = subparsers.add_parser('all', help='同步所有數據')
    all_parser.add_argument('--date', default=datetime.now().strftime('%Y-%m-%d'), help='查詢日期（YYYY-MM-DD 格式），預設為今天')
    all_parser.add_argument('--days', type=int, default=1, help='查詢天數，預設為 1')
    
    # 僅航班同步指令（不更新航空公司和機場資料）
    flights_only_parser = subparsers.add_parser('flights-only', help='僅同步航班資料（不更新航空公司和機場資料）')
    flights_only_parser.add_argument('--date', default=datetime.now().strftime('%Y-%m-%d'), help='查詢日期（YYYY-MM-DD 格式），預設為今天')
    flights_only_parser.add_argument('--days', type=int, default=1, help='查詢天數，預設為 1')
    
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
    
    elif args.command == 'taiwan':
        sync_tool.sync_taiwan_flights(args.date, args.days)
    
    elif args.command == 'all':
        sync_tool.sync_all(args.date, args.days)
    
    elif args.command == 'flights-only':
        sync_tool.sync_flights_only(args.date, args.days)
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()