<template>
  <div class="journey-search-container">
    <!-- 搜尋標題區域 -->
    <div class="search-header">
      <h1 class="search-title">探索您的下一趟旅程</h1>
      <p class="search-subtitle">找到完美的航班，開始您的精彩旅程</p>
    </div>

    <!-- 主要搜尋表單 -->
    <div class="search-form-wrapper">
      <form @submit.prevent="submitSearch" class="journey-form">
        
        <RouteSelection
          :departure-airport="searchParams.departureAirport"
          :arrival-airport="searchParams.arrivalAirport"
          @update:departure-airport="store.updateSearchParams({ departureAirport: $event })"
          @update:arrival-airport="store.updateSearchParams({ arrivalAirport: $event })"
          :taiwan-airports="taiwanAirports"
          :destination-airports="destinationAirports"
          :loading-taiwan-airports="loadingTaiwanAirports"
          :loading-destinations="loadingDestinations"
          :departure-error="errors.departureAirport"
          :arrival-error="errors.arrivalAirport"
          @swap="swapAirports"
          @departure-change="onDepartureChange"
          @select-recent-route="handleRecentRouteSelected"
        />
        
        <TravelOptions
          :departure-date="searchParams.departureDate"
          :return-date="searchParams.returnDate"
          @update:departure-date="store.updateSearchParams({ departureDate: $event })"
          @update:return-date="store.updateSearchParams({ returnDate: $event })"
          :departure-date-error="errors.departureDate"
          :return-date-error="errors.returnDate"
          :passenger-cabin-display="passengerCabinDisplay"
          @open-passenger-modal="openPassengerModal"
          @departure-date-change="onDepartureDateChange"
        />
        
        <!-- 搜尋按鈕區域 -->
        <div class="search-action">
          <button 
            type="submit" 
            class="search-button"
            :disabled="isSearching || loadingTaiwanAirports || loadingDestinations"
          >
            <div class="button-content">
              <span v-if="!isSearching" class="button-text">
                <span class="search-icon">🔍</span>
                搜尋航班
              </span>
              <div v-else class="searching-state">
                <div class="search-loader">
                  <div class="loader-ring"></div>
                  <div class="loader-dot"></div>
                </div>
                <span class="searching-text">搜尋中...</span>
              </div>
            </div>
          </button>
        </div>
      </form>

      <!-- 最近搜尋快捷方式 -->
      <div class="recent-searches" v-if="recentSearches.length > 0">
        <h3 class="recent-title">最近搜尋</h3>
        <div class="recent-routes">
          <button
            v-for="(route, index) in recentSearches.slice(0, 3)"
            :key="index"
            @click="handleRecentRouteSelected(route)"
            class="recent-route-chip"
          >
            <span class="route-text">
              {{ route.departureAirport?.name || route.departureAirport?.code }} 
              → 
              {{ route.arrivalAirport?.name || route.arrivalAirport?.code }}
            </span>
          </button>
        </div>
      </div>
    </div>

    <!-- 乘客艙等選擇彈窗 -->
    <PassengerCabinSelectModal
      v-if="isPassengerModalVisible"
      :passengers="searchParams.passengers"
      :cabinClass="searchParams.cabinClass"
      @close="closePassengerModal"
      @confirm="handlePassengerConfirm"
    />
  </div>
</template>

<script>
import { reactive, computed, onMounted } from 'vue';
import { useSearchStore } from '@/store/modules/search';
import { storeToRefs } from 'pinia';
import PassengerCabinSelectModal from '@/components/ui/PassengerCabinSelectModal.vue';
import RouteSelection from './RouteSelection.vue';
import TravelOptions from './TravelOptions.vue';
import { useAirportManagement } from '@/composables/useAirportManagement';
import { usePassengerModal } from '@/composables/usePassengerModal';

