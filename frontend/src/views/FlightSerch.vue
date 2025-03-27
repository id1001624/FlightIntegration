<template>
  <div class="flight-search">
    <h1>台灣航班查詢系統</h1>
    
    <!-- 查詢表單 -->
    <div class="search-form">
      <div class="form-group">
        <label for="departure">出發地</label>
        <select id="departure" v-model="searchParams.departureAirport" required>
          <option value="">請選擇出發機場</option>
          <option v-for="airport in airports" :key="airport.id" :value="airport.code">
            {{ airport.name }} ({{ airport.code }})
          </option>
        </select>
      </div>
      
      <div class="form-group">
        <label for="arrival">目的地</label>
        <select id="arrival" v-model="searchParams.arrivalAirport" required>
          <option value="">請選擇目的地機場</option>
          <option v-for="airport in airports" :key="airport.id" :value="airport.code">
            {{ airport.name }} ({{ airport.code }})
          </option>
        </select>
      </div>
      
      <div class="form-group">
        <label for="departure-date">出發日期</label>
        <input 
          type="date" 
          id="departure-date" 
          v-model="searchParams.departureDate" 
          required
        >
      </div>
      
      <div class="form-group">
        <label>
          <input type="checkbox" v-model="searchParams.useDateRange">
          使用日期範圍搜尋 (30天內)
        </label>
        <div v-if="searchParams.useDateRange" class="date-range-control">
          <label for="date-range-days">日期範圍 (天):</label>
          <input
            type="number"
            id="date-range-days"
            v-model.number="searchParams.dateRangeDays"
            min="1"
            max="30"
            required
          >
        </div>
      </div>
      
      <div class="form-group">
        <label for="airline">航空公司</label>
        <select id="airline" v-model="searchParams.airlineId">
          <option value="">所有航空公司</option>
          <option v-for="airline in airlines" :key="airline.id" :value="airline.id">
            {{ airline.name }}
          </option>
        </select>
      </div>
      
      <div class="form-group">
        <label>價格範圍</label>
        <div class="price-range">
          <input 
            type="number" 
            placeholder="最低價格" 
            v-model.number="searchParams.minPrice"
          >
          <span>至</span>
          <input 
            type="number" 
            placeholder="最高價格" 
            v-model.number="searchParams.maxPrice"
          >
        </div>
      </div>
      
      <button @click="searchFlights" :disabled="isLoading" class="search-button">
        {{ isLoading ? '搜尋中...' : '搜尋航班' }}
      </button>
    </div>

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
    
    <!-- 搜尋結果 -->
    <div class="search-results" v-if="hasSearched">
      <h2>搜尋結果</h2>
      
      <div v-if="isLoading" class="loading">
        載入中...
      </div>
      
      <div v-else-if="flights.length === 0" class="no-results">
        沒有找到符合條件的航班。
      </div>
      
      <div v-else class="flight-list">
        <div class="flight-card" v-for="flight in flights" :key="flight.id">
          <div class="flight-header">
            <div class="airline">
              <strong>{{ flight.airline.name }}</strong>
              <span>{{ flight.flight_number }}</span>
            </div>
            <div class="price">NT$ {{ flight.price.toLocaleString() }}</div>
          </div>
          
          <div class="flight-details">
            <div class="departure">
              <div class="time">{{ formatTime(flight.departure_time) }}</div>
              <div class="code">{{ flight.departure_airport.code }}</div>
              <div class="city">{{ flight.departure_airport.city }}</div>
            </div>
            
            <div class="flight-duration">
              <!-- 這裡可以計算飛行時間 -->
              <div class="line"></div>
              <div class="duration">直飛</div>
            </div>
            
            <div class="arrival">
              <div class="time">{{ formatTime(flight.arrival_time) }}</div>
              <div class="code">{{ flight.arrival_airport.code }}</div>
              <div class="city">{{ flight.arrival_airport.city }}</div>
            </div>
          </div>
          
          <div class="flight-info">
            <div class="info-item">
              <strong>機長:</strong> {{ flight.captain_name || '暫無資料' }}
            </div>
            <div class="info-item">
              <strong>飛機型號:</strong> {{ flight.aircraft_model || '暫無資料' }}
            </div>
            <div class="purchase-link" v-if="flight.purchase_link">
              <a :href="flight.purchase_link" target="_blank" class="btn-purchase">購買機票</a>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';  // 引入axios用於發送HTTP請求，將JSON資料轉換為對象

