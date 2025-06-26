# 台灣航班整合系統 (Flight Integration System)

這是一個整合性的航班查詢系統，結合了 Flask 後端、Vue.js 3 前端，並部署在 Render 和 Vercel 上，同時包含基礎的 LINE Bot 整合。

## 系統特點

- **全端架構**: 使用 Flask (Python) 作為後端 API，Vue.js 3 (Vite + Tailwind CSS) 作為前端介面。
- **數據整合**: 使用 SQLAlchemy ORM 與 PostgreSQL (Neon) 資料庫交互。
- **異步處理**: 後端部分採用 async/await 提高性能。
- **API 驅動**: 前後端通過 RESTful API 進行通信。
- **雲端部署**: 後端部署於 Render，前端部署於 Vercel (均使用免費方案)。
- **LINE Bot 整合**: 提供基礎 Webhook 處理和 Rich Menu 重定向至前端。

## 技術棧

- **後端**: Python 3, Flask, SQLAlchemy, Flask-CORS, Gunicorn, asyncpg, psycopg2, line-bot-sdk, Amadeus for Developers Python SDK
- **前端**: Node.js, Vue.js 3 (Composition API), Vite, Tailwind CSS, Axios, Pinia, Vue Router
- **資料庫**: PostgreSQL (Neon)
- **部署**: Render (後端), Vercel (前端)
- **主要 API**: Amadeus for Developers

## 安裝與設定 (本地開發)

### 系統需求

- Python 3.8+ (建議 3.10+)
- Node.js (包含 npm)
- PostgreSQL 客戶端工具 (可選，用於直接操作資料庫)

### 後端設定

1.  **進入後端目錄**: `cd backend`
2.  **創建並激活虛擬環境**:
    ```bash
    # Windows
    python -m venv venv
    venv\Scripts\activate
    
    # macOS / Linux
    python3 -m venv venv
    source venv/bin/activate
    ```
3.  **安裝依賴**: `pip install -r requirements.txt`
4.  **設定環境變數**: 複製 `.env.example` 為 `.env`，並填寫必要的值:
    ```dotenv
    DATABASE_URL="postgresql://user:password@host:port/dbname" # 您的 Neon DB 連接字串
    FLASK_ENV=development
    # 填寫從 LINE Developers Console 獲取的憑證
    LINE_CHANNEL_ACCESS_TOKEN="YOUR_CHANNEL_ACCESS_TOKEN"
    LINE_CHANNEL_SECRET="YOUR_CHANNEL_SECRET"
    # 填寫從 Amadeus for Developers 獲取的憑證
    AMADEUS_CLIENT_ID="YOUR_AMADEUS_CLIENT_ID"
    AMADEUS_CLIENT_SECRET="YOUR_AMADEUS_CLIENT_SECRET"
    ```
5.  **啟動與資料庫檢查**: 由於我們不再使用 `Flask-Migrate`，請確保您的資料庫 schema 是最新的。您可以直接在 Neon 控制台或使用 SQL 客戶端工具進行管理。
6.  **維護腳本**:
    - 檢查有無需要更新的機場或航空公司
        `python -m app.scripts.show_pending_updates`

### 前端設定

1.  **進入前端目錄**: `cd ../frontend` (假設您在 backend 目錄)
2.  **安裝依賴**: `npm install`
3.  **設定環境變數**: 創建 `.env` 文件，並添加後端 API 地址:
    ```dotenv
    # 指向本地運行的後端服務
    VITE_API_BASE_URL=http://127.0.0.1:5000
    ```

## 本地運行

1.  **啟動後端服務**:
    *   確保在 `backend` 目錄下，且虛擬環境已激活。
    *   運行: `python run.py`
    *   服務預設在 `http://127.0.0.1:5000` 運行。
2.  **啟動前端開發伺服器**:
    *   確保在 `frontend` 目錄下。
    *   運行: `npm run dev`
    *   前端通常在 `http://localhost:5173` 或 `http://localhost:8080` 可訪問。

## 主要 API 端點

### Amadeus API (`/api/amadeus`)
- `GET /flights/offers`: 從 Amadeus API 實時搜索航班。這是系統目前獲取航班資訊的主要方式。
  - **查詢參數**:
    - `origin` (起飛機場 IATA 代碼, 必填)
    - `destination` (抵達機場 IATA 代碼, 必填)
    - `date` (出發日期 YYYY-MM-DD, 必填)
    - `adults` (成人乘客數量, 可選, 預設 1)
    - `nonStop` (是否僅查詢直飛航班, 'true' 或 'false', 可選, 預設 'false')

### 資料庫 API (從本地資料庫讀取)

