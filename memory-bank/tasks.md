# 台灣航班整合系統任務追蹤

> **當前模式:** PLAN MODE  
> **複雜度評估:** Level 3 - Intermediate Feature

## 進行中任務

### 前端調適與優化
- [x] 優化起飛機場排序：根據可用航班數量對台灣機場進行排序
- [x] 實現中文名稱搜索：允許用戶在 `AirportSelector` 元件中使用中文名稱搜索機場
- [x] 搜索後自動滾動功能：點擊「搜尋航班」按鈕後自動滑動至結果區域
- [ ] 航班卡片詳情彈窗持續顯示修復

### 後端功能擴展
- [x] 開發虛擬航班資料生成腳本 (`generate_dummy_flight_data.py`)
- [x] Refactor TDX Client: 將 `tdx_client.py` 切換至使用 `/v2/Air/DailyFlightSchedule/Domestic/{IATA}` 端點，以獲取更完整的預定航班列表。
- [x] **後續處理 (TDX Refactor):** 更新資料同步腳本 (`sync_manager.py`, `db_manager.py`) 以適應新的 `get_domestic_flight_schedules` 回應結構 (新增 `aircraft`，移除即時狀態/航廈)。

### LINE Bot功能擴展
- [ ] FollowEvent 處理，發送歡迎訊息
- [ ] 基於文字指令的航班查詢功能
- [ ] 常用詞彙查詢功能
- [ ] Flex Message 航班資訊卡片

## 已完成任務

### 核心航班查詢功能
- [x] 航班搜索API實現
- [x] 航空公司資訊API實現
- [x] 機場資訊API實現
- [x] 基本搜索頁面設計與開發
- [x] 航班結果卡片設計與實現
- [x] 機場選擇器元件開發

### 前端介面開發
- [x] 航空公司Logo整合
- [x] 搜索表單元件開發
- [x] 航班結果頁面實現
- [x] 航班詳情頁面設計
- [x] 機場選擇器加載動畫優化
- [x] 視覺設計標準建立 (參見 `memory-bank/visual-standards.md`)
- [x] 實現中文名稱搜索：允許用戶在 `AirportSelector` 元件中使用中文名稱搜索機場
- [x] 保留搜尋結果：關閉彈窗後保持搜尋狀態 (使用 Pinia 狀態管理)
- [x] 搜索後自動滾動功能：點擊「搜尋航班」按鈕後自動滑動至結果區域

### 後端功能擴展
- [x] 票價功能擴展
- [x] LINE Bot 基礎整合
- [x] 開發虛擬航班資料生成腳本 (`generate_dummy_flight_data.py`)
- [x] 自動刪除flights、ticket_prices資料庫舊資料功能：
  - 增強 `cleanup_old_data.py` 清理腳本，支援可配置的保留時間（預設90天）、資料類型過濾（測試/真實/全部）、備份功能和執行報告
  - 優化 `auto_cleanup_data.bat` 排程批處理檔，提供詳細日誌輸出和錯誤處理
  - 提供完整的排程任務設置說明文件，方便自動化定期清理
  - 實現資料庫效能維護策略，自動維護資料庫大小和效能
- [x] Refactor TDX Client: 將 `tdx_client.py` 切換至使用 `/v2/Air/DailyFlightSchedule/Domestic/{IATA}` 端點
- [x] 更新資料同步腳本以適應新的資料結構

### 部署與環境配置
- [x] 後端服務部署到 Render (Free Tier)
- [x] 前端網站部署到 Vercel (Free Tier)
- [x] 修復相對導入錯誤和依賴問題
- [x] 雲端資料庫 Neon 設置

## 未來規劃 (暫不開發)

### 進階功能
- [ ] 航班延誤預測系統
- [ ] 購票功能整合
- [ ] 社群功能開發
- [ ] 天氣資料整合
- [ ] 機場設施導覽地圖

### 安全性與效能優化
- [ ] API速率限制實現
- [ ] 資料緩存策略優化
- [ ] 資料庫查詢效能提升 