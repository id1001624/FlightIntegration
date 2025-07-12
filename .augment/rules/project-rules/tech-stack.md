---
type: "always_apply"
---

# **台灣航班整合系統技術棧規範**

## 1. 系統架構概述

### 1.1 整體架構
```
航班整合系統架構:

前端 (Vue.js):
├── 核心模組
│   ├── 航班搜索元件
│   ├── 結果顯示元件
│   └── 票價比較元件
├── 共用元件
│   ├── 機場選擇器
│   ├── 日期選擇器
│   └── 航空公司過濾器
└── 頁面視圖
    ├── 首頁/搜索頁
    ├── 搜索結果頁
    └── 航班詳情頁

後端 (Flask):
├── API層
│   ├── 控制器 (Controllers)
│   └── 路由 (Routes)
├── 服務層 (Services)
│   ├── 搜索服務
│   ├── 航班服務
│   └── LINE服務
├── 資料層
│   ├── 模型 (Models)
│   ├── 資料庫訪問
│   └── 外部API客戶端
└── 公用元件
    ├── 錯誤處理
    ├── 日誌系統
    └── 配置管理
```

### 1.2 技術選型原則
- **成熟穩定**: 選擇有長期支持的成熟框架和工具
- **輕量靈活**: 優先選擇輕量級解決方案，避免過度工程
- **易於部署**: 適合雲端免費託管方案的技術選擇
- **團隊熟悉**: 團隊已掌握或易於學習的技術棧

### 1.3 核心技術棧

| 層級 | 技術選擇 | 說明 |
|------|---------|------|
| 前端框架 | Vue.js 3 | 使用組合式API，結合TypeScript提高代碼健壯性 |
| 前端樣式 | Tailwind CSS | 採用utility-first策略，提高開發效率 |
| 狀態管理 | Pinia | 替代Vuex的輕量級狀態管理方案 |
| 後端框架 | Flask + Blueprint | 模組化API設計，便於擴展 |
| ORM | SQLAlchemy | 支持複雜查詢和關聯模型 |
| 資料庫 | PostgreSQL (Neon) | 雲端數據庫服務，支持JSON和地理數據 |
| API整合 | TDX, FlightStats | 主要航班數據來源 |
| LINE整合 | LINE Messaging API v3 | 提供LINE Bot功能 |
| 部署 | Render, Vercel | 免費託管方案 |

## 2. 前端技術規範

### 2.1 核心庫與框架
- **Vue.js 3**: 採用組合式API (`setup()`, `ref()`, `computed()`)
- **Vue Router 4**: 採用新的路由守衛和組合式API
- **Pinia**: 使用store模式組織狀態
- **Axios**: 統一的HTTP請求客戶端
- **Tailwind CSS**: 實用優先的CSS框架

### 2.2 代碼組織與最佳實踐
- **命名規範**:
  - 組件名: PascalCase (如 `FlightCard.vue`)
  - 方法/變量: camelCase (如 `getFlight`, `userData`)
  - 常量: UPPER_SNAKE_CASE (如 `API_URL`)
  
- **文件組織**:
  ```
  src/
  ├── api/           # API服務封裝
  ├── assets/        # 靜態資源
  ├── components/    # 可重用元件
  │   ├── common/    # 通用元件
  │   └── specific/  # 特定頁面元件
  ├── router/        # 路由定義
  ├── store/         # Pinia狀態
  ├── utils/         # 工具函數
  └── views/         # 頁面組件
  ```

- **元件設計原則**:
  - 單一職責: 每個元件只做一件事
  - Props驗證: 明確定義輸入參數類型
  - 避免深層嵌套: 組件層級不超過3層
  - 合理解耦: 使用事件通信而非直接引用

- **性能優化策略**:
  - 使用 `v-memo` 減少不必要的渲染
  - 大列表使用虛擬滾動 (`vue-virtual-scroller`)
  - 路由組件使用動態導入 (`import()`)
  - 避免大量計算屬性和監聽器

