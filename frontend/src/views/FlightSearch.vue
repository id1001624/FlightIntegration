<template>
  <div class="flight-search-page">
    <!-- 載入指示器 -->
    <div class="loading-overlay" v-if="loading">
      <div class="loading-spinner"></div>
    </div>
    
    <div class="container">
      <h1 class="page-title">航班搜尋</h1>
      
      <!-- 搜索表單組件 -->
      <SearchForm
        :is-searching="isSearching"
        @search="handleSearch"
      />
      
      <div class="main-content" v-if="hasSearched">
        <div class="route-info" v-if="searchParams.departureAirport && searchParams.arrivalAirport">
          <h2>
            {{ formatAirportCode(searchParams.departureAirport) }} → 
            {{ formatAirportCode(searchParams.arrivalAirport) }}
          </h2>
          <p class="date-info">{{ formattedDepartureDate }}</p>
        </div>
        
        <div class="content-layout">
          <!-- 篩選面板組件 -->
          <div class="filter-container">
            <FilterPanel 
              :flights="flights"
              @filter-change="handleFilterChange"
            />
          </div>
          
          <!-- 結果顯示組件 -->
          <div class="results-container">
            <FlightResults 
              :flights="filteredFlights"
              :searched="hasSearched"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import SearchForm from '@/components/search/SearchForm.vue';
import FilterPanel from '@/components/search/FilterPanel.vue';
import FlightResults from '@/components/search/FlightResults.vue';
import flightService from '@/api/services/flightService';

export default {
  name: 'FlightSearch',
  components: {
    SearchForm,
    FilterPanel,
    FlightResults
  },
  data() {
    return {
      // 主要數據
      flights: [],
      filteredFlights: [],
      
      // 搜索相關狀態
      loading: false,
      isSearching: false,
      hasSearched: false,
      
      // 機場數據
      taiwanAirports: [],
      destinationAirports: [],
      
      // 搜索參數
      searchParams: {
        departureAirport: null,
        arrivalAirport: null,
        departureDate: new Date().toISOString().split('T')[0],
        returnDate: '',
        classType: 'economy'
      },
      
      // 篩選相關
      filters: {
        airlines: [],
        priceRange: {
          min: 0,
          max: 50000
        }
      }
    };
  },
  computed: {
    formattedDepartureDate() {
      if (!this.searchParams.departureDate) return '';
      
      const date = new Date(this.searchParams.departureDate);
      return date.toLocaleDateString('zh-TW', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        weekday: 'long'
      });
    }
  },
  methods: {
    async fetchTaiwanAirports() {
      try {
        const airports = await flightService.getTaiwanAirports();
        if (airports && airports.length > 0) {
          this.taiwanAirports = airports;
        }
      } catch (error) {
        console.error('獲取台灣機場資料時出錯:', error);
      }
    },
    
    async handleSearch(searchParams) {
      this.loading = true;
      this.isSearching = true;
      this.hasSearched = true;
      this.searchParams = { ...searchParams };
      
      try {
        // 獲取格式化的參數
        const departureCode = searchParams.departureAirport?.code;
        const arrivalCode = searchParams.arrivalAirport?.code;
        
        // 確保必要參數存在
        if (!departureCode || !arrivalCode) {
          throw new Error('缺少必要的參數: 出發地或目的地');
        }
        
        const apiSearchParams = {
          departureAirportCode: departureCode,
          arrivalAirportCode: arrivalCode,
          departureDate: searchParams.departureDate,
          returnDate: searchParams.returnDate || undefined,
          classType: searchParams.classType || 'economy'
        };
        
        const response = await flightService.searchFlights(apiSearchParams);
        
        // 處理 API 回應
        let flightsData = [];
        
        // 確保響應不是字符串
        if (typeof response === 'string') {
          try {
            const parsed = JSON.parse(response);
            if (parsed && Array.isArray(parsed)) {
              flightsData = parsed;
            } else if (parsed && parsed.outbound) {
              flightsData = parsed.outbound;
            } else if (parsed && parsed.outbound_flights) {
              flightsData = parsed.outbound_flights;
            } else {
              flightsData = flightService._handleResponse(parsed);
            }
          } catch (e) {
            console.error('無法解析 JSON 響應:', e);
            flightsData = [];
          }
        } else if (response && response.outbound) {
          flightsData = response.outbound;
        } else if (response && response.outbound_flights) {
          flightsData = response.outbound_flights;
        } else {
          flightsData = flightService._handleResponse(response);
        }
        
        // 如果沒有航班數據
        if (!flightsData || flightsData.length === 0) {
          this.flights = [];
          alert(`沒有找到從 ${searchParams.departureAirport.name} 到 ${searchParams.arrivalAirport.name} 的航班，請選擇其他日期或目的地。`);
          return;
        }
        
        // 處理每個航班對象，確保屬性格式一致
        this.flights = flightsData.map(flight => {
          // 確保價格是數字
          if (flight.price && typeof flight.price === 'string') {
            flight.price = parseFloat(flight.price);
          }
          return flight;
        });
        
        // 更新篩選後的航班
        this.filteredFlights = [...this.flights];
        
      } catch (error) {
        console.error('搜索航班時出錯:', error);
        alert('搜索航班時發生錯誤。請檢查後端連接和伺服器日誌。');
        this.flights = [];
        this.filteredFlights = [];
      } finally {
        this.loading = false;
        this.isSearching = false;
      }
    },
    
    handleFilterChange(filters) {
      // 應用篩選條件
      this.filters = { ...filters };
      
      // 篩選航班
      this.filteredFlights = this.flights.filter(flight => {
        // 航空公司篩選
        if (filters.airlines && filters.airlines.length > 0) {
          const airlineCode = flight.airline_code || (flight.airline ? flight.airline.code : '');
          if (!filters.airlines.includes(airlineCode)) {
            return false;
          }
        }
        
        // 價格篩選
        const flightPrice = parseFloat(flight.price) || 0;
        if (flightPrice < filters.priceRange.min || flightPrice > filters.priceRange.max) {
          return false;
        }
        
        return true;
      });
    },
    
    formatAirportCode(airport) {
      if (!airport) return '';
      return `${airport.code} - ${airport.name}`;
    }
  },
  created() {
    this.fetchTaiwanAirports();
  }
};
</script>

<style scoped>
.flight-search-page {
  padding: 2rem 0;
  background-color: #f8f8f8;
  min-height: calc(100vh - 60px);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1rem;
}

.page-title {
  margin-bottom: 2rem;
  color: #000;
  font-weight: 600;
  text-align: center;
  letter-spacing: 0.05em;
  font-size: 2rem;
}

.main-content {
  margin-top: 2rem;
}

.route-info {
  margin-bottom: 1.5rem;
}

.route-info h2 {
  font-size: 1.5rem;
  margin: 0 0 0.5rem 0;
  font-weight: 600;
}

.date-info {
  color: #666;
  margin: 0;
  font-size: 1rem;
}

.content-layout {
  display: flex;
  gap: 2rem;
}

.filter-container {
  width: 280px;
  flex-shrink: 0;
}

.results-container {
  flex: 1;
}

/* 載入中指示器 */
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.8);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.loading-spinner {
  border: 3px solid #f3f3f3;
  border-top: 3px solid #000;
  border-radius: 50%;
  width: 30px;
  height: 30px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@media (max-width: 992px) {
  .content-layout {
    flex-direction: column;
  }
  
  .filter-container {
    width: 100%;
    margin-bottom: 1.5rem;
  }
}

@media (max-width: 768px) {
  .page-title {
    font-size: 1.8rem;
  }
}
</style> 