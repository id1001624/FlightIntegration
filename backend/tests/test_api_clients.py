#!/usr/bin/env python
"""
簡化版API客戶端測試腳本
只測試TDX API和FlightStats API客戶端的基本功能
"""
import os
import sys
import json
from datetime import datetime, timedelta

# 設置環境變數
os.environ['TDX_CLIENT_ID'] = 'n1116440-eff4950c-7994-47de'
os.environ['TDX_CLIENT_SECRET'] = 'efc87a00-3930-4be2-bca9-37f3b8f46d1d'
os.environ['FLIGHTSTATS_APP_ID'] = 'cb5c8184'
os.environ['FLIGHTSTATS_APP_KEY'] = '82304b41352d18995b0e7440a977cc1b'

# 導入要測試的API客戶端類別
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 將當前目錄添加到路徑
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# 創建TDX API測試類
class TdxApiClientTest:
    """TDX API客戶端測試"""
    
    def __init__(self):
        """初始化測試類"""
        self.client_id = os.environ.get('TDX_CLIENT_ID')
        self.client_secret = os.environ.get('TDX_CLIENT_SECRET')
        self.token_url = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
        self.base_url = "https://tdx.transportdata.tw/api/basic"
        self.access_token = None
    
    def get_token(self):
        """獲取API訪問令牌"""
        import requests
        
        try:
            headers = {'content-type': 'application/x-www-form-urlencoded'}
            data = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }
            
            response = requests.post(self.token_url, headers=headers, data=data)
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get('access_token')
                print("✓ 成功獲取TDX API訪問令牌")
                return True
            else:
                print(f"✗ 獲取TDX API訪問令牌失敗: {response.status_code}")
                print(f"  錯誤訊息: {response.text}")
                return False
        except Exception as e:
            print(f"! 獲取TDX API訪問令牌時出錯: {str(e)}")
            return False
    
    def test_get_airports(self):
        """測試獲取機場列表"""
        import requests
        
        if not self.access_token and not self.get_token():
            return False
        
        try:
            url = f"{self.base_url}/v2/Air/Airport"
            params = {
                '$format': 'JSON'
            }
            headers = {
                'Authorization': f'Bearer {self.access_token}'
            }
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    airports = data
                else:
                    airports = data.get('Airports', [])
                
                print(f"✓ 成功獲取 {len(airports)} 個機場")
                if airports and len(airports) > 0:
                    sample = airports[0]
                    print(f"  範例: {sample}")
                return True
            else:
                print(f"✗ 獲取機場列表失敗: {response.status_code}")
                print(f"  錯誤訊息: {response.text}")
                return False
        except Exception as e:
            print(f"! 獲取機場列表時出錯: {str(e)}")
            return False
    
    def test_get_airport(self, iata_code='TPE'):
        """測試獲取特定機場"""
        import requests
        
        if not self.access_token and not self.get_token():
            return False
        
        try:
            # 嘗試新的API路徑
            url = f"{self.base_url}/v2/Air/Airport/AirportID/{iata_code}"
            params = {'$format': 'JSON'}
            headers = {
                'Authorization': f'Bearer {self.access_token}'
            }
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    airport = data[0]
                    print(f"✓ 成功獲取機場 {iata_code}")
                    print(f"  機場數據: {airport}")
                    return True
                else:
                    print(f"✗ 找不到機場 {iata_code}")
                    print(f"  返回數據: {data}")
                    return False
            else:
                print(f"✗ 獲取機場 {iata_code} 失敗: {response.status_code}")
                print(f"  錯誤訊息: {response.text}")
                
                # 嘗試列出所有API端點
                print("\n嘗試調用API獲取可用端點...")
                try:
                    url = f"{self.base_url}/$metadata"
                    response = requests.get(url)
                    if response.status_code == 200:
                        print(f"  成功獲取API元數據，可以查看完整響應了解API結構")
                    else:
                        print(f"  獲取API元數據失敗: {response.status_code}")
                except Exception as e:
                    print(f"  獲取API元數據時出錯: {str(e)}")
                    
                return False
        except Exception as e:
            print(f"! 獲取機場時出錯: {str(e)}")
            return False
    
    def test_get_flight_schedule(self):
        """測試獲取航班時刻表"""
        import requests
        
        if not self.access_token and not self.get_token():
            return False
        
        try:
            date_str = datetime.now().strftime('%Y-%m-%d')
            url = f"{self.base_url}/v2/Air/FIDS/Airport/Departure/TPE"
            params = {
                '$format': 'JSON',
                '$filter': f"date(ScheduleDepartureTime) eq {date_str}"
            }
            headers = {
                'Authorization': f'Bearer {self.access_token}'
            }
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    flights = data
                else:
                    flights = data.get('FIDSAirport', [])
                
                print(f"✓ 成功獲取 {len(flights)} 個航班時刻")
                if flights and len(flights) > 0:
                    sample = flights[0]
                    print(f"  範例: {sample}")
                return True
            else:
                print(f"✗ 獲取航班時刻表失敗: {response.status_code}")
                print(f"  錯誤訊息: {response.text}")
                return False
        except Exception as e:
            print(f"! 獲取航班時刻表時出錯: {str(e)}")
            return False

