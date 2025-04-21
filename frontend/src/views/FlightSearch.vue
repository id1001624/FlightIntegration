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
              :flights="flights"
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

      <!-- <MinimalParent /> -->

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

    // 輔助函數：獲取本地時區的 YYYY-MM-DD 日期
    const getLocalDateString = () => {
      const date = new Date();
      const year = date.getFullYear();
      const month = (date.getMonth() + 1).toString().padStart(2, '0');
      const day = date.getDate().toString().padStart(2, '0');
      return `${year}-${month}-${day}`;
    };

    // 搜索參數
    const searchParams = reactive({
      departureAirport: null,
      arrivalAirport: null,
      departureDate: getLocalDateString(), // 使用本地日期
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
      // 添加日誌：確認函數被調用
      console.log('[FlightSearch] handleSearch called with params:', params);
      
      loading.value = true;
      isSearching.value = true;
      hasSearched.value = true;
      // 更新本地狀態以顯示路線摘要 (可選，但保留原始結構)
      // 注意：params 已經包含 code，不再是 airport object
      searchParams.departureAirport = { code: params.departure };
      searchParams.arrivalAirport = { code: params.arrival };
      searchParams.departureDate = params.date;
      searchParams.returnDate = params.return_date;
      searchParams.classType = params.class_type;

      // 重置篩選條件
      filters.airlines = [];

      try {
        // 直接使用傳入的 params 中的代碼
        const departureCode = params.departure;
        const arrivalCode = params.arrival;
        if (!departureCode || !arrivalCode) {
          // 可以添加更詳細的錯誤處理或日誌記錄
          console.error('搜索參數錯誤:', params);
          throw new Error('缺少必要的參數: 出發地或目的地代碼');
        }

        // 構建符合後端 API 要求的參數對象
        const apiSearchParams = {
          departure: departureCode,
          arrival: arrivalCode,
          date: params.date, // 使用正確的鍵名 'date'
          return_date: params.return_date || null, // 使用正確的鍵名 'return_date'
          class_type: params.class_type || 'economy' // 使用正確的鍵名 'class_type'
        };

        console.log('發送搜索請求參數:', apiSearchParams);

        // --- API 呼叫 ---
        let response;
        try {
          response = await flightService.searchFlights(apiSearchParams);
          // **直接打印 response 看看它到底是什麼**
          console.log('<<< DEBUGGING: Raw response from service >>>', response);
          // **修改：移動到這裡立即打印**
          console.log('Raw API response received. Type:', typeof response, 'Content snippet:', String(response).substring(0, 500)); // 增加片段長度
        } catch (apiError) {
          console.error('[FlightSearch] API call to searchFlights failed:', apiError);
          // 將錯誤重新拋出，讓外層的 catch 處理 UI 更新
          throw apiError; 
        }
        // --- End API 呼叫 ---

        // --- 數據提取 ---
        console.log('[FlightSearch] Starting data extraction from response.');
        let flightsData = [];
        try {
            // *** 添加額外日誌 ***
            console.log('[FlightSearch] Before check: Type of response is:', typeof response);
            console.log('[FlightSearch] Before check: Is response truly an array?', Array.isArray(response));
            console.log('[FlightSearch] Before check: Response content snippet:', JSON.stringify(response)?.substring(0, 200)); // 打印片段

            // *** 最終修正：直接檢查 response 是否為陣列 ***
            if (Array.isArray(response)) { 
                flightsData = response; // 直接賦值
                console.log('[FlightSearch] Check PASSED: response is an array. Assigning flightsData.');
            } else {
                // 如果收到的不是預期的陣列，記錄警告
                console.warn('[FlightSearch] Check FAILED: response is NOT an array. Received:', response);
                flightsData = []; // 確保清空
            }
        } catch (extractionError) {
            console.error('[FlightSearch] Error during data extraction logic:', extractionError);
            flightsData = []; // 確保出錯時清空
        }
        // --- End 數據提取 ---

        // 添加日誌：打印提取出的 flightsData
        console.log('[FlightSearch] Extracted flightsData:', JSON.stringify(flightsData));

        if (!flightsData || flightsData.length === 0) { 
          flights.value = []; // 確保清空
          filteredFlights.value = []; // 確保清空
          console.log('handleSearch: No flights data extracted, returning.');
          return;
        }

        const processedFlights = flightsData.map((flight, index) => {
          // 添加日誌：打印每個原始 flight 對象
          console.log(`[FlightSearch] Processing original flight ${index}:`, JSON.stringify(flight));
          // 移除錯誤的日誌
          // console.log(`[FlightSearch] Original scheduled_departure for flight ${index}:`, flight.scheduled_departure);
          // console.log(`[FlightSearch] Original scheduled_arrival for flight ${index}:`, flight.scheduled_arrival);

          const priceAmount = typeof flight.price?.amount === 'number' ? flight.price.amount : null;

          // 構建 FlightCard 需要的嵌套結構
          const newFlight = {
            flight_id: flight.flight_id,
            flight_number: flight.flight_number,
            duration_minutes: flight.duration_minutes,
            aircraft: flight.aircraft, // 從頂層讀取 aircraft
            airline: flight.airline || { // airline 已經是嵌套好的
              code: 'N/A',
              name_zh: '未知航空',
              logo_path: null
            },
            departure: {
              code: flight.departure?.code || 'N/A',       // *** 修正：從 flight.departure 讀取 code ***
              airport_id: flight.departure?.code || null, // *** 修正：從 flight.departure 讀取 code ***
              time: flight.departure?.time || null,        // *** 修正：從 flight.departure 讀取 time ***
              terminal: flight.departure?.terminal || null // *** 修正：從 flight.departure 讀取 terminal ***
            },
            arrival: {
              code: flight.arrival?.code || 'N/A',         // *** 修正：從 flight.arrival 讀取 code ***
              airport_id: flight.arrival?.code || null,   // *** 修正：從 flight.arrival 讀取 code ***
              time: flight.arrival?.time || null,          // *** 修正：從 flight.arrival 讀取 time ***
              terminal: flight.arrival?.terminal || null   // *** 修正：從 flight.arrival 讀取 terminal ***
            },
            price: { // price 已經是嵌套好的
              amount: priceAmount,
              available_seats: flight.price?.available_seats ?? flight.available_seats ?? null, // 優先從嵌套price讀，再從頂層讀
              cabin_class: flight.price?.cabin_class || '洽詢',
              currency: flight.price?.currency || 'TWD'
            }
          };

          console.log(`Mapped flight ${index}:`, JSON.parse(JSON.stringify(newFlight)));
          return newFlight;
        });

        // 過濾掉 flight_id 無效的航班
        const validFlights = processedFlights.filter(f => f.flight_id && String(f.flight_id).trim() !== '');

        if (validFlights.length !== processedFlights.length) {
          console.warn('Some flights were filtered out due to missing or invalid flight_id.');
        }

        console.log('Valid flights:', JSON.parse(JSON.stringify(validFlights)));
        flights.value = validFlights; // 使用過濾後的列表

        // 搜索後動態設定價格範圍最大值
        const maxPrice = Math.max(...validFlights.map(f => f.price.amount || 0), 0);
        filters.priceRange.max = Math.ceil(maxPrice / 1000) * 1000 || 50000;
        filters.priceRange.min = 0;

        // 初次搜索後，filteredFlights 等於 flights
        // filteredFlights.value = [...flights.value]; 

      } catch (error) {
        // 添加錯誤日誌
        console.error('[FlightSearch] Error in handleSearch:', error);
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
          const airlineCode = flight.airline.code || '';
          if (!airlineCode || !filters.airlines.includes(airlineCode)) {
            return false;
          }
        }

        // 價格篩選
        const flightPrice = flight.price?.amount; // 使用可選鏈接
        // 如果價格是 null 或 undefined，根據篩選器的最小值決定是否包含
        if (flightPrice === null || typeof flightPrice === 'undefined') {
          // 如果篩選器的最小值大於 0，則排除無價格航班
          if (filters.priceRange.min > 0) {
            return false;
          }
          // 否則 (最小值為 0)，包含無價格航班 (顯示為洽詢)
        } else if (flightPrice < filters.priceRange.min || flightPrice > filters.priceRange.max) {
          // 如果有價格但不符合範圍，則排除
          return false;
        }

        return true;
      });
    };

    const handleFilterChange = (newFilters) => {
      // 更新篩選條件
      if (newFilters.airlines) {
        filters.airlines = [...newFilters.airlines];
      }
      if (newFilters.priceRange) {
        filters.priceRange.min = newFilters.priceRange.min;
        filters.priceRange.max = newFilters.priceRange.max;
      }
      // applyFilters(); 
    };

    // 監聽原始航班數據變化，以更新篩選器（例如價格範圍）
    watch(flights, (newFlights) => {
      if (newFlights && newFlights.length > 0) {
        const maxPrice = Math.max(...newFlights.map(f => f.price.amount || 0), 0);
        filters.priceRange.max = Math.ceil(maxPrice / 1000) * 1000 || 50000;
        filters.priceRange.min = 0;
      } else {
        // 如果沒有航班，重置價格範圍
        filters.priceRange.min = 0;
        filters.priceRange.max = 50000;
      }
    }, { deep: true });

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
  min-height: 90vh;
  background-color: var(--color-background);
}

