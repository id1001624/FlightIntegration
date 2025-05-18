# 優化起飛機場排序計畫

## 需求分析
- **核心需求**:
  - [ ] **台灣機場排序優化**：主要機場（如TPE、TSA、KHH）按預設順序優先顯示，其他台灣機場根據近期出發航班活躍度（降序）進行排序。
  - [ ] 在 `AirportSelector` 元件中顯示此排序後的台灣機場列表。
  - [ ] 維持其他國家/地區機場的現有分類和排序邏輯。
  - [ ] 優化用戶選擇台灣出發機場的體驗，使其更快找到活躍機場。
  - [ ] 後端 API 需提供機場的近期活躍度數據。

- **技術限制**:
  - [ ] 需與現有的機場分類邏輯整合。
  - [ ] 需修改現有的 `AirportSelector` 元件。
  - [ ] 後端計算活躍度時應考慮效能，避免 API 回應過慢。

## 組件分析
- **受影響的組件**:
  - **後端 - 機場服務 (`app/services/airport_service.py`)**:
    - 變更需求: 新增計算台灣機場「近期活躍度」（例如未來7天出發航班數量）的邏輯。
    - 依賴關係: 依賴 `flights` 和 `airports` 資料庫表。
  - **後端 - 機場控制器/API (`app/controllers/airport_controller.py` 或相關API)**:
    - 變更需求: 修改機場列表 API，使其在返回數據時包含各台灣機場的 `activity_score`。
    - 依賴關係: 依賴機場服務。
  - **前端 - `AirportSelector.vue` 元件**:
    - 變更需求:
      - 接收從 API 傳來的機場 `activity_score`。
      - 修改 `taiwanAirports` 計算屬性的排序邏輯，實現核心機場固定優先、其餘按活躍度（再按預設/名稱）排序。
    - 依賴關係: 依賴機場列表 API 的回應結構。
  - **前端 - 狀態管理 (可能影響 `store/modules/search.js` 或父組件)**:
    - 變更需求: 確保傳遞給 `AirportSelector` 的機場數據包含 `activity_score`。

## 設計決策
- **架構**:
  - [ ] **後端計算，前端使用**：後端負責計算 `activity_score` 並透過 API 提供。前端專注於根據此分數進行顯示和排序。
  - [ ] **快取策略 (後端)**：考慮為計算出的機場活躍度分數實現快取機制，以降低資料庫負載和 API 回應時間。
  - [ ] **API 設計**: 機場列表 API 回應中，每個機場物件應包含 `activity_score` 欄位 (例如 `{'airport_id': 'RMQ', ..., 'activity_score': 15}`)。

- **演算法**:
  - **後端 (活躍度計算)**:
    - [ ] 使用 SQLAlchemy 查詢 `flights` 表，統計每個台灣機場在指定未來天數內（如7天）的出發航班總數。
    - [ ] 確保查詢的效率，適當使用資料庫索引 (`flights.scheduled_departure`, `flights.departure_airport_id`, `airports.country`)。
  - **前端 (台灣機場排序)**:
    - [ ] 在 `taiwanAirports` 計算屬性中：
      1. 過濾出台灣機場。
      2. 對機場列表進行排序：
         a. 核心機場 (TPE, TSA, KHH) 按其在 `desiredOrder` 中的順序排在最前面。
         b. 其他台灣機場，優先按 `activity_score` 降序排列。
         c. 若 `activity_score` 相同，則按 `desiredOrder` 中的次序或機場名稱/代碼作為次要排序標準。

