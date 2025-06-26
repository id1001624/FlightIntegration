# 專案改進計畫

## 第一階段：後端 API 功能增強與標準化 (解決問題 1, 3)

### 任務 1.1: 機場服務與控制器增強 - 支援航班數量統計與排序
- **目標**: 使後端能夠統計每個機場的航班數量，並提供按航班數量排序機場列表的 API 功能。
- **具體行動**:
    1.  **資料庫/服務層**:
        *   在 `search_service.py` 或設計一個新的 `airport_stats_service.py` 中，新增邏輯來計算每個機場的活躍航班數量（例如，未來N天內的航班，或總航班數，需明確定義）。
        *   考慮為航班數量統計結果設計快取機制，以提高重複查詢的效能。
    2.  **API 控制器層 (`airport_controller.py`)**:
        *   修改現有的機場列表 API 端點 (例如 `/api/airports`, `/api/airports/taiwan`, `/api/airports/available-departures`)：
            *   允許傳入新的查詢參數，如 `sort_by=flight_count` (以及可能的 `sort_order=asc/desc`)。
            *   在回傳的機場物件中，選擇性地加入 `flight_count` 欄位。
        *   確保在 `flight_count` 不可用或計算耗時的情況下，API 仍能正常回傳（例如，預設按名稱排序）。
- **受影響檔案**:
    *   `backend/app/services/search_service.py` (或新的服務檔案)
    *   `backend/app/controllers/airport_controller.py`
    *   可能需要修改 `backend/app/models/airport.py` (如果決定將 flight_count 作為非持久化屬性或需要關聯查詢)
    *   相關的 Schema 檔案 (如果使用 Marshmallow/Pydantic)。

### 任務 1.2: 標準化機場相關 API 的回應結構
- **目標**: 統一所有回傳機場資訊的 API 端點的資料結構，特別是機場代碼和名稱欄位。
- **具體行動**:
    1.  **盤點 API**: 審查 `airport_controller.py` 中的所有端點 (`/`, `/taiwan`, `/available-departures`, `/available-destinations/<id>`, `/<id>`)。
    2.  **定義標準**:
        *   確定機場代碼的統一鍵名 (例如，統一使用 `code` 而非 `id`，或兩者皆提供但明確其一為主要識別碼)。
        *   確定機場名稱的統一表示方式 (例如，總是提供 `name_zh` 和 `name_en`，並可選提供一個 `display_name` 作為預設顯示名稱)。
    3.  **實施修改**:
        *   更新 `airport_controller.py` 中各端點的資料序列化邏輯，使其符合定義的標準結構。
        *   更新相關的 Schema 檔案。
- **受影響檔案**:
    *   `backend/app/controllers/airport_controller.py`
    *   相關的 Schema 檔案。

## 第二階段：優化 API 以支援前端資料需求 (解決問題 2)

### 任務 2.1: 分析前端機場分組與篩選需求
- **目標**: 深入理解前端 `AirportSelector.vue` 及其他可能使用機場列表的元件，其對於機場資料分組和篩選的具體需求。
- **具體行動**:
    1.  **檢視前端**: 詳細分析 `AirportSelector.vue` 中按國家/地區分類的邏輯。
    2.  **識別模式**: 確認是否有其他常見的篩選或分組模式（例如，按洲、按是否有國際航班等）。

### 任務 2.2: 增強機場 API 以支援伺服器端分組與篩選
- **目標**: 讓後端 API 能夠直接回傳經過分組或篩選的機場資料，減輕前端處理負擔。
- **具體行動**:
    1.  **設計 API 參數**:
        *   為機場列表 API 端點 (如 `/api/airports`) 增加新的查詢參數，例如：
            *   `region=[region_name]` (例如，`region=亞洲`)
            *   `country=[country_name]` (例如，`country=Taiwan`)
            *   `group_by=region` 或 `group_by=country` (讓後端回傳已分組的資料結構)。
    2.  **實作後端邏輯**:
        *   在 `airport_controller.py` 和相關的服務層 (`search_service.py` 或其他) 中實作新的篩選和分組查詢邏輯。
        *   考慮 API 回傳分組資料的結構，使其易於前端使用。
