# 航班整合系統 API 文檔

本目錄存放與航班整合系統 API 相關的技術文件。

## API 參考

### 主要 API

本專案目前主要使用 **Amadeus for Developers** API 作為即時航班數據的來源。所有與 Amadeus 相關的客戶端邏輯都封裝在後端的 `app/services/amadeus_service.py` 中。

前端通過呼叫後端的 `/api/amadeus/flights/offers` 端點來獲取航班資訊。

### OpenAPI 規範

- [openapi.json](./openapi.json) - 本專案後端 API 的 OpenAPI 3.0 規範文件。您可以使用 Swagger Editor 或其他相容工具來查看 API 的詳細端點、請求和響應結構。

## 使用說明

1.  參考 `openapi.json` 來了解後端提供的所有端點。
2.  開發時，前端應通過 `flightService.js` 中定義的服務來與後端 API 互動。
3.  後端與 Amadeus API 互動需要有效的 `AMADEUS_CLIENT_ID` 和 `AMADEUS_CLIENT_SECRET` 環境變數。

## 整合建議

在系統中整合多個資料來源時，建議：

1. 優先使用TDX作為台灣本地航班的資料來源
2. 使用Cirium FlightStats補充國際航班資訊
3. 實現緩存機制以減少API調用次數
4. 建立資料同步策略，以最佳頻率更新本地資料庫 