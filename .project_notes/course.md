# 專案教學

請接續你的台灣航班整合系統開發教學()，你幫我在網站上收尋，並教會我。
以下是我們的核心功能，我作為專案組的全端人員，我還需要學會什麼請一步一步教我。要根據我的專案結構，把我當幼稚園來教，輸出不超過1000行，刪掉正確的廢話，直覺好理解。

## 主要目標讓我學會並完成專案。
## 專案核心功能:

專案是以網頁端結合linebot的專案，python為主要語言，前端為Vue。
請依序功能教學

- 查詢飛機航班(網頁)

條件：起飛地點、降落地點、時間起訖日（30 天內）、航空公司、價錢
結果：預計起飛時間、預計降落時間、航班公司、機長、飛機型號、價錢

整合購票功能、旅遊保險、各航空累積哩程查詢
- 同步 LINE 機器人

查詢飛機航班、延誤停飛提示、常用詞小幫手、推薦當地旅遊行程、機票價格漲幅提示
- 預測航班起降狀態

預測起降、預測當地天氣
- 社群平台(進階)

社群互動、舒適度評分

- 導覽地圖(進階)

查詢各機場內部設施平面圖

基於專案結構和網路搜尋，我為您準備了第二堂課：

# 第二堂課：整合外部航班API並優化航班查詢功能

## 一、什麼是外部API

外部API就像是別人提供的服務窗口，我們通過發送請求，就能獲取他們的資料。

例如：
- PTX 交通部運輸資料流通服務平臺 - 提供臺灣航班資訊
- FlightAware - 提供全球航班追蹤服務
- Skyscanner - 提供航班價格比較

## 二、申請API金鑰（Key）

以PTX平台為例：
1. 註冊帳號：到 PTX 網站註冊
2. 建立應用：填寫應用名稱、介紹
3. 獲取金鑰：系統會給你 ID 和 Key

## 三、環境設定

在`.env`檔案中加入：

```
PTX_APP_ID=你的應用ID
PTX_APP_KEY=你的應用金鑰
```

## 四、建立API服務層

在`backend/app/services`下創建`external_api.py`：

```python
import requests
import hmac
import hashlib
import base64
import time
from datetime import datetime
import os

class PTXService:
    """交通部PTX平台服務"""
    
    def __init__(self):
        # 從環境變數獲取金鑰
        self.app_id = os.environ.get('PTX_APP_ID')
        self.app_key = os.environ.get('PTX_APP_KEY')
        self.base_url = "https://ptx.transportdata.tw/MOTC/v2/Air"
    
    def _get_auth_header(self):
        """產生API驗證標頭"""
        xdate = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
        hashed = hmac.new(
            self.app_key.encode('utf-8'),
            f"x-date: {xdate}".encode('utf-8'),
            hashlib.sha1
        ).digest()
        signature = base64.b64encode(hashed).decode()
        
        return {
            'Authorization': f'hmac username="{self.app_id}", algorithm="hmac-sha1", headers="x-date", signature="{signature}"',
            'x-date': xdate,
            'Accept-Encoding': 'gzip'
        }
    
    def get_flights(self, airline_code=None, flight_date=None):
        """獲取航班資訊"""
        url = f"{self.base_url}/FIDS/Airport/Departure"
        params = {'$format': 'JSON'}
        
        if airline_code:
            params['$filter'] = f"AirlineID eq '{airline_code}'"
        if flight_date:
            # 將日期轉換為適當格式
            date_str = flight_date.strftime('%Y-%m-%d')
            if '$filter' in params:
                params['$filter'] += f" and Date(FlightDate) eq {date_str}"
            else:
                params['$filter'] = f"Date(FlightDate) eq {date_str}"
        
        try:
            response = requests.get(
                url,
                params=params,
                headers=self._get_auth_header()
            )
            response.raise_for_status()  # 拋出HTTP錯誤
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API請求錯誤: {e}")
            return None
    
    def sync_flight_data(self):
        """同步航班資料到資料庫"""
        from app.models.flights import Flights
        from app.models.airports import Airports
        from app.models.airlines import Airlines
        from app import db
        
        # 獲取PTX最新航班資料
        flight_data = self.get_flights()
        if not flight_data:
            return False
            
        # 遍歷航班資料並更新資料庫
        for flight in flight_data:
            # 從API資料中提取資訊
            flight_number = flight.get('FlightNumber')
            airline_code = flight.get('AirlineID')
            departure_code = flight.get('DepartureAirportID')
            arrival_code = flight.get('ArrivalAirportID')
            departure_time = datetime.strptime(flight.get('ScheduleDepartureTime'), '%Y-%m-%dT%H:%M:%S')
            arrival_time = datetime.strptime(flight.get('ScheduleArrivalTime'), '%Y-%m-%dT%H:%M:%S')
            
            # 查找或創建航空公司
            airline = Airlines.query.filter_by(code=airline_code).first()
            if not airline:
                continue  # 跳過未知航空公司的航班
                
            # 查找機場
            departure_airport = Airports.query.filter_by(code=departure_code).first()
            arrival_airport = Airports.query.filter_by(code=arrival_code).first()
            if not departure_airport or not arrival_airport:
                continue  # 跳過無法辨識機場的航班
                
            # 查找或創建航班
            flight_obj = Flights.query.filter_by(flight_number=flight_number).first()
            if not flight_obj:
                flight_obj = Flights(
                    flight_number=flight_number,
                    airline_id=airline.id,
                    departure_airport_id=departure_airport.id,
                    arrival_airport_id=arrival_airport.id,
                    departure_time=departure_time,
                    arrival_time=arrival_time,
                    price=0  # 需要從其他源獲取價格資訊
                )
                db.session.add(flight_obj)
            else:
                # 更新現有航班
                flight_obj.departure_time = departure_time
                flight_obj.arrival_time = arrival_time
                
        # 提交所有變更
        try:
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"資料庫更新錯誤: {e}")
            return False
```

