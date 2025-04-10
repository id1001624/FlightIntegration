<template>
  <div class="flight-app">
    <!-- 全螢幕背景輪播 -->
    <div class="fullscreen-bg">
      <div
        v-for="(bg, index) in backgrounds"
        :key="index"
        :class="['bg-slide', { active: currentBg === index }]"
        :style="{ backgroundImage: `url(${bg.image})` }"
      >
        <div class="overlay" :style="{ opacity: bg.overlayOpacity }"></div>
      </div>
    </div>

    <!-- 導航欄 -->
    <header class="app-header">
      <div class="container mx-auto px-4 py-4 flex justify-between items-center">
        <div class="logo-container">
          <h1 class="text-white text-2xl font-light tracking-wider">
            <span class="font-bold">Taiwan</span>Flight
          </h1>
        </div>
        <nav class="hidden md:flex items-center space-x-8">
          <a href="#" class="nav-link active">首頁</a>
          <a href="#" class="nav-link">航班查詢</a>
          <a href="#" class="nav-link">航空公司</a>
          <a href="#" class="nav-link">會員專區</a>
          <a href="#" class="nav-link">關於我們</a>
        </nav>
        <button class="menu-button md:hidden text-white">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" class="w-6 h-6">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16m-7 6h7"></path>
          </svg>
        </button>
      </div>
    </header>

    <!-- 主內容區 -->
    <main class="main-content relative z-10">
      <div class="container mx-auto px-4 py-12 md:py-24">
        <!-- 標語 -->
        <div class="hero-section mb-12 md:mb-20 text-center md:text-left max-w-3xl">
          <h2 class="text-4xl md:text-5xl lg:text-6xl font-light mb-4 text-white leading-tight">
            探索<span class="font-bold">台灣的天際</span>，
            <br class="hidden md:block">從這裡起飛
          </h2>
          <p class="text-lg md:text-xl text-gray-200 mb-8">
            整合台灣所有航空公司的航班資訊，幫助您輕鬆找到最理想的飛行計劃。
          </p>
        </div>

        <!-- 載入指示器 -->
        <div v-if="loading" class="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50">
          <div class="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-white"></div>
        </div>

        <!-- 搜尋面板 -->
        <div class="search-card bg-white/90 backdrop-blur-lg p-8 rounded-xl shadow-xl">
          <SearchForm @search="handleSearch" :is-searching="isSearching" />
        </div>

        <!-- 如果已經有搜尋結果 -->
        <div v-if="hasSearched" class="mt-12">
          <div class="bg-white/90 backdrop-blur-lg p-8 rounded-xl shadow-xl">
            <!-- 結果標題 (可選) -->
            <div class="mb-6 p-4 bg-gradient-to-r from-primary-light/10 to-transparent rounded-lg" v-if="searchParams.departureAirport && searchParams.arrivalAirport">
              <h2 class="text-xl font-medium text-text-primary">
                {{ searchParams.departureAirport.code }} → {{ searchParams.arrivalAirport.code }}
              </h2>
              <p class="text-sm text-text-secondary mt-1">{{ formattedDepartureDate }}</p>
            </div>

            <div class="grid grid-cols-1 lg:grid-cols-4 gap-8">
              <!-- 篩選面板 -->
              <div class="lg:col-span-1">
                <div class="sticky top-24">
                  <FilterPanel
                    :flights="flights"
                    :initial-filters="filters"
                    @filter-change="handleFilterChange"
                  />
                </div>
              </div>

              <!-- 結果顯示 -->
              <div class="lg:col-span-3">
                <FlightResults
                  :flights="filteredFlights"
                  :searched="hasSearched"
                />
              </div>
            </div>
          </div>
        </div>
        <!-- 初始提示 (如果需要) -->
        <div v-else class="mt-12 text-center text-white/80">
          <!-- 可以放一些引導用戶搜索的提示或圖標 -->
        </div>
      </div>
    </main>

    <!-- 特色區塊 -->
    <section class="features-section relative z-10 py-12 md:py-20 bg-white/10 backdrop-blur-sm mt-16">
      <div class="container mx-auto px-4">
        <h3 class="text-2xl md:text-3xl font-light text-center text-white mb-12">
          <span class="font-bold">專業服務</span>特色
        </h3>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
          <!-- Feature Cards -->
          <div class="feature-card">
            <div class="icon-wrapper">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" class="h-8 w-8"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
            </div>
            <h4 class="text-xl font-medium mb-2">快速查詢</h4>
            <p class="text-gray-600">整合全台航班資訊，幫您快速找到最合適的航班選擇。</p>
          </div>
          <div class="feature-card">
            <div class="icon-wrapper">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" class="h-8 w-8"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3 15a4 4 0 004 4h9a5 5 0 10-4.5-8.599A5 5 0 105.5 10.5H9a4.5 4.5 0 018.9.4" /></svg>
            </div>
            <h4 class="text-xl font-medium mb-2">實時動態</h4>
            <p class="text-gray-600">提供航班實時動態更新，讓您掌握最新航班狀態。</p>
          </div>
          <div class="feature-card">
            <div class="icon-wrapper">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" class="h-8 w-8"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2z" /></svg>
            </div>
            <h4 class="text-xl font-medium mb-2">票價比較</h4>
            <p class="text-gray-600">智能比較各航空公司票價，協助您找到最優惠的選擇。</p>
          </div>
        </div>
      </div>
    </section>

    <!-- 頁尾 -->
    <footer class="app-footer relative z-10">
      <div class="container mx-auto px-4 py-8">
        <div class="flex flex-col md:flex-row justify-between items-center">
          <div class="mb-4 md:mb-0">
            <h1 class="text-white text-xl font-light">
              <span class="font-bold">Taiwan</span>Flight
            </h1>
          </div>
          <div class="text-sm text-gray-300">
            © 2023 台灣航班整合系統 版權所有
          </div>
        </div>
      </div>
    </footer>
  </div>
