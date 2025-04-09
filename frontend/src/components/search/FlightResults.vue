<template>
  <div class="flight-results">
    <!-- 搜索結果數量和提示 -->
    <div class="results-header" v-if="flights && flights.length > 0">
      <div class="results-info">
        <h2>搜索結果</h2>
        <p class="flight-count">{{ flights.length }} 個航班</p>
      </div>
      <div class="results-sort">
        <label for="sort-select">排序：</label>
        <select id="sort-select" v-model="sortOption" @change="sortFlights">
          <option value="price-asc">價格：由低至高</option>
          <option value="price-desc">價格：由高至低</option>
          <option value="departure-asc">出發時間：最早優先</option>
          <option value="departure-desc">出發時間：最晚優先</option>
          <option value="duration-asc">飛行時間：最短優先</option>
        </select>
      </div>
    </div>

    <!-- 航班列表 -->
    <div class="flight-list" v-if="flights && flights.length > 0">
      <FlightList :flights="sortedFlights" />
    </div>

    <!-- 無搜索結果時顯示 -->
    <div class="no-results" v-else-if="searched && (!flights || flights.length === 0)">
      <div class="no-results-content">
        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round" class="no-results-icon">
          <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path>
          <line x1="4.93" y1="4.93" x2="19.07" y2="19.07"></line>
        </svg>
        <h3>沒有找到符合條件的航班</h3>
        <p>請嘗試修改搜索條件或日期</p>
        <div class="suggestion-list">
          <div class="suggestion">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="suggestion-icon">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="12" y1="8" x2="12" y2="16"></line>
              <line x1="8" y1="12" x2="16" y2="12"></line>
            </svg>
            <span>選擇不同的出發/目的地機場</span>
          </div>
          <div class="suggestion">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="suggestion-icon">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="12" y1="8" x2="12" y2="16"></line>
              <line x1="8" y1="12" x2="16" y2="12"></line>
            </svg>
            <span>嘗試附近日期</span>
          </div>
          <div class="suggestion">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="suggestion-icon">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="12" y1="8" x2="12" y2="16"></line>
              <line x1="8" y1="12" x2="16" y2="12"></line>
            </svg>
            <span>移除價格或航空公司篩選</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 尚未搜索時顯示 -->
    <div class="initial-state" v-else-if="!searched">
      <div class="initial-state-content">
        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round" class="initial-icon">
          <path d="M22 2L11 13"></path>
          <path d="M22 2L15 22L11 13L2 9L22 2Z"></path>
        </svg>
        <h3>搜索航班以查看結果</h3>
        <p>請選擇出發地、目的地和日期</p>
      </div>
    </div>
  </div>
</template>

<script>
import FlightList from './FlightList.vue';

export default {
  name: 'FlightResults',
  components: {
    FlightList
  },
  props: {
    flights: {
      type: Array,
      default: () => []
    },
    searched: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      sortOption: 'price-asc'
    };
  },
  computed: {
    sortedFlights() {
      if (!this.flights || this.flights.length === 0) {
        return [];
      }
      
      // 創建一個新的數組來進行排序，不修改原數組
      const sorted = [...this.flights];
      
      switch (this.sortOption) {
        case 'price-asc':
          return sorted.sort((a, b) => parseFloat(a.price) - parseFloat(b.price));
        
        case 'price-desc':
          return sorted.sort((a, b) => parseFloat(b.price) - parseFloat(a.price));
        
        case 'departure-asc':
          return sorted.sort((a, b) => {
            const dateA = new Date(`${a.departure_date}T${a.departure_time}`);
            const dateB = new Date(`${b.departure_date}T${b.departure_time}`);
            return dateA - dateB;
          });
        
        case 'departure-desc':
          return sorted.sort((a, b) => {
            const dateA = new Date(`${a.departure_date}T${a.departure_time}`);
            const dateB = new Date(`${b.departure_date}T${b.departure_time}`);
            return dateB - dateA;
          });
        
        case 'duration-asc':
          return sorted.sort((a, b) => {
            // 如果可以獲取到分鐘形式的飛行時間
            if (a.flight_time_minutes && b.flight_time_minutes) {
              return a.flight_time_minutes - b.flight_time_minutes;
            }
            
            // 如果沒有分鐘形式，則嘗試解析時間字符串
            const getDuration = (flight) => {
              if (!flight.flight_time) return 0;
              
              const parts = flight.flight_time.split('h');
              if (parts.length < 2) return 0;
              
              const hours = parseInt(parts[0].trim(), 10) || 0;
              const minutes = parseInt(parts[1].replace('m', '').trim(), 10) || 0;
              
              return hours * 60 + minutes;
            };
            
            return getDuration(a) - getDuration(b);
          });
        
        default:
          return sorted;
      }
    }
  },
  methods: {
    sortFlights() {
      // 觸發通知外部組件排序已經變更
      this.$emit('sort-change', this.sortOption);
    }
  }
};
</script>

<style scoped>
.flight-results {
  min-height: 200px;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.results-info h2 {
  font-size: 1.5rem;
  margin: 0 0 0.5rem 0;
  font-weight: 600;
}

.flight-count {
  margin: 0;
  color: #666;
  font-size: 0.9rem;
}

.results-sort {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.results-sort label {
  font-size: 0.9rem;
  color: #666;
}

.results-sort select {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  background-color: white;
  font-size: 0.9rem;
}

.no-results, .initial-state {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 3rem 1rem;
  text-align: center;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.no-results-content, .initial-state-content {
  max-width: 500px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.no-results-icon, .initial-icon {
  color: #999;
  margin-bottom: 1.5rem;
}

.no-results h3, .initial-state h3 {
  font-size: 1.3rem;
  margin: 0 0 0.5rem 0;
  font-weight: 600;
}

.no-results p, .initial-state p {
  margin: 0 0 1.5rem 0;
  color: #666;
  font-size: 1rem;
}

.suggestion-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  align-items: flex-start;
  margin-top: 1rem;
  text-align: left;
}

.suggestion {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.95rem;
  color: #444;
}

.suggestion-icon {
  color: #555;
}

@media (max-width: 768px) {
  .results-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  
  .results-sort {
    width: 100%;
  }
  
  .results-sort select {
    flex-grow: 1;
  }
}
</style> 