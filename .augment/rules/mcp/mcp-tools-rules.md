---
type: "always_apply"
---

# MCP 工具使用規則與最佳實踐

## 📋 概述

本文檔定義了 FlightIntegration 專案中 MCP (Model Context Protocol) 工具的使用規則、最佳實踐和工作流程。

## 🛠️ 可用工具分類

### 1. 文件系統工具
- `view` - 查看文件和目錄
- `str-replace-editor` - 編輯文件
- `save-file` - 創建新文件
- `remove-files` - 刪除文件

**使用規則：**
- 編輯代碼前必須先用 `codebase-retrieval` 了解上下文
- 大型文件修改時分批進行，每次最多 150 行
- 刪除文件前必須確認並詢問用戶

### 2. 代碼庫工具
- `codebase-retrieval` - 檢索代碼庫資訊

**使用規則：**
- 任何代碼修改前的第一步
- 詢問時要具體描述需要的資訊
- 包含所有相關的類、方法、屬性

### 3. 資料庫工具 (Neon)
- `run_sql_neon` - 執行 SQL 查詢
- `run_sql_transaction_neon` - 執行事務
- `prepare_database_migration_neon` - 準備遷移
- `complete_database_migration_neon` - 完成遷移

**使用規則：**
- 重要操作前先在臨時分支測試
- 遷移操作必須先準備再確認
- 查詢大量數據時使用 LIMIT
- 專案 ID: `red-mud-66444885`

### 4. 瀏覽器工具
- `takeScreenshot_browser-tools` - 截圖
- `getConsoleLogs_browser-tools` - 獲取控制台日誌
- `getNetworkLogs_browser-tools` - 獲取網路日誌
- `runAccessibilityAudit_browser-tools` - 無障礙審計

**使用規則：**
- 需要 Chrome 擴展和 server 運行
- 測試前端功能時優先使用
- 截圖用於文檔和問題報告

### 5. 終端工具
- `launch-process` - 啟動進程
- `read-terminal` - 讀取終端輸出
- `read-process` - 讀取進程輸出

**使用規則：**
- 長時間運行的命令使用 `wait=false`
- 短命令使用 `wait=true`
- 工作目錄：`C:\Users\Aliothouo\OneDrive\文件\學校\AlphaVision\FlightIntegration`

### 6. 記憶系統
- `remember` (Augment Memories) - 專案記憶
- `add-memory_mem0-mcp` - 個人記憶
- `search-memories_mem0-mcp` - 搜尋記憶

**使用策略：**
- **Augment Memories**: 專案技術決策、架構變更、錯誤學習
- **mem0-mcp**: 個人偏好、工作習慣、跨專案知識
- **memory-bank**: 保留作為歷史文檔參考（不再更新）

### 7. 任務管理工具
- `view_tasklist` - 查看任務列表
- `add_tasks` - 添加任務
- `update_tasks` - 更新任務狀態

**使用規則：**
- 複雜工作必須先規劃任務
- 批量更新任務狀態
- 每個子任務約 20 分鐘工作量

## 🔄 工作流程規則

### 代碼修改流程
1. `codebase-retrieval` - 了解相關代碼
2. `view` - 查看目標文件
3. `str-replace-editor` - 進行修改
4. 建議測試驗證

### 資料庫操作流程
1. `prepare_database_migration_neon` - 準備遷移
2. `run_sql_neon` - 在臨時分支測試
3. 用戶確認後 `complete_database_migration_neon`

### 前端測試流程
1. `takeScreenshot_browser-tools` - 截圖記錄
2. `getConsoleLogs_browser-tools` - 檢查錯誤
3. `runAccessibilityAudit_browser-tools` - 無障礙檢查

## ⚠️ 安全規則

### 禁止操作
- 不得在未經用戶明確許可下：
  - 提交或推送代碼
  - 刪除重要文件
  - 執行資料庫遷移
  - 安裝依賴套件

### 必須確認操作
- 資料庫結構變更
- 文件刪除
- 分支合併
- 部署相關操作

## 🎯 專案特定規則

### FlightIntegration 專案
- **資料庫**: Neon PostgreSQL (專案 ID: red-mud-66444885)
- **範圍**: 國際航線（排除台灣國內航線）
- **API**: 主要使用 Amadeus API
- **部署**: Render (後端) + Vercel (前端)

### 工具優先級
1. **高頻使用**: `view`, `codebase-retrieval`, `str-replace-editor`
2. **中頻使用**: Neon 工具, 瀏覽器工具
3. **低頻使用**: 任務管理, 記憶工具

## 📝 更新記錄

- 2025-07-10: 初始版本創建
- 包含所有已測試的 MCP 工具規則