/* 搜索背景 */
.search-background {
  background-image: url('@/assets/images/sky-views/vista-wei-xYNC73QAqc8-unsplash.jpg');
  background-size: cover;
  background-position: center;
  position: relative;
  color: var(--color-primary);
  padding: 40px 0;
  overflow: hidden;
}

.search-background::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.7);
  z-index: 0;
}

.search-background .page-container {
  position: relative;
  z-index: 1;
}

/* 頁面容器 */
.page-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

/* 頁面標題區 */
.page-header {
  text-align: center;
  margin-bottom: 30px;
}

.page-title {
  font-size: 2rem;
  margin-bottom: 8px;
  font-weight: 700;
  color: var(--color-primary);
}

.page-description {
  font-size: 1.1rem;
  font-weight: 300;
  opacity: 0.9;
  color: var(--color-text-secondary);
}

/* 搜索面板 */
.search-panel {
  max-width: 1000px;
  margin: 0 auto;
}

/* 結果容器 */
.results-container {
  margin-top: 20px;
  min-height: 50vh;
}

/* 路線摘要 */
.route-summary {
  background-color: white;
  padding: 16px;
  margin-bottom: 20px;
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
}

.route-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.airports-display {
  display: flex;
  align-items: center;
}

.airport-code {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-primary);
}

