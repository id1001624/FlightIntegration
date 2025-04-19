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
    
    航班真資料調用 TDX、FlightStats API 導入資料庫
    ```bash
    python app/scripts/generate_fake_prices.py
    ```

    目前還沒有票價資料，先用腳本模擬資料
    ```bash
    python app/scripts/generate_fake_prices.py
    ```

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

- `GET /api/flights/search`: 搜索航班 (主要端點)
  - 參數: `departure`, `arrival`, `date`, `class_type`, `return_date` (可選)
- `GET /api/flights/<flight_id>`: 獲取單一航班詳情
- `GET /api/airports/taiwan`: 獲取台灣機場列表
- `GET /api/flights/{departure}/destinations`: 獲取從指定機場出發的可達目的地
- `GET /api/airlines`: 獲取航空公司列表 (包含 logo_path)

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

- 後端包含一個基礎的 Webhook Handler (`/api/line/webhook`)，用於驗證 LINE 簽名並響應。
- 在 LINE Developers Console 中設置 Webhook URL 指向部署後的後端地址。
- 創建了一個簡單的 Rich Menu，其按鈕動作類型為 `uri`，指向部署後的前端網站 URL。

## 授權資訊

本專案僅供教育目的使用。使用外部 API 時，請遵守各自的使用條款和授權規定。