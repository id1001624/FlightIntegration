# TDX 航空 API 使用文檔

## 概述

本文檔說明如何使用 TDX（Transport Data eXchange，運輸資料流通服務平臺）提供的航空相關 API。TDX 平臺提供了豐富的交通資料，包括航空、鐵路、公車等多種交通方式的即時和靜態資料。本文檔專注於航空相關 API 的使用方法。

## 目錄

- [前置準備](#前置準備)
- [API 認證機制](#api-認證機制)
- [Python 程式碼範例](#python-程式碼範例)
- [航空 API 說明](#航空-api-說明)
- [常見問題與解決方案](#常見問題與解決方案)
- [API 使用限制](#api-使用限制)
- [參考資源](#參考資源)

## 前置準備

在開始使用 TDX 航空 API 之前，您需要：

1. 註冊成為 TDX 會員
2. 取得 API 金鑰（Client ID 和 Client Secret）
3. 準備開發環境，安裝必要的 Python 套件

### 必要的 Python 套件

```bash
pip install requests
```

## API 認證機制

TDX API 使用 OIDC Client Credentials 流程進行身份認證。取得 Access Token 後，將其帶入 API 請求中即可存取 TDX API 服務。

### 認證流程簡述

1. **註冊為 TDX 會員**：在 [TDX 官網](https://tdx.transportdata.tw/register) 完成註冊和信箱驗證。
2. **取得 API 金鑰**：登入後，在 [TDX 會員中心](https://tdx.transportdata.tw/user/dataservice/key) 取得 Client ID 和 Client Secret。
3. **取得 Access Token**：使用 API 金鑰通過 API 取得 Access Token。
4. **呼叫 API 服務**：在 API 請求中帶入 Access Token。

### Token 獲取範例 

```python
import requests
import json

class TDXAuth:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.auth_url = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
        self.token = None
        
    def get_token(self):
        """取得 TDX API 的 Access Token"""
        # 如果已有 token，直接返回
        if self.token:
            return self.token
            
        # 準備取得 token 的請求資料
        headers = {"content-type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        # 發送請求取得 token
        response = requests.post(self.auth_url, headers=headers, data=data)
        
        # 檢查回應狀態
        if response.status_code != 200:
            raise Exception(f"取得 token 失敗: {response.status_code} {response.text}")
            
        # 解析回應並儲存 token
        response_data = json.loads(response.text)
        self.token = response_data.get("access_token")
        
        return self.token
    
    def get_auth_header(self):
        """取得用於 API 請求的認證 header"""
        token = self.get_token()
        return {
            "authorization": f"Bearer {token}",
            "Accept-Encoding": "gzip"  # 建議加入，可減少回傳資料量
        }
```

## Python 程式碼範例

以下是使用 Python 獲取航班即時資訊的完整範例：

```python
import requests
import json
from datetime import datetime

# TDX 認證類
class TDXAuth:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.auth_url = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
        self.token = None
        
    def get_token(self):
        """取得 TDX API 的 Access Token"""
        # 如果已有 token，直接返回
        if self.token:
            return self.token
            
        # 準備取得 token 的請求資料
        headers = {"content-type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        # 發送請求取得 token
        response = requests.post(self.auth_url, headers=headers, data=data)
        
        # 檢查回應狀態
        if response.status_code != 200:
            raise Exception(f"取得 token 失敗: {response.status_code} {response.text}")
            
        # 解析回應並儲存 token
        response_data = json.loads(response.text)
        self.token = response_data.get("access_token")
        
        return self.token
    
    def get_auth_header(self):
        """取得用於 API 請求的認證 header"""
        token = self.get_token()
        return {
            "authorization": f"Bearer {token}",
            "Accept-Encoding": "gzip"  # 建議加入，可減少回傳資料量
        }

# 航空資料類
class TDXAirAPI:
    def __init__(self, auth):
        self.auth = auth
        self.base_url = "https://tdx.transportdata.tw/api/basic/v2/Air"
    
    def get_airport_info(self, airport_code=None):
        """獲取機場基本資訊
        
        Args:
            airport_code: 機場 IATA 代碼，如 'TPE' 代表臺灣桃園國際機場
                          若不指定，則獲取所有機場資訊
        
        Returns:
            機場資訊的 JSON 資料
        """
        url = f"{self.base_url}/Airport"
        if airport_code:
            url = f"{url}/{airport_code}"
        
        url = f"{url}?$format=JSON"
        
        response = requests.get(url, headers=self.auth.get_auth_header())
        
        if response.status_code != 200:
            raise Exception(f"獲取機場資訊失敗: {response.status_code} {response.text}")
            
        return json.loads(response.text)
    
    def get_flight_arrival(self, airport_code):
        """獲取指定機場的抵達航班即時資訊
        
        Args:
            airport_code: 機場 IATA 代碼
        
        Returns:
            抵達航班資訊的 JSON 資料
        """
        url = f"{self.base_url}/FIDS/Airport/Arrival/{airport_code}?$format=JSON"
        
        response = requests.get(url, headers=self.auth.get_auth_header())
        
        if response.status_code != 200:
            raise Exception(f"獲取抵達航班資訊失敗: {response.status_code} {response.text}")
            
        return json.loads(response.text)
    
    def get_flight_departure(self, airport_code):
        """獲取指定機場的出發航班即時資訊
        
        Args:
            airport_code: 機場 IATA 代碼
        
        Returns:
            出發航班資訊的 JSON 資料
        """
        url = f"{self.base_url}/FIDS/Airport/Departure/{airport_code}?$format=JSON"
        
        response = requests.get(url, headers=self.auth.get_auth_header())
        
        if response.status_code != 200:
            raise Exception(f"獲取出發航班資訊失敗: {response.status_code} {response.text}")
            
        return json.loads(response.text)
    
    def get_airline_info(self, airline_code=None):
        """獲取航空公司基本資訊
        
        Args:
            airline_code: 航空公司 IATA 代碼，如 'CI' 代表中華航空
                          若不指定，則獲取所有航空公司資訊
        
        Returns:
            航空公司資訊的 JSON 資料
        """
        url = f"{self.base_url}/Airline"
        if airline_code:
            url = f"{url}/{airline_code}"
        
        url = f"{url}?$format=JSON"
        
        response = requests.get(url, headers=self.auth.get_auth_header())
        
        if response.status_code != 200:
            raise Exception(f"獲取航空公司資訊失敗: {response.status_code} {response.text}")
            
        return json.loads(response.text)
    
    def get_flight_info(self, airline_code, flight_number, date=None):
        """獲取特定航班的資訊
        
        Args:
            airline_code: 航空公司 IATA 代碼
            flight_number: 航班編號
            date: 日期，格式為 "YYYY-MM-DD"，若不指定則使用今天的日期
        
        Returns:
            航班資訊的 JSON 資料
        """
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
            
        url = f"{self.base_url}/Flight/{airline_code}/{flight_number}/{date}?$format=JSON"
        
        response = requests.get(url, headers=self.auth.get_auth_header())
        
        if response.status_code != 200:
            raise Exception(f"獲取航班資訊失敗: {response.status_code} {response.text}")
            
        return json.loads(response.text)

# 使用範例
if __name__ == "__main__":
    # 請替換為您的 Client ID 和 Client Secret
    client_id = "YOUR_CLIENT_ID"
    client_secret = "YOUR_CLIENT_SECRET"
    
    # 創建認證實例
    auth = TDXAuth(client_id, client_secret)
    
    # 創建航空 API 實例
    air_api = TDXAirAPI(auth)
    
    try:
        # 獲取台灣桃園國際機場資訊
        airport_info = air_api.get_airport_info("TPE")
        print("桃園機場資訊:")
        print(json.dumps(airport_info, indent=2, ensure_ascii=False))
        
        # 獲取桃園機場的抵達航班
        arrival_flights = air_api.get_flight_arrival("TPE")
        print("\n桃園機場抵達航班:")
        print(json.dumps(arrival_flights, indent=2, ensure_ascii=False))
        
        # 獲取中華航空的資訊
        airline_info = air_api.get_airline_info("CI")
        print("\n中華航空資訊:")
        print(json.dumps(airline_info, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"發生錯誤: {str(e)}")
```

## 航空 API 說明

TDX 提供了多種航空相關的 API，以下是一些主要的 API 端點和說明：

### 1. 機場資訊 API

取得國內外機場的基本資料，如機場名稱、位置、代碼等。

- 端點：`/api/basic/v2/Air/Airport`
- 參數：
  - `$format`：回傳資料格式，如 JSON
  - `$select`：指定所需欄位
  - `$filter`：篩選條件
  - `$orderby`：排序條件
  - `$top`：回傳資料筆數

### 2. 航空公司資訊 API

取得航空公司的基本資料，如航空公司名稱、代碼等。

- 端點：`/api/basic/v2/Air/Airline`
- 參數：同上

### 3. 航班資訊 API

取得特定航班的詳細資訊。

- 端點：`/api/basic/v2/Air/Flight/{AirlineID}/{FlightNumber}/{ScheduleDate}`
- 參數：
  - `AirlineID`：航空公司 IATA 代碼
  - `FlightNumber`：航班編號
  - `ScheduleDate`：航班日期 (YYYY-MM-DD)

### 4. 機場航班動態顯示系統 API

取得機場出發或抵達航班的即時資訊。

- 出發航班：`/api/basic/v2/Air/FIDS/Airport/Departure/{AirportID}`
- 抵達航班：`/api/basic/v2/Air/FIDS/Airport/Arrival/{AirportID}`
- 參數：
  - `AirportID`：機場 IATA 代碼

## 常見問題與解決方案

### 1. Access Token 過期

問題：API 回應 401 Unauthorized 錯誤。

解決方案：重新取得 Access Token。建議實作 Token 快取機制，只在 Token 過期時才重新取得。

### 2. 呼叫頻率限制

問題：API 回應 429 "API rate limit exceeded" 錯誤。

解決方案：減少 API 呼叫頻率，或升級您的 TDX 會員方案。

### 3. 資料解析錯誤

問題：從 API 獲取的資料無法正確解析。

解決方案：確認使用的 API 版本和回傳格式是否正確。例如，在 API 端點添加 `?$format=JSON` 確保回傳 JSON 格式。

## API 使用限制

TDX API 有使用頻率限制，具體限制取決於您的會員訂閱方案：

1. **Access Token API**：每個 IP 來源每分鐘最多呼叫 20 次。
2. **API 服務**：根據您的訂閱方案有不同的限制，詳情請參考 [TDX 訂閱收費](https://tdx.transportdata.tw/pricing)。

為避免頻繁取得 Token 造成資源浪費，建議實作 Token 快取機制：

1. 程式定期重新取得 Token，如每 4-6 小時一次。
2. 初次呼叫 API 時取得 Token，只在 Token 過期時才重新取得。

## 參考資源

- [TDX API Swagger 文件](https://tdx.transportdata.tw/api-service/swagger)
- [TDX 新手指引](https://motc-ptx.gitbook.io/tdx-xin-shou-zhi-yin/api-shi-yong-shuo-ming/api-shou-quan-yan-zheng-yu-shi-yong-fang-shi)
- [TDX 訂閱收費方案](https://tdx.transportdata.tw/pricing) 