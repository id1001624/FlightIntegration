<template>
  <div class="mb-4">
    <label v-if="label" :for="id" class="label">{{ label }}</label>
    <div class="relative" :id="id">
      <!-- 主互動元件：顯示已選機場 或 作為下拉觸發器 -->
      <div 
        @click="toggleDropdown" 
        ref="triggerElement"
        class="input w-full pr-10 border-gray-300 focus-within:border-primary flex items-center cursor-pointer"
        :class="{ 'border-red-500': error, 'opacity-50 cursor-not-allowed': disabled }"
      >
        <div v-if="internalLoading && !selectedAirport" class="loader-wrapper">
          <div class="cool-loader">
            <div class="cool-loader-ring"></div>
            <div class="cool-loader-ring"></div>
            <div class="cool-loader-dot"></div>
          </div>
        </div>
        <div :class="{ 'pl-8': internalLoading && !selectedAirport }">
          <span v-if="selectedAirport && !isOpen">{{ selectedAirport.code }} - {{ selectedAirport.name }}</span>
          <input
            v-else-if="isOpen || !selectedAirport"
            type="text"
            v-model="searchQuery"
            :placeholder="selectedAirport ? '搜尋其他機場...' : (placeholder || '搜尋機場名稱或代碼...')"
            class="w-full focus:outline-none bg-transparent"
            @click.stop
            @focus="isOpen = true" 
            ref="searchInput"
          />
        </div>
      </div>

      <!-- Dropdown Arrow -->
      <div 
        class="absolute inset-y-0 right-0 pr-3 flex items-center"
        :class="{'pointer-events-none': !isOpen}" 
        @click="toggleDropdown"
      >
        <svg class="h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
          <path fill-rule="evenodd" d="M10 3a.75.75 0 01.53.22l3.75 3.75a.75.75 0 01-1.06 1.06L10 5.06l-3.22 3.22a.75.75 0 01-1.06-1.06l3.75-3.75A.75.75 0 0110 3zM10 17a.75.75 0 01-.53-.22l-3.75-3.75a.75.75 0 011.06-1.06L10 14.94l3.22-3.22a.75.75 0 011.06 1.06l-3.75 3.75A.75.75 0 0110 17z" clip-rule="evenodd" />
        </svg>
      </div>
      
      <button 
        v-if="selectedAirport && !disabled" 
        @click.stop="clearSelection" 
        type="button"
        class="absolute inset-y-0 right-8 pr-3 flex items-center text-gray-400 hover:text-gray-600"
        aria-label="Clear selection"
      >
        <svg class="h-4 w-4" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path></svg>
      </button>

      <!-- 下拉選單 - 使用 fixed 定位 -->
      <div 
        v-if="isOpen" 
        ref="dropdownElement"
        class="fixed z-[9999] bg-white border border-gray-300 shadow-lg max-h-80 overflow-y-auto rounded-md"
        :style="{ top: dropdownTop + 'px', left: dropdownLeft + 'px', width: dropdownWidth + 'px' }"
      >
        <!-- 最近搜尋路線 -->
        <div v-if="recentSearches && recentSearches.length > 0" class="recent-searches p-2 border-b border-gray-200">
          <div class="text-xs text-gray-500 px-1 pb-1 sticky top-0 bg-white z-10">最近搜尋</div>
          <div 
            v-for="(route, index) in recentSearches" 
            :key="`recent-${index}-${route.departureAirport.code}-${route.arrivalAirport.code}`"
            class="recent-search-item px-2 py-1.5 hover:bg-gray-100 cursor-pointer text-sm flex items-center justify-between"
            @click="selectRecentRoute(route)"
          >
            <span>
              {{ route.departureAirport.name_zh || route.departureAirport.name }} ({{ route.departureAirport.code }}) 
              <span class="mx-1">→</span>
              {{ route.arrivalAirport.name_zh || route.arrivalAirport.name }} ({{ route.arrivalAirport.code }})
            </span>
          </div>
        </div>
        <div v-else-if="isOpen && (!recentSearches || recentSearches.length === 0) && !searchQuery && !selectedRegion" class="px-3 py-2 text-xs text-gray-400 border-b border-gray-200">
          尚無最近搜尋記錄
        </div>
        
        <!-- 台灣出發地特殊顯示 (僅當作為出發地選擇器時) -->
        <div v-if="isTaiwanDeparture && !searchQuery" class="border-b border-gray-200">
          <div class="bg-primary text-white px-3 py-2.5 font-medium sticky top-0">台灣出發</div>
          <div 
            v-for="airport in taiwanAirports" 
            :key="airport.code" 
            @click="selectAirport(airport, $event)"
            class="px-3 py-2.5 hover:bg-primary hover:bg-opacity-10 cursor-pointer flex items-center"
            :class="{'bg-primary bg-opacity-20': isSelected(airport)}"
          >
            <span class="font-medium text-text-primary w-14">{{ airport.code }}</span>
            <span class="mx-1">-</span>
            <span class="text-text-secondary">{{ airport.name }}</span>
          </div>
        </div>
        
        <!-- 國家/地區選擇 (非搜尋時顯示) -->
        <div v-if="!selectedRegion && !searchQuery && !isTaiwanDeparture" class="border-b border-gray-200">
          <!-- 熱門目的地分類 -->
          <div 
            v-if="popularDestinations.length > 0"
            @click="handleRegionClick($event, '熱門目的地')" 
            class="px-3 py-3 hover:bg-primary hover:bg-opacity-10 cursor-pointer flex items-center border-b border-gray-100"
          >
            <span class="font-medium text-[#212529]">熱門目的地</span> <!-- #006D77 -->
            <span class="ml-auto">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-gray-400" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd" />
              </svg>
            </span>
          </div>
          
          <!-- 國家/地區列表 -->
          <div class="px-3 py-2 font-medium bg-gray-50 text-gray-600 text-sm sticky top-0">國家 / 地區</div>
          <div 
            v-for="region in availableRegions" 
            :key="region" 
            @click="handleRegionClick($event, region)"
            class="px-3 py-3 hover:bg-primary hover:bg-opacity-10 cursor-pointer flex items-center"
          >
            <span class="text-text-primary font-medium">{{ region }}</span>
            <span class="ml-auto">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-gray-400" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd" />
              </svg>
            </span>
          </div>
        </div>

        <!-- 選擇了地區後顯示機場 -->
        <div v-if="selectedRegion && !searchQuery" class="border-b border-gray-200">
          <div class="bg-gray-50 px-3 py-2 flex items-center sticky top-0">
            <button 
              @click="handleBackButtonClick($event)" 
              class="mr-2 text-primary hover:text-primary-dark"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clip-rule="evenodd" />
              </svg>
            </button>
            <span class="font-medium text-gray-600 text-sm">{{ selectedRegion }}</span>
          </div>
          <div 
            v-for="airport in getSelectedAirports" 
            :key="airport.code" 
            @click="selectAirport(airport, $event)"
            class="px-3 py-2.5 hover:bg-primary hover:bg-opacity-10 cursor-pointer flex items-center"
            :class="{'bg-primary bg-opacity-20': isSelected(airport)}"
          >
            <span class="font-medium text-text-primary w-14">{{ airport.code }}</span>
            <span class="mx-1">-</span>
            <span class="text-text-secondary">{{ airport.name }}</span>
          </div>
        </div>

        <!-- 搜尋結果 -->
        <div v-if="searchQuery" class="border-b border-gray-200">
          <div class="px-3 py-2 font-medium bg-gray-50 text-gray-600 text-sm sticky top-0">搜尋結果</div>
          <div 
            v-for="airport in searchResults" 
            :key="airport.code" 
            @click="selectAirport(airport, $event)"
            class="px-3 py-2.5 hover:bg-primary hover:bg-opacity-10 cursor-pointer flex items-center"
            :class="{'bg-primary bg-opacity-20': isSelected(airport)}"
          >
            <span class="font-medium text-text-primary w-14">{{ airport.code }}</span>
            <span class="mx-1">-</span>
            <span class="text-text-secondary">{{ airport.name }}</span>
          </div>
          
          <!-- 無匹配結果 -->
          <div v-if="searchResults.length === 0" class="p-3 text-center text-gray-500">
            無匹配結果
          </div>
        </div>
      </div>
    </div>
    <p v-if="error" class="absolute bottom-[-1.25rem] left-0 w-full text-xs text-red-600 px-1">{{ error }}</p>
  </div>
