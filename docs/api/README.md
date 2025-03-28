# 航班整合系統 API 文檔目錄

本目錄包含了航班整合系統使用的各種API相關文檔。

## 可用文檔

### TDX API 文檔

- [TDX 航空 API 文檔](./tdx_air_api.md) - 台灣交通部運輸資料流通服務平台(TDX)提供的航空相關API文檔
- [TDX 範例程式](./tdx_examples/) - TDX API 使用範例程式目錄

### Cirium FlightStats API 文檔

- [Cirium FlightStats API 文檔](./cirium_flightstats_api.md) - Cirium FlightStats提供的航班相關API文檔

## 使用說明

1. API文檔提供了每個端點的詳細說明、請求和響應格式
2. 在實際開發中，請先申請相應的API密鑰
3. 參考範例程式來了解如何調用和處理API數據

## 整合建議

在系統中整合多個資料來源時，建議：

1. 優先使用TDX作為台灣本地航班的資料來源
2. 使用Cirium FlightStats補充國際航班資訊
3. 實現緩存機制以減少API調用次數
4. 建立資料同步策略，以最佳頻率更新本地資料庫 