### 2.3 UI/UX規範
- 嚴格遵循 [UI設計指南](mdc:ui-design-guidelines.mdc) 的Structured Journey Minimalism風格
- 使用Tailwind配置擴展自定義主題:
  ```js
  // tailwind.config.js
  module.exports = {
    theme: {
      extend: {
        colors: {
          primary: '#005F73',
          secondary: '#F4A261',
          // 其他品牌色彩
        },
        // 其他自定義
      }
    }
  }
  ```

### 2.4 UI動畫與加載狀態

#### 2.4.1 標準加載動畫

系統定義了三種標準加載動畫，應在不同場景中使用：

- **航班搜索加載動畫**: 用於頁面級全屏加載（搜索結果頁）
  - 水平進度條帶有圓形節點，模擬飛行軌跡
  - 主色調進度條從左至右自動動畫
  - 實現於 `FlightSearchLoader.vue` 組件
  
- **機場選擇加載動畫**: 用於元素內嵌加載（下拉選單、表單元素）
  - 三個圓環元素排列並輕脈衝
  - 適合空間有限的內嵌場景
  - 實現於 `OrbitalLoader.vue` 組件，具有SM/MD/LG尺寸變體
  
- **航班詳情加載動畫**: 用於航班相關加載（詳情頁）
  - 包含出發/到達點、連接路徑和骨架佔位符
  - 使用主色調和次色調實現出發地/目的地差異化
  - 實現於 `FlightDetailLoader.vue` 組件

#### 2.4.2 動畫實現技術

- **CSS優先**：盡可能使用純CSS實現動畫以確保性能
- **動畫技術選擇**:
  - 簡單狀態轉換：CSS transitions
  - 循環或複雜動畫：CSS animations (@keyframes)
  - 頁面轉場：Vue's `<transition>` 和 `<transition-group>`
  - 觸發型複雜動畫：可選用GSAP（謹慎考慮包大小）
 
- **動畫性能優化**:
  - 優先使用 `transform` 和 `opacity` 屬性
  - 避免使用觸發重排的屬性如 `width`, `height`, `top`, `left`
  - 對滾動和窗口調整事件進行去抖動(debounce)處理
  - 長動畫序列使用 `will-change` 屬性（謹慎使用）
  - 使用Chrome DevTools檢測動畫性能

#### 2.4.3 組件實現範例

```vue
<!-- AirportSelector.vue 中的加載狀態 -->
<template>
  <!-- Input field... -->
  <div v-if="loading" class="orbital-loader-sm">
    <div class="orbital-dot"></div>
    <div class="orbital-dot"></div>
    <div class="orbital-dot"></div>
  </div>
</template>

<style scoped>
.orbital-loader-sm {
  /* 樣式定義... */
}
.orbital-dot {
  /* 樣式定義... */
}
@keyframes pulseScale {
  0%, 100% { transform: scale(1); opacity: 0.7; }
  50% { transform: scale(1.3); opacity: 1; }
}
</style>
```

### 2.5 前端狀態管理

## 3. 後端技術規範

### 3.1 核心庫與框架
- **Flask**: Web框架核心
- **Flask-RESTful**: REST API構建
- **SQLAlchemy**: ORM數據訪問
- **Marshmallow**: 數據序列化
- **Pydantic**: 數據驗證
- **Asyncpg**: 異步PostgreSQL驅動
- **LINE SDK v3**: LINE Bot整合

### 3.2 代碼組織與最佳實踐
- **命名規範**:
  - 文件/模塊: snake_case (如 `flight_controller.py`)
  - 類: PascalCase (如 `FlightService`)
  - 函數/變量: snake_case (如 `get_flight_info`, `user_data`)
  - 常量: UPPER_SNAKE_CASE (如 `MAX_RESULTS`)
  
- **文件組織**:
  ```
  app/
  ├── controllers/   # API端點處理
  ├── models/        # 數據模型定義
  ├── services/      # 業務邏輯層
  ├── schemas/       # 序列化模式
  ├── utils/         # 工具函數
  └── scripts/       # 數據處理腳本
  ```

- **分層架構原則**:
  - 控制器層: 處理HTTP請求/響應，不包含業務邏輯
  - 服務層: 實現核心業務邏輯，依賴注入模型
  - 數據層: 數據庫訪問與外部API調用
  - 嚴格單向依賴: 上層依賴下層，避免循環依賴

