<template>
  <div class="flight-search-page">
    <!-- 搜尋區域 -->
    <section class="search-section">
      <div class="search-container">
        <SearchForm
          @search="handleSearch"
          :isSearching="isSearching"
        />
      </div>
    </section>

    <!-- 搜尋結果區域 -->
    <section class="results-section" v-if="showResults" ref="resultsSection">
      <div class="results-container">
        <!-- 搜尋摘要 -->
        <div class="search-summary" v-if="searchResults.length > 0">
          <div class="summary-content">
            <h2 class="summary-title">
              <span class="result-count">{{ searchResults.length }}</span>
              個航班符合您的需求
            </h2>
            <p class="summary-details">
              {{ formatSearchSummary() }}
            </p>
          </div>

          <!-- 排序與篩選 -->
          <div class="search-controls">
            <select v-model="sortBy" @change="sortResults" class="sort-select">
              <option value="price">價格排序</option>
              <option value="time">時間排序</option>
              <option value="duration">飛行時間</option>
              <option value="airline">航空公司</option>
            </select>
            
            <button @click="toggleFilters" class="filter-toggle">
              <span class="filter-icon">⚙️</span>
              篩選條件
            </button>
          </div>
        </div>

        <!-- 航班列表 -->
        <div class="flight-list" v-if="searchResults.length > 0">
          <FlightCard
            v-for="flight in sortedResults"
            :key="flight.id || `${flight.flight_number}-${flight.scheduled_departure}`"
            :flight="flight"
            @select-flight="handleFlightSelection"
            @view-details="handleViewDetails"
          />
        </div>

        <!-- 空結果狀態 -->
        <div v-if="showResults && searchResults.length === 0 && !isSearching" class="empty-results">
          <div class="empty-content">
            <div class="empty-icon">✈️</div>
            <h3 class="empty-title">找不到符合條件的航班</h3>
            <p class="empty-description">
              請嘗試調整搜尋條件，或選擇其他日期進行搜尋
            </p>
            <button @click="resetSearch" class="reset-search-btn">
              重新搜尋
            </button>
          </div>
        </div>
      </div>
    </section>

    <!-- 預設畫面 -->
    <section class="default-state-section" v-if="!showResults && !isSearching">
      <EmptySearchState />
    </section>

    <!-- 專業級搜尋加載動畫 -->
    <FlightSearchLoader
      v-if="isSearching"
      :departureCode="currentSearch?.departure"
      :arrivalCode="currentSearch?.arrival"
      @cancel="cancelSearch"
    />

    <!-- 航班詳情彈窗 -->
    <FlightDetailCard
      v-if="selectedFlight"
      :flight="selectedFlight"
      @close="closeFlightDetails"
      @select-flight="handleFlightSelection"
    />
  </div>
</template>

<script>
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue';
import { useSearchStore } from '@/store/modules/search';
import SearchForm from '@/components/search/SearchForm.vue';
import FlightCard from '@/components/FlightCard.vue';
import FlightDetailCard from '@/components/specific/FlightDetailCard.vue';
import FlightSearchLoader from '@/components/ui/FlightSearchLoader.vue';
import EmptySearchState from '@/components/search/EmptySearchState.vue';
import { searchFlights } from '@/api/services/flightService';

