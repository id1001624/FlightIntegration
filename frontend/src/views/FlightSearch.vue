<template>
  <div class="flight-search-page">
    <!-- 載入指示器 -->
    <div v-if="loading" class="loading-overlay">
      <div class="loading-spinner"></div>
    </div>

    <!-- 搜索表單區域 - 添加雲層背景 -->
    <div class="search-background">
      <div class="page-container">
        <div class="page-header">
          <h1 class="page-title">航班搜尋</h1>
          <p class="page-description">搜尋國內、離島及國際直飛航班</p>
        </div>

        <section class="search-panel">
          <SearchForm
            :is-searching="isSearching"
            @search="handleSearch"
          />
        </section>
      </div>
    </div>

    <!-- 結果區域 -->
    <div class="page-container">
      <div v-if="hasSearched" class="results-container">
        <!-- 搜索路線顯示 -->
        <div class="route-summary" v-if="searchParams.departureAirport && searchParams.arrivalAirport">
          <div class="route-info">
            <div class="airports-display">
              <span class="airport-code">{{ searchParams.departureAirport.code }}</span>
              <div class="route-line">
                <div class="route-arrow"></div>
              </div>
              <span class="airport-code">{{ searchParams.arrivalAirport.code }}</span>
            </div>
            <div class="date-display">{{ formattedDepartureDate }}</div>
          </div>
        </div>

        <div class="search-results-layout">
          <!-- 篩選面板 -->
          <aside class="filters-panel">
            <div class="filters-header">
              <h2 class="filters-title">篩選條件</h2>
            </div>
            <FilterPanel
              :flights="flights"
              :initial-filters="filters"
              @filter-change="handleFilterChange"
            />
          </aside>

          <!-- 航班結果列表 -->
          <div class="flights-panel">
            <FlightResults
              :flights="filteredFlights"
              :searched="hasSearched"
            />
          </div>
        </div>
      </div>

      <!-- 首次載入提示 -->
      <div v-else class="empty-state">
        <div class="empty-state-content">
          <div class="empty-icon">✈</div>
          <h2 class="empty-title">開始您的旅程</h2>
          <p class="empty-message">請輸入出發地、目的地和日期開始搜尋航班</p>
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
import { ref, reactive, computed, watch } from 'vue';

export default {
  name: 'FlightSearch',
  components: {
    SearchForm,
    FilterPanel,
    FlightResults
  },
  setup() {
    // 主要數據
    const flights = ref([]);
    const filteredFlights = ref([]);

    // 搜索相關狀態
    const loading = ref(false);
    const isSearching = ref(false);
    const hasSearched = ref(false);

    // 機場數據
    const taiwanAirports = ref([]);
    const destinationAirports = ref([]);

    // 搜索參數
    const searchParams = reactive({
      departureAirport: null,
      arrivalAirport: null,
      departureDate: new Date().toISOString().split('T')[0],
      returnDate: '',
      classType: 'economy'
    });

    // 篩選相關
    const filters = reactive({
      airlines: [],
      priceRange: {
        min: 0,
        max: 50000
      }
    });

    const formattedDepartureDate = computed(() => {
      if (!searchParams.departureDate) return '';
      const date = new Date(searchParams.departureDate);
      return date.toLocaleDateString('zh-TW', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        weekday: 'long'
      });
    });

    const fetchTaiwanAirports = async () => {
      try {
        const airports = await flightService.getTaiwanAirports();
        if (airports && airports.length > 0) {
          taiwanAirports.value = airports;
        }
      } catch (error) {
        console.error('獲取台灣機場資料時出錯:', error);
      }
    };

    const handleSearch = async (params) => {
      loading.value = true;
      isSearching.value = true;
      hasSearched.value = true;
      Object.assign(searchParams, params);
      
      // 重置篩選條件
      filters.airlines = [];

      try {
        const departureCode = params.departureAirport?.code;
        const arrivalCode = params.arrivalAirport?.code;
        if (!departureCode || !arrivalCode) {
          throw new Error('缺少必要的參數: 出發地或目的地');
        }

        const apiSearchParams = {
          departureAirportCode: departureCode,
          arrivalAirportCode: arrivalCode,
          departureDate: params.departureDate,
          returnDate: params.returnDate || undefined,
          classType: params.classType || 'economy'
        };

        const response = await flightService.searchFlights(apiSearchParams);
        let flightsData = [];

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

        if (!flightsData || flightsData.length === 0) {
          flights.value = [];
          alert(`沒有找到從 ${params.departureAirport.name} 到 ${params.arrivalAirport.name} 的航班，請選擇其他日期或目的地。`);
          return;
        }

        const processedFlights = flightsData.map(flight => {
          if (flight.price && typeof flight.price === 'string') {
            flight.price = parseFloat(flight.price);
          } else if (flight.price == null) {
            flight.price = 0;
          }
          return flight;
        });

        flights.value = processedFlights;

        // 搜索後動態設定價格範圍最大值
        const maxPrice = Math.max(...processedFlights.map(f => f.price), 0);
        filters.priceRange.max = Math.ceil(maxPrice / 1000) * 1000 || 50000;
        filters.priceRange.min = 0;

        // 初次搜索後，filteredFlights 等於 flights
        filteredFlights.value = [...flights.value];

      } catch (error) {
        console.error('搜索航班時出錯:', error);
        alert('搜索航班時發生錯誤。請檢查後端連接和伺服器日誌。');
        flights.value = [];
        filteredFlights.value = [];
      } finally {
        loading.value = false;
        isSearching.value = false;
      }
    };

    const applyFilters = () => {
      filteredFlights.value = flights.value.filter(flight => {
        // 航空公司篩選
        if (filters.airlines.length > 0) {
          const airlineCode = flight.airline_code || (flight.airline ? flight.airline.code : '');
          if (!airlineCode || !filters.airlines.includes(airlineCode)) {
            return false;
          }
        }

        // 價格篩選
        const flightPrice = flight.price || 0;
        if (flightPrice < filters.priceRange.min || flightPrice > filters.priceRange.max) {
          return false;
        }

        return true;
      });
    };

    const handleFilterChange = (newFilters) => {
      Object.assign(filters, newFilters);
      applyFilters();
    };

    // 監聽原始航班數據變化，以更新篩選器（例如價格範圍）
    watch(flights, (newFlights) => {
      if (newFlights && newFlights.length > 0) {
        const maxPrice = Math.max(...newFlights.map(f => f.price || 0), 0);
        filters.priceRange.max = Math.ceil(maxPrice / 1000) * 1000 || 50000;
      } else {
        // 如果沒有航班，重置價格範圍
        filters.priceRange.min = 0;
        filters.priceRange.max = 50000;
      }
      // 重新應用篩選，確保UI同步
      applyFilters();
    });

    fetchTaiwanAirports();

    return {
      flights,
      filteredFlights,
      loading,
      isSearching,
      hasSearched,
      taiwanAirports,
      destinationAirports,
      searchParams,
      filters,
      formattedDepartureDate,
      handleSearch,
      handleFilterChange
    };
  }
};
</script>