- **API命名和版本控制**:
  - 使用URL前綴區分版本 (`/api/v1/...`)
  - 資源使用複數名詞 (`/flights` 而非 `/flight`)
  - 使用適當的HTTP動詞 (GET, POST, PUT, DELETE)
  - 統一響應格式:
   ```json
   {
      "success": true,
     "data": [...],
      "message": "操作成功",
      "metadata": {"total": 100, "page": 1, "per_page": 20}
    }
    ```

### 3.3 服務設計模式
- **Repository模式**: 封裝數據訪問邏輯
- **工廠模式**: 創建複雜對象
- **策略模式**: 處理不同的搜索算法
- **適配器模式**: 統一不同API數據格式

## 4. 數據庫設計與優化

### 4.1 資料模型設計
- **核心模型**:
  - `airlines`: 航空公司資訊
  - `airports`: 機場資訊
  - `flights`: 航班資訊
  - `ticket_prices`: 票價資訊

- **關聯設計**:
  - 一個航班關聯一個航空公司(多對一)
  - 一個航班關聯兩個機場(多對一，出發和到達)
  - 一個航班可以有多個票價(一對多)
  
- **索引策略**:
  - `flights.flight_number`: 加速航班號查詢
  - `flights.departure_airport_id, scheduled_departure`: 加速特定出發地和日期的查詢
  - `flights.arrival_airport_id, scheduled_arrival`: 加速特定目的地和日期的查詢
  - `ticket_prices.flight_id`: 加速票價查詢

### 4.2 資料庫優化
- **查詢優化**:
  - 使用 `EXPLAIN ANALYZE` 分析慢查詢
  - 避免 N+1 查詢問題，使用 `joinedload`
  - 針對複雜查詢使用索引視圖
  - 當查詢超過3個join時，考慮分解或使用視圖

- **分頁處理**:
  ```python
  # 後端分頁實現
  def get_paginated_flights(page=1, per_page=20):
      pagination = Flight.query.paginate(page=page, per_page=per_page)
      return {
          "items": pagination.items,
          "metadata": {
              "page": pagination.page,
              "per_page": pagination.per_page,
              "total": pagination.total
          }
      }
  ```

- **批量操作**:
  - 使用 `bulk_insert` 或 `bulk_update` 處理批量數據
  - 大量數據導入使用 `COPY` 而非 `INSERT`

### 4.3 緩存策略
- **緩存層次**:
  - 應用內存緩存: 適用於機場、航空公司等靜態數據
  - 外部緩存(可選): Redis用於分布式緩存

- **緩存粒度**:
  - 基於URL的響應緩存: 對於頻繁訪問的API端點
  - 對象級緩存: 對於計算成本高的結果
  - 細粒度數據: 對於經常訪問但不常變化的數據

## 5. API整合與第三方服務

### 5.1 外部API管理
- **API客戶端封裝**:
  ```python
  class TDXApiClient:
      def __init__(self, client_id, client_secret):
          self.client_id = client_id
          self.client_secret = client_secret
          self.token = None
          
      def _get_token(self):
          # 獲取或刷新令牌
          pass
          
      def get_flights(self, date, from_airport, to_airport):
          # 調用航班API，處理結果
          pass
  ```

- **重試與熔斷機制**:
  - 使用指數退避算法處理重試
  - 實現熔斷器模式避免雪崩效應
  - 對於不可靠API設置超時和備份策略

### 5.2 LINE Bot整合
- 遵循 [LINE Bot整合指南](mdc:line-bot-integration.mdc)
- 實現事件驅動架構處理LINE Webhook
- 使用模板消息和Flex消息提供豐富視覺體驗

### 5.3 API效率與限流
- **使用批量請求**:
  ```python
  # 不好的做法: 循環調用API
  for airport in airports:
      get_weather(airport.code)
      
  # 好的做法: 批量請求
  airport_codes = [a.code for a in airports]
  get_weather_batch(airport_codes)
  ```

