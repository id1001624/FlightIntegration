#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
API客戶端測試腳本
用於測試重構後的API客戶端架構和功能
測試以下組件：
1. 基礎客戶端 (BaseAPIClient)
2. TDX API客戶端 (TdxApiClient)
3. FlightStats API客戶端 (FlightStatsApiClient)
4. 緩存工具 (cache_utils)
5. 日期時間工具 (date_utils)
"""
import os
import sys
import json
import logging
import time
from datetime import datetime, timedelta
import unittest

# 設置環境變數
os.environ['TDX_CLIENT_ID'] = 'n1116440-eff4950c-7994-47de'
os.environ['TDX_CLIENT_SECRET'] = 'efc87a00-3930-4be2-bca9-37f3b8f46d1d'
os.environ['FLIGHTSTATS_APP_ID'] = 'cb5c8184'
os.environ['FLIGHTSTATS_APP_KEY'] = '82304b41352d18995b0e7440a977cc1b'

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('api_test')

# 添加應用路徑
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 導入要測試的模組
try:
    from app.clients.base_client import BaseAPIClient
    from app.clients.tdx_client import TdxApiClient
    from app.clients.flightstats_client import FlightStatsApiClient
    from app.utils.cache_utils import cached, SimpleCache, invalidate_cache
    from app.utils.date_utils import parse_datetime, format_datetime, get_date_range
    from app.scripts.constants import TAIWAN_AIRPORTS, TARGET_AIRLINES
    USING_NEW_STRUCTURE = True
except ImportError as e:
    logger.warning(f"無法導入新結構模組: {e}")
    USING_NEW_STRUCTURE = False
    # 台灣機場列表
    TAIWAN_AIRPORTS = ['TPE', 'TSA', 'RMQ', 'KHH', 'TNN', 'CYI', 'HUN', 'TTT', 'KNH', 'MZG', 'LZN', 'MFK', 'KYD', 'GNI', 'WOT']
    # 目標航空公司
    TARGET_AIRLINES = ['BR', 'JL', 'JX', 'IT', 'CX', 'DA', 'CI', 'OZ', 'AE', 'B7']


class BaseAPIClientTest(unittest.TestCase):
    """測試基礎API客戶端"""
    
    @unittest.skipIf(not USING_NEW_STRUCTURE, "需要新結構才能測試")
    def test_initialization(self):
        """測試基礎客戶端初始化"""
        client = BaseAPIClient()
        self.assertIsNotNone(client)
        self.assertIsNotNone(client.logger)
        self.assertEqual(client.max_retries, 3)
        print("✓ 基礎API客戶端初始化成功")
    
    @unittest.skipIf(not USING_NEW_STRUCTURE, "需要新結構才能測試")
    def test_make_request(self):
        """測試基礎請求方法"""
        client = BaseAPIClient()
        
        # 測試無效URL (應返回None)
        result = client.make_request("https://example.com/invalid/endpoint")
        self.assertIsNone(result)
        print("✓ 處理無效請求")
        
        # 測試有效URL
        result = client.make_request("https://httpbin.org/get")
        self.assertIsNotNone(result)
        print("✓ 處理有效請求")
        
        # 測試帶參數請求
        params = {"test": "value"}
        result = client.make_request("https://httpbin.org/get", params=params)
        self.assertIsNotNone(result)
        self.assertIn("args", result)
        self.assertEqual(result["args"]["test"], "value")
        print("✓ 處理帶參數請求")
    
    @unittest.skipIf(not USING_NEW_STRUCTURE, "需要新結構才能測試")
    def test_close(self):
        """測試關閉會話"""
        client = BaseAPIClient()
        client.close()
        print("✓ 關閉客戶端會話")


class TdxApiClientTest(unittest.TestCase):
    """測試TDX API客戶端"""
    
    @classmethod
    def setUpClass(cls):
        """測試類初始化"""
        if USING_NEW_STRUCTURE:
            cls.client = TdxApiClient()
            print("使用新結構TDX API客戶端")
            else:
            cls.client = None
            print("跳過TDX API客戶端測試")
    
    @unittest.skipIf(not USING_NEW_STRUCTURE, "需要新結構才能測試")
    def test_get_access_token(self):
        """測試獲取訪問令牌"""
        token = self.client.get_access_token()
        self.assertIsNotNone(token)
        print(f"✓ 成功獲取TDX API訪問令牌")
    
    @unittest.skipIf(not USING_NEW_STRUCTURE, "需要新結構才能測試")
    def test_get_airports(self):
        """測試獲取機場列表"""
        airports = self.client.get_airports()
        self.assertIsNotNone(airports)
        self.assertIsInstance(airports, list)
        self.assertGreater(len(airports), 0)
        print(f"✓ 成功獲取 {len(airports)} 個機場")
        
        # 顯示範例
        if airports:
            print(f"  範例: {airports[0]}")
    
    @unittest.skipIf(not USING_NEW_STRUCTURE, "需要新結構才能測試")
    def test_get_airport(self):
        """測試獲取特定機場"""
        airport = self.client.get_airport('TPE')
        self.assertIsNotNone(airport)
        self.assertIsInstance(airport, dict)
        self.assertEqual(airport.get('iata_code'), 'TPE')
        print(f"✓ 成功獲取機場 TPE: {airport.get('name')}")
    
    @unittest.skipIf(not USING_NEW_STRUCTURE, "需要新結構才能測試")
    def test_get_flight_schedules(self):
        """測試獲取航班時刻表"""
        date = datetime.now().strftime('%Y-%m-%d')
        schedules = self.client.get_flight_schedules(date)
        self.assertIsNotNone(schedules)
        self.assertIsInstance(schedules, list)
        print(f"✓ 成功獲取 {len(schedules)} 個航班時刻")
        
        # 顯示範例
        if schedules:
            print(f"  範例: {schedules[0]}")


class FlightStatsApiClientTest(unittest.TestCase):
    """測試FlightStats API客戶端"""
    
    @classmethod
    def setUpClass(cls):
        """測試類初始化"""
        if USING_NEW_STRUCTURE:
            cls.client = FlightStatsApiClient()
            print("使用新結構FlightStats API客戶端")
                else:
            cls.client = None
            print("跳過FlightStats API客戶端測試")
    
    @unittest.skipIf(not USING_NEW_STRUCTURE, "需要新結構才能測試")
    def test_get_airports(self):
        """測試獲取機場列表"""
        airports = self.client.get_airports()
        self.assertIsNotNone(airports)
        self.assertIsInstance(airports, list)
        self.assertGreater(len(airports), 0)
                print(f"✓ 成功獲取 {len(airports)} 個機場")
        
        # 顯示範例
        if airports:
            print(f"  範例: {airports[0]}")
    
    @unittest.skipIf(not USING_NEW_STRUCTURE, "需要新結構才能測試")
    def test_get_airport(self):
        """測試獲取特定機場"""
        # 測試獲取台灣機場
        airport = self.client.get_airport('TPE')
        self.assertIsNotNone(airport)
        self.assertIsInstance(airport, dict)
        print(f"✓ 成功獲取機場 TPE: {airport.get('name', '')}")
        
        # 測試獲取日本機場
        airport = self.client.get_airport('NRT')
        self.assertIsNotNone(airport)
        self.assertIsInstance(airport, dict)
        print(f"✓ 成功獲取機場 NRT: {airport.get('name', '')}")
    
    @unittest.skipIf(not USING_NEW_STRUCTURE, "需要新結構才能測試")
    def test_get_airline(self):
        """測試獲取特定航空公司"""
        # 測試獲取台灣航空公司
        airline = self.client.get_airline('BR')
        self.assertIsNotNone(airline)
        self.assertIsInstance(airline, dict)
        print(f"✓ 成功獲取航空公司 BR: {airline.get('name', '')}")
        
        # 測試獲取非目標航空公司（應返回默認值或API數據）
        airline = self.client.get_airline('NH')
        self.assertIsNotNone(airline)
        self.assertIsInstance(airline, dict)
        print(f"✓ 成功獲取航空公司 NH: {airline.get('name', '')}")
    
    @unittest.skipIf(not USING_NEW_STRUCTURE, "需要新結構才能測試")
    def test_get_flights(self):
        """測試獲取航班"""
        date = datetime.now().strftime('%Y-%m-%d')
        flights = self.client.get_flights('TPE', 'NRT', date)
        self.assertIsNotNone(flights)
        self.assertIsInstance(flights, list)
        print(f"✓ 成功獲取 TPE->NRT 航班: {len(flights)} 個")
        
        # 顯示範例
        if flights:
            print(f"  範例: {flights[0]}")
    
    @unittest.skipIf(not USING_NEW_STRUCTURE, "需要新結構才能測試")
    def test_get_flight_status(self):
        """測試獲取航班狀態"""
        date = datetime.now().strftime('%Y-%m-%d')
        # 使用有效的航空公司代碼和航班號
        status = self.client.get_flight_status('BR', '196', date)
        print(f"✓ 獲取航班狀態: {status}")


class CacheUtilsTest(unittest.TestCase):
    """測試緩存工具"""
    
    @unittest.skipIf(not USING_NEW_STRUCTURE, "需要新結構才能測試")
    def test_simple_cache(self):
        """測試簡單緩存類"""
        cache = SimpleCache(default_ttl=10)
        
        # 測試設置和獲取
        cache.set('test_key', 'test_value')
        value = cache.get('test_key')
        self.assertEqual(value, 'test_value')
        print("✓ 緩存設置和獲取")
        
        # 測試過期項
        cache.set('expire_key', 'expire_value', ttl=1)
        self.assertEqual(cache.get('expire_key'), 'expire_value')
        time.sleep(1.5)  # 等待過期
        self.assertIsNone(cache.get('expire_key'))
        print("✓ 緩存項過期")
        
        # 測試刪除
        cache.set('delete_key', 'delete_value')
        self.assertEqual(cache.get('delete_key'), 'delete_value')
        cache.delete('delete_key')
        self.assertIsNone(cache.get('delete_key'))
        print("✓ 緩存項刪除")
        
        # 測試清理
        cache.set('clean1', 'value1', ttl=1)
        cache.set('clean2', 'value2')
        time.sleep(1.5)  # 等待過期
        cleaned = cache.cleanup()
        self.assertEqual(cleaned, 1)
        print(f"✓ 清理過期項: {cleaned} 個")
        
        # 測試清空
        cache.clear()
        self.assertIsNone(cache.get('clean2'))
        print("✓ 清空緩存")
    
    @unittest.skipIf(not USING_NEW_STRUCTURE, "需要新結構才能測試")
    def test_cached_decorator(self):
        """測試緩存裝飾器"""
        call_count = 0
        
        @cached(ttl=10)
        def test_func(param):
            nonlocal call_count
            call_count += 1
            return f"result_{param}"
        
        # 第一次調用會執行函數
        result1 = test_func("test")
        self.assertEqual(result1, "result_test")
        self.assertEqual(call_count, 1)
        
        # 第二次調用相同參數應使用緩存
        result2 = test_func("test")
        self.assertEqual(result2, "result_test")
        self.assertEqual(call_count, 1)  # 沒有再次調用
        
        # 不同參數應該重新調用
        result3 = test_func("different")
        self.assertEqual(result3, "result_different")
        self.assertEqual(call_count, 2)
        
        print("✓ 緩存裝飾器正常工作")
    
    @unittest.skipIf(not USING_NEW_STRUCTURE, "需要新結構才能測試")
    def test_invalidate_cache(self):
        """測試使緩存失效"""
        # 創建一些緩存項
        @cached(ttl=60, key_prefix="test_prefix")
        def prefixed_func(param):
            return f"prefixed_{param}"
        
        @cached(ttl=60)
        def normal_func(param):
            return f"normal_{param}"
        
        # 調用函數填充緩存
        prefixed_func("a")
        prefixed_func("b")
        normal_func("c")
        
        # 使特定前綴的緩存失效
        invalidated = invalidate_cache("test_prefix")
        self.assertGreaterEqual(invalidated, 2)
        
        print(f"✓ 使緩存失效: {invalidated} 個項")


class DateUtilsTest(unittest.TestCase):
    """測試日期時間工具"""
    
    @unittest.skipIf(not USING_NEW_STRUCTURE, "需要新結構才能測試")
    def test_parse_datetime(self):
        """測試日期時間解析"""
        # 測試各種格式
        formats = [
            "2025-04-11T00:05:00.000",  # ISO 格式帶毫秒
            "2025-04-11T00:05:00",      # ISO 格式
            "2025-04-11T00:05",         # ISO 格式不帶秒
            "2025-04-11 00:05:00",      # 標準格式
            "2025-04-11 00:05",         # 標準格式不帶秒
            "04/11/2025 00:05",         # FlightStats 格式
            "04/11/2025 00:05:00"       # FlightStats 格式帶秒
        ]
        
        for dt_str in formats:
            parsed = parse_datetime(dt_str)
            self.assertIsNotNone(parsed)
            self.assertIsInstance(parsed, datetime)
            print(f"✓ 成功解析: {dt_str} -> {parsed}")
    
    @unittest.skipIf(not USING_NEW_STRUCTURE, "需要新結構才能測試")
    def test_format_datetime(self):
        """測試日期時間格式化"""
        dt = datetime(2025, 4, 11, 0, 5, 0)
        
        # 測試默認格式
        formatted = format_datetime(dt)
        self.assertEqual(formatted, "2025-04-11T00:05:00")
        
        # 測試自定義格式
        formatted = format_datetime(dt, "%Y/%m/%d %H:%M")
        self.assertEqual(formatted, "2025/04/11 00:05")
        
        print(f"✓ 成功格式化日期時間")
    
    @unittest.skipIf(not USING_NEW_STRUCTURE, "需要新結構才能測試")
    def test_get_date_range(self):
        """測試獲取日期範圍"""
        # 測試從字符串開始
        dates = get_date_range("2025-04-11", 3)
        self.assertEqual(len(dates), 3)
        self.assertEqual(dates[0], "2025-04-11")
        self.assertEqual(dates[1], "2025-04-12")
        self.assertEqual(dates[2], "2025-04-13")
        
        # 測試從datetime對象開始
        dt = datetime(2025, 4, 11)
        dates = get_date_range(dt, 3)
        self.assertEqual(len(dates), 3)
        self.assertEqual(dates[0], "2025-04-11")
        
        print(f"✓ 成功生成日期範圍: {dates}")


def run_tests():
    """運行所有測試"""
    if not USING_NEW_STRUCTURE:
        print("\n警告: 未找到新的API客戶端結構，將跳過大部分測試")
        print("請確保在正確的環境中運行，並且新的客戶端和工具類已經實現")
        return
    
    print("\n========== 測試新的API客戶端結構 ==========")
    
    # 創建測試套件
    suite = unittest.TestSuite()
    
    # 添加基礎客戶端測試
    print("\n----- 測試基礎API客戶端 -----")
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(BaseAPIClientTest))
    
    # 添加TDX客戶端測試
    print("\n----- 測試TDX API客戶端 -----")
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TdxApiClientTest))
    
    # 添加FlightStats客戶端測試
    print("\n----- 測試FlightStats API客戶端 -----")
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(FlightStatsApiClientTest))
    
    # 添加緩存工具測試
    print("\n----- 測試緩存工具 -----")
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(CacheUtilsTest))
    
    # 添加日期工具測試
    print("\n----- 測試日期時間工具 -----")
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(DateUtilsTest))
    
    # 運行測試
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
    
    print("\n測試完成")


if __name__ == "__main__":
    run_tests() 