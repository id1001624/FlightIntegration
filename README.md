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

- **後端**: Python 3, Flask, SQLAlchemy, Flask-Migrate, Flask-CORS, Gunicorn, asyncpg, psycopg2, line-bot-sdk
- **前端**: Node.js, Vue.js 3 (Composition API), Vite, Tailwind CSS, Axios, Pinia (如果使用), Vue Router
- **資料庫**: PostgreSQL (Neon)
- **部署**: Render (後端), Vercel (前端)

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
    ```
5.  **資料庫遷移**: (如果這是首次設定或模型有變更)
    ```bash
    flask db init # 只需要第一次
    flask db migrate -m "Initial migration" # 或描述性訊息
    flask db upgrade
    ```
6.  **填充初始/航班真資料、票價假資料**: 
    
    只導入某路線測試
    ```bash
    python -m backend.app.scripts.sync_flight_data flights -d TPE -a NRT --limit 5
    ```
    
    航班真資料調用 TDX、FlightStats API 導入資料庫
    ```bash
    python -m backend.app.scripts.sync_flight_data flights-only
    ```

    目前還沒有票價資料，先用腳本模擬資料
    ```bash
    python backend/app/scripts/generate_fake_prices.py
    ```

    模擬航班資料
    - 生成3天的資料，每天約200個航班，從今天開始
        python app/scripts/generate_dummy_flight_data.py

    - 生成7天的資料，每天約500個航班，從2023-12-01開始
        python backend/app/scripts/generate_dummy_flight_data.py --days 7 --flights-per-day 300 --start-date 2025-05-05

    - 刪除測試的航班資料
        python backend/app/scripts/generate_dummy_flight_data.py --start-date 2030-01-01 --clear-only

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
    *   前端通常在 `http://localhost:8080` 可訪問。

## 主要 API 端點

### 航班 (`/api/flights`)
- `GET /search`: 搜索航班。
  - **查詢參數**:
    - `departure` (起飛機場代碼, 必填)
    - `arrival` (抵達機場代碼, 必填)
    - `date` (日期 YYYY-MM-DD, 必填)
    - `return_date` (回程日期 YYYY-MM-DD, 可選)
    - `airlines` (航空公司代碼列表，以逗號分隔，可選)
    - `price_min` (最低價格, 可選)
    - `price_max` (最高價格, 可選)
    - `cabin_class` (艙等, 預設 "經濟")
    - `only_target_airlines` (布林值，是否僅搜索目標航空公司, 預設 false)
    - `adults` (成人乘客數量, 預設 1)
    - `max_results` (最大結果數量, 預設 50)
    - `sort_by` (排序依據, 例如 "price", "departure_time", 預設 "price")
- `GET /from_taiwan/<string:arrival_iata>`: 獲取從台灣所有機場飛往指定 `arrival_iata` 機場的航班。
  - **路徑參數**: `arrival_iata` (抵達機場的IATA代碼)
  - **查詢參數**:
    - `date` (日期 YYYY-MM-DD, 必填)
    - `airlines` (航空公司代碼列表，以逗號分隔，可選)
    - `price_min` (最低價格, 可選)
    - `price_max` (最高價格, 可選)
    - `cabin_class` (艙等, 預設 "經濟")
    - `adults` (成人乘客數量, 預設 1)
    - `max_results` (最大結果數量, 預設 50)
    - `sort_by` (排序依據, 預設 "price")
    - `only_target_airlines` (布林值，是否僅搜索目標航空公司, 預設 false)
- `GET /<string:flight_id>`: 獲取特定航班的詳細資訊。
  - **路徑參數**: `flight_id` (航班的唯一ID)
- `GET /<string:departure_code>/destinations`: 獲取從指定 `departure_code` 機場出發可以到達的所有目的地機場列表。
  - **路徑參數**: `departure_code` (出發機場的IATA代碼)
  - **查詢參數**:
    - `date` (日期 YYYY-MM-DD, 可選，用於過濾特定日期的目的地)
- `GET /popular-routes`: 獲取熱門航線列表，分類為 `domestic` (台灣境內) 和 `international` (國際)。
- `GET /all-routes`: 獲取所有可查詢到的直飛航線列表，包含是否為熱門航線的標記。
- `GET /<string:flight_id>/status`: 獲取特定航班的最新狀態 (資訊來源 FlightStats)。
  - **路徑參數**: `flight_id` (航班的唯一ID)
- `GET /popular`: 獲取熱門航線的未來航班資訊。
  - **查詢參數**:
    - `limit` (返回的最大航班數量, 預設 20, 最大 100)
    - `cabin_class` (用於格式化價格的艙等，例如 "經濟", "商務", "頭等", 預設 "經濟")