#### 航班 (`/api/flights`)
- `GET /<string:flight_id>`: 獲取特定航班的詳細資訊。
- `GET /<string:departure_code>/destinations`: 獲取從指定 `departure_code` 機場出發可以到達的所有目的地機場列表。
- `GET /popular-routes`: 獲取熱門航線列表，分類為 `domestic` (台灣境內) 和 `international` (國際)。
- `GET /all-routes`: 獲取所有可查詢到的直飛航線列表，包含是否為熱門航線的標記。
- `GET /popular`: 獲取熱門航線的未來航班資訊。

#### 機場 (`/api/airports`)
- `GET /taiwan`: 獲取台灣所有機場的列表。
- `GET /<string:airport_id>`: 根據機場ID (IATA代碼) 獲取特定機場的詳細資訊。
- `GET /available-departures`: 獲取所有有未來出發航班的機場列表，按未來航班數量降序排序。
- `GET /available-destinations/<string:departure_code>`: 獲取從指定 `departure_code` 機場出發，有未來航班可達的目的地機場列表。

#### 航空公司 (`/api/airlines`)
- `GET /`: 獲取所有航空公司的列表 (包含 `logo_path`)。
- `GET /<string:airline_id>`: 根據航空公司ID (IATA代碼) 獲取特定航空公司的詳細資訊。
- `GET /search`: 根據名稱搜索航空公司。

### 價格分析 (未來規劃)
- `POST /api/flights/analyze-prices` (尚未實現): 分析指定航線的歷史價格趨勢。
  - **預期請求體 (JSON)**: `{ "departure_code": "TPE", "arrival_code": "NRT", "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD" }`
- `GET /api/ticket-prices/low-fare-calendar` (尚未實現): 查詢在指定日期範圍內，每天特定航線和艙等的最低票價。
  - **預期查詢參數**: `departure_code`, `arrival_code`, `start_date`, `end_date`, `cabin_class`

### LINE Bot
- `POST /api/line/webhook`: LINE Platform 的 Webhook 端點，用於接收和處理來自 LINE 的事件 (例如：用戶訊息、追蹤事件等)。

## 部署

### 後端 (Render - Free Tier)

1.  連接 GitHub 倉庫。
2.  創建 Web Service，選擇 Python 3 Runtime。
3.  **Root Directory**: `backend`
4.  **Build Command**: `pip install -r requirements.txt`
5.  **Start Command**: `gunicorn run:app`
6.  **環境變數**: 添加 `DATABASE_URL`, `FLASK_ENV=production`, `PYTHONUNBUFFERED=1`, `LINE_CHANNEL_ACCESS_TOKEN`, `LINE_CHANNEL_SECRET`, `AMADEUS_CLIENT_ID`, `AMADEUS_CLIENT_SECRET`。

### 前端 (Vercel - Free Tier)

1.  連接 GitHub 倉庫。
2.  框架選擇 `Vite`。
3.  **環境變數**: 添加 `VITE_API_BASE_URL`，指向您部署在 Render 上的後端服務地址。

## LINE Bot 整合

- 後端通過 `/api/line/webhook` 端點接收來自 LINE Platform 的事件。此端點負責驗證 LINE 簽名、解析事件內容，並根據事件類型（如文字訊息、追蹤事件、Postback 事件等）調用相應的處理邏輯。
- LINE Bot 的主要功能實現在 `backend/app/services/line_service.py` 和 `backend/app/controllers/line_webhook_controller.py` 中。
- 在 LINE Developers Console 中，Webhook URL 需設置為您後端服務部署後的 `/api/line/webhook` 地址。
- Rich Menu 功能已設計並可通過 LINE Developers Console 上傳設定，其按鈕動作可配置為發送 Postback 事件或 `uri` 動作（例如，重定向至前端網站的特定頁面）。

## 專案結構

```
FlightIntegration/
├── backend/              # Flask後端
│   ├── app/              # 應用核心
│   │   ├── controllers/  # API端點控制器 (包含 amadeus_controller.py)
│   │   ├── services/     # 業務邏輯服務 (包含 amadeus_service.py)
│   │   └── ...
│   ├── requirements.txt
│   └── run.py
├── frontend/             # Vue 3前端
│   ├── src/
│   │   ├── api/
│   │   │   └── services/
│   │   │       └── flightService.js  # API 呼叫服務
│   │   ├── views/
│   │   │   └── FlightSearch.vue      # 主要搜索頁面
│   │   └── ...
│   └── vite.config.js
└── README.md
```

## 未來工作

- **航班狀態查詢**: 使用 Amadeus API 重新實現航班狀態查詢功能。
- **資料清理腳本**: 建立一個定期清理舊航班資料的自動化腳本。
- **價格分析**: 擴展價格趨勢分析功能。
- **LINE Bot 增強**: 實現更多互動式查詢功能。

## 授權資訊

本專案僅供教育目的使用。使用外部 API 時，請遵守各自的使用條款和授權規定。