</template>

<script>
import { ref, reactive, computed, watch, onMounted, onBeforeUnmount } from 'vue';
import SearchForm from '@/components/search/SearchForm.vue';
import FilterPanel from '@/components/search/FilterPanel.vue';
import FlightResults from '@/components/search/FlightResults.vue';
import flightService from '@/api/services/flightService';

export default {
  name: 'FlightSearchPage', // Renamed for clarity
  components: {
    SearchForm,
    FilterPanel,
    FlightResults
  },
  setup() {
    // --- Background Slideshow ---
    const backgrounds = [
      { image: '/src/images/sky-views/vista-wei-xYNC73QAqc8-unsplash.jpg', overlayOpacity: 0.4 },
      { image: '/src/images/sky-views/7vscsixj.png', overlayOpacity: 0.5 },
      { image: '/src/images/sky-views/kxk3ipb8.png', overlayOpacity: 0.4 },
      { image: '/src/images/sky-views/3gzzr6tf.png', overlayOpacity: 0.3 }
    ];
    const currentBg = ref(0);
    const bgInterval = ref(null);

    const rotateBg = () => {
      currentBg.value = (currentBg.value + 1) % backgrounds.length;
    };
    // --- End Background Slideshow ---

    const flights = ref([]);
    const filteredFlights = ref([]);
    const loading = ref(false);
    const isSearching = ref(false);
    const hasSearched = ref(false);

    const searchParams = reactive({
      departureAirport: null,
      arrivalAirport: null,
      departureDate: new Date().toISOString().split('T')[0],
      returnDate: '',
      classType: 'economy'
    });

    const filters = reactive({
      airlines: [],
      priceRange: { min: 0, max: 50000 }
    });

    const formattedDepartureDate = computed(() => {
      if (!searchParams.departureDate) return '';
      const date = new Date(searchParams.departureDate);
      return date.toLocaleDateString('zh-TW', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' });
    });

    const handleSearch = async (params) => {
      loading.value = true;
      isSearching.value = true;
      hasSearched.value = true;
      Object.assign(searchParams, params);
      filters.airlines = []; // Reset filters on new search

      try {
        // ... (API call logic remains the same)
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
        // ... (Response handling logic remains the same)
        // MOCK DATA FOR NOW
        const mockFlights = [
          // Add some mock flight objects here for testing UI
        ];
        const processedFlights = mockFlights.map(flight => {
            if (flight.price && typeof flight.price === 'string') {
                flight.price = parseFloat(flight.price);
            } else if (flight.price == null) {
                flight.price = Math.floor(Math.random() * 40000) + 5000; // Example random price
            }
            // Add other necessary fields if missing from mock data
            flight.airline_name = flight.airline_name || '模擬航空';
            flight.flight_number = flight.flight_number || 'XX123';
            flight.departure_time = flight.departure_time || '10:00';
            flight.arrival_time = flight.arrival_time || '12:00';
            flight.departure_airport_code = flight.departure_airport_code || params.departureAirport.code;
            flight.arrival_airport_code = flight.arrival_airport_code || params.arrivalAirport.code;
            flight.duration = flight.duration || 120; // Example duration in minutes
            flight.status = flight.status || 'scheduled';
            flight.class_type = flight.class_type || params.classType;
            return flight;
        });
        // END MOCK DATA

        flights.value = processedFlights; // Use real data: processedFlights;
        if (!flights.value || flights.value.length === 0) {
            alert(`沒有找到從 ${params.departureAirport.name} 到 ${params.arrivalAirport.name} 的航班，請選擇其他日期或目的地。`);
            filteredFlights.value = [];
        } else {
            // Update price filter range based on results
            const prices = flights.value.map(f => f.price).filter(p => p != null);
            const maxPrice = prices.length > 0 ? Math.max(...prices) : 50000;
            filters.priceRange.max = Math.ceil(maxPrice / 1000) * 1000 || 50000;
            filters.priceRange.min = 0;
            applyFilters(); // Apply initial filters (which might be none)
        }

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
        if (filters.airlines.length > 0) {
          const airlineCode = flight.airline_code || flight.airline?.code;
          if (!airlineCode || !filters.airlines.includes(airlineCode)) return false;
        }
        const flightPrice = flight.price || 0;
        if (flightPrice < filters.priceRange.min || flightPrice > filters.priceRange.max) return false;
        return true;
      });
    };

    const handleFilterChange = (newFilters) => {
      Object.assign(filters, newFilters);
      applyFilters();
    };

    watch(flights, () => {
        // When original flights change (new search), re-apply filters
        applyFilters();
    });

    onMounted(() => {
      bgInterval.value = setInterval(rotateBg, 7000);
      // No initial search or airport loading here, let user trigger it
    });

    onBeforeUnmount(() => {
      if (bgInterval.value) clearInterval(bgInterval.value);
    });

    return {
      backgrounds,
      currentBg,
      loading,
      isSearching,
      hasSearched,
      searchParams, // Pass search params for display
      formattedDepartureDate, // Pass formatted date
      flights,
      filteredFlights,
      filters,
      handleSearch,
      handleFilterChange,
    };
  }
};
</script>

