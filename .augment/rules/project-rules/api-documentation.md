---
type: "agent_requested"
description: "請根據project-cursor-rules.md自動使用規則"
---
# API 文件規範

本文檔定義了臺灣航班整合系統的 API 文件規範，確保 API 設計一致且易於理解和維護。

## 1. API 設計原則

### 1.1 RESTful 設計

- 使用標準 HTTP 方法 (GET, POST, PUT, DELETE)
- 使用資源導向的 URL 路徑 (名詞複數形式)
- 使用正確的 HTTP 狀態碼表示響應結果
- 使用查詢參數處理過濾、排序和分頁

### 1.2 API 版本控制

- 在 URL 路徑中包含版本號: `/api/v1/...`
- 主要版本變更需考慮向後兼容性
- 減少破壞性變更，優先使用擴展現有 API

### 1.3 API 基本路徑

- 基礎路徑: `/api/v1`
- 本地開發: `http://localhost:5000/api/v1`
- 生產環境: `https://<render-backend-url>/api/v1`

## 2. API 代碼註解規範

### 2.1 控制器函數註解格式

所有 API 端點處理函數必須使用以下格式的文檔字符串:

```python
@app.route("/api/v1/flights", methods=["GET"])
def get_flights():
    """獲取符合條件的航班列表。
    
    ---
    tags:
      - 航班
    parameters:
      - name: departure
        in: query
        schema:
          type: string
        required: true
        description: 出發機場代碼 (如 TPE)
      - name: arrival
        in: query
        schema:
          type: string
        required: true
        description: 到達機場代碼 (如 HKG)
      - name: date
        in: query
        schema:
          type: string
          format: date
        required: true
        description: 出發日期 (YYYY-MM-DD 格式)
      - name: page
        in: query
        schema:
          type: integer
          default: 1
        description: 分頁頁碼
      - name: limit
        in: query
        schema:
          type: integer
          default: 20
        description: 每頁結果數量
    responses:
      200:
        description: 成功返回航班列表
        content:
          application/json:
            schema: FlightListSchema
      400:
        description: 請求參數無效
        content:
          application/json:
            schema: ErrorSchema
      500:
        description: 伺服器內部錯誤
    """
    # 實現代碼...
```

註解應包含的關鍵部分:
- 簡短的功能描述
- 使用 OpenAPI (Swagger) 格式的 YAML 定義
- 完整的參數描述 (包括類型、是否必需、默認值)
- 所有可能的響應狀態碼及其含義
- 應使用引用 Schema 而非內聯定義複雜響應結構

## 3. API 請求與回應規範

### 3.1 請求參數

- **URL 參數 (Path Parameters)**: 用於標識特定資源
  ```
  /api/v1/flights/{flight_id}
  ```

- **查詢參數 (Query Parameters)**: 用於過濾、排序、分頁
  ```
  /api/v1/flights?departure=TPE&arrival=HKG&date=2023-12-25
  ```

- **請求體 (Request Body)**: 使用 JSON 格式
  ```json
  {
    "passenger_count": 2,
    "class_type": "economy"
  }
  ```

### 3.2 回應格式

所有 API 回應應使用一致的格式:

```json
{
  "success": true,
  "data": [...],  // 主要數據載荷
  "message": "",  // 成功或錯誤訊息
  "pagination": {  // 若適用
    "current_page": 1,
    "total_pages": 5,
    "total_results": 95,
    "next_page": 2,
    "prev_page": null
  }
}
```

#### 成功範例:

```json
{
  "success": true,
  "data": [
    {
      "flight_id": "CX123-20251225",
      "flight_number": "CX123",
      "departure": {
        "airport_id": "TPE",
        "name": "台灣桃園國際機場",
        "time": "2025-12-25T08:30:00+08:00"
      },
      "arrival": {
        "airport_id": "HKG",
        "name": "香港國際機場",
        "time": "2025-12-25T10:30:00+08:00"
      },
      "airline": {
        "airline_id": "CX",
        "name": "國泰航空",
        "logo_path": "/images/airlines/cx.png"
      },
      "price": 3500
    }
  ],
  "message": "",
  "pagination": {
    "current_page": 1,
    "total_pages": 3,
    "total_results": 52,
    "next_page": 2,
    "prev_page": null
  }
}
```

#### 錯誤範例:

```json
{
  "success": false,
  "data": null,
  "message": "無效的出發機場代碼: XYZ",
  "error_code": "INVALID_DEPARTURE"
}
```

### 3.3 錯誤處理

系統中使用的標準錯誤碼:

