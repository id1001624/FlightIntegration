<template>
  <div class="mb-6">
    <h4 class="text-base font-medium text-text-primary mb-3">航空公司</h4>
    
    <!-- 全選選項 -->
    <div class="mb-2 border-b pb-2" v-if="availableAirlines.length > 0">
      <label class="flex items-center cursor-pointer text-sm py-1">
        <input
          type="checkbox"
          :checked="modelValue.length === availableAirlines.length && availableAirlines.length > 0"
          @change="toggleAllAirlines"
          class="mr-3 h-4 w-4 border-gray-300 text-primary focus:ring-primary flex-shrink-0"
        />
        <span class="text-text-primary font-medium">所有航空公司</span>
      </label>
    </div>
    
    <div class="text-sm text-text-secondary py-2" v-if="loading">載入中...</div>
    <div class="text-sm text-text-secondary py-2" v-else-if="availableAirlines.length === 0">沒有可用的航空公司</div>
    <div v-else class="max-h-48 overflow-y-auto space-y-2.5 pr-2">
      <div
        v-for="airline in availableAirlines"
        :key="airline.code"
      >
        <label class="flex items-center cursor-pointer text-sm py-1">
          <input
            type="checkbox"
            :value="airline.code"
            :checked="isSelected(airline.code)"
            @change="toggleAirline(airline.code)"
            class="mr-3 h-4 w-4 border-gray-300 text-primary focus:ring-primary flex-shrink-0"
          />
          <span class="flex items-center text-text-primary flex-grow min-w-0">
            <img 
              v-if="getFullLogoUrl(airline.logo)" 
              :src="getFullLogoUrl(airline.logo)" 
              :alt="airline.name" 
              class="h-6 w-6 mr-2 object-contain flex-shrink-0"
            />
            <span v-else class="inline-block mr-2 w-6 h-6 flex-shrink-0"></span>
            <span class="truncate">{{ airline.name }}</span>
          </span>
          <span class="ml-auto text-xs text-text-secondary pl-2">({{ airline.flightCount || 0 }})</span>
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
    airlines: { // 原始傳入的航班列表，現在應為 flight 對象列表
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
    
    // 從航班列表中提取不重複的航空公司資訊，包含 logo_path
    const availableAirlines = computed(() => {
      if (!props.airlines || props.airlines.length === 0) {
        return [];
      }
      
      const seenCodes = new Set();
      const uniqueAirlines = [];
      const flightCounts = {};
      
      props.airlines.forEach(flight => {
        const airlineData = flight.airline; // 直接從 flight.airline 取數據
        
        if (airlineData && airlineData.code) {
          const airlineCode = airlineData.code;
          const airlineName = airlineData.name || airlineData.name_zh || '未知航空';
          const airlineLogoPath = airlineData.logo_path || null; // 獲取 logo_path

          // 計算航班數量
          if (!flightCounts[airlineCode]) {
            flightCounts[airlineCode] = 0;
          }
          flightCounts[airlineCode]++;
          
          // 添加唯一的航空公司
          if (!seenCodes.has(airlineCode)) {
            seenCodes.add(airlineCode);
            uniqueAirlines.push({ 
              code: airlineCode, 
              name: airlineName,
              logo: airlineLogoPath // 存儲 logo_path
              // flightCount 將在後面添加
            });
          }
        } else {
          // 可以記錄或處理缺少 airline data 的情況
          console.warn('Flight data missing airline information:', flight);
        }
      });
      
      // 添加航班數量信息
      uniqueAirlines.forEach(airline => {
        airline.flightCount = flightCounts[airline.code] || 0;
      });
      
      // 按航班數量降序排序
      return uniqueAirlines.sort((a, b) => b.flightCount - a.flightCount);
    });

    const isSelected = (airlineCode) => {
      return props.modelValue.includes(airlineCode);
    };

    const toggleAirline = (airlineCode) => {
      const selected = [...props.modelValue];
      const index = selected.indexOf(airlineCode);

      if (index === -1) {
        selected.push(airlineCode);
      } else {
        selected.splice(index, 1);
      }

      emit('update:modelValue', selected);
    };
    
    const toggleAllAirlines = (event) => {
      if (event.target.checked) {
        const allCodes = availableAirlines.value.map(a => a.code);
        emit('update:modelValue', allCodes);
      } else {
        emit('update:modelValue', []);
      }
    };

    return {
      availableAirlines,
      isSelected,
      toggleAirline,
      toggleAllAirlines,
      getFullLogoUrl // 暴露給模板使用
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