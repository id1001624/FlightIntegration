<template>
  <div class="min-h-[200px]">
    <!-- 只有在搜索過且有結果時才顯示標題和排序 -->
    <div class="flex justify-between items-center mb-6 flex-col md:flex-row gap-4 md:gap-0" v-if="searched && sortedFlights.length > 0">
      <div>
        <h2 class="text-xl font-semibold m-0 mb-1">搜索結果</h2>
        <p class="m-0 text-text-secondary text-sm">{{ sortedFlights.length }} 個航班</p>
      </div>
      <div class="flex items-center gap-2 w-full md:w-auto">
        <label for="sort-select" class="text-sm text-text-secondary">排序：</label>
        <select 
          id="sort-select" 
          v-model="sortOption" 
          @change="sortFlights"
          class="input py-1.5 w-full md:w-auto border-gray-300 focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-50"
        >
          <option value="price-asc">價格：由低至高</option>
          <option value="price-desc">價格：由高至低</option>
          <option value="departure-asc">出發時間：最早優先</option>
          <option value="departure-desc">出發時間：最晚優先</option>
          <option value="duration-asc">飛行時間：最短優先</option>
        </select>
      </div>
    </div>

    <!-- 只有在搜索過且有結果時才顯示航班列表 -->
    <div v-if="searched && sortedFlights.length > 0">
      <FlightList :flights="sortedFlights" />
    </div>

    <!-- 只有在搜索過但無結果時才顯示提示 -->
    <div class="flex justify-center items-center p-12 text-center bg-white shadow-sm" v-else-if="searched && sortedFlights.length === 0">
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

    <!-- 只有在尚未搜索時才顯示提示 -->
    <div class="flex justify-center items-center p-12 text-center bg-white shadow-sm" v-else-if="!searched">
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
import { ref, computed, watch } from 'vue';

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
      console.log('[FlightResults] Computing sortedFlights. Input flights:', props.flights.length);
      if (!props.flights || props.flights.length === 0) {
        return [];
      }
      
      const sorted = [...props.flights];
      const option = sortOption.value;
      console.log(`[FlightResults] Sorting by: ${option}`);

      try {
        sorted.sort((a, b) => {
          let comparison = 0;
          switch (option) {
            case 'price-asc':
            case 'price-desc':
              const priceA = a.price?.amount;
              const priceB = b.price?.amount;
              // 確保價格正確轉換為數字進行比較（處理字串和數字）
              const valA = (priceA !== null && priceA !== undefined) ? parseFloat(priceA) : Infinity; 
              const valB = (priceB !== null && priceB !== undefined) ? parseFloat(priceB) : Infinity;
              // 檢查轉換後是否為有效數字
              const finalA = isNaN(valA) ? Infinity : valA;
              const finalB = isNaN(valB) ? Infinity : valB;
              comparison = finalA - finalB;
              if (option === 'price-desc') comparison = -comparison;
              console.log(`[Sort Price] A: ${priceA} (${finalA}), B: ${priceB} (${finalB}), Comparison: ${comparison}`);
              break;
            case 'departure-asc':
            case 'departure-desc':
              const timeA = a.departure?.time;
              const timeB = b.departure?.time;
              // 嘗試轉換為 Date 對象，無效則視為 0 或最大值
              const dateA = timeA ? new Date(timeA).getTime() : (option === 'departure-asc' ? Infinity : 0); 
              const dateB = timeB ? new Date(timeB).getTime() : (option === 'departure-asc' ? Infinity : 0);
              comparison = (isNaN(dateA) ? (option === 'departure-asc' ? Infinity : 0) : dateA) - (isNaN(dateB) ? (option === 'departure-asc' ? Infinity : 0) : dateB);
              if (option === 'departure-desc') comparison = -comparison;
              // console.log(`[Sort DepTime] A: ${timeA}, B: ${timeB}, dA: ${dateA}, dB: ${dateB}, Comp: ${comparison}`);
              break;
            case 'duration-asc':
              const durationA = a.duration_minutes;
              const durationB = b.duration_minutes;
              const durA = (typeof durationA === 'number') ? durationA : Infinity;
              const durB = (typeof durationB === 'number') ? durationB : Infinity;
              comparison = durA - durB;
              // console.log(`[Sort Duration] A: ${durationA}, B: ${durationB}, Comp: ${comparison}`);
              break;
          }
          // console.log(`Comparing ${a.flight_number} and ${b.flight_number}: ${comparison}`);
          return comparison;
        });
      } catch (error) {
        console.error('[FlightResults] Error during sorting:', error, sorted);
        return []; // 出錯時返回空數組
      }

      console.log('[FlightResults] Sorting finished. Result length:', sorted.length);
      return sorted;
    });

    // 添加 watch 來監控 sortedFlights 的變化
    watch(sortedFlights, (newValue) => {
      console.log('[FlightResults] sortedFlights updated:', newValue.length, newValue);
    }, { immediate: true }); // immediate: true 確保初始值也被記錄

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
</style> 