| HTTP 狀態碼 | 錯誤代碼 | 說明 |
|---|---|---|
| 400 | INVALID_PARAMETER | 請求參數無效 |
| 400 | MISSING_PARAMETER | 缺少必要參數 |
| 400 | INVALID_DATE_FORMAT | 日期格式錯誤 |
| 404 | FLIGHT_NOT_FOUND | 找不到指定航班 |
| 404 | AIRPORT_NOT_FOUND | 找不到指定機場 |
| 404 | AIRLINE_NOT_FOUND | 找不到指定航空公司 |
| 429 | RATE_LIMIT_EXCEEDED | 超過 API 請求限制 |
| 500 | INTERNAL_SERVER_ERROR | 伺服器內部錯誤 |
| 503 | EXTERNAL_API_ERROR | 外部 API 異常 |

## 4. API 文件生成工具

### 4.1 使用 Flask-RESTX

本專案使用 [Flask-RESTX](mdc:https:/flask-restx.readthedocs.io) 自動生成 API 文件:

```python
from flask import Flask
from flask_restx import Api, Resource, fields

app = Flask(__name__)
api = Api(app, version='1.0', title='航班整合系統 API',
    description='臺灣航班整合系統 RESTful API 文件')

ns = api.namespace('flights', description='航班操作')

flight_model = api.model('Flight', {
    'flight_id': fields.String(description='航班 ID'),
    'flight_number': fields.String(description='航班編號'),
    # ... 其他欄位定義
})

@ns.route('/')
class FlightList(Resource):
    @ns.doc('list_flights')
    @ns.param('departure', '出發機場代碼')
    @ns.param('arrival', '到達機場代碼')
    @ns.param('date', '出發日期 (YYYY-MM-DD)')
    @ns.response(200, '成功', flight_model)
    def get(self):
        """獲取符合條件的航班列表"""
        # 實現代碼...
```

### 4.2 文件訪問

- 本地開發: `http://localhost:5000/api/v1/doc/`
- 生產環境: `https://<render-backend-url>/api/v1/doc/`

### 4.3 API 測試

- 使用 Swagger UI 進行在線測試
- 使用 Postman 進行更複雜的測試場景
- 為常用 API 請求保存 Postman 集合

## 5. Schema 定義標準

### 5.1 Schema 命名規範

- 使用 CamelCase 命名 (如 `FlightDetailSchema`)
- 基本 Schema 使用 `Basic` 前綴 (如 `AirportBasicSchema`)
- 列表響應使用 `List` 後綴 (如 `FlightListSchema`)

### 5.2 Schema 重用

- 定義并重用通用模式 (如 `PaginationSchema`, `ErrorSchema`)
- 使用嵌套保持模式一致性 (如 `airline` 欄位在不同 Schema 中定義一致)
- 使用繼承擴展現有模式

### 5.3 Schema 示例

```python
from marshmallow import Schema, fields

class AirportBasicSchema(Schema):
    """機場基本信息模式"""
    code = fields.Str(required=True, attribute="airport_id")
    name = fields.Str(required=True, attribute="name_zh")
    
class AirlineBasicSchema(Schema):
    """航空公司基本信息模式"""
    code = fields.Str(required=True, attribute="airline_id")
    name = fields.Str(required=True, attribute="name_zh")
    logo_path = fields.Str()

class FlightSchema(Schema):
    """航班詳情模式"""
    flight_id = fields.Str(required=True)
    flight_number = fields.Str(required=True)
    departure = fields.Nested(AirportBasicSchema, required=True)
    arrival = fields.Nested(AirportBasicSchema, required=True)
    airline = fields.Nested(AirlineBasicSchema, required=True)
    price = fields.Float(required=True)
    # 其他欄位...
```

## 6. API 端點清單

記錄系統中的關鍵 API 端點:

| 端點 | 方法 | 描述 | 狀態 |
|---|---|---|---|
| `/api/v1/flights/search` | GET | 搜索航班 | 已實現 |
| `/api/v1/flights/{flight_id}` | GET | 獲取航班詳情 | 已實現 |
| `/api/v1/airports/taiwan` | GET | 獲取台灣機場列表 | 已實現 |
| `/api/v1/flights/{departure}/destinations` | GET | 獲取可達目的地 | 已實現 |
| `/api/v1/airlines` | GET | 獲取航空公司列表 | 已實現 |
| `/api/v1/prices/track` | POST | 追蹤價格變動 | 計劃中 |
| `/api/v1/line/webhook` | POST | LINE Bot Webhook | 已實現 |

