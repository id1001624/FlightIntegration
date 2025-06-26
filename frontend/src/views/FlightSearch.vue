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
      console.log('[FlightSearch] handleSearch 觸發，派遣 searchStore.searchFlights action，參數:', params);

      // 設置最小載入動畫時間，提升用戶體驗
      const minLoadingTime = 1500;
      const startTime = Date.now();
  
      loading.value = true; // 控制本地動畫的顯示

      // 派遣 store action 來執行搜索，不再在組件中直接調用 service
      await searchStore.searchFlights(params);

      // 搜索完成後（無論成功或失敗），平滑滾動到結果區域
      await nextTick();
      if (searchStore.hasResults) {
        scrollToResults();
      }
    
      // 計算已過時間，確保載入動畫至少顯示一段時間
      const elapsedTime = Date.now() - startTime;
      const remainingTime = minLoadingTime - elapsedTime;
    
      if (remainingTime > 0) {
        setTimeout(() => {
          loading.value = false;
        }, remainingTime);
      } else {
        loading.value = false;
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