</template>

<script>
import { computed, ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useSearchStore } from '@/store/modules/search';

export default {
  name: 'AirportSelector',
  props: {
    id: {
      type: String,
      default: 'airport-selector'
    },
    label: {
      type: String,
      default: ''
    },
    placeholder: {
      type: String,
      default: '選擇機場'
    },
    airports: {
      type: Array,
      default: () => []
    },
    modelValue: {
      type: [Object, String],
      default: null
    },
    disabled: {
      type: Boolean,
      default: false
    },
    loading: {
      type: Boolean,
      default: false
    },
    error: {
      type: String,
      default: ''
    },
    isDeparture: {
      type: Boolean,
      default: false
    }
  },
  emits: ['update:modelValue', 'change', 'select-recent-route'],
  setup(props, { emit }) {
    const isOpen = ref(false);
    const searchQuery = ref('');
    const selectedRegion = ref(null);
    const searchStore = useSearchStore();
    const searchInput = ref(null);

    const triggerElement = ref(null);    
    const dropdownElement = ref(null);
    
    // 添加下拉選單位置計算所需的變數
    const dropdownTop = ref(0);
    const dropdownLeft = ref(0);
    const dropdownWidth = ref(0);

    // 從 store 獲取最近搜尋記錄
    const recentSearches = computed(() => searchStore.recentSearches);

    // 內部加載狀態
    const internalLoading = ref(props.loading);
    const loadingTimer = ref(null);
    const loadingStartTime = ref(null);
    const MIN_LOADING_DURATION = 800; // 0.8秒

    // 監視外部loading屬性的變化
    watch(() => props.loading, (newVal, oldVal) => {
      // 如果開始加載
      if (newVal && !oldVal) {
        loadingStartTime.value = Date.now();
        internalLoading.value = true;
        
        // 清除可能存在的計時器
        if (loadingTimer.value) {
          clearTimeout(loadingTimer.value);
          loadingTimer.value = null;
        }
      } 
      // 如果停止加載
      else if (!newVal && oldVal) {
        const elapsedTime = Date.now() - (loadingStartTime.value || 0);
        
        // 如果已經顯示足夠時間，直接關閉
        if (elapsedTime >= MIN_LOADING_DURATION) {
          internalLoading.value = false;
        } else {
          // 否則延遲關閉以確保最小顯示時間
          const remainingTime = MIN_LOADING_DURATION - elapsedTime;
          loadingTimer.value = setTimeout(() => {
            internalLoading.value = false;
            loadingTimer.value = null;
          }, remainingTime);
        }
      }
    });

    // 清除計時器
    onBeforeUnmount(() => {
      if (loadingTimer.value) {
        clearTimeout(loadingTimer.value);
      }
      document.removeEventListener('click', closeDropdownOnClickOutside);
    });
    
    // 選中的機場
    const selectedAirport = computed(() => {
      if (!props.modelValue) return null;
      if (typeof props.modelValue === 'string') {
        return props.airports.find(airport => airport.code === props.modelValue) || null;
      }
      return props.modelValue;
    });

    // 判斷是否為台灣出發地選擇器
    const isTaiwanDeparture = computed(() => {
      return props.isDeparture && props.airports.some(airport => airport.country === 'Taiwan');
    });

    // 台灣機場列表
    const taiwanAirports = computed(() => {
      // 定義期望的排序順序
      const desiredOrder = [
        'TPE', 'TSA', 'KHH', 'RMQ', 'TNN', 
        'HUN', 'TTT', 'KNH', 'MZG', 'GNI', 
        'KYD', 'CYI', 'MFK', 'LZN', 'WOT', 
        'CMJ'
      ];

      const filteredAirports = props.airports.filter(airport => 
        airport.country === 'Taiwan' || 
        // 包含所有已知台灣機場代碼以防萬一 country 資訊缺失
        ['TPE', 'TSA', 'KHH', 'RMQ', 'TNN', 'CYI', 'HUN', 'TTT', 'MZG', 'KNH', 'MFK', 'LZN', 'KYD', 'GNI', 'TXG', 'PIF', 'WOT', 'CMJ'].includes(airport.code)
      );

      // 根據 desiredOrder 排序
      filteredAirports.sort((a, b) => {
        const indexA = desiredOrder.indexOf(a.code);
        const indexB = desiredOrder.indexOf(b.code);

        // 如果兩個都在 desiredOrder 中，按其索引排序
        if (indexA !== -1 && indexB !== -1) {
          return indexA - indexB;
        }
        // 如果只有 a 在 desiredOrder 中，a 排前面
        if (indexA !== -1) {
          return -1;
        }
        // 如果只有 b 在 desiredOrder 中，b 排前面
        if (indexB !== -1) {
          return 1;
        }
        // 如果都不在 desiredOrder 中，按名稱排序 (備用)
        return (a.name || '').localeCompare(b.name || '');
      });

      return filteredAirports;
    });

    // 熱門目的地
    const popularDestinations = computed(() => {
      const popularCities = ['東京', '大阪', '首爾', '香港', '曼谷', '新加坡', '上海', '北京', '倫敦', '紐約'];
      const popularAirports = ['NRT', 'HND', 'KIX', 'ICN', 'HKG', 'BKK', 'SIN', 'PVG', 'SHA', 'PEK', 'LHR', 'JFK'];
      
      return props.airports.filter(airport => 
        popularAirports.includes(airport.code) || 
        popularCities.some(city => airport.name.includes(city) || (airport.city && airport.city.includes(city)))
      );
    });

    // 搜尋結果
    const searchResults = computed(() => {
      if (!searchQuery.value) return [];
      
      const lowerCaseQuery = searchQuery.value.toLowerCase();

      return props.airports.filter(airport => {
        // 確保 airport.code 和 airport.name 存在且為字符串
        const codeMatch = airport.code && typeof airport.code === 'string' && 
                          airport.code.toLowerCase().includes(lowerCaseQuery);
        const nameMatch = airport.name && typeof airport.name === 'string' && 
                          airport.name.toLowerCase().includes(lowerCaseQuery); // 檢查中文名稱
                          
        return codeMatch || nameMatch;
      });
    });

    // 按地區分組機場
    const airportsByRegion = computed(() => {
      const result = {};
      
      // 預設地區分類
      const regionGroups = {
        '台灣': [],
        '中國': [],
        '香港/澳門': [],
        '東北亞': [],
        '東南亞': [],
        '美洲': [],
        '歐洲': [],
        '大洋洲': [],
        '非洲': [],
        '中東': [],
        '其他': []
      };
      
      // 分配機場到各地區
      props.airports.forEach(airport => {
        const region = airport.region || '其他';
        
        if (!result[region]) {
          result[region] = [];
        }
        
        result[region].push(airport);
      });
      
      // 添加熱門目的地分類
      if (popularDestinations.value.length > 0) {
        result['熱門目的地'] = popularDestinations.value;
      }
      
      return result;
    });

    // 可用地區列表
    const availableRegions = computed(() => {
      // 地區優先順序
      const regionOrder = [
        '台灣', '中國', '香港/澳門', '東北亞', '東南亞', 
        '美洲', '歐洲', '大洋洲', '非洲', '中東', '其他'
      ];
      
      // 取得所有存在機場的地區
      const regions = Object.keys(airportsByRegion.value).filter(r => r !== '熱門目的地');
      
      // 按照優先順序排序
      return regionOrder.filter(region => regions.includes(region));
    });

    // 根據選擇的地區獲取機場列表
    const getSelectedAirports = computed(() => {
      if (selectedRegion.value === '熱門目的地') {
        return popularDestinations.value;
      }
      return airportsByRegion.value[selectedRegion.value] || [];
    });

    // 檢查某機場是否已選中
    const isSelected = (airport) => {
      if (!selectedAirport.value) return false;
      return selectedAirport.value.code === airport.code;
    };

    const toggleDropdown = () => {
      if (props.disabled) return;
      isOpen.value = !isOpen.value;
      if (isOpen.value) {
        nextTick(() => {
          searchInput.value?.focus();
          updateDropdownPosition(); // 新增: 更新下拉選單位置
        });
      }
    };

    const selectRegion = (region) => {
      selectedRegion.value = region;
    };

    const handleRegionClick = (event, region) => {
      event.stopPropagation();
      selectRegion(region);
    };

    const handleBackButtonClick = (event) => {
      event.stopPropagation();
      selectedRegion.value = null;
    };

    const selectAirport = (airport, event) => {
      if (event) event.stopPropagation();
      emit('update:modelValue', airport); 
      emit('change', airport); 
      searchQuery.value = '';
      selectedRegion.value = null; 
      isOpen.value = false;
    };

    const clearSelection = () => {
      selectAirport(null); 
      searchQuery.value = ''; 
      isOpen.value = false; 
    };

    const selectRecentRoute = (route) => {
      emit('select-recent-route', route);
      isOpen.value = false;
    };

    const closeDropdownOnClickOutside = (e) => {
      if (
        isOpen.value &&
        triggerElement.value && 
        !triggerElement.value.contains(e.target) &&
        dropdownElement.value && 
        !dropdownElement.value.contains(e.target)
      ) {
        isOpen.value = false;
        selectedRegion.value = null;
        searchQuery.value = '';
      }
    };

    // 新增: 更新下拉選單位置的方法
    const updateDropdownPosition = () => {
      if (!triggerElement.value) return;
      
      const rect = triggerElement.value.getBoundingClientRect();
      dropdownTop.value = rect.bottom;
      dropdownLeft.value = rect.left;
      dropdownWidth.value = rect.width;
    };

    // 新增: 處理滾動和調整大小事件
    const handleScrollResize = () => {
      if (isOpen.value) {
        updateDropdownPosition();
      }
    };

    onMounted(() => {
      searchStore.loadRecentSearches();
      document.addEventListener('click', closeDropdownOnClickOutside);
      window.addEventListener('scroll', handleScrollResize, true);
      window.addEventListener('resize', handleScrollResize);
    });

    onBeforeUnmount(() => {
      if (loadingTimer.value) {
        clearTimeout(loadingTimer.value);
      }
      document.removeEventListener('click', closeDropdownOnClickOutside);
      window.removeEventListener('scroll', handleScrollResize, true);
      window.removeEventListener('resize', handleScrollResize);
    });
    
    watch(isOpen, (newValue) => {
      if (newValue) {
        nextTick(() => {
          updateDropdownPosition(); // 新增: 當下拉選單打開時更新位置
        });
      }
    });

    return {
      isOpen,
      searchQuery,
      selectedAirport,
      selectedRegion,
      taiwanAirports,
      popularDestinations,
      searchResults,
      availableRegions,
      airportsByRegion,
      isTaiwanDeparture,
      toggleDropdown,
      selectRegion,
      handleRegionClick,
      handleBackButtonClick,
      selectAirport,
      isSelected,
      getSelectedAirports,
      internalLoading,
      recentSearches,
      selectRecentRoute,
      triggerElement,
      dropdownElement,
      // 新增: 導出下拉選單位置變數
      dropdownTop,
      dropdownLeft,
      dropdownWidth,
    };
  }
}
</script>

