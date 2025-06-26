# 台灣航班整合系統任務

## 優先級任務：端對端測試與驗證

### 複雜度評估：Level 3

### 1. 需求分析 (Requirements Analysis)
- **核心目標**: 驗證在移除 TDX/FlightStats 並完全遷移至 Amadeus API 後，航班搜尋的核心功能依然能從前端到後端無誤地運作。
- **成功標準**:
    1.  用戶可以在前端介面成功搜尋國際航班。
    2.  後端能正確處理請求、調用 Amadeus API 並返回適配後的數據。
    3.  所有舊的、已刪除的程式碼不會引起任何副作用或錯誤。
    4.  資料同步腳本能正常運作，填充必要的靜態數據。

### 2. 受影響的組件 (Components Affected)
- **前端**: `FlightSearch.vue`, `AirportSelector.vue`, `FlightCard.vue`, `flightService.js`。
- **後端**: `amadeus_controller.py`, `amadeus_service.py`, `amadeus_offers_adapter.py`, `sync_manager.py`。
- **資料庫**: `airlines` 和 `airports` 表格（由 `sync_manager` 維護）。

### 3. 實施策略與詳細步驟 (Implementation Strategy & Detailed Steps)

這將是一個多階段的測試流程，模擬從用戶操作到後端處理的全過程。

- **階段一：資料同步驗證 (待執行)**
    1.  **任務**: 執行 `sync_manager.py` 腳本，確保其能從 Amadeus 正確獲取並儲存航空公司和機場的靜態資料。
    2.  **驗證**: 檢查資料庫中的 `airlines` 和 `airports` 表格，確認資料已被填充，且沒有出現與舊 API 相關的錯誤。

- **階段二：前端使用者介面測試 (UI Test) (待執行)**
    1.  **任務**: 啟動前端和後端服務，在瀏覽器中開啟航班搜尋頁面。
    2.  **操作**:
        -   **起點**: 從下拉選單中選擇一個台灣的機場（例如：TPE）。
        -   **終點**: 選擇一個國際機場（例如：NRT）。
        -   **日期**: 選擇一個**未來**的有效日期。
    3.  **驗證**:
        -   點擊「搜尋航班」按鈕。
        -   觀察 UI 是否顯示載入狀態，然後是否成功渲染出 `FlightCard` 列表。
        -   檢查瀏覽器開發者工具的控制台，確保沒有 `400` 或 `500` 系列的網路錯誤。

- **階段三：後端 API 直接測試 (待執行)**
    1.  **任務**: 使用 API 工具（如 Postman）或腳本，直接向後端 `/api/amadeus/flights/offers` 端點發送一個 GET 請求。
    2.  **參數**: 使用與前端測試相同的參數（`origin`, `destination`, `date`）。
    3.  **驗證**: 確認 API 返回 `200 OK` 狀態碼，且響應的 JSON 結構符合 `amadeus_offers_adapter.py` 的輸出格式。

- **階段四：最終程式碼清理驗證 (待執行)**
    1.  **任務**: 在整個程式庫中執行最後一次 `grep` 搜尋。
    2.  **關鍵字**: `TDX`, `FlightStats`, `flightstats`, `tdx`。
    3.  **驗證**: 確認搜尋結果中沒有任何殘留的功能性程式碼。

### 4. 挑戰與應對策略 (Challenges & Mitigations)
- **挑戰**: UI 顯示的資料與後端提供的格式可能不匹配。
- **應對**: 在 API 測試階段，仔細比對返回的 JSON 物件鍵名與 `FlightCard.vue` 元件中 `props` 的預期。
- **挑戰**: 可能仍有隱藏的、對已刪除檔案的依賴。
- **應對**: 執行測試時密切關注後端日誌中的 `ImportError` 或 `NameError`。

---

## 已完成的重構任務
- ✅ **程式碼清理 (第一輪)**:
    - ✅ 刪除 `flightstats_client.py`, `tdx_client.py`, `api_client.py`, `cache_manager.py`, `cache_utils.py`, `rate_limiter.py`, `data_sync_service.py`。
    - ✅ 重構 `flight_controller.py` 和 `sync_manager.py` 為異步模式。
    - ✅ 移除 `airline_service.py` 和 `airport_service.py` 中的同步函式。
    - ✅ 移除 `db.py` 中與 SQLAlchemy 的相關程式碼。

- ✅ **程式碼清理 (第二輪 - 深度清理)**:
    - ✅ 修正 `utils/__init__.py` 和 `services/__init__.py` 的無效 import。
    - ✅ 刪除 `sync_flight_data.py`。
    - ✅ 精煉 `constants.py`，移除國內線機場和航空公司。
    - ✅ 刪除 `generate_dummy_flight_data.py`。
    - ✅ 修正 `amadeus_controller.py` 中對已刪除 `cache_manager` 的引用。
