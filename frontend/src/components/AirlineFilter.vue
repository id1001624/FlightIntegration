<template>
  <div class="mb-6">
    <h4 class="text-base font-medium text-text-primary mb-3">航空公司</h4>
    
    <!-- 全選選項 -->
    <div class="mb-2 border-b pb-2" v-if="availableAirlines.filter(a => a.flightCount > 0).length > 0">
      <label class="flex items-center cursor-pointer text-sm py-1">
        <input
          type="checkbox"
          :checked="modelValue.length === availableAirlines.filter(a => a.flightCount > 0).length && availableAirlines.filter(a => a.flightCount > 0).length > 0"
          @change="toggleAllAirlines"
          class="h-4 w-4 border-gray-300 text-primary focus:ring-primary flex-shrink-0"
        />
        <span class="text-text-primary font-medium ml-3">所有有航班的航空公司</span>
      </label>
    </div>
    
    <div class="text-sm text-text-secondary py-2" v-if="loading">載入中...</div>
    <div class="text-sm text-text-secondary py-2" v-else-if="availableAirlines.length === 0">沒有可用的航空公司</div>
    <div v-else class="space-y-1 max-h-60 overflow-y-auto">
      <div v-for="airline in availableAirlines" :key="airline.code" class="flex items-center">
        <label class="flex items-center cursor-pointer text-sm py-1 w-full" :class="{ 'opacity-50 cursor-not-allowed': airline.flightCount === 0 }">
          <input
            type="checkbox"
            :value="airline.code"
            :checked="isSelected(airline.code)"
            :disabled="airline.flightCount === 0"
            @change="toggleAirline(airline.code)"
            class="h-4 w-4 border-gray-300 text-primary focus:ring-primary flex-shrink-0 disabled:opacity-50 disabled:cursor-not-allowed"
          />
          <div class="ml-3 flex items-center flex-1 min-w-0">
            <div class="w-6 h-6 flex-shrink-0 mr-2 flex items-center justify-center">
              <img
                v-if="getFullLogoUrl(airline.logo)"
                :src="getFullLogoUrl(airline.logo)"
                :alt="airline.name + ' logo'"
                class="w-6 h-6 object-contain"
                @error="handleImageError"
              />
              <div v-else class="w-6 h-6 bg-gray-200 rounded text-xs flex items-center justify-center text-gray-500">
                {{ airline.code.slice(0, 2) }}
              </div>
            </div>
            <span class="text-text-primary truncate flex-1">{{ airline.name }}</span>
            <span class="text-text-secondary text-xs ml-2 flex-shrink-0" :class="{ 'text-gray-400': airline.flightCount === 0 }">
              ({{ airline.flightCount }})
            </span>
          </div>
        </label>
      </div>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue';

// **讀取環境變數並移除 /api**
const backendUrl = import.meta.env.VITE_API_BASE_URL.replace('/api', '');

