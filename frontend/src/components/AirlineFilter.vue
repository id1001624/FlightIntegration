<template>
  <div class="mb-6">
    <h4 class="text-base font-medium text-text-primary mb-3">航空公司</h4>
    
    <!-- 全選選項 -->
    <div class="mb-2 border-b pb-2" v-if="availableAirlines.length > 0">
      <label class="flex items-center cursor-pointer text-sm">
        <input
          type="checkbox"
          :checked="modelValue.length === availableAirlines.length && availableAirlines.length > 0"
          @change="toggleAllAirlines"
          class="mr-2 h-4 w-4 border-gray-300 text-primary focus:ring-primary"
        />
        <span class="text-text-primary font-medium">所有航空公司</span>
      </label>
    </div>
    
    <div class="text-sm text-text-secondary py-2" v-if="loading">載入中...</div>
    <div class="text-sm text-text-secondary py-2" v-else-if="availableAirlines.length === 0">沒有可用的航空公司</div>
    <div v-else class="max-h-48 overflow-y-auto space-y-2 pr-2">
      <div
        v-for="airline in availableAirlines"
        :key="airline.code"
      >
        <label class="flex items-center cursor-pointer text-sm">
          <input
            type="checkbox"
            :value="airline.code"
            :checked="isSelected(airline.code)"
            @change="toggleAirline(airline.code)"
            class="mr-2 h-4 w-4 border-gray-300 text-primary focus:ring-primary"
          />
          <span class="flex items-center text-text-primary">
            <img 
              v-if="airline.logo" 
              :src="airline.logo" 
              :alt="airline.name" 
              class="h-4 w-4 mr-1.5 object-contain"
            />
            <span v-else-if="getAirlineLogo(airline.code)" 
              class="inline-block mr-1.5 w-4 h-4" 
              :style="`background-image: url('${getAirlineLogo(airline.code)}'); background-size: contain; background-repeat: no-repeat;`"
            ></span>
            {{ airline.name }} ({{ airline.flightCount || 0 }})
          </span>
        </label>
      </div>
    </div>
  </div>
</template>

<script>
import { computed, ref } from 'vue';

export default {
  name: 'AirlineFilter',
  props: {
    airlines: { // 原始傳入的航班列表
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
    // 常見航空公司標誌和名稱映射
    const airlineLogos = {
      'CI': '/logos/china-airlines.png',
      'BR': '/logos/eva-air.png',
      'CX': '/logos/cathay-pacific.png',
      'JL': '/logos/japan-airlines.png',
      'NH': '/logos/ana.png',
      'KE': '/logos/korean-air.png',
      'OZ': '/logos/asiana-airlines.png',
      'SQ': '/logos/singapore-airlines.png',
      'MU': '/logos/china-eastern.png',
      'CA': '/logos/air-china.png',
      'CZ': '/logos/china-southern.png',
      'FM': '/logos/shanghai-airlines.png'
    };
    
    const airlineNames = {
      'CI': '中華航空',
      'BR': '長榮航空',
      'AE': '華信航空',
      'B7': '立榮航空',
      'CX': '國泰航空',
      'JL': '日本航空',
      'NH': '全日空航空',
      'KE': '大韓航空',
      'OZ': '韓亞航空',
      'SQ': '新加坡航空',
      'MU': '東方航空',
      'CA': '中國國際航空',
      'CZ': '南方航空',
      'FM': '上海航空',
      'NX': '澳門航空',
      'HX': '香港航空',
      'TG': '泰國航空',
      'VN': '越南航空'
    };
    
    // 獲取航空公司標誌
    const getAirlineLogo = (code) => {
      return airlineLogos[code] || null;
    };
    
    // 從航班列表中提取不重複的航空公司資訊
    const availableAirlines = computed(() => {
      if (!props.airlines || props.airlines.length === 0) {
        // 如果沒有航班數據，返回空數組或常見航空公司
        return [];
      }
      
      const seenCodes = new Set();
      const uniqueAirlines = [];
      const flightCounts = {};
      
      props.airlines.forEach(flight => {
        // 嘗試所有可能的航空公司代碼字段
        let airlineCode = null;
        let airlineName = null;
        
        // 檢查各種可能的字段路徑
        if (flight.airline_code) {
          airlineCode = flight.airline_code;
        } else if (flight.airline && flight.airline.code) {
          airlineCode = flight.airline.code;
        } else if (flight.carrier_code) {
          airlineCode = flight.carrier_code;
        } else if (flight.flight_number && flight.flight_number.length >= 2) {
          // 嘗試從航班號提取航空公司代碼 (通常前2字母/數字)
          airlineCode = flight.flight_number.substring(0, 2);
        }
        
        // 檢查航空公司名稱
        if (flight.airline_name) {
          airlineName = flight.airline_name;
        } else if (flight.airline && flight.airline.name) {
          airlineName = flight.airline.name;
        } else if (airlineCode && airlineNames[airlineCode]) {
          airlineName = airlineNames[airlineCode];
        } else {
          airlineName = '未知航空公司';
        }
        
        // 計算每個航空公司的航班數量
        if (airlineCode) {
          if (!flightCounts[airlineCode]) {
            flightCounts[airlineCode] = 0;
          }
          flightCounts[airlineCode]++;
        }
        
        // 只添加有效的航空公司
        if (airlineCode && !seenCodes.has(airlineCode)) {
          seenCodes.add(airlineCode);
          uniqueAirlines.push({ 
            code: airlineCode, 
            name: airlineName,
            logo: null // 將在後面設置
          });
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
        // 全選
        const allCodes = availableAirlines.value.map(a => a.code);
        emit('update:modelValue', allCodes);
      } else {
        // 取消全選
        emit('update:modelValue', []);
      }
    };

    return {
      availableAirlines,
      isSelected,
      toggleAirline,
      toggleAllAirlines,
      getAirlineLogo
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
  border: 1px solid #dee2e6;
  display: grid;
  place-content: center;
}

input[type="checkbox"]:checked {
  background-color: #005F73;
  border-color: #005F73;
}

input[type="checkbox"]::before {
  content: "";
  width: 0.5rem;
  height: 0.5rem;
  transform: scale(0);
  transition: 120ms transform ease-in-out;
  box-shadow: inset 1rem 1rem #fff;
  transform-origin: center;
  clip-path: polygon(14% 44%, 0 65%, 50% 100%, 100% 16%, 80% 0%, 43% 62%);
}

input[type="checkbox"]:checked::before {
  transform: scale(1);
}
</style> 