## 五、定時更新航班資料

在`app/__init__.py`新增排程任務：

```python
from apscheduler.schedulers.background import BackgroundScheduler
from app.services.external_api import PTXService

def create_app():
    # 原有代碼...
    
    # 初始化排程器
    scheduler = BackgroundScheduler()
    ptx_service = PTXService()
    
    # 每天凌晨2點同步航班資料
    scheduler.add_job(
        ptx_service.sync_flight_data,
        'cron',
        hour=2,
        minute=0
    )
    
    # 啟動排程器
    scheduler.start()
    
    return app
```

## 六、創建管理API工具

建立航班同步管理界面：

1. 在`app/controllers/api.py`添加管理路由：

```python
@api.route('/admin/sync-flights', methods=['POST'])
def admin_sync_flights():
    """手動同步航班資料"""
    from app.services.external_api import PTXService
    
    ptx_service = PTXService()
    success = ptx_service.sync_flight_data()
    
    if success:
        return jsonify({
            'success': True,
            'message': '航班資料同步成功'
        })
    else:
        return jsonify({
            'success': False,
            'message': '航班資料同步失敗'
        }), 500
```

2. 前端Admin界面：

在`frontend/src/views/admin/FlightManager.vue`添加同步按鈕：

```vue
<template>
  <div class="flight-manager">
    <h1>航班資料管理</h1>
    
    <div class="actions">
      <button @click="syncFlights" :disabled="isSyncing" class="sync-button">
        {{ isSyncing ? '同步中...' : '從PTX同步航班資料' }}
      </button>
    </div>
    
    <!-- 其他管理介面 -->
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      isSyncing: false
    }
  },
  methods: {
    async syncFlights() {
      this.isSyncing = true;
      try {
        const response = await axios.post('http://localhost:5000/api/admin/sync-flights');
        if (response.data.success) {
          alert('航班資料同步成功！');
        } else {
          alert('航班資料同步失敗：' + response.data.message);
        }
      } catch (error) {
        alert('發生錯誤：' + error.message);
      } finally {
        this.isSyncing = false;
      }
    }
  }
}
</script>
```

## 七、擴展航班查詢功能

更新航班查詢API，支援更多條件：

1. 修改`backend/app/controllers/api.py`中的`search_flights`：

```python
@api.route('/flights/search', methods=['GET'])
def search_flights():
    """增強版航班搜尋"""
    # 基本參數
    departure_code = request.args.get('departure_airport')
    arrival_code = request.args.get('arrival_airport')
    departure_date_str = request.args.get('departure_date')
    is_round_trip = request.args.get('is_round_trip', 'false').lower() == 'true'
    return_date_str = request.args.get('return_date')
    
    # 新增參數
    direct_only = request.args.get('direct_only', 'false').lower() == 'true'
    sort_by = request.args.get('sort_by', 'price')  # 預設按價格排序
    sort_order = request.args.get('sort_order', 'asc')  # 預設升序
    
    # 查詢邏輯...
    
    # 根據排序參數排序結果
    if sort_by == 'price':
        sorted_flights = sorted(flights, key=lambda x: x.price, reverse=(sort_order=='desc'))
    elif sort_by == 'departure_time':
        sorted_flights = sorted(flights, key=lambda x: x.departure_time, reverse=(sort_order=='desc'))
    elif sort_by == 'arrival_time':
        sorted_flights = sorted(flights, key=lambda x: x.arrival_time, reverse=(sort_order=='desc'))
    else:
        sorted_flights = flights
    
    # 返回結果...
```

## 八、改善前端介面

更新`frontend/src/views/FlightSearch.vue`添加排序選項：

```vue
<template>
  <!-- 查詢表單... -->
  
  <!-- 排序選項 -->
  <div class="sort-options" v-if="hasSearched && flights.length > 0">
    <label for="sort-by">排序方式：</label>
    <select id="sort-by" v-model="sortOptions.by" @change="applySort">
      <option value="price">價格</option>
      <option value="departure_time">出發時間</option>
      <option value="arrival_time">抵達時間</option>
    </select>
    
    <label for="sort-order">順序：</label>
    <select id="sort-order" v-model="sortOptions.order" @change="applySort">
      <option value="asc">升序</option>
      <option value="desc">降序</option>
    </select>
  </div>
  
  <!-- 搜尋結果... -->
</template>

<script>
export default {
  data() {
    return {
      // 現有data...
      
      // 排序選項
      sortOptions: {
        by: 'price',
        order: 'asc'
      }
    }
  },
  methods: {
    // 現有methods...
    
    // 更新搜尋參數以包含排序選項
    searchFlights() {
      // ...現有代碼
      const params = {
        // ...現有參數
        sort_by: this.sortOptions.by,
        sort_order: this.sortOptions.order
      };
      // ...其餘代碼
    },
    
    // 應用排序
    applySort() {
      if (this.hasSearched) {
        this.searchFlights();
      }
    }
  }
}
</script>
```

## 九、總結與練習

今天我們學會了：
1. 整合外部API獲取即時航班資料
2. 使用定時任務自動更新資料
3. 建立管理介面手動同步資料
4. 增強查詢功能支援排序

練習：
1. 嘗試整合其他航班API（如FlightAware）
2. 添加航班延誤通知功能
3. 實現航班價格比較功能