export default {
  name: 'FlightSearch',
  components: {
    SearchForm,
    FlightCard,
    FlightDetailCard,
    FlightSearchLoader,
    EmptySearchState
  },
  setup() {
    const searchStore = useSearchStore();
    
    // 響應式數據
    const isSearching = ref(false);
    const showResults = ref(false);
    const searchResults = ref([]);
    const selectedFlight = ref(null);
    const currentSearch = ref(null);
    const sortBy = ref('price');
    const showFilters = ref(false);
    const resultsSection = ref(null);
    
    let searchTimeout = null;
    
    // 計算屬性
    const sortedResults = computed(() => {
      const results = [...searchResults.value];
      
      switch (sortBy.value) {
        case 'price':
          return results.sort((a, b) => {
            const priceA = a.economy_price || a.business_price || a.first_price || 0;
            const priceB = b.economy_price || b.business_price || b.first_price || 0;
            return priceA - priceB;
          });
        case 'time':
          return results.sort((a, b) => 
            new Date(a.scheduled_departure) - new Date(b.scheduled_departure)
          );
        case 'duration':
          return results.sort((a, b) => {
            const durationA = new Date(a.scheduled_arrival) - new Date(a.scheduled_departure);
            const durationB = new Date(b.scheduled_arrival) - new Date(b.scheduled_departure);
            return durationA - durationB;
          });
        case 'airline':
          return results.sort((a, b) => 
            (a.airline_name || '').localeCompare(b.airline_name || '')
          );
        default:
          return results;
      }
    });
    
    // 方法
    const handleSearch = async (searchParams) => {
      if (isSearching.value) return;
      
      isSearching.value = true;
      currentSearch.value = searchParams;
      showResults.value = false;
      searchResults.value = [];
      
      try {
        // 模擬搜尋時間，讓用戶看到專業的加載動畫
        const minSearchTime = 4000; // 最少顯示4秒加載動畫
        const searchStartTime = Date.now();
        
        const response = await searchFlights(searchParams);
        
        if (response.success && response.data) {
          searchResults.value = response.data;
          searchStore.setSearchResults(response.data);
          
          // 確保加載動畫至少顯示最小時間
          const searchDuration = Date.now() - searchStartTime;
          const remainingTime = Math.max(0, minSearchTime - searchDuration);
          
          if (remainingTime > 0) {
            await new Promise(resolve => setTimeout(resolve, remainingTime));
          }
          
          showResults.value = true;
          
          // 平滑滾動到結果區域
          await nextTick();
          scrollToResults();
        } else {
          console.error('搜尋失敗:', response.message);
          searchResults.value = [];
          showResults.value = true;
        }
      } catch (error) {
        console.error('搜尋時發生錯誤:', error);
        searchResults.value = [];
        showResults.value = true;
      } finally {
        isSearching.value = false;
      }
    };
    
    const handleFlightSelection = (flight) => {
      console.log('選擇航班:', flight);
      searchStore.setSelectedFlight(flight);
      // 這裡可以導航到預訂頁面或其他處理
    };
    
    const handleViewDetails = (flight) => {
      selectedFlight.value = flight;
    };
    
    const closeFlightDetails = () => {
      selectedFlight.value = null;
    };
    
    const cancelSearch = () => {
      isSearching.value = false;
      currentSearch.value = null;
    };
    
    const resetSearch = () => {
      showResults.value = false;
      searchResults.value = [];
      selectedFlight.value = null;
      currentSearch.value = null;
    };
    
    const sortResults = () => {
      // 排序邏輯在 computed 中處理
    };
    
    const toggleFilters = () => {
      showFilters.value = !showFilters.value;
    };
    
    const formatSearchSummary = () => {
      if (!currentSearch.value) return '';
      
      const { departure, arrival, date, return_date } = currentSearch.value;
      const formatDate = (dateStr) => {
        const date = new Date(dateStr);
        return date.toLocaleDateString('zh-TW', { 
          month: 'long', 
          day: 'numeric' 
        });
      };
      
      const tripType = return_date ? '往返' : '單程';
      const dateRange = return_date 
        ? `${formatDate(date)} - ${formatDate(return_date)}`
        : formatDate(date);
      
      return `${departure} → ${arrival} • ${tripType} • ${dateRange}`;
    };
    
    const scrollToResults = () => {
      if (resultsSection.value) {
        const headerOffset = 100;
        const elementPosition = resultsSection.value.offsetTop;
        const offsetPosition = elementPosition - headerOffset;
        
        window.scrollTo({
          top: offsetPosition,
          behavior: 'smooth'
        });
      }
    };
    
    // 生命週期
    onMounted(() => {
      // 如果有之前的搜尋結果，顯示它們
      const existingResults = searchStore.searchResults;
      if (existingResults && existingResults.length > 0) {
        searchResults.value = existingResults;
        showResults.value = true;
      }
    });
    
    onBeforeUnmount(() => {
      if (searchTimeout) {
        clearTimeout(searchTimeout);
      }
    });

    return {
      isSearching,
      showResults,
      searchResults,
      selectedFlight,
      currentSearch,
      sortBy,
      showFilters,
      resultsSection,
      sortedResults,
      handleSearch,
      handleFlightSelection,
      handleViewDetails,
      closeFlightDetails,
      cancelSearch,
      resetSearch,
      sortResults,
      toggleFilters,
      formatSearchSummary
    };
  }
};
</script>