# 創建FlightStats API測試類
class FlightStatsApiClientTest:
    """FlightStats API客戶端測試"""
    
    def __init__(self):
        """初始化測試類"""
        self.app_id = os.environ.get('FLIGHTSTATS_APP_ID')
        self.app_key = os.environ.get('FLIGHTSTATS_APP_KEY')
        self.base_url = "https://api.flightstats.com/flex"
    
    def test_get_airport(self, iata_code='NRT'):
        """測試獲取特定機場"""
        import requests
        
        try:
            url = f"{self.base_url}/airports/rest/v1/json/iata/{iata_code}"
            params = {
                'appId': self.app_id,
                'appKey': self.app_key
            }
            
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                airport = data.get('airport', {})
                if airport:
                    print(f"✓ 成功獲取機場 {iata_code} - {airport.get('name')}")
                    return True
                else:
                    print(f"✗ 找不到機場 {iata_code}")
                    return False
            else:
                print(f"✗ 獲取機場 {iata_code} 失敗: {response.status_code}")
                print(f"  錯誤訊息: {response.text}")
                return False
        except Exception as e:
            print(f"! 獲取機場時出錯: {str(e)}")
            return False
    
    def test_get_airline(self, iata_code='NH'):
        """測試獲取特定航空公司"""
        import requests
        
        try:
            url = f"{self.base_url}/airlines/rest/v1/json/iata/{iata_code}"
            params = {
                'appId': self.app_id,
                'appKey': self.app_key
            }
            
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                airline = data.get('airline', {})
                if airline:
                    print(f"✓ 成功獲取航空公司 {iata_code} - {airline.get('name')}")
                    return True
                else:
                    print(f"✗ 找不到航空公司 {iata_code}")
                    return False
            else:
                print(f"✗ 獲取航空公司 {iata_code} 失敗: {response.status_code}")
                print(f"  錯誤訊息: {response.text}")
                return False
        except Exception as e:
            print(f"! 獲取航空公司時出錯: {str(e)}")
            return False
    
    def test_get_flights(self, departure_iata='TPE', arrival_iata='NRT', date=None):
        """測試獲取航班"""
        import requests
        
        if date is None:
            now = datetime.now() + timedelta(days=1)
            year = now.year
            month = now.month
            day = now.day
        else:
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            year = date_obj.year
            month = date_obj.month
            day = date_obj.day
        
        try:
            url = f"{self.base_url}/schedules/rest/v1/json/from/{departure_iata}/to/{arrival_iata}/departing/{year}/{month}/{day}"
            params = {
                'appId': self.app_id,
                'appKey': self.app_key
            }
            
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                flights = data.get('scheduledFlights', [])
                print(f"✓ 成功獲取 {len(flights)} 個 {departure_iata}->{arrival_iata} 航班")
                if flights and len(flights) > 0:
                    sample = flights[0]
                    flight_info = []
                    
                    if 'carrier' in sample and 'iata' in sample['carrier']:
                        flight_info.append(sample['carrier']['iata'])
                    
                    if 'flightNumber' in sample:
                        flight_info.append(sample['flightNumber'])
                    
                    if 'departureTime' in sample:
                        dep_time = sample['departureTime']
                        if 'dateLocal' in dep_time and 'timeLocal' in dep_time:
                            flight_info.append(f"{dep_time['dateLocal']} {dep_time['timeLocal']}")
                    
                    print(f"  範例: {' - '.join(flight_info)}")
                return True
            else:
                print(f"✗ 獲取航班失敗: {response.status_code}")
                print(f"  錯誤訊息: {response.text}")
                return False
        except Exception as e:
            print(f"! 獲取航班時出錯: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

def run_tests():
    """運行所有測試"""
    print("\n========== 測試 TDX API ==========")
    tdx_test = TdxApiClientTest()
    
    print("1. 測試獲取訪問令牌")
    tdx_test.get_token()
    
    print("\n2. 測試獲取機場列表")
    tdx_test.test_get_airports()
    
    print("\n3. 測試獲取特定機場")
    tdx_test.test_get_airport('TPE')
    
    print("\n4. 測試獲取航班時刻表")
    tdx_test.test_get_flight_schedule()
    
    print("\n========== 測試 FlightStats API ==========")
    fs_test = FlightStatsApiClientTest()
    
    print("1. 測試獲取特定機場")
    fs_test.test_get_airport('NRT')
    
    print("\n2. 測試獲取特定航空公司")
    fs_test.test_get_airline('NH')
    
    print("\n3. 測試獲取航班")
    fs_test.test_get_flights('TPE', 'NRT')
    
    print("\n測試完成")

if __name__ == "__main__":
    run_tests() 