<style>
/* Import styles from Home.vue or create a shared style file */
.flight-app {
  min-height: 100vh;
  position: relative;
  color: #1f2937; /* text-text-primary */
  overflow-x: hidden;
}

.fullscreen-bg {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: -2; /* Behind content */
}

.bg-slide {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-size: cover;
  background-position: center;
  opacity: 0;
  transition: opacity 1.5s ease-in-out;
}

.bg-slide.active {
  opacity: 1;
}

.overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(180deg, rgba(0,0,0,0.6) 0%, rgba(0,0,0,0.2) 70%, rgba(0,0,0,0.7) 100%);
  z-index: -1;
}

.app-header {
  position: sticky; /* Make header sticky */
  top: 0;
  z-index: 20; /* Above background, below modals */
  padding: 1rem 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  background-color: rgba(0, 0, 0, 0.2);
  backdrop-filter: blur(10px);
}

.nav-link {
  color: rgba(255, 255, 255, 0.8);
  font-weight: 500;
  transition: all 0.2s;
  position: relative;
  padding-bottom: 4px;
}

.nav-link:hover, .nav-link.active {
  color: white;
}

.nav-link.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 2px;
  background-color: white;
}

.main-content {
  min-height: 60vh; /* Adjust as needed */
}

.search-card {
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
}

.feature-card {
  background-color: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.feature-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 15px rgba(0, 0, 0, 0.1);
}

.icon-wrapper {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 60px;
  height: 60px;
  border-radius: 12px;
  background-color: #f0f9ff; /* sky-50 */
  color: #0ea5e9; /* primary */
  margin-bottom: 1.5rem;
}

.app-footer {
  background-color: rgba(0, 0, 0, 0.7);
  padding: 2rem 0;
  margin-top: 2rem; /* Ensure space before footer */
  backdrop-filter: blur(10px);
}

</style> 