- **受影響檔案**:
    *   `backend/app/controllers/airport_controller.py`
    *   `backend/app/services/search_service.py` (或相關服務檔案)
    *   前端獲取機場資料的服務 (`frontend/src/api/services/flightService.js` 或新建的 `airportService.js`)
    *   前端元件 `frontend/src/components/AirportSelector.vue` (將改為使用新的 API 功能)

## 第三階段：全域錯誤處理審查與強化 (解決問題 6)

### 任務 3.1: 後端錯誤處理機制審查
- **目標**: 確保後端所有 API 端點和服務層邏輯都有健全、一致的錯誤處理和日誌記錄。
- **具體行動**:
    1.  **全面審查**:
        *   檢查 `backend/app/controllers/` 下所有控制器的每個路由處理函數。
        *   檢查 `backend/app/services/` 下所有服務的主要公共方法。
    2.  **一致性檢查**:
        *   確保統一使用如 `_error_response` 的輔助函數來回傳錯誤，保證錯誤回應格式的一致性。
        *   檢查 `try...except` 區塊是否捕獲了足夠具體的異常類型，避免過於寬泛的 `except Exception`。
    3.  **日誌記錄**:
        *   確保在捕獲到異常時，都有記錄足夠的上下文資訊到日誌中（例如，請求參數、錯誤堆疊）。
        *   對於嚴重錯誤，日誌級別應設為 ERROR 或 CRITICAL。
    4.  **邊界條件**: 檢查對於無效輸入、資源未找到等情況是否都有適當的處理和回應 (例如，400, 404 狀態碼)。
- **受影響檔案**:
    *   `backend/app/controllers/` 目錄下的所有 Python 檔案。
    *   `backend/app/services/` 目錄下的所有 Python 檔案。
    *   通用錯誤處理工具函數。

## 第四階段：`generate_dummy_flight_data.py` 腳本功能增強 (可選，依實現簡易度)

### 任務 4.1: 提升模擬航班數量分佈的真實感
- **目標**: 使生成的模擬航班在不同機場和航線上的數量分佈更接近實際情況 (簡化版)。
- **具體行動**:
    1.  **分析與調整**:
        *   檢視 `generate_flights_for_day` 和 `select_airline_for_route`。
        *   可以考慮為 `REGIONS` 中的機場或 `COMBINED_POPULAR_ROUTES_TUPLES` 中的航線引入一個簡單的「熱度」或「規模」因子。
        *   根據此因子，微調每日為特定機場/航線生成的航班數量或選擇航空公司的權重。
        *   例如，可以讓像 TPE、KIX 這樣的大型機場比較小的機場（如 MZG）有更高的基礎航班數量。
- **受影響檔案**:
    *   `backend/app/scripts/generate_dummy_flight_data.py`
    *   `backend/app/scripts/constants.py` (如果引入新的輔助常數)

### 任務 4.2: 擴大模擬航班的機場覆蓋範圍
- **目標**: 確保腳本能為更多（甚至所有）資料庫中定義的機場生成至少一些模擬航班，而不僅僅是預定義的熱門航線。
- **具體行動**:
    1.  **獲取機場列表**: 在腳本初始化時，從資料庫讀取所有機場的 IATA 代碼。
    2.  **調整航線選擇**:
        *   修改 `select_route_templates` 或其調用邏輯。
        *   除了從 `ALL_ROUTES_TUPLES` 中選擇，可以額外加入一個機制：隨機選擇資料庫中的任一機場作為出發地，再隨機選擇另一個機場作為目的地（需考慮國內/國際的合理性），從而覆蓋更多未在常量中定義的航線組合。
        *   確保新生成的航線也有合理的航空公司和飛行時長分配。
- **受影響檔案**:
    *   `backend/app/scripts/generate_dummy_flight_data.py`

### (未來考量 - 較複雜) 任務 4.3: 模擬航班狀態 (延誤、取消)
- **目標**: 讓模擬數據包含航班延誤或取消等狀態，使測試場景更豐富。
- **說明**: 此任務實現起來相對複雜，可能涉及資料庫 Schema 的修改 (若 `flights` 表尚無 `status` 欄位)，以及更複雜的生成邏輯。**建議作為未來進一步的增強點，初期可暫不實施。** 