<style scoped>
.flight-search-page {
  min-height: 100%;
  position: relative;
}

.search-background {
  background-image: url('@/assets/images/sky-views/vista-wei-xYNC73QAqc8-unsplash.jpg');
  background-size: cover;
  background-position: center;
  position: relative;
  padding: var(--spacing-xl) 0;
}

.search-background::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.75);
  z-index: 1;
}

.search-background .page-container {
  position: relative;
  z-index: 2;
}

.page-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 var(--spacing-md);
}

.page-header {
  margin-bottom: var(--spacing-lg);
  text-align: left;
}

.page-title {
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: var(--spacing-xs);
  color: var(--color-text-primary);
}

.page-description {
  color: var(--color-text-secondary);
  font-size: 1.1rem;
  max-width: 600px;
}

/* 載入指示器 */
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
  width: 50px;
  height: 50px;
  border: 4px solid rgba(0, 95, 115, 0.1);
  border-left-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 搜索面板 */
.search-panel {
  margin-bottom: var(--spacing-lg);
}

/* 結果容器 */
.results-container {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
  margin-top: var(--spacing-xl);
}

/* 路線摘要 */
.route-summary {
  background-color: var(--color-white);
  padding: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.route-info {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.airports-display {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.airport-code {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-text-primary);
}

.route-line {
  flex-grow: 1;
  height: 2px;
  background-color: var(--color-border);
  position: relative;
  margin: 0 var(--spacing-sm);
}

.route-arrow {
  position: absolute;
  top: 50%;
  right: 0;
  transform: translateY(-50%);
  width: 0;
  height: 0;
  border-top: 5px solid transparent;
  border-bottom: 5px solid transparent;
  border-left: 5px solid var(--color-border);
}

.date-display {
  color: var(--color-text-secondary);
  font-size: 0.9rem;
}

/* 搜索結果佈局 */
.search-results-layout {
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: var(--spacing-lg);
}

/* 篩選面板 */
.filters-panel {
  background-color: var(--color-white);
  padding: var(--spacing-lg);
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.filters-header {
  margin-bottom: var(--spacing-md);
  border-bottom: 1px solid var(--color-border);
  padding-bottom: var(--spacing-sm);
}

.filters-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--color-text-primary);
}

/* 航班面板 */
.flights-panel {
  background-color: var(--color-white);
  min-height: 400px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  padding: var(--spacing-lg);
}

/* 空狀態 */
.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
  background-color: var(--color-white);
  padding: var(--spacing-xl);
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  margin-top: var(--spacing-xl);
}

.empty-state-content {
  text-align: center;
  max-width: 500px;
}

.empty-icon {
  font-size: 3rem;
  color: var(--color-primary);
  margin-bottom: var(--spacing-md);
}

.empty-title {
  font-size: 1.5rem;
  margin-bottom: var(--spacing-sm);
  color: var(--color-text-primary);
}

.empty-message {
  color: var(--color-text-secondary);
  line-height: 1.5;
}

/* 媒體查詢 */
@media (max-width: 992px) {
  .search-results-layout {
    grid-template-columns: 1fr;
  }
  
  .filters-panel {
    margin-bottom: var(--spacing-lg);
  }
}

@media (max-width: 576px) {
  .page-title {
    font-size: 1.75rem;
  }
  
  .page-description {
    font-size: 1rem;
  }
  
  .airport-code {
    font-size: 1.25rem;
  }
}
</style> 