export default {
  name: 'AirlineFilter',
  props: {
    airlines: { // 所有可用的航空公司列表（從API獲取）
      type: Array,
      default: () => []
    },
    flights: { // 當前搜索結果的航班列表
      type: Array,
      default: () => []
    },
    modelValue: {
      type: Array,
      default: () => []
    },
    loading: {
      type: Boolean,
      default: false
    }
  },
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    // --- 移除硬編碼的 Logo 和名稱映射 ---
    // const airlineLogos = { ... };
    // const airlineNames = { ... };
    // const getAirlineLogo = (code) => { ... };

    // 輔助函數：構建完整的 Logo URL
    const getFullLogoUrl = (logoPath) => {
        if (logoPath && typeof logoPath === 'string' && logoPath.trim() !== '') {
            if (logoPath.startsWith('http://') || logoPath.startsWith('https://')) {
                return logoPath;
            }
            const correctedPath = logoPath.startsWith('/') ? logoPath : `/${logoPath}`;
            return `${backendUrl}${correctedPath}`;
        }
        return null;
    };
    
    // 計算可用的航空公司列表，並添加航班數量信息
    const availableAirlines = computed(() => {
      if (!props.airlines || props.airlines.length === 0) {
        return [];
      }
      
      // 計算每個航空公司在當前搜索結果中的航班數量
      const flightCounts = {};
      if (props.flights && props.flights.length > 0) {
        props.flights.forEach(flight => {
          const airlineData = flight.airline;
          if (airlineData && airlineData.code) {
            const airlineCode = airlineData.code;
            if (!flightCounts[airlineCode]) {
              flightCounts[airlineCode] = 0;
            }
            flightCounts[airlineCode]++;
          }
        });
      }
      
      // 處理所有航空公司，添加航班數量信息
      const airlinesWithCounts = props.airlines.map(airline => ({
        code: airline.code,
        name: airline.name || airline.name_zh || airline.name_en || airline.code,
        logo: airline.logo_path,
        flightCount: flightCounts[airline.code] || 0,
        is_domestic: airline.is_domestic
      }));
      
      // 顯示所有航空公司，有航班的排在前面，然後按航班數量排序
      return airlinesWithCounts.sort((a, b) => {
        // 有航班的排在前面
        if (a.flightCount > 0 && b.flightCount === 0) return -1;
        if (a.flightCount === 0 && b.flightCount > 0) return 1;
        // 都有航班或都沒有航班時，按數量排序
        return b.flightCount - a.flightCount;
      });
    });

    const isSelected = (airlineCode) => {
      return props.modelValue.includes(airlineCode);
    };

    const toggleAirline = (airlineCode) => {
      const selected = [...props.modelValue];
      const index = selected.indexOf(airlineCode);

      if (index === -1) {
        // 添加航空公司
        selected.push(airlineCode);
      } else {
        // 移除航空公司，但至少要保留一個
        if (selected.length > 1) {
          selected.splice(index, 1);
        } else {
          // 如果只有一個選中的航空公司，不允許取消選擇
          console.log('至少需要選擇一個航空公司');
          return;
        }
      }

      emit('update:modelValue', selected);
    };
    
    const toggleAllAirlines = (event) => {
      if (event.target.checked) {
        // 選中所有有航班的航空公司
        const availableCodesWithFlights = availableAirlines.value
          .filter(a => a.flightCount > 0)
          .map(a => a.code);
        emit('update:modelValue', availableCodesWithFlights);
      } else {
        // 取消全選時，不能完全清空，至少要保留一個有航班的航空公司
        const availableCodesWithFlights = availableAirlines.value
          .filter(a => a.flightCount > 0)
          .map(a => a.code);
        
        if (availableCodesWithFlights.length > 0) {
          // 保留第一個有航班的航空公司
          emit('update:modelValue', [availableCodesWithFlights[0]]);
        } else {
          // 如果沒有任何有航班的航空公司，保持當前狀態
          console.log('沒有可用的航空公司航班');
        }
      }
    };

    const handleImageError = (event) => {
      event.target.src = '/path/to/default-image.jpg'; // 替換為實際的默認圖片路徑
    };

    return {
      availableAirlines,
      isSelected,
      toggleAirline,
      toggleAllAirlines,
      getFullLogoUrl,
      handleImageError
    };
  }
}
</script>

<style scoped>
input[type="checkbox"] {
  appearance: none;
  background-color: #fff;
  margin: 0;
  width: 1rem;
  height: 1rem;
  border: 1px solid #dee2e6; /* 使用中性灰色邊框，符合極簡 */
  display: grid;
  place-content: center;
}

input[type="checkbox"]:checked {
  background-color: #005F73; /* 使用指南中的主強調色 */
  border-color: #005F73;
}

input[type="checkbox"]::before {
  content: "";
  width: 0.5rem;
  height: 0.5rem;
  transform: scale(0);
  transition: 120ms transform ease-in-out; /* 快速輕量動畫 */
  box-shadow: inset 1rem 1rem #fff;
  transform-origin: center;
  clip-path: polygon(14% 44%, 0 65%, 50% 100%, 100% 16%, 80% 0%, 43% 62%);
}

input[type="checkbox"]:checked::before {
  transform: scale(1);
}

/* 增加對圖片旁邊文字的垂直對齊 */
label span {
  vertical-align: middle;
}
img {
  vertical-align: middle;
}
</style> 