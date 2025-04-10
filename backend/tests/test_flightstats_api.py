#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
測試 FlightStats API 的請求路徑，確保使用 languageCode:zh 參數
"""
import os
import requests
import json
import logging
from datetime import datetime, timedelta

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('flightstats_api_test')

class FlightStatsApiTester:
    """測試 FlightStats API 請求路徑"""

    def __init__(self):
        """初始化測試器"""
        # 從環境變數獲取 API 金鑰
        self.app_id = os.environ.get('FLIGHTSTATS_APP_ID')
        self.app_key = os.environ.get('FLIGHTSTATS_APP_KEY')
        
        if not self.app_id or not self.app_key:
            raise ValueError("請設置 FLIGHTSTATS_APP_ID 和 FLIGHTSTATS_APP_KEY 環境變數")
        
        self.base_url = "https://api.flightstats.com/flex"
        self.language_param = "languageCode:zh"
        
        logger.info("初始化 FlightStats API 測試器")

    def make_request(self, endpoint, params=None):
        """發送 API 請求並檢查回應"""
        if params is None:
            params = {}
        
        # 添加基本的身份驗證參數
        params.update({
            'appId': self.app_id,
            'appKey': self.app_key,
            'extendedOptions': self.language_param
        })
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            logger.info(f"正在請求: {url}")
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"請求成功: {url}")
                return response.json()
            else:
                logger.error(f"API 請求失敗: {response.status_code}, 回應: {response.text}")
                return None
        except Exception as e:
            logger.error(f"請求出錯: {str(e)}")
            return None

    def test_airlines_api(self):
        """測試航空公司 API"""
        logger.info("=== 測試航空公司 API ===")
        endpoint = "airlines/rest/v1/json/active"
        response = self.make_request(endpoint)
        
        if response and 'airlines' in response:
            logger.info(f"成功獲取 {len(response['airlines'])} 個航空公司")
            # 輸出一個範例航空公司資料
            if response['airlines']:
                logger.info(f"範例航空公司: {json.dumps(response['airlines'][0], ensure_ascii=False)}")
            return True
        else:
            logger.error("獲取航空公司失敗")
            return False

    def test_airports_api(self):
        """測試機場 API"""
        logger.info("=== 測試機場 API ===")
        endpoint = "airports/rest/v1/json/active"
        response = self.make_request(endpoint)
        
        if response and 'airports' in response:
            logger.info(f"成功獲取 {len(response['airports'])} 個機場")
            # 輸出一個範例機場資料
            if response['airports']:
                logger.info(f"範例機場: {json.dumps(response['airports'][0], ensure_ascii=False)}")
            return True
        else:
            logger.error("獲取機場失敗")
            return False

    def test_specific_airport_api(self, iata_code="TPE"):
        """測試特定機場 API"""
        logger.info(f"=== 測試特定機場 API: {iata_code} ===")
        endpoint = f"airports/rest/v1/json/{iata_code}/today"
        params = {'codeType': 'IATA'}
        response = self.make_request(endpoint, params)
        
        if response and 'airport' in response:
            logger.info(f"成功獲取機場 {iata_code} 資料")
            logger.info(f"機場資料: {json.dumps(response['airport'], ensure_ascii=False)}")
            return True
        else:
            logger.error(f"獲取機場 {iata_code} 失敗")
            return False

    def test_airport_delay_api(self, airports=["TPE", "NRT"]):
        """測試機場延誤指數 API"""
        logger.info(f"=== 測試機場延誤指數 API: {','.join(airports)} ===")
        # 將機場代碼列表轉換為逗號分隔的字符串
        airports_str = ','.join(airports)
        
        endpoint = f"delayindex/rest/v1/json/airports/{airports_str}"
        params = {'codeType': 'IATA'}
        response = self.make_request(endpoint, params)
        
        if response and 'delayIndexes' in response:
            logger.info(f"成功獲取機場 {airports_str} 延誤指數")
            logger.info(f"延誤指數: {json.dumps(response['delayIndexes'], ensure_ascii=False)}")
            return True
        else:
            logger.error(f"獲取機場 {airports_str} 延誤指數失敗")
            return False

    def test_flight_status_api(self, carrier="CI", flight_number="100"):
        """測試航班狀態 API"""
        logger.info(f"=== 測試航班狀態 API: {carrier}{flight_number} ===")
        # 獲取明天的日期
        tomorrow = datetime.now() + timedelta(days=1)
        year = tomorrow.year
        month = tomorrow.month
        day = tomorrow.day
        
        endpoint = f"flightstatus/rest/v2/json/flight/status/{carrier}/{flight_number}/arr/{year}/{month}/{day}"
        params = {'codeType': 'IATA'}
        response = self.make_request(endpoint, params)
        
        if response and 'flightStatuses' in response:
            logger.info(f"成功獲取航班 {carrier}{flight_number} 狀態")
            if response['flightStatuses']:
                logger.info(f"航班狀態: {json.dumps(response['flightStatuses'][0], ensure_ascii=False, indent=2)}")
            else:
                logger.warning(f"找不到航班 {carrier}{flight_number} 的狀態信息")
            return True
        else:
            logger.error(f"獲取航班 {carrier}{flight_number} 狀態失敗")
            return False

    def test_weather_api(self, airport_code="TPE"):
        """測試天氣 API"""
        logger.info(f"=== 測試天氣 API: {airport_code} ===")
        endpoint = f"weather/rest/v1/json/all/{airport_code}"
        params = {'codeType': 'IATA'}
        response = self.make_request(endpoint, params)
        
        if response and 'metar' in response:
            logger.info(f"成功獲取機場 {airport_code} 天氣")
            logger.info(f"天氣資訊: {json.dumps(response['metar'], ensure_ascii=False)}")
            return True
        else:
            logger.error(f"獲取機場 {airport_code} 天氣失敗")
            return False

    def test_flights_api(self, departure="TPE", arrival="NRT"):
        """測試航班 API"""
        logger.info(f"=== 測試航班 API: {departure} -> {arrival} ===")
        # 獲取明天的日期
        tomorrow = datetime.now() + timedelta(days=1)
        year = tomorrow.year
        month = tomorrow.month
        day = tomorrow.day
        
        endpoint = f"schedules/rest/v1/json/from/{departure}/to/{arrival}/departing/{year}/{month}/{day}"
        params = {'codeType': 'IATA'}
        response = self.make_request(endpoint, params)
        
        if response and 'scheduledFlights' in response:
            flights = response['scheduledFlights']
            logger.info(f"成功獲取 {len(flights)} 個 {departure}->{arrival} 航班")
            if flights:
                logger.info(f"範例航班: {json.dumps(flights[0], ensure_ascii=False, indent=2)}")
            return True
        else:
            logger.error(f"獲取 {departure}->{arrival} 航班失敗")
            return False

    def test_create_alert_api(self, carrier="CI", flight_number="100", arrival_airport="NRT"):
        """測試創建航班提醒 API"""
        logger.info(f"=== 測試創建航班提醒 API: {carrier}{flight_number} 到 {arrival_airport} ===")
        # 獲取明天的日期
        tomorrow = datetime.now() + timedelta(days=1)
        year = tomorrow.year
        month = tomorrow.month
        day = tomorrow.day
        
        endpoint = f"alerts/rest/v1/json/create/{carrier}/{flight_number}/to/{arrival_airport}/arriving/{year}/{month}/{day}"
        params = {
            'name': 'Default',
            'type': 'JSON'
        }
        response = self.make_request(endpoint, params)
        
        if response and 'alert' in response:
            logger.info(f"成功為航班 {carrier}{flight_number} 創建提醒")
            logger.info(f"提醒詳情: {json.dumps(response['alert'], ensure_ascii=False)}")
            return True
        else:
            logger.error(f"為航班 {carrier}{flight_number} 創建提醒失敗")
            return False

    def run_all_tests(self):
        """執行所有測試"""
        tests = [
            self.test_airlines_api,
            self.test_airports_api,
            self.test_specific_airport_api,
            self.test_airport_delay_api,
            self.test_flight_status_api,
            self.test_weather_api,
            self.test_flights_api,
            self.test_create_alert_api
        ]
        
        results = []
        
        for test in tests:
            try:
                result = test()
                results.append((test.__name__, result))
            except Exception as e:
                logger.error(f"測試 {test.__name__} 出錯: {str(e)}")
                results.append((test.__name__, False))
        
        # 輸出測試結果摘要
        logger.info("\n=== 測試結果摘要 ===")
        for name, result in results:
            status = "✓ 成功" if result else "✗ 失敗"
            logger.info(f"{status} - {name}")
        
        success_count = sum(1 for _, r in results if r)
        logger.info(f"總計: {success_count}/{len(results)} 個測試通過")

if __name__ == "__main__":
    try:
        tester = FlightStatsApiTester()
        tester.run_all_tests()
    except Exception as e:
        logger.error(f"測試過程中發生錯誤: {str(e)}") 