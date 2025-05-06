<template>
  <div class="mb-4">
    <label v-if="label" :for="id" class="label">{{ label }}</label>
    <div class="relative" :id="id">
      <!-- 顯示選擇的機場 -->
      <div 
        @click="toggleDropdown" 
        class="input w-full pr-10 border-gray-300 focus:border-primary flex items-center cursor-pointer"
        :class="{ 'border-red-500': error, 'opacity-50 cursor-not-allowed': disabled, 'pl-3': !loading, 'pl-10': loading }"
      >
        <span v-if="selectedAirport">{{ selectedAirport.code }} - {{ selectedAirport.name }}</span>
        <span v-else class="text-gray-500">{{ placeholder }}</span>
      </div>

      <!-- Loading Spinner -->
      <div v-if="loading" class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
        <div class="orbital-loader-sm">
          <div class="orbital-dot"></div>
          <div class="orbital-dot"></div>
          <div class="orbital-dot"></div>
        </div>
      </div>
      
      <!-- Dropdown Arrow -->
      <div class="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
        <svg class="h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
          <path fill-rule="evenodd" d="M10 3a.75.75 0 01.53.22l3.75 3.75a.75.75 0 01-1.06 1.06L10 5.06l-3.22 3.22a.75.75 0 01-1.06-1.06l3.75-3.75A.75.75 0 0110 3zM10 17a.75.75 0 01-.53-.22l-3.75-3.75a.75.75 0 011.06-1.06L10 14.94l3.22-3.22a.75.75 0 011.06 1.06l-3.75 3.75A.75.75 0 0110 17z" clip-rule="evenodd" />
        </svg>
      </div>

      <!-- 下拉選單 -->
      <div v-if="isOpen" class="absolute z-50 w-full mt-1 bg-white border border-gray-300 shadow-lg max-h-80 overflow-y-auto">
        <!-- 搜尋框 -->
        <div class="p-2 border-b border-gray-200">
          <input 
            type="text" 
            v-model="searchQuery" 
            placeholder="搜尋機場..." 
            class="w-full p-2 border border-gray-300 focus:border-primary focus:outline-none"
            @click.stop
          />
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
    <p v-if="error" class="mt-1 text-xs text-red-600">{{ error }}</p>
  </div>
</template>

<script>
import { computed, ref, watch, onMounted, onBeforeUnmount } from 'vue'

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
  emits: ['update:modelValue', 'change'],
  setup(props, { emit }) {
    const isOpen = ref(false);
    const searchQuery = ref('');
    const selectedRegion = ref(null);
    
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
      if (props.disabled || props.loading) return;
      
      // 如果已經選擇了地區且下拉框是打開的，不要關閉它
      if (isOpen.value && selectedRegion.value) {
        return;
      }
      
      isOpen.value = !isOpen.value;
      
      // 重置選擇的地區，僅當下拉框關閉時
      if (!isOpen.value) {
        selectedRegion.value = null;
        searchQuery.value = '';
      }
    };

    const selectRegion = (region) => {
      selectedRegion.value = region;
    };

    const handleRegionClick = (event, region) => {
      // 阻止事件冒泡
      event.stopPropagation();
      selectRegion(region);
    };

    const handleBackButtonClick = (event) => {
      // 阻止事件冒泡
      event.stopPropagation();
      selectedRegion.value = null;
    };

    const selectAirport = (airport, event) => {
      // 阻止事件冒泡
      if (event) {
        event.stopPropagation();
      }
      
      // *** 創建一個普通對象副本 ***
      const plainAirport = { ...airport };
      // const airportCode = plainAirport.code; // No longer needed here
      
      console.log('AirportSelector: 即將 emit 的 airport (原始):', JSON.parse(JSON.stringify(airport)));
      console.log('AirportSelector: 即將 emit 的 airport (複製後, restored):', plainAirport); 
      // console.log('AirportSelector: 即將 emit 的 code:', airportCode); // No longer needed here
      
      // Emit the plain object for v-model compatibility
      emit('update:modelValue', plainAirport); 

      // *** Emit the plain object again for the change event ***
      emit('change', plainAirport); 
      
      isOpen.value = false;
      selectedRegion.value = null;
      searchQuery.value = '';
    };

    // 點擊外部關閉下拉選單
    const closeDropdown = (e) => {
      // 檢查點擊是否在組件內
      const targetElement = e.target;
      const selectorElement = document.getElementById(props.id);
      
      if (selectorElement && selectorElement.contains(targetElement)) {
        return; // 點擊在組件內部，不關閉
      }
      
      isOpen.value = false;
      selectedRegion.value = null;
      searchQuery.value = '';
    };

    onMounted(() => {
      document.addEventListener('click', closeDropdown);
    });

    onBeforeUnmount(() => {
      document.removeEventListener('click', closeDropdown);
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
      getSelectedAirports
    };
  }
}
</script>

<style scoped>
.input {
  display: block;
  width: 100%;
  padding: 0.5rem 0.75rem;
  border-width: 1px;
  background-color: #fff;
  transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
}

.input:focus {
  outline: none;
}

.label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #212529;
}

/* 機場選擇加載動畫-小型版 */
.orbital-loader-sm {
  position: relative;
  width: 1.5rem;
  height: 1.5rem;
  display: flex;
  justify-content: center;
  align-items: center;
}

.orbital-loader-sm .orbital-dot {
  position: absolute;
  width: 0.3rem;
  height: 0.3rem;
  background-color: #005F73;
  border-radius: 9999px;
}

.orbital-loader-sm .orbital-dot:nth-child(1) {
  top: 0;
  animation: pulseScale 1.5s infinite;
}

.orbital-loader-sm .orbital-dot:nth-child(2) {
  bottom: 0.1rem;
  left: 0.1rem;
  animation: pulseScale 1.5s infinite 0.2s;
}

.orbital-loader-sm .orbital-dot:nth-child(3) {
  bottom: 0.1rem;
  right: 0.1rem;
  animation: pulseScale 1.5s infinite 0.4s;
}

@keyframes pulseScale {
  0%, 100% { transform: scale(1); opacity: 0.7; }
  50% { transform: scale(1.3); opacity: 1; }
}
</style> 