## 實施策略
1. **第一階段: 後端 - 活躍度計算與API調整**
   - [ ] **資料庫確認**: 再次確認 `flights` (含 `scheduled_departure`, `departure_airport_id`) 和 `airports` (含 `country`, `airport_id`) 表結構及索引。
   - [ ] **服務層邏輯 (`app/services/airport_service.py`)**:
     - [ ] 實現 `get_airport_activity_scores(days_ahead=7)` 函數，使用 SQLAlchemy 查詢並返回 `{airport_id: flight_count}` 的字典。
   - [ ] **API層修改 (`app/controllers/airport_controller.py`)**:
     - [ ] 在獲取機場列表的 API 中調用 `get_airport_activity_scores`。
     - [ ] 將 `activity_score` 整合到 API 回傳給前端的每個台灣機場物件中。
   - [ ] **後端測試 (單元/整合)**:
     - [ ] 測試 `get_airport_activity_scores` 函數的正確性與邊界條件。
     - [ ] 測試 API 是否正確返回包含 `activity_score` 的機場數據。
   - [ ] **(可選) 後端快取**: 評估是否需要為活躍度分數添加快取。

2. **第二階段: 前端 - `AirportSelector` 整合與排序邏輯更新**
   - [ ] **資料接收**: 確保 `AirportSelector.vue` 能從 `props.airports` 或相關 store 狀態中正確獲取到包含 `activity_score` 的機場物件。
   - [ ] **排序邏輯修改 (`AirportSelector.vue`)**:
     - [ ] 更新 `taiwanAirports` 計算屬性中的 `sort` 方法，實現新的混合排序邏輯（核心機場優先 + 活躍度排序）。
   - [ ] **前端測試 (單元/整合)**:
     - [ ] 測試 `taiwanAirports` 在不同 `activity_score` 和機場組合下的排序結果是否符合預期。
     - [ ] 驗證 `AirportSelector` 下拉選單中台灣機場的顯示順序。

3. **第三階段: 整體測試與使用者體驗驗證**
   - [ ] 進行端對端測試，確保前後端整合無誤。
   - [ ] 評估優化後的機場選擇體驗，確認是否更直觀、高效。
   - [ ] 根據測試結果和反饋進行微調。

## 測試策略
- **後端單元測試**:
  - [ ] 測試 `get_airport_activity_scores` 函數：
    - [ ] 不同 `days_ahead` 參數的影響。
    - [ ] 台灣機場有航班、無航班、多個機場有不同航班數的情況。
    - [ ] 資料庫中無符合條件航班的情況。
- **後端整合測試**:
  - [ ] 測試機場列表 API 是否能正確返回帶有 `activity_score` 的數據，且分數與資料庫數據一致。
- **前端單元測試 (`AirportSelector.vue`)**:
  - [ ] 測試 `taiwanAirports` 計算屬性的排序邏輯：
    - [ ] 核心機場是否總在最前且順序正確。
    - [ ] 非核心機場是否按 `activity_score` 降序排列。
    - [ ] `activity_score` 相同時的次要排序是否正確。
    - [ ] 機場列表為空或不含台灣機場的情況。
- **端對端測試**:
  - [ ] 模擬使用者操作，驗證從點擊機場選擇器到選擇機場的完整流程，確認台灣機場排序符合預期。
- **用戶體驗測試**:
  - [ ] 內部評估或小範圍使用者測試，收集關於新排序邏輯的直觀性和實用性的反饋。

## 文檔計畫
- [ ] 更新後端 API 文檔，說明機場列表 API 回應中新增的 `activity_score` 欄位。
- [ ] 更新 `AirportSelector.vue` 元件的相關註解或開發文檔，解釋新的排序機制。
- [ ] (若有) 更新系統設計文檔中關於機場資料處理和排序的部分。

## 創意階段需求
- [ ] ⚙️ **演算法設計 (後端)**: 設計高效的 SQLAlchemy 查詢以計算機場活躍度，並考慮快取策略。
- [ ] ⚙️ **演算法設計 (前端)**: 設計清晰且穩定的前端混合排序邏輯。

## 檢查點
- [ ] 後端活躍度計算邏輯與 API 調整完成並測試。
- [ ] 前端 `AirportSelector` 排序邏輯更新完成並測試。
- [ ] 端對端測試與使用者體驗初步驗證完成。
- [ ] 相關文檔更新完成。

## 當前狀態
- 階段: 計畫階段 (已更新細化方案)
- 狀態: 進行中
- 阻礙: 無 