export default {
  name: 'SearchForm',
  components: {
    PassengerCabinSelectModal,
    RouteSelection,
    TravelOptions
  },
  props: {
    isSearching: {
      type: Boolean,
      default: false
    }
  },
  emits: ['search'],
  setup(props, { emit }) {
    const store = useSearchStore();
    const { searchParams } = storeToRefs(store);
    
    const { 
      taiwanAirports, 
      destinationAirports, 
      loadingTaiwanAirports, 
      loadingDestinations, 
      fetchTaiwanAirports, 
      fetchDestinations 
    } = useAirportManagement(searchParams);

    const { 
      isPassengerModalVisible, 
      openPassengerModal, 
      closePassengerModal 
    } = usePassengerModal();

    const errors = reactive({
      departureAirport: '',
      arrivalAirport: '',
      departureDate: '',
      returnDate: ''
    });

    const recentSearches = computed(() => store.recentSearches);
    
    const passengerCabinDisplay = computed(() => {
      const total = searchParams.value.passengers.adults + searchParams.value.passengers.children + searchParams.value.passengers.infants;
      const classMap = {
        ECONOMY: '經濟艙',
        PREMIUM_ECONOMY: '豪華經濟艙',
        BUSINESS: '商務艙',
        FIRST: '頭等艙',
      };
      return `${total} 位乘客, ${classMap[searchParams.value.cabinClass]}`;
    });

    const onDepartureChange = (newDepartureAirport) => {
      store.updateSearchParams({ departureAirport: newDepartureAirport });
      if (newDepartureAirport) {
        fetchDestinations(newDepartureAirport.code);
      }
      if (searchParams.value.arrivalAirport?.code === newDepartureAirport?.code) {
        store.updateSearchParams({ arrivalAirport: null });
      }
    };

    const swapAirports = () => {
      const departure = searchParams.value.departureAirport;
      const arrival = searchParams.value.arrivalAirport;
      store.updateSearchParams({
        departureAirport: arrival,
        arrivalAirport: departure,
      });
    };

    const onDepartureDateChange = () => {
      if (searchParams.value.returnDate && searchParams.value.returnDate < searchParams.value.departureDate) {
        store.updateSearchParams({ returnDate: '' });
      }
    };
    
    const handlePassengerConfirm = (data) => {
      store.updateSearchParams({
        passengers: { ...data.passengers },
        cabinClass: data.cabinClass,
      });
      closePassengerModal();
    };

    const submitSearch = () => {
      errors.departureAirport = !searchParams.value.departureAirport ? '請選擇出發地' : '';
      errors.arrivalAirport = !searchParams.value.arrivalAirport ? '請選擇目的地' : '';
      errors.departureDate = !searchParams.value.departureDate ? '請選擇出發日期' : '';

      if (Object.values(errors).some(e => e)) return;
      
      const searchData = {
        departureCode: searchParams.value.departureAirport.code,
        arrivalCode: searchParams.value.arrivalAirport.code,
        departureDate: searchParams.value.departureDate,
        returnDate: searchParams.value.returnDate,
        passengers: searchParams.value.passengers,
        cabinClass: searchParams.value.cabinClass
      };
      
      emit('search', searchData);
      store.addRecentSearch({
        departureAirport: searchParams.value.departureAirport,
        arrivalAirport: searchParams.value.arrivalAirport,
      });
    };
    
    const handleRecentRouteSelected = (route) => {
      store.updateSearchParams({
        departureAirport: route.departureAirport,
        arrivalAirport: route.arrivalAirport,
      });
    };

    onMounted(() => {
      fetchTaiwanAirports();
      // 在 store 中初始化 searchParams
      store.loadRecentSearches();
    });

    return {
      searchParams, // 直接從 store 暴露
      store, // 暴露整個 store 以便在模板中使用 action
      errors,
      recentSearches,
      passengerCabinDisplay,
      taiwanAirports,
      destinationAirports,
      loadingTaiwanAirports,
      loadingDestinations,
      isPassengerModalVisible,
      openPassengerModal,
      closePassengerModal,
      handlePassengerConfirm,
      submitSearch,
      onDepartureChange,
      swapAirports,
      onDepartureDateChange,
      handleRecentRouteSelected
    };
  }
}
</script>

<style scoped>
/* 基本容器和背景 - 現代化設計 */
.journey-search-container {
  padding: 3rem 1rem;
  background: linear-gradient(135deg, #F8FAFC 0%, #E2E8F0 100%);
  display: flex;
  flex-direction: column;
  align-items: center;
  min-height: 60vh;
  position: relative;
}

/* 搜尋標題 - 增強視覺層次 */
.search-header {
  text-align: center;
  margin-bottom: 3rem;
  position: relative;
  z-index: 2;
}

.search-title {
  font-size: 3rem;
  font-weight: 700;
  background: linear-gradient(135deg, #005F73 0%, #0A9396 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 1rem;
  line-height: 1.2;
}

.search-subtitle {
  font-size: 1.2rem;
  color: #64748B;
  margin-top: 0.5rem;
  font-weight: 400;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
  line-height: 1.6;
}

/* 表單容器 - 玻璃態設計 */
.search-form-wrapper {
  width: 100%;
  max-width: 1100px;
  background: rgba(255, 255, 255, 0.95);
  padding: 3rem;
  border-radius: 24px;
  box-shadow:
    0 20px 60px rgba(0, 0, 0, 0.08),
    0 8px 32px rgba(0, 0, 0, 0.04);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  position: relative;
  overflow: hidden;
}

.search-form-wrapper::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(0, 95, 115, 0.3), transparent);
}

.journey-form {
  display: flex;
  flex-direction: column;
  gap: 2.5rem;
}

/* 搜尋按鈕區域 - 現代化設計 */
.search-action {
  margin-top: 1.5rem;
  display: flex;
  justify-content: center;
}

.search-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 0 3rem;
  height: 64px;
  min-width: 240px;
  border-radius: 16px;
  font-size: 1.1rem;
  font-weight: 700;
  color: #fff;
  background: linear-gradient(135deg, #005F73 0%, #0A9396 50%, #94D3AC 100%);
  border: none;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow:
    0 8px 32px rgba(0, 95, 115, 0.3),
    0 4px 16px rgba(0, 0, 0, 0.1);
}

.search-button:hover:not(:disabled) {
  transform: translateY(-3px);
  box-shadow: 0 8px 25px rgba(0, 95, 115, 0.3);
}

.search-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.button-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

/* 搜尋中狀態 */
.searching-state {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.search-loader {
  width: 24px;
  height: 24px;
  position: relative;
}

.loader-ring {
  width: 100%;
  height: 100%;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  position: absolute;
}

.loader-dot {
  width: 100%;
  height: 100%;
  border: 3px solid transparent;
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  position: absolute;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 最近搜尋 */
.recent-searches {
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid #E2E8F0;
}

.recent-title {
  font-size: 1rem;
  font-weight: 600;
  color: #4A5568;
  margin-bottom: 1rem;
  text-align: center;
}

.recent-routes {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0.75rem;
}

.recent-route-chip {
  background-color: #E0F2F1;
  color: #004D40;
  border: 1px solid #B2DFDB;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.recent-route-chip:hover {
  background-color: #B2DFDB;
  transform: translateY(-2px);
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
}

@media (max-width: 768px) {
  .search-form-wrapper {
    padding: 1.5rem;
  }
  .search-title {
    font-size: 2rem;
  }
}
</style> 