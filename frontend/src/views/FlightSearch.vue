<template>
  <div class="flight-search-page">
    <!-- 載入指示器 -->
    <div v-if="loading" class="loading-overlay">
      <div class="flight-search-loader">
        <div class="loader-track">
          <div class="loader-progress">
            <div class="loader-dot"></div>
          </div>
        </div>
        <p class="loader-text">搜尋航班中...</p>
      </div>
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
      <div v-if="hasSearched" class="results-container" ref="resultsContainer">
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
      <div v-else class="empty-state-container">
        <EmptySearchState />
      </div>

      <!-- <MinimalParent /> -->

    </div>
  </div>
</template>

<script>
import SearchForm from '@/components/search/SearchForm.vue';
import FilterPanel from '@/components/search/FilterPanel.vue';
import FlightResults from '@/components/search/FlightResults.vue';
import EmptySearchState from '@/components/search/EmptySearchState.vue';
import flightService from '@/api/services/flightService';
import { ref, reactive, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue';
import { useSearchStore } from '@/store/modules/search'; // 引入 search store
import { useRoute, useRouter } from 'vue-router'; // 確保 useRouter 被引入

export default {
  name: 'FlightSearch',
  components: {
    SearchForm,
    FilterPanel,
    FlightResults,
    EmptySearchState
  },
  setup() {
    // 使用 search store
    const searchStore = useSearchStore();
    const route = useRoute();
    const router = useRouter(); // 獲取 router 實例
    
    // 添加結果容器參考，用於自動滾動功能
    const resultsContainer = ref(null);
    
    // 使用 reactive refs 來包裝 store 中的狀態，以便在模板中直接使用
    const loading = ref(false);
    
    // 計算屬性：從 store 獲取格式化的出發日期
    const formattedDepartureDate = computed(() => searchStore.formattedDepartureDate);
    
    // 映射 store 中的搜索參數到本地 reactive 對象
    const searchParams = computed(() => searchStore.searchParams);
    
    // 獲取篩選後的航班數據
    const filteredFlights = computed(() => searchStore.filteredFlights);
    
    // 是否已經搜索過
    const hasSearched = computed(() => searchStore.hasSearched);
    
    // 是否正在搜索
    const isSearching = computed(() => searchStore.isSearching);
    
    // 獲取原始航班數據
    const flights = computed(() => searchStore.flights);
    
    // 獲取篩選條件
    const filters = computed(() => searchStore.filters);

    // 自動滾動到結果區域
    const scrollToResults = () => {
      if (resultsContainer.value) {
        console.log('[FlightSearch] 準備滾動到結果區域');
        // 使用 nextTick 確保 DOM 已更新
        nextTick(() => {
          // 使用平滑滾動
          resultsContainer.value.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
          });
          console.log('[FlightSearch] 已滾動到結果區域');
        });
      } else {
        console.warn('[FlightSearch] 無法找到結果容器，滾動失敗');
      }
    };

    // 滾動到特定航班卡片
    const scrollToFlightCard = (flightId) => {
      console.log(`[FlightSearch] 嘗試滾動到航班卡片 ID: ${flightId}`);
      nextTick(() => {
        const flightCard = document.getElementById(`flight-card-${flightId}`);
        if (flightCard) {
          console.log(`[FlightSearch] 找到航班卡片，準備滾動`);
          flightCard.scrollIntoView({
            behavior: 'smooth',
            block: 'center'
          });
          
          // 高亮效果時間延長
          flightCard.classList.add('highlight-card');
          
          // 延長高亮時間為3秒鐘
          setTimeout(() => {
            flightCard.classList.remove('highlight-card');
          }, 3000);
          
          console.log(`[FlightSearch] 已滾動到航班卡片`);
        } else {
          console.warn(`[FlightSearch] 未找到航班卡片 ID: ${flightId}，改為滾動到結果區域`);
          scrollToResults();
        }
      });
    };

    // 從詳情頁返回時檢查URL參數
    onMounted(() => {
      const fromDetail = route.query.fromDetail === 'true';
      const shouldScrollToResults = route.query.scrollToResults === 'true';
      const lastViewedFlight = route.query.lastViewedFlight;
      
      console.log('[FlightSearch] onMounted - fromDetail:', fromDetail, 
                  'scrollToResults:', shouldScrollToResults,
                  'lastViewedFlight:', lastViewedFlight);

      if (fromDetail && shouldScrollToResults && searchStore.hasSearched) {
        setTimeout(() => {
          if (lastViewedFlight) {
            scrollToFlightCard(lastViewedFlight);
          } else {
            scrollToResults();
          }
        }, 300);
      } 
      else if (!fromDetail && searchStore.hasSearched && route.name === 'FlightSearch') { // 只有當前就是 FlightSearch 且非 fromDetail 才重置
        console.log('[FlightSearch] 不是從詳情頁返回，重置搜索狀態');
        searchStore.resetAll();
        window.scrollTo(0, 0); // 新增：滾動到頂部
        
        if (Object.keys(route.query).length > 0) {
          router.replace({ query: {} });
        }
      } else if (!fromDetail) { // 如果不是從詳情頁，且未觸發其他條件（例如首次加載或從其他非詳情頁跳轉）
        window.scrollTo(0, 0); // 新增：滾動到頂部
      }
    });

    const fetchTaiwanAirports = async () => {
      try {
        const airports = await flightService.getTaiwanAirports();
        if (airports && airports.length > 0) {
          // 這裡我們不需要存儲機場數據，因為 SearchForm 組件會自己處理
        }
      } catch (error) {
        console.error('獲取台灣機場資料時出錯:', error);
      }
    };

    const handleSearch = async (params) => {
      // 添加日誌：確認函數被調用
      console.log('[FlightSearch] handleSearch called with params:', params);
      
      // 記錄動畫開始時間
      const animationStartTime = Date.now();
      // 設置最小動畫顯示時間（毫秒）
      const minAnimationDuration = 1500;
      
      loading.value = true;
      searchStore.setSearchState(true, true);
      
      try {
        // 嘗試獲取機場完整信息
        let departureAirport = null;
        let arrivalAirport = null;
        
        // 獲取出發機場詳細資訊
        if (params.departure) {
          try {
            // 首先嘗試在已加載的機場中查找
            const depCode = params.departure;
            const localDepartureAirport = searchStore.searchParams.departureAirport;
            
            if (localDepartureAirport && localDepartureAirport.code === depCode) {
              // 如果 store 中有完整的機場對象且代碼匹配，直接使用
              departureAirport = { ...localDepartureAirport };
              console.log('[FlightSearch] 使用本地存儲的出發機場:', departureAirport);
            } else {
              // 否則使用簡單對象
              departureAirport = { code: depCode };
            }
          } catch (error) {
            console.error('[FlightSearch] 獲取出發機場詳情時出錯:', error);
            departureAirport = { code: params.departure };
          }
        }
        
        // 獲取目的地機場詳細資訊
        if (params.arrival) {
          try {
            // 首先嘗試在已加載的機場中查找
            const arrCode = params.arrival;
            const localArrivalAirport = searchStore.searchParams.arrivalAirport;
            
            if (localArrivalAirport && localArrivalAirport.code === arrCode) {
              // 如果 store 中有完整的機場對象且代碼匹配，直接使用
              arrivalAirport = { ...localArrivalAirport };
              console.log('[FlightSearch] 使用本地存儲的目的地機場:', arrivalAirport);
            } else {
              // 否則使用簡單對象
              arrivalAirport = { code: arrCode };
            }
          } catch (error) {
            console.error('[FlightSearch] 獲取目的地機場詳情時出錯:', error);
            arrivalAirport = { code: params.arrival };
          }
        }
        
        // 更新本地狀態以顯示路線摘要
        searchStore.setSearchParams({
          departureAirport: departureAirport,
          arrivalAirport: arrivalAirport,
          departureDate: params.date,
          returnDate: params.return_date,
          classType: params.class_type
        });

        // 直接使用傳入的 params 中的代碼
        const departureCode = params.departure;
        const arrivalCode = params.arrival;
        if (!departureCode || !arrivalCode) {
          console.error('搜索參數錯誤:', params);
          throw new Error('缺少必要的參數: 出發地或目的地代碼');
        }

        // 構建符合後端 API 要求的參數對象
        const apiSearchParams = {
          departure: departureCode,
          arrival: arrivalCode,
          date: params.date,
          return_date: params.return_date || null,
          class_type: params.class_type || 'economy'
        };

        console.log('發送搜索請求參數:', apiSearchParams);

        // API 呼叫
        let response;
        try {
          response = await flightService.searchFlights(apiSearchParams);
          console.log('<<< DEBUGGING: Raw response from service >>>', response);
          console.log('Raw API response received. Type:', typeof response, 'Content snippet:', String(response).substring(0, 500));
        } catch (apiError) {
          console.error('[FlightSearch] API call to searchFlights failed:', apiError);
          throw apiError; 
        }

        // 數據提取
        console.log('[FlightSearch] Starting data extraction from response.');
        let flightsData = [];
        try {
            console.log('[FlightSearch] Before check: Type of response is:', typeof response);
            console.log('[FlightSearch] Before check: Is response truly an array?', Array.isArray(response));
            console.log('[FlightSearch] Before check: Response content snippet:', JSON.stringify(response)?.substring(0, 200));

            if (Array.isArray(response)) { 
                flightsData = response;
                console.log('[FlightSearch] Check PASSED: response is an array. Assigning flightsData.');
            } else {
                console.warn('[FlightSearch] Check FAILED: response is NOT an array. Received:', response);
                flightsData = [];
            }
        } catch (extractionError) {
            console.error('[FlightSearch] Error during data extraction logic:', extractionError);
            flightsData = [];
        }

        console.log('[FlightSearch] Extracted flightsData:', JSON.stringify(flightsData));

        if (!flightsData || flightsData.length === 0) { 
          searchStore.setFlights([]);
          console.log('handleSearch: No flights data extracted, returning.');
          return;
        }

        const processedFlights = flightsData.map((flight, index) => {
          console.log(`[FlightSearch] Processing original flight ${index}:`, JSON.stringify(flight));

          const priceAmount = typeof flight.price?.amount === 'number' ? flight.price.amount : null;

          // 構建 FlightCard 需要的嵌套結構
          const newFlight = {
            flight_id: flight.flight_id,
            flight_number: flight.flight_number,
            duration_minutes: flight.duration_minutes,
            aircraft: flight.aircraft,
            airline: flight.airline || {
              code: 'N/A',
              name_zh: '未知航空',
              logo_path: null
            },
            departure: {
              code: flight.departure?.code || 'N/A',
              airport_id: flight.departure?.code || null,
              time: flight.departure?.time || null,
              terminal: flight.departure?.terminal || null
            },
            arrival: {
              code: flight.arrival?.code || 'N/A',
              airport_id: flight.arrival?.code || null,
              time: flight.arrival?.time || null,
              terminal: flight.arrival?.terminal || null
            },
            price: {
              amount: priceAmount,
              available_seats: flight.price?.available_seats ?? flight.available_seats ?? null,
              cabin_class: flight.price?.cabin_class || '洽詢',
              currency: flight.price?.currency || 'TWD',
              isAvailable: flight.price?.isAvailable
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
        
        // 更新 store 中的航班數據
        searchStore.setFlights(validFlights);

        if (validFlights && validFlights.length > 0) {
          validFlights.forEach(flight => {
            console.log('航班:', flight.flight_number, 
                        '價格數據:', flight.price,
                        '價格可用性:', flight.price?.isAvailable,
                        '艙等:', flight.price?.cabin_class);
          });
          
          // 移除這裡的立即滾動
          // scrollToResults();
        }

      } catch (error) {
        console.error('[FlightSearch] Error in handleSearch:', error);
        alert('搜索航班時發生錯誤。請檢查後端連接和伺服器日誌。');
        searchStore.setFlights([]);
      } finally {
        // 計算已經過的時間
        const elapsedTime = Date.now() - animationStartTime;
        
        // 如果搜索速度太快，確保動畫至少顯示最小時間
        if (elapsedTime < minAnimationDuration) {
          const remainingTime = minAnimationDuration - elapsedTime;
          console.log(`[FlightSearch] 搜索在 ${elapsedTime}ms 完成，動畫將再顯示 ${remainingTime}ms`);
          
          // 使用延時來確保最小顯示時間
          setTimeout(() => {
            loading.value = false;
            searchStore.setSearchState(false);
            
            // 在動畫結束後滾動到結果區域
            if (searchStore.flights && searchStore.flights.length > 0) {
              console.log('[FlightSearch] 動畫結束後準備滾動到結果區域');
              nextTick(() => scrollToResults());
            }
          }, remainingTime);
        } else {
          // 搜索時間已超過最小動畫顯示時間，直接關閉
          loading.value = false;
          searchStore.setSearchState(false);
          
          // 在動畫結束後滾動到結果區域
          if (searchStore.flights && searchStore.flights.length > 0) {
            console.log('[FlightSearch] 動畫結束後準備滾動到結果區域');
            nextTick(() => scrollToResults());
          }
        }
      }
    };

    const handleFilterChange = (newFilters) => {
      // 使用 store 的 applyFilters 方法應用篩選
      searchStore.applyFilters(newFilters);
    };

    // 監聽路由變化以決定是否清除機場選擇
    watch(
      () => route.name, // 監聽路由名稱的變化
      (toName, fromName) => {
        console.log(`[FlightSearch] Route changed from ${fromName} to ${toName}`);
        // 條件：導航到 FlightSearch 頁面，且來源不是 FlightDetail
        if (toName === 'FlightSearch' && fromName && fromName !== 'FlightDetail') {
          console.log('[FlightSearch] Clearing airport selections due to navigation from non-detail page.');
          searchStore.clearAirportSelections();
        }
      }
    );

    fetchTaiwanAirports();

    return {
      flights,
      filteredFlights,
      loading,
      isSearching,
      hasSearched,
      searchParams,
      filters,
      formattedDepartureDate,
      handleSearch,
      handleFilterChange,
      resultsContainer
    };
  }
};
</script>

<style scoped>
.flight-search-page {
  min-height: 90vh;
  background-color: var(--color-background);
  scroll-behavior: smooth; /* 添加平滑滾動支持 */
}

/* 添加高亮效果 */
:deep(.highlight-card) {
  animation: highlight-pulse 2s ease-in-out;
  position: relative;
  z-index: 5; /* 提高 z-index 使卡片顯示在前面 */
  border-radius: 0.5rem;
  overflow: hidden;
}

:deep(.highlight-card::before) {
  content: '';
  position: absolute;
  inset: 0;
  border: 2px solid rgba(0, 95, 115, 0.4);
  border-radius: 0.5rem;
  animation: border-glow 2s ease-in-out;
  pointer-events: none;
}

@keyframes highlight-pulse {
  0% { 
    box-shadow: 0 0 0 0 rgba(0, 95, 115, 0);
    transform: translateY(0);
  }
  20% {
    box-shadow: 0 0 15px 2px rgba(0, 95, 115, 0.2);
    transform: translateY(-2px);
  }
  50% { 
    box-shadow: 0 0 20px 5px rgba(0, 95, 115, 0.3); 
    transform: translateY(-4px);
  }
  80% {
    box-shadow: 0 0 15px 2px rgba(0, 95, 115, 0.2);
    transform: translateY(-2px);
  }
  100% { 
    box-shadow: 0 0 0 0 rgba(0, 95, 115, 0);
    transform: translateY(0);
  }
}

@keyframes border-glow {
  0% { 
    opacity: 0;
    border-color: rgba(0, 95, 115, 0);
  }
  25% { 
    opacity: 1;
    border-color: rgba(0, 95, 115, 0.6);
  }
  75% { 
    opacity: 1;
    border-color: rgba(0, 95, 115, 0.6);
  }
  100% { 
    opacity: 0;
    border-color: rgba(0, 95, 115, 0);
  }
}

/* 搜索背景 */
.search-background {
  background-image: url('@/assets/images/sky-views/vista-wei-xYNC73QAqc8-unsplash.jpg'); /* 恢復背景圖片 */
  background-size: cover;
  background-position: center;
  /* background-color: var(--color-secondary); */ /* 移除橘色背景 */
  position: relative;
  color: #333; /* 將文字顏色改回深色以適應淺色背景 */
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
  background-color: rgba(255, 255, 255, 0.7); /* 恢復淺色半透明遮罩 */
  /* background-color: rgba(0, 0, 0, 0.1); */ /* 移除深色遮罩 */
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

/* 空狀態容器樣式 */
.empty-state-container {
  margin-top: 40px; /* 增加與搜尋區塊的間距 */
  margin-bottom: 60px; /* 控制與頁腳的間距 */
  padding: 0;
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
  color: var(--color-primary); /* 修改顏色 */
}

.page-description {
  font-size: 1.1rem;
  font-weight: 300;
  opacity: 0.9;
  /* color: var(--color-text-secondary); */ /* Changed to a lighter shade of white for orange background */
  color: rgba(255, 255, 255, 0.85);
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
  scroll-margin-top: 20px; /* 滾動時的上邊距，確保頂部不會被遮擋 */
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

.flight-search-loader {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2rem;
  padding: 3rem 0;
}

.loader-track {
  position: relative;
  width: 10rem;
  height: 0.25rem;
  background-color: #f3f4f6;
  border-radius: 9999px;
  overflow: hidden;
}

.loader-progress {
  position: absolute;
  height: 100%;
  width: 0%;
  background-color: #005F73;
  border-radius: 9999px;
  animation: flightPath 2s infinite;
}

.loader-dot {
  position: absolute;
  right: -0.5rem;
  top: -0.375rem;
  width: 1rem;
  height: 1rem;
  background-color: #005F73;
  border-radius: 9999px;
}

.loader-text {
  color: #6C757D;
  font-weight: 500;
  font-size: 1rem;
}

@keyframes flightPath {
  0% { width: 0; opacity: 0; }
  20% { opacity: 1; }
  80% { opacity: 1; }
  100% { width: 100%; opacity: 0; }
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