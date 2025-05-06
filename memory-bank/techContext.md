# 技術環境上下文

## 技術堆疊

### 前端技術

- **前端框架**: Vue.js 3 (Composition API)
- **構建工具**: Vite
- **CSS 框架**: Tailwind CSS
- **HTTP 客戶端**: Axios
- **狀態管理**: Pinia
- **路由**: Vue Router
- **編程語言**: JavaScript/TypeScript

### 後端技術

- **Web 框架**: Flask
- **ORM**: SQLAlchemy
- **遷移工具**: Flask-Migrate
- **API 框架**: Flask-RESTful/Flask-RESTX
- **跨域支持**: Flask-CORS
- **Web 服務器**: Gunicorn
- **API 文檔工具**: Swagger UI (通過 Flask-RESTX)
- **編程語言**: Python 3

### 資料庫

- **資料庫系統**: PostgreSQL
- **雲服務**: Neon (Cloud PostgreSQL)
- **連接庫**: 
  - asyncpg (異步連接)
  - psycopg2 (同步連接)

### 外部 API 整合

- **TDX API**: 交通部開放資料平台
- **FlightStats API**: 航班狀態和動態信息
- **LINE Messaging API**: LINE 機器人功能

### 部署環境

- **後端部署**: Render (Free Tier)
- **前端部署**: Vercel (Free Tier)
- **CI/CD**: GitHub Actions

## 系統架構

### 後端結構

```
backend/
├── app/                # 應用核心
│   ├── models/         # 資料庫模型
│   ├── controllers/    # API 端點控制器
│   ├── services/       # 業務邏輯服務
│   ├── schemas/        # 資料序列化模式
│   ├── utils/          # 工具函數
│   ├── scripts/        # 資料同步腳本
│   └── static/         # 靜態資源
├── tests/              # 測試
├── debug/              # 調試工具
└── logs/               # 日誌文件
```

### 前端結構

```
frontend/
├── src/             # 源代碼
│   ├── components/  # UI 元件
│   ├── views/       # 頁面
│   ├── router/      # 路由
│   ├── store/       # 狀態管理
│   ├── api/         # API 服務
│   └── utils/       # 工具函數
└── dist/            # 構建輸出
```

## 開發環境設置

### 系統要求

- **Python**: 3.8+ (推薦 3.10+)
- **Node.js**: 16+
- **PostgreSQL 客戶端工具**: 可選，用於本地調試

### 後端設置

