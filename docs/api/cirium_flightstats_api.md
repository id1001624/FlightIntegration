# Cirium FlightStats API 文檔

## 概述

Cirium FlightStats API 提供全球航班即時和歷史資料，包括航班狀態、延誤信息、天氣條件等。本文檔概述了可用的API端點和使用方法。

## 目錄

1. [認證](#認證)
2. [航空公司 API](#航空公司-api)
3. [機場 API](#機場-api)
4. [機場延誤指數 API](#機場延誤指數-api)
5. [FIDS API](#fids-api)
6. [航班提醒 API](#航班提醒-api)
7. [航班狀態 API](#航班狀態-api)
8. [歷史航班狀態 API](#歷史航班狀態-api)
9. [航班時刻表 API](#航班時刻表-api)
10. [天氣 API](#天氣-api)
11. [錯誤處理](#錯誤處理)
12. [資料限制與最佳實踐](#資料限制與最佳實踐)

## 認證

所有 Cirium FlightStats API 請求都需要 API 密鑰和 app ID 進行認證。

**請求格式**：
```
https://api.flightstats.com/flex/[endpoint]?appId=YOUR_APP_ID&appKey=YOUR_APP_KEY
```

## 航空公司 API

提供全球航空公司資訊和標識符。

### 獲取所有航空公司列表

**請求**：
```
GET /airlines/rest/v1/json/all
```

**回應**：
```json
{
  "airlines": [
    {
      "fs": "CX",
      "iata": "CX",
      "icao": "CPA",
      "name": "Cathay Pacific Airways",
      "active": true
    }
  ]
}
```

### 獲取特定航空公司資訊

**請求**：
```
GET /airlines/rest/v1/json/{airline_code}
```

**參數**：
- `airline_code`：航空公司的 IATA 或 ICAO 代碼

## 機場 API

提供全球機場位置和細節資訊。

### 獲取所有機場列表

**請求**：
```
GET /airports/rest/v1/json/all
```

### 獲取特定機場資訊

**請求**：
```
GET /airports/rest/v1/json/{airport_code}
```

**參數**：
- `airport_code`：機場的 IATA 或 ICAO 代碼

**回應**：
```json
{
  "airport": {
    "fs": "TPE",
    "iata": "TPE",
    "icao": "RCTP",
    "name": "Taiwan Taoyuan International Airport",
    "city": "Taipei",
    "cityCode": "TPE",
    "countryCode": "TW",
    "countryName": "Taiwan",
    "regionName": "Asia",
    "timeZoneRegionName": "Asia/Taipei",
    "latitude": 25.077731,
    "longitude": 121.232822,
    "elevationFeet": 106,
    "classification": 1
  }
}
```

## 機場延誤指數 API

提供主要機場的延誤情況和趨勢。

### 獲取機場延誤指數

**請求**：
```
GET /delayindex/rest/v1/json/airports/{airport_code}
```

**參數**：
- `airport_code`：機場的 IATA 代碼

**回應**：
```json
{
  "delayIndexes": [
    {
      "airport": {
        "fs": "TPE",
        "name": "Taiwan Taoyuan International Airport",
        "city": "Taipei",
        "countryCode": "TW"
      },
      "dateStart": "2023-04-10T13:00:00.000Z",
      "dateEnd": "2023-04-10T13:30:00.000Z",
      "delayIndex": 0.42,
      "observations": 20,
      "canceled": 0,
      "runway": {
        "delayIndex": 0.2
      },
      "departure": {
        "delayIndex": 0.33
      },
      "arrival": {
        "delayIndex": 0.5
      }
    }
  ]
}
```

## FIDS API

Flight Information Display System API 提供機場顯示屏樣式的航班資訊。

### 獲取出發航班

**請求**：
```
GET /fids/rest/v1/json/{airport_code}/departures
```

**參數**：
- `airport_code`：機場的 IATA 代碼
- `requestedFields`：（可選）需要的欄位清單
- `airline`：（可選）航空公司 IATA 代碼
- `maxResults`：（可選）最大結果數

### 獲取抵達航班

**請求**：
```
GET /fids/rest/v1/json/{airport_code}/arrivals
```

**回應**：
```json
{
  "fidsData": [
    {
      "airline": {
        "fs": "CI",
        "name": "China Airlines"
      },
      "flightNumber": "601",
      "city": "Hong Kong",
      "airport": {
        "fs": "HKG",
        "name": "Hong Kong International Airport"
      },
      "scheduledTime": "2023-04-10T13:00:00.000Z",
      "estimatedTime": "2023-04-10T13:15:00.000Z",
      "actualTime": null,
      "term": "1",
      "gate": "A12",
      "status": "ON TIME"
    }
  ]
}
```

## 航班提醒 API

允許訂閱航班狀態變更的通知。

### 創建航班提醒

**請求**：
```
POST /alerts/rest/v1/json/create
```

**請求體**：
```json
{
  "deliverTo": {
    "type": "email",
    "address": "user@example.com"
  },
  "flights": [
    {
      "carrier": "CI",
      "flightNumber": "601",
      "departureAirport": "TPE",
      "arrivalAirport": "HKG",
      "year": 2023,
      "month": 4,
      "day": 10
    }
  ],
  "alertTypes": ["DEPARTURE", "ARRIVAL", "CANCELLATION"]
}
```

## 航班狀態 API

提供近期航班的狀態資訊。

### 依航班號查詢航班狀態

**請求**：
```
GET /flightstatus/rest/v2/json/flight/status/{airline}/{flight}/{departure_date}
```

**參數**：
- `airline`：航空公司 IATA 代碼
- `flight`：航班號
- `departure_date`：出發日期（YYYY/MM/DD 格式）

### 依航線查詢航班狀態

**請求**：
```
GET /flightstatus/rest/v2/json/route/status/{departure}/{arrival}/{departure_date}
```

**參數**：
- `departure`：出發機場 IATA 代碼
- `arrival`：抵達機場 IATA 代碼
- `departure_date`：出發日期（YYYY/MM/DD 格式）

**回應**：
```json
{
  "flightStatuses": [
    {
      "flightId": 123456789,
      "carrierFsCode": "CI",
      "flightNumber": "601",
      "departureAirportFsCode": "TPE",
      "arrivalAirportFsCode": "HKG",
      "departureDate": {
        "dateLocal": "2023-04-10T13:00:00.000",
        "dateUtc": "2023-04-10T05:00:00.000Z"
      },
      "arrivalDate": {
        "dateLocal": "2023-04-10T14:55:00.000",
        "dateUtc": "2023-04-10T06:55:00.000Z"
      },
      "status": "S",
      "schedule": { ... },
      "operationalTimes": { ... },
      "delays": { ... },
      "airportResources": { ... }
    }
  ]
}
```

## 歷史航班狀態 API

提供過去航班的詳細資訊。

### 獲取歷史航班狀態

**請求**：
```
GET /flightstatus/rest/v2/json/flight/status/{airline}/{flight}/{year}/{month}/{day}
```

**參數**：
- `airline`：航空公司 IATA 代碼
- `flight`：航班號
- `year`：四位數年份
- `month`：兩位數月份
- `day`：兩位數日期

## 航班時刻表 API

提供未來計劃航班的詳細資訊。

### 依航班號查詢時刻表

**請求**：
```
GET /schedules/rest/v1/json/flight/{airline}/{flight}/{departure_date}
```

**參數**：
- `airline`：航空公司 IATA 代碼
- `flight`：航班號
- `departure_date`：出發日期（YYYY/MM/DD 格式）

### 依航線查詢時刻表

**請求**：
```
GET /schedules/rest/v1/json/from/{departure}/to/{arrival}/{departure_date}
```

**參數**：
- `departure`：出發機場 IATA 代碼
- `arrival`：抵達機場 IATA 代碼
- `departure_date`：出發日期（YYYY/MM/DD 格式）

**回應**：
```json
{
  "scheduledFlights": [
    {
      "carrierFsCode": "CI",
      "flightNumber": "601",
      "departureAirportFsCode": "TPE",
      "arrivalAirportFsCode": "HKG",
      "departureTime": "2023-04-10T13:00:00.000Z",
      "arrivalTime": "2023-04-10T14:55:00.000Z",
      "stops": 0,
      "flightEquipmentIataCode": "77W",
      "isCodeshare": false
    }
  ]
}
```

## 天氣 API

提供機場天氣資訊。

### 獲取機場天氣

**請求**：
```
GET /weather/rest/v1/json/{airport_code}
```

**參數**：
- `airport_code`：機場的 IATA 代碼

**回應**：
```json
{
  "weather": {
    "airport": {
      "fs": "TPE",
      "iata": "TPE",
      "icao": "RCTP",
      "name": "Taiwan Taoyuan International Airport",
      "city": "Taipei",
      "countryCode": "TW"
    },
    "metar": "RCTP 100500Z 06003KT 9999 SCT020 FEW040 22/22 Q1014",
    "taf": "RCTP 100200Z 1003/1103 09008KT 9999 SCT020",
    "temprature": {
      "celsius": 22,
      "fahrenheit": 71.6
    },
    "visibility": {
      "distanceKm": 10,
      "distanceMi": 6.21
    },
    "pressureMb": 1014,
    "pressureIn": 29.95,
    "sky": {
      "cloudCoverage": "SCT",
      "cloudCoveragePercent": 40,
      "condition": "Partly Cloudy"
    },
    "wind": {
      "speedKts": 3,
      "directionDegrees": 60,
      "direction": "NE"
    }
  }
}
```

## 錯誤處理

API 可能返回以下 HTTP 狀態碼：

- `200 OK`：請求成功
- `400 Bad Request`：請求參數無效
- `401 Unauthorized`：認證失敗
- `403 Forbidden`：無權限訪問資源
- `404 Not Found`：請求的資源不存在
- `429 Too Many Requests`：超過API調用限制
- `500 Internal Server Error`：伺服器內部錯誤

錯誤響應格式：
```json
{
  "error": {
    "httpStatusCode": 400,
    "errorCode": "INVALID_REQUEST",
    "errorMessage": "The request contains invalid parameters"
  }
}
```

## 資料限制與最佳實踐

1. **節約API調用**：考慮緩存常用數據，比如航空公司和機場列表

2. **批量請求**：盡可能合併請求以減少API調用次數

3. **請求頻率**：根據訂閱等級，可能有不同的請求頻率限制

4. **數據時效性**：
   - 航班狀態數據通常每5分鐘更新一次
   - 天氣數據通常每30分鐘更新一次
   - FIDS數據通常每10分鐘更新一次

5. **錯誤處理**：實現指數退避重試機制，處理臨時性錯誤

## 與其他API整合

Cirium FlightStats API 可與以下其他系統整合：

1. **TDX 交通資料平台**：整合台灣本地交通數據
2. **地圖API**：可視化航班和機場位置
3. **通知服務**：發送航班狀態變更通知

## 支援和資源

- API文檔：https://developer.cirium.com/apis/flightstats-apis/
- 支援郵箱：support@cirium.com

---

*注意：本文檔基於公開資料整理，實際使用時請參考Cirium官方最新文檔* 