# TDX 航空 API 使用範例

此目錄包含了使用 TDX（Transport Data eXchange，運輸資料流通服務平臺）航空相關 API 的範例程式碼。這些範例展示了如何獲取航班資訊、預測航班延誤以及整合航班與氣象資訊等功能。

## 範例檔案說明

- **get_taiwan_flights.py**: 展示如何獲取台灣主要機場的航班資訊
- **flight_prediction.py**: 示範如何建立航班延誤預測模型
- **flight_weather_integration.py**: 展示如何整合航班資訊與目的地氣象資訊

## 安裝必要套件

在執行範例程式之前，請先安裝以下必要的 Python 套件：

```bash
pip install requests pandas numpy scikit-learn
```

## 執行範例

### 1. 獲取 TDX API 金鑰

在執行範例之前，您需要先獲取 TDX API 的 Client ID 和 Client Secret：

1. 在 [TDX 官網](https://tdx.transportdata.tw/register) 完成註冊和信箱驗證
2. 登入後，在 [TDX 會員中心](https://tdx.transportdata.tw/user/dataservice/key) 取得 Client ID 和 Client Secret

### 2. 修改範例程式

在每個範例程式中，找到以下程式碼並替換為您的 API 金鑰：

```python
# 請替換為您的 Client ID 和 Client Secret
client_id = "YOUR_CLIENT_ID"
client_secret = "YOUR_CLIENT_SECRET"
```

### 3. 執行範例程式

#### 獲取台灣航班資訊

```bash
python get_taiwan_flights.py
```

這個範例會獲取台灣主要機場的航班資訊，包括：
- 台灣機場資訊
- 台灣航空公司資訊
- 桃園機場今日出發航班
- 桃園機場今日抵達航班
- 桃園到松山機場的航班

執行後，資料會儲存為 JSON 檔案。

#### 航班延誤預測

```bash
python flight_prediction.py
```

這個範例會：
1. 獲取過去 30 天的航班歷史資料（注意：實際 TDX API 可能沒有直接提供過去的歷史資料，您可能需要長期收集資料建立自己的歷史數據庫）
2. 使用航班資料訓練延誤預測模型
3. 預測今日航班的延誤機率
4. 輸出高延誤風險航班

執行後，預測結果會儲存為 CSV 檔案。

#### 航班與氣象資訊整合

```bash
python flight_weather_integration.py
```

這個範例會：
1. 獲取台北松山機場的今日出發航班
2. 根據目的地機場獲取對應城市的天氣資訊
3. 整合航班與天氣資訊
4. 獲取台灣地區天氣預報

執行後，整合資料會儲存為 JSON 檔案。

## 注意事項

1. 所有範例程式都包含錯誤處理和認證機制，以確保可靠的 API 存取
2. TDX API 有使用頻率限制，詳情請參考 [TDX 訂閱收費方案](https://tdx.transportdata.tw/pricing)
3. 如果您需要頻繁存取 API，建議實作 Token 快取機制（範例程式已包含）
4. 程式中的某些氣象 API 路徑可能需要根據實際 TDX API 文件調整 