.route-line {
  position: relative;
  width: 100px;
  height: 2px;
  background-color: var(--color-border);
  margin: 0 16px;
}

.route-arrow {
  position: absolute;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 0;
  height: 0;
  border-top: 5px solid transparent;
  border-bottom: 5px solid transparent;
  border-left: 8px solid var(--color-border);
}

.date-display {
  font-size: 1rem;
  color: var(--color-text-secondary);
}

/* 搜索結果佈局 */
.search-results-layout {
  display: grid;
  grid-template-columns: 250px 1fr;
  gap: 20px;
}

/* 篩選面板 */
.filters-panel {
  background-color: white;
  padding: 16px;
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
}

.filters-header {
  margin-bottom: 16px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--color-border);
}

.filters-title {
  font-size: 1.2rem;
  font-weight: 600;
  color: var(--color-primary);
}

/* 航班結果面板 */
.flights-panel {
  min-height: 400px;
}

/* 空狀態 */
.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 50vh;
}

.empty-state-content {
  text-align: center;
  padding: 30px;
  background-color: white;
  width: 100%;
  max-width: 500px;
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 16px;
  color: var(--color-secondary);
}

.empty-title {
  font-size: 1.5rem;
  margin-bottom: 8px;
  color: var(--color-text-primary);
}

.empty-message {
  color: var(--color-text-secondary);
}

/* 載入指示器 */
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(255, 255, 255, 0.8);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.loading-spinner {
  width: 50px;
  height: 50px;
  border: 5px solid var(--color-border);
  border-top-color: #005F73;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* 響應式 */
@media (max-width: 768px) {
  .search-results-layout {
    grid-template-columns: 1fr;
  }

  .route-summary {
    flex-direction: column;
    gap: 10px;
  }

  .route-info {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
}
</style> 