<style scoped>
/* 簡潔航班搜尋頁面設計 */
.flight-search-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #F8FAFC 0%, #E2E8F0 100%);
  padding-bottom: 4rem; /* 增加底部空間 */
}

/* 搜尋區域 */
.search-section {
  background: white;
  padding: 3rem 0;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

.search-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1rem;
}

/* 結果區域 */
.results-section {
  background: white;
  min-height: 50vh;
  margin-top: 2rem;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  max-width: 1200px; /* 統一最大寬度 */
  margin-left: auto;
  margin-right: auto;
}

.results-container {
  padding: 3rem 1rem;
}

/* 預設畫面 */
.default-state-section {
  max-width: 1200px;
  margin: 2rem auto 0;
}

/* 搜尋摘要 */
.search-summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  padding: 1.5rem;
  background: linear-gradient(135deg, 
    rgba(248, 250, 252, 0.8) 0%, 
    rgba(255, 255, 255, 0.9) 100%
  );
  border-radius: 20px;
  border: 1px solid rgba(229, 231, 235, 0.8);
}

.summary-content {
  flex: 1;
}

.summary-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: #005F73;
  margin: 0 0 0.5rem 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.result-count {
  background: linear-gradient(135deg, #F4A261 0%, #E76F51 100%);
  color: white;
  padding: 0.25rem 0.75rem;
  border-radius: 16px;
  font-size: 1.25rem;
  font-weight: 700;
}

.summary-details {
  color: #6B7280;
  font-size: 1rem;
  margin: 0;
}

/* 搜尋控制項 */
.search-controls {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.sort-select {
  padding: 0.75rem 1rem;
  border: 2px solid #E5E7EB;
  border-radius: 12px;
  background: white;
  color: #374151;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.sort-select:hover,
.sort-select:focus {
  border-color: #005F73;
  outline: none;
  box-shadow: 0 4px 12px rgba(0, 95, 115, 0.08);
}

.filter-toggle {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: rgba(0, 95, 115, 0.1);
  border: 2px solid #005F73;
  border-radius: 12px;
  color: #005F73;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.filter-toggle:hover {
  background: #005F73;
  color: white;
  transform: translateY(-1px);
}

.filter-icon {
  font-size: 1rem;
}

/* 航班列表 */
.flight-list {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

/* 空結果狀態 */
.empty-results {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.empty-content {
  text-align: center;
  max-width: 500px;
  padding: 3rem 2rem;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1.5rem;
  opacity: 0.6;
}

.empty-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #005F73;
  margin-bottom: 1rem;
}

.empty-description {
  color: #6B7280;
  margin-bottom: 2rem;
  line-height: 1.6;
}

.reset-search-btn {
  background: #005F73;
  color: white;
  border: none;
  padding: 1rem 2rem;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.reset-search-btn:hover {
  background: #004A5A;
  transform: translateY(-2px);
}

/* 響應式設計 */
@media (max-width: 768px) {
  .search-section {
    padding: 2rem 0;
  }

  .search-summary {
    flex-direction: column;
    gap: 1rem;
    align-items: flex-start;
  }
  
  .search-controls {
    width: 100%;
    justify-content: flex-start;
  }
  
  .default-title {
    font-size: 2rem;
  }
  
  .search-tips {
    grid-template-columns: 1fr;
  }
}
</style> 