<style scoped>
.input {
  display: block;
  width: 100%;
  padding: 0.5rem 0.75rem calc(0.5rem + 1em); /* 假設錯誤文字高度約為1em */
  border-width: 1px;
  background-color: #fff;
  transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
}

.input:focus {
  outline: none;
}

.label {
  display: block;
  margin-bottom: 0.5rem; /* 確保 label 和 input 之間有足夠間距 */
  font-weight: 500;
  color: #212529;
}

/* 給 AirportSelector 的根 div 增加 padding-bottom 以容納絕對定位的錯誤訊息 */
.mb-4 {
  position: relative; 
  padding-bottom: 1.5rem; 
}

/* 機場選擇加載動畫-酷炫版 */
.loader-wrapper {
  position: absolute;
  left: 0.75rem; /* pl-3 */
  top: 50%;
  transform: translateY(-50%);
  z-index: 5; /* 確保在文字之上 */
}

.cool-loader {
  position: relative;
  width: 20px;
  height: 20px;
}

.cool-loader-ring {
  position: absolute;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  border: 2px solid transparent;
  border-top-color: var(--color-primary, #005F73);
  animation: cool-loader-rotate 1.5s linear infinite;
}

.cool-loader-ring:nth-child(1) {
  animation-delay: 0s;
}

.cool-loader-ring:nth-child(2) {
  width: 60%;
  height: 60%;
  top: 20%;
  left: 20%;
  border-top-color: var(--color-secondary, #F4A261);
  animation-direction: reverse;
  animation-duration: 1s;
}

.cool-loader-dot {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 30%;
  height: 30%;
  background-color: var(--color-primary, #005F73);
  border-radius: 50%;
  transform: translate(-50%, -50%);
  animation: cool-loader-pulse 1s ease-in-out infinite;
}

@keyframes cool-loader-rotate {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@keyframes cool-loader-pulse {
  0%, 100% { transform: translate(-50%, -50%) scale(0.8); opacity: 0.8; }
  50% { transform: translate(-50%, -50%) scale(1.2); opacity: 1; }
}

/* 增加 focus-within 樣式使父容器在 input focus 時有邊框 */
.input.focus-within\\:border-primary:focus-within {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 1px var(--color-primary);
}

/* 微調 sticky top 的值，確保在滾動時正確覆蓋 */
.recent-searches .sticky,
.p-2.border-b.sticky {
  top: 0; /* 確保搜尋框和最近搜尋標題在滾動時固定在下拉選單頂部 */
}
</style> 