export default {
  name: 'FlightSearch',
  
  data() {
    return {
      // 存放所有機場資料，用於下拉選單
      airports: [],
      
      // 存放所有航空公司資料，用於下拉選單
      airlines: [],
      
      // 搜尋參數
      searchParams: {
        departureAirport: '',
        arrivalAirport: '',
        departureDate: new Date().toISOString().split('T')[0],  // 預設為今天
        useDateRange: false,
        dateRangeDays: 7,
        airlineId: '',
        minPrice: '',
        maxPrice: ''
      },
      
      // 搜尋結果
      flights: [],
      
      // 狀態標記
      isLoading: false,
      hasSearched: false,
      error: null,

      // 排序選項
      sortOptions: {
        by: 'price',
        order: 'asc'
      }
    }
  },
  
  // 頁面載入時執行
  created() {
    // 獲取所有機場資料
    this.fetchAirports();
    // 獲取所有航空公司資料
    this.fetchAirlines();
  },
  
  methods: {
    // 獲取所有機場資料的方法
    async fetchAirports() {
      try {
        this.isLoading = true;
        // 發送GET請求到機場API
        const response = await axios.get('http://localhost:5000/api/airports');
        
        if (response.data.success) {
          // 獲取成功，保存機場資料，response.data 已經是解析後的JavaScript物件
          this.airports = response.data.data;
        } else {
          console.error('獲取機場資料失敗:', response.data.message);
          this.error = '無法載入機場資料，請稍後再試。';
        }
      } catch (error) {
        console.error('獲取機場資料出錯:', error);
        this.error = '無法連接到伺服器，請確認網路連接。';
      } finally {
        this.isLoading = false;
      }
    },
    
    // 獲取所有航空公司資料的方法
    async fetchAirlines() {
      try {
        // 發送GET請求到航空公司API
        const response = await axios.get('http://localhost:5000/api/airlines');
        
        if (response.data.success) {
          // 獲取成功，保存航空公司資料
          this.airlines = response.data.data;
        } else {
          console.error('獲取航空公司資料失敗:', response.data.message);
          this.error = '無法載入航空公司資料，請稍後再試。';
        }
      } catch (error) {
        console.error('獲取航空公司資料出錯:', error);
        this.error = '無法連接到伺服器，請確認網路連接。';
      }
    },
    
    // 搜尋航班的方法
    async searchFlights() {
      // 檢查是否填寫了必要欄位
      if (!this.searchParams.departureAirport || 
          !this.searchParams.arrivalAirport || 
          !this.searchParams.departureDate) {
        alert('請填寫所有必要欄位');
        return;
      }
      
      try {
        this.isLoading = true;
        this.hasSearched = true;  // 標記已進行搜尋
        
        // 構建請求URL和參數
        const url = 'http://localhost:5000/api/flights/search';
        const params = {
          departure_airport: this.searchParams.departureAirport,
          arrival_airport: this.searchParams.arrivalAirport,
          departure_date: this.searchParams.departureDate
        };
        
        // 添加可選參數
        if (this.searchParams.useDateRange) {
          params.date_range = 'true';
          params.date_range_days = this.searchParams.dateRangeDays;
        }
        
        if (this.searchParams.airlineId) {
          params.airline_id = this.searchParams.airlineId;
        }
        
        if (this.searchParams.minPrice) {
          params.min_price = this.searchParams.minPrice;
        }
        
        if (this.searchParams.maxPrice) {
          params.max_price = this.searchParams.maxPrice;
        }
        
        // 發送GET請求搜尋航班
        const response = await axios.get(url, { params });
        
        if (response.data.success) {
          // 獲取成功，保存航班資料
          this.flights = response.data.data;
        } else {
          console.error('搜尋航班失敗:', response.data.message);
          this.error = response.data.message || '搜尋航班時發生錯誤，請稍後再試。';
          this.flights = [];
        }
      } catch (error) {
        console.error('搜尋航班出錯:', error);
        this.error = '無法連接到伺服器，請確認網路連接。';
        this.flights = [];
      } finally {
        this.isLoading = false;
      }
    },
    // 更新搜尋參數以包含排序選項
    searchFlights() {
      // ...現有代碼
      const params = {
        // ...現有參數
        sort_by: this.sortOptions.by,
        sort_order: this.sortOptions.order
      };
    },
    // 格式化時間的方法
    formatTime(dateTimeStr) {
      // 將時間字串轉成對象並格式化為HH:MM顯示
      const date = new Date(dateTimeStr);
      return date.toLocaleTimeString('zh-TW', { 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: false  // 使用24小時制
      });
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
  
  <style src="@/assets/styles/flight-search.css" scoped></style>