1. **創建虛擬環境**:
   ```bash
   cd backend
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

2. **安裝依賴**:
   ```bash
   pip install -r requirements.txt
   ```

3. **環境變量設置**:
   創建 `.env` 文件（基於 `.env.example`）並設置必要的環境變量:
   ```
   DATABASE_URL=postgresql://user:password@localhost/flight_integration
   FLASK_APP=app
   FLASK_ENV=development
   TDX_CLIENT_ID=your_tdx_client_id
   TDX_CLIENT_SECRET=your_tdx_client_secret
   LINE_CHANNEL_SECRET=your_line_channel_secret
   LINE_CHANNEL_ACCESS_TOKEN=your_line_access_token
   ```

4. **遷移數據庫**:
   ```bash
   flask db upgrade
   ```

5. **啟動服務**:
   ```bash
   # 開發模式
   flask run --debug
   # 或使用 Gunicorn
   gunicorn -w 4 -b 127.0.0.1:5000 "app:create_app()"
   ```

### 前端設置

1. **安裝依賴**:
   ```bash
   cd frontend
   npm install
   ```

2. **環境變量設置**:
   創建 `.env` 文件:
   ```
   VITE_API_BASE_URL=http://localhost:5000/api/v1
   ```

3. **啟動開發服務器**:
   ```bash
   npm run dev
   ```

4. **構建生產版本**:
   ```bash
   npm run build
   ```

## 技術限制與注意事項

### API 限制

- **TDX API**:
  - 每日請求限制: 20,000 次/日
  - 突發請求限制: 600 次/分鐘
  - API 密鑰需要註冊並定期更新

- **FlightStats API**:
  - 免費帳戶有每月使用量限制
  - 響應時間可能較慢
  - 部分高級功能需要付費

- **LINE Messaging API**:
  - 每月可發送 500 條推送消息（免費額度）
  - Webhook 必須設置於 HTTPS 端點
  - 收到 LINE 事件後需在 30 秒內回應

### 性能考量

- **資料庫**:
  - Neon 免費方案可能在閒置時進入休眠狀態，首次連接有延遲
  - 每天最多執行時間有限制
  - 連接池大小配置對性能至關重要

- **後端**:
  - Render 免費方案在閒置時會進入休眠，首次啟動有延遲
  - 需要優化大量數據的查詢
  - 自動更新腳本需要定時執行

- **前端**:
  - 處理大量航班數據時客戶端渲染可能成為瓶頸
  - 大型機場搜索結果需要分頁或虛擬滾動

### 部署與維護

- **後端部署流程**:
  ```bash
  # 確保 requirements.txt 更新
  pip freeze > requirements.txt
  # 提交到 Git
  git add .
  git commit -m "Update backend"
  git push
  # Render 自動部署
  ```

- **前端部署流程**:
  ```bash
  # 本地構建
  npm run build
  # 提交到 Git
  git add .
  git commit -m "Update frontend"
  git push
  # Vercel 自動部署
  ```

- **環境變量管理**:
  - 使用 Render 和 Vercel 的環境變量管理
  - 敏感信息不應提交到代碼庫
  - 不同環境使用不同的環境變量集

## 數據同步與整合

### 資料同步策略

- **定時同步**:
  - 使用排程任務每日自動更新航班數據（`update_flights_only.bat`）
  - 定期更新機場和航空公司基本資料
  - 票價信息每小時更新一次

- **資料來源整合**:
  - TDX API 提供台灣本地航班資訊
  - FlightStats API 補充國際航班資訊
  - 自定義爬蟲提取特定航空公司網站數據

### 數據處理流程

1. **資料獲取**: 從多個來源獲取原始數據
2. **資料清洗**: 統一格式、去除重複、修正錯誤
3. **資料整合**: 合併不同來源的數據
4. **資料存儲**: 保存到資料庫
5. **資料更新**: 定期重複以上流程保持數據新鮮度

## 資料庫結構

### 核心表結構

- **airports**: 機場資訊
  - `airport_id` (主鍵): 機場代碼
  - `name_zh`: 中文名稱
  - `name_en`: 英文名稱
  - `city`: 城市
  - `country`: 國家
  - `timezone`: 時區

- **airlines**: 航空公司資訊
  - `airline_id` (主鍵): 航空公司代碼
  - `name_zh`: 中文名稱
  - `name_en`: 英文名稱
  - `logo_path`: Logo圖片路徑

- **flights**: 航班資訊
  - `flight_id` (主鍵): 系統生成ID
  - `flight_number`: 航班號
  - `airline_id` (外鍵): 航空公司ID
  - `departure_airport_id` (外鍵): 出發機場
  - `arrival_airport_id` (外鍵): 到達機場
  - `scheduled_departure`: 表定出發時間
  - `scheduled_arrival`: 表定到達時間
  - `aircraft`: 飛機型號
  - `departure_terminal`: 出發航廈
  - `arrival_terminal`: 抵達航廈
  - `updated_at`: 數據更新時間

- **ticket_prices**: 票價資訊
  - `price_id` (主鍵): 系統生成ID
  - `flight_id` (外鍵): 關聯航班
  - `class_type`: 艙等
  - `economy_price`: 經濟艙價格
  - `business_price`: 商務艙價格
  - `first_class_price`: 頭等艙價格
  - `available_seats`: 可用座位數
  - `price_updated_at`: 價格更新時間

## 版本控制與依賴管理

### 版本控制

- **工具**: Git
- **主要分支**:
  - `main`: 產品主線
  - `develop`: 開發主線
  - 功能分支: `feature/xxx`
  - 修復分支: `bugfix/xxx`

### 依賴管理

- **後端**:
  - 使用 `requirements.txt` 管理 Python 依賴
  - 依賴版本應明確指定，避免自動升級
  - 定期審查並更新依賴項

- **前端**:
  - 使用 `package.json` 管理 Node.js 依賴
  - 使用 Yarn/NPM 鎖定檔案確保版本一致性
  - Tailwind 配置文件控制 UI 樣式

## 測試與品質保證

### 測試架構

- **後端測試**: 使用 pytest
  - 單元測試位於 `tests/` 目錄
  - 測試 API 端點、服務層和數據存取

- **前端測試**: Vue Testing Library
  - 組件測試
  - 整合測試

### 品質檢查工具

- **後端**:
  - Flake8: 代碼風格檢查
  - Mypy: 類型檢查

- **前端**:
  - ESLint: 代碼檢查
  - Prettier: 代碼格式化

## 6. 前端視覺標準

### 6.1 加載動畫規範
- **標準加載動畫**: 使用 SVG 格式的旋轉動畫，具有漸變不透明度效果
  ```html
  <svg class="animate-spin h-4 w-4 text-primary" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
  </svg>
  ```
- **大小規範**:
  - 小型元素內（如輸入框）: `h-4 w-4`
  - 頁面級加載: `h-12 w-12`
- **顏色規範**: 統一使用 `text-primary` (#005F73)

### 6.2 元素視覺一致性
- **輸入框和按鈕**: 方形設計 (border-radius: 0)
- **交互反饋**: 使用 `hover:bg-primary hover:bg-opacity-10` 構建統一的懸停效果
- **選中狀態**: 使用 `bg-primary bg-opacity-20` 標示已選擇項目
- **陰影效果**: 使用預設的 `shadow-card` 和 `shadow-card-hover` 定義

### 6.3 動畫效果
- **基本過渡**: 使用 `transition` 屬性，時長設定為 0.15s 到 0.3s 之間
- **特效動畫**: 優先使用 Tailwind 的動畫類
  - `animate-fade-in`: 漸入效果
  - `animate-slide-up`: 上滑效果
  - `animate-journey-line`: 旅程線動畫
  - `animate-pulse-gentle`: 柔和脈動效果 