### 機場 (`/api/airports`)
- `GET /`: 獲取機場列表 (當前實現為獲取台灣機場，與 `/taiwan` 功能相似)。
- `GET /taiwan`: 獲取台灣所有機場的列表。
- `GET /<string:airport_id>`: 根據機場ID (IATA代碼) 獲取特定機場的詳細資訊。
  - **路徑參數**: `airport_id` (機場的IATA代碼)
- `GET /available-departures`: 獲取所有有未來出發航班的機場列表，按未來航班數量降序排序。
- `GET /available-destinations/<string:departure_code>`: 獲取從指定 `departure_code` 機場出發，有未來航班可達的目的地機場列表。
  - **路徑參數**: `departure_code` (出發機場的IATA代碼)

### 航空公司 (`/api/airlines`)
- `GET /`: 獲取所有航空公司的列表 (包含 `logo_path`)。
- `GET /domestic`: 獲取所有被標記為台灣國內線的航空公司。
- `GET /international`: 獲取所有被標記為國際線的航空公司。
- `GET /<string:airline_id>`: 根據航空公司ID (IATA代碼) 獲取特定航空公司的詳細資訊。
  - **路徑參數**: `airline_id` (航空公司的IATA代碼)
- `GET /search`: 根據名稱搜索航空公司。
  - **查詢參數**: `name` (搜索關鍵詞, 必填)

### 價格分析 (未來規劃)
- `POST /api/flights/analyze-prices` (尚未實現): 分析指定航線的歷史價格趨勢。
  - **預期請求體 (JSON)**: `{ "departure_code": "TPE", "arrival_code": "NRT", "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD" }`
- `GET /api/ticket-prices/low-fare-calendar` (尚未實現): 查詢在指定日期範圍內，每天特定航線和艙等的最低票價。
  - **預期查詢參數**: `departure_code`, `arrival_code`, `start_date`, `end_date`, `cabin_class`

### 資料同步與生成 (POST請求，主要用於開發和維護)
- `POST /api/flights/sync-taiwan-flights`: 從外部源同步特定日期範圍內台灣出發的航班數據。
  - **請求體 (JSON)**:
    - `date` (開始同步的日期 YYYY-MM-DD, 必填)
    - `days` (從開始日期算起，需要同步的天數, 必填)
- `POST /api/flights/generate-test-data`: 為特定航線生成指定天數的測試航班和票價數據。
  - **請求體 (JSON)**:
    - `departure` (起飛機場IATA代碼, 必填)
    - `arrival` (抵達機場IATA代碼, 必填)
    - `start_date` (開始日期 YYYY-MM-DD, 必填)
    - `num_days` (生成數據的天數, 必填)
    - `flights_per_day` (每天生成的航班數量, 必填)

### LINE Bot
- `POST /api/line/webhook`: LINE Platform 的 Webhook 端點，用於接收和處理來自 LINE 的事件 (例如：用戶訊息、追蹤事件等)。

## 部署

### 後端 (Render - Free Tier)

1.  連接 GitHub 倉庫。
2.  創建 Web Service，選擇 Python 3 Runtime。
3.  **Root Directory**: `backend`
4.  **Build Command**: `pip install -r requirements.txt`
5.  **Start Command**: `gunicorn run:app`
6.  **環境變數**: 添加 `DATABASE_URL`, `FLASK_ENV=production`, `PYTHONUNBUFFERED=1`, `LINE_CHANNEL_ACCESS_TOKEN`, `LINE_CHANNEL_SECRET`。

### 前端 (Vercel - Free Tier)

1.  連接 GitHub 倉庫。
2.  **Framework Preset**: Vite
3.  **Root Directory**: `frontend`
4.  **環境變數**: 添加 `VITE_API_BASE_URL`，值為部署後 Render 後端的 URL (例如 `https://your-backend-name.onrender.com`)。

## LINE Bot 整合

- 後端通過 `/api/line/webhook` 端點接收來自 LINE Platform 的事件。此端點負責驗證 LINE 簽名、解析事件內容，並根據事件類型（如文字訊息、追蹤事件、Postback 事件等）調用相應的處理邏輯。
- LINE Bot 的主要功能實現在 `backend/app/services/line_service.py` 和 `backend/app/controllers/line_controller.py` 中。
- 在 LINE Developers Console 中，Webhook URL 需設置為您後端服務部署後的 `/api/line/webhook` 地址。
- Rich Menu 功能已設計並可通過 LINE Developers Console 上傳設定，其按鈕動作可配置為發送 Postback 事件或 `uri` 動作（例如，重定向至前端網站的特定頁面）。

## 授權資訊

本專案僅供教育目的使用。使用外部 API 時，請遵守各自的使用條款和授權規定。