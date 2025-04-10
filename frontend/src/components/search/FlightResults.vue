<template>
  <div class="min-h-[200px]">
    <!-- 搜索結果數量和提示 -->
    <div class="flex justify-between items-center mb-6 flex-col md:flex-row gap-4 md:gap-0" v-if="flights && flights.length > 0">
      <div>
        <h2 class="text-xl font-semibold m-0 mb-1">搜索結果</h2>
        <p class="m-0 text-text-secondary text-sm">{{ flights.length }} 個航班</p>
      </div>
      <div class="flex items-center gap-2 w-full md:w-auto">
        <label for="sort-select" class="text-sm text-text-secondary">排序：</label>
        <select 
          id="sort-select" 
          v-model="sortOption" 
          @change="sortFlights"
          class="input py-1.5 w-full md:w-auto"
        >
          <option value="price-asc">價格：由低至高</option>
          <option value="price-desc">價格：由高至低</option>
          <option value="departure-asc">出發時間：最早優先</option>
          <option value="departure-desc">出發時間：最晚優先</option>
          <option value="duration-asc">飛行時間：最短優先</option>
        </select>
      </div>
    </div>

    <!-- 航班列表 -->
    <div v-if="flights && flights.length > 0">
      <FlightList :flights="sortedFlights" />
    </div>

    <!-- 無搜索結果時顯示 -->
    <div class="flex justify-center items-center p-12 text-center bg-white rounded-lg shadow-sm" v-else-if="searched && (!flights || flights.length === 0)">
      <div class="max-w-md flex flex-col items-center">
        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round" class="text-gray-400 mb-6">
          <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path>
          <line x1="4.93" y1="4.93" x2="19.07" y2="19.07"></line>
        </svg>
        <h3 class="text-lg font-semibold m-0 mb-1">沒有找到符合條件的航班</h3>
        <p class="m-0 mb-6 text-text-secondary">請嘗試修改搜索條件或日期</p>
        <div class="flex flex-col gap-4 items-start mt-4 text-left">
          <div class="flex items-center gap-2 text-text-primary text-sm">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-text-secondary">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="12" y1="8" x2="12" y2="16"></line>
              <line x1="8" y1="12" x2="16" y2="12"></line>
            </svg>
            <span>選擇不同的出發/目的地機場</span>
          </div>
          <div class="flex items-center gap-2 text-text-primary text-sm">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-text-secondary">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="12" y1="8" x2="12" y2="16"></line>
              <line x1="8" y1="12" x2="16" y2="12"></line>
            </svg>
            <span>嘗試附近日期</span>
          </div>
          <div class="flex items-center gap-2 text-text-primary text-sm">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-text-secondary">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="12" y1="8" x2="12" y2="16"></line>
              <line x1="8" y1="12" x2="16" y2="12"></line>
            </svg>
            <span>移除價格或航空公司篩選</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 尚未搜索時顯示 -->
    <div class="flex justify-center items-center p-12 text-center bg-white rounded-lg shadow-sm" v-else-if="!searched">
      <div class="max-w-md flex flex-col items-center">
        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round" class="text-gray-400 mb-6">
          <path d="M22 2L11 13"></path>
          <path d="M22 2L15 22L11 13L2 9L22 2Z"></path>
        </svg>
        <h3 class="text-lg font-semibold m-0 mb-1">搜索航班以查看結果</h3>
        <p class="m-0 text-text-secondary">請選擇出發地、目的地和日期</p>
      </div>
    </div>
  </div>
</template>

<script>
import FlightList from './FlightList.vue';
import { ref, computed } from 'vue';

export default {
  name: 'FlightResults',
  components: {
    FlightList
  },
  props: {
    flights: {
      type: Array,
      default: () => []
    },
    searched: {
      type: Boolean,
      default: false
    }
  },
  emits: ['sort-change'],
  setup(props, { emit }) {
    const sortOption = ref('price-asc');
    
    const sortedFlights = computed(() => {
      if (!props.flights || props.flights.length === 0) {
        return [];
      }
      
      // 創建一個新的數組來進行排序，不修改原數組
      const sorted = [...props.flights];
      
      switch (sortOption.value) {
        case 'price-asc':
          return sorted.sort((a, b) => parseFloat(a.price || a.ticket_price || 0) - parseFloat(b.price || b.ticket_price || 0));
        
        case 'price-desc':
          return sorted.sort((a, b) => parseFloat(b.price || b.ticket_price || 0) - parseFloat(a.price || a.ticket_price || 0));
        
        case 'departure-asc':
          return sorted.sort((a, b) => {
            const dateA = new Date(a.departure_time || a.scheduled_departure);
            const dateB = new Date(b.departure_time || b.scheduled_departure);
            return dateA - dateB;
          });
        
        case 'departure-desc':
          return sorted.sort((a, b) => {
            const dateA = new Date(a.departure_time || a.scheduled_departure);
            const dateB = new Date(b.departure_time || b.scheduled_departure);
            return dateB - dateA;
          });
        
        case 'duration-asc':
          return sorted.sort((a, b) => {
            // 優先使用已有的 duration 屬性 (假設是分鐘)
            if (a.duration && b.duration && typeof a.duration === 'number' && typeof b.duration === 'number') {
              return a.duration - b.duration;
            }
            
            // 如果沒有分鐘形式，則嘗試解析時間字符串
            const getDuration = (flight) => {
              if (!flight.flight_time) return 0;
              
              const parts = flight.flight_time.split('h');
              if (parts.length < 2) return 0;
              
              const hours = parseInt(parts[0].trim(), 10) || 0;
              const minutes = parseInt(parts[1].replace('m', '').trim(), 10) || 0;
              
              return hours * 60 + minutes;
            };
            
            return getDuration(a) - getDuration(b);
          });
        
        default:
          return sorted;
      }
    });

    const sortFlights = () => {
      // 觸發通知外部組件排序已經變更
      emit('sort-change', sortOption.value);
    };

    return {
      sortOption,
      sortedFlights,
      sortFlights
    };
  }
};
</script> 