- **實現API配額管理**:
  - 每日/小時API調用跟踪
  - 接近限制時降級服務
  - 使用隊列系統處理非實時需求

## 6. 安全性與防禦策略

### 6.1 輸入驗證與清理
- **後端驗證**:
  ```python
  # 使用Pydantic或Marshmallow進行數據驗證
  class FlightSearchSchema(Schema):
      departure_code = fields.Str(required=True, validate=validate.Length(min=3, max=3))
      arrival_code = fields.Str(required=True, validate=validate.Length(min=3, max=3))
      date = fields.Date(required=True)
      
  # 控制器中使用
  def search_flights():
      schema = FlightSearchSchema()
      errors = schema.validate(request.json)
      if errors:
          return {"success": False, "errors": errors}, 400
  ```

- **防止SQL注入**:
  - 使用參數化查詢，避免字符串連接
  - 使用ORM處理複雜查詢

- **防止XSS攻擊**:
  - 在前端使用 `v-text` 而非 `v-html`
  - 必要時使用DOMPurify清理HTML

### 6.2 API安全
- **速率限制**:
  ```python
  # 使用Flask-Limiter實現API限流
  from flask_limiter import Limiter
  
  limiter = Limiter(app, key_func=get_remote_address)
  
  @app.route("/api/flights/search")
  @limiter.limit("100 per day")
  def search_flights():
      # 實現
  ```

- **安全頭信息**:
  - 設置適當的 `Content-Security-Policy`
  - 使用 `X-Content-Type-Options: nosniff`
  - 實現 `X-XSS-Protection: 1; mode=block`

### 6.3 敏感資訊處理
- **環境變量管理**:
  - API密鑰存儲在環境變量中
  - 使用 `.env` 文件配合 `python-dotenv`
  - 不同環境使用不同配置文件

- **日誌安全**:
  - 避免記錄敏感信息 (密碼, API密鑰)
  - 實現日誌輪轉，防止日誌文件過大
  - 根據環境調整日誌級別

## 7. 部署與運維策略

### 7.1 開發環境
- 使用 Docker 統一開發環境
- 實現熱重載提高開發效率
- 使用 `pre-commit` 鉤子確保代碼質量

### 7.2 生產部署
- **後端部署 (Render)**:
  - 設置自動化部署流程
  - 配置健康檢查端點
  - 使用環境變量管理配置

- **前端部署 (Vercel)**:
  - 配置構建腳本優化資源
  - 啟用自動化預覽部署
  - 實現靜態資源CDN

### 7.3 監控與日誌
- 實現結構化日誌輸出
- 配置錯誤監控與告警
- 設置API性能跟踪點

## 8. 效能優化準則

### 8.1 前端優化
- **請求優化**:
  - 實現請求合併
  - 使用 Axios 攔截器處理通用邏輯
  - 添加智能緩存, 避免重複請求

- **渲染優化**:
  - 使用 KeepAlive 緩存組件
  - 實現骨架屏提高感知性能
  - 延遲加載非關鍵資源

### 8.2 後端優化
- **數據庫查詢**:
  - 避免在循環中查詢數據庫
  - 使用適當的預取和延遲加載策略
  - 實現查詢結果緩存

- **異步處理**:
  - 對於耗時任務使用後台作業
  - 實現非阻塞IO處理大量請求

### 8.3 網絡優化
- 最小化API有效載荷
- 實現壓縮響應 (gzip/brotli)
- 優化API批次處理

## 9. 特殊考量

### 9.1 航班數據特性
- **時區處理**:
  - 統一存儲UTC時間
  - 客戶端顯示時轉換為本地時間
  - 處理日期線問題

- **數據同步策略**:
  - 高頻更新關鍵數據 (航班狀態)
  - 低頻更新穩定數據 (機場、航空公司)
  - 設計差量更新減少數據傳輸

### 9.2 數據保留策略
- 實現數據清理腳本，移除過期數據
- 定期備份重要數據
- 設置數據分層存儲策略

### 9.3 維護模式
- 設計系統維護模式頁面
- 實現平滑維護切換機制
- 提供維護期間的最小可用功能

   