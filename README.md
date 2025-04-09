# 台灣航班整合系統 (Flight Integration System)

這個系統整合了台灣交通資料平台(TDX)和FlightStats的API，提供台灣航班資料的查詢和同步功能。

## 系統特點

- 整合TDX和FlightStats兩種航班API資料來源
- 自動同步航空公司、機場和航班資料到本地資料庫
- 支援台灣出發的國內和國際航線資料查詢
- 自動翻譯航班相關資訊（如機場和航空公司名稱）
- 提供簡單的資料同步和查詢介面

## 安裝與設定

### 系統需求

- Python 3.8+
- PostgreSQL資料庫
- 必要的Python套件（詳見下方設定步驟）

### 設定步驟

1. 克隆此專案到本地：
   ```
   git clone [專案網址]
   cd FlightIntegration
   ```

2. 啟動虛擬環境:
   ```
   venv\Scripts\activate
   ```

3. 安裝所需的Python套件：
   ```
   pip install -r requirements.txt
   ```

4. 確認或修改`.env`檔案中的設定，包括資料庫連接和API金鑰：
   ```
   # 資料庫設定
   DB_USER=neondb_owner
   DB_PASSWORD=你的密碼
   DB_HOST=你的資料庫主機
   DB_PORT=5432
   DB_NAME=flight_integration
   
   # TDX API設定
   TDX_CLIENT_ID=你的TDX客戶端ID
   TDX_CLIENT_SECRET=你的TDX客戶端密鑰
   
   # FlightStats API設定
   FLIGHTSTATS_APP_ID=你的FlightStats應用ID
   FLIGHTSTATS_APP_KEY=你的FlightStats應用金鑰
   ```

## 執行流程

### 1. 資料同步與更新

使用`sync_flight_data.py`腳本可以一次完成API調用和資料庫更新。

```bash
# 測試API和資料庫連接狀態
python backend/sync_flight_data.py test

# 同步所有資料（航空公司、機場和台灣出發的航班）
python backend/sync_flight_data.py all

# 只同步航空公司資料
python backend/sync_flight_data.py airlines

# 只同步機場資料
python backend/sync_flight_data.py airports

# 同步特定航線的航班資料（例如：台北飛東京）
python backend/sync_flight_data.py flights --departure TPE --arrival NRT --date 2025-04-01 --days 2

# 同步所有從台灣出發的航班
python backend/sync_flight_data.py taiwan --date 2025-04-01 --days 2

# 同步航班表而已
python sync_flight_data.py flights-only --date 2025-04-07

```



### 2. 啟動後端服務

同步資料後，可以啟動Flask後端服務：

```bash
# 切換到backend目錄
cd backend

# 啟動Flask應用
python run.py
```

服務預設會在 http://localhost:5000 運行。

### 3. 前端查詢

前端可以通過API查詢航班資料，例如：

- 取得航空公司列表：`GET /api/airlines`
- 取得機場列表：`GET /api/airports`
- 查詢航班詳情API：`/api/flights/{flightId}`
- 查詢機場出發的航班：`GET /api/airports/TPE/departures`
- 查詢機場到達的航班：`GET /api/airports/TPE/arrivals`
- 航線：`GET /api/flights/search?departure=TPE&arrival=KHH&date=2025-04-07`

## 演示步驟（適合向老師展示）

1. **測試系統連接狀態**：
   ```bash
   python backend/sync_flight_data.py test
   ```
   此步驟會檢查API連接和資料庫連接是否正常。

2. **同步基礎資料**：
   ```bash
   python backend/sync_flight_data.py airlines
   python backend/sync_flight_data.py airports
   ```
   此步驟會從API獲取航空公司和機場資料，並同步到資料庫。

3. **同步航班資料**：
   ```bash
   # 同步台北飛東京的航班
   python backend/sync_flight_data.py flights --departure TPE --arrival NRT --date 2025-04-01 --days 1
   ```
   此步驟會同步特定航線的航班資料到資料庫。

4. **啟動後端服務**：
   ```bash
   cd backend
   python run.py
   ```
   此步驟會啟動後端服務，使前端可以查詢資料。

5. **前端查詢演示**：
   訪問 http://localhost:5000/debug/flights 可以查看已同步的航班資料。

## 常見問題解答

1. **為什麼需要同時使用TDX和FlightStats API？**
   
   TDX API提供的是台灣本地航班資料，而FlightStats提供全球航班資料。TDX的資料更新較及時但國際航線資料較少，FlightStats的國際航線資料較完整但收費較高，兩者互補可提供更完整的航班資訊。

2. **資料庫中的航班資料多久更新一次？**
   
   建議每天更新一次資料，可以設定自動排程每天執行`sync_flight_data.py all`命令。

3. **如何獲取TDX和FlightStats的API金鑰？**
   
   - TDX API：前往[台灣交通資料平台](https://tdx.transportdata.tw/)註冊會員並申請API金鑰。
   - FlightStats API：前往[FlightStats Developer Center](https://developer.flightstats.com/)註冊開發者帳號並申請API金鑰。

## 授權資訊

本專案僅供教育目的使用。使用TDX和FlightStats API時，請遵守各自的使用條款和授權規定。