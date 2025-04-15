<template>
  <div class="bg-white shadow-card rounded-lg p-6 md:p-8 border border-gray-200">
    <!-- Header: Airline, Flight Number, Status, Refresh Button -->
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 pb-4 border-b border-gray-200">
      <div class="mb-3 sm:mb-0">
        <div class="flex items-center space-x-3 mb-2">
          <img :src="flightData.airline?.logo_url || defaultLogo" alt="Airline Logo" class="h-8 w-8 object-contain rounded-full border border-gray-100" />
          <span class="text-xl font-semibold text-text-primary">{{ flightData.airline?.name }} {{ flightData.flight_number }}</span>
        </div>
        <span :class="statusClass" class="text-sm font-medium px-2.5 py-1 rounded-full inline-block">
          {{ currentStatus || '未知' }}
        </span>
      </div>
      <button
        @click="handleRefreshStatus"
        :disabled="isRefreshing"
        class="btn btn-secondary text-sm flex items-center w-full sm:w-auto justify-center"
        :class="{ 'opacity-50 cursor-not-allowed': isRefreshing }"
      >
        <svg v-if="isRefreshing" class="animate-spin -ml-1 mr-2 h-4 w-4 text-current" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 00-15.357-2m15.357 2H15" />
        </svg>
        {{ isRefreshing ? '正在刷新...' : '刷新狀態' }}
      </button>
    </div>

    <!-- Refresh Status Info -->
    <div v-if="refreshError || lastRefreshedAt" class="mb-4 p-3 rounded-md text-xs"
         :class="refreshError ? 'bg-red-50 text-red-700 border border-red-200' : 'bg-blue-50 text-blue-700 border border-blue-200'">
      <p v-if="refreshError">刷新狀態失敗: {{ refreshError }}</p>
      <p v-if="lastRefreshedAt">上次狀態更新於: {{ formatDateTime(lastRefreshedAt) }} (來源: {{ refreshSource || '未知' }})</p>
    </div>

    <!-- Flight Path Visualization (Minimalist Line) -->
    <div class="flex items-center justify-between mb-6 px-4">
        <div class="text-center">
            <div class="text-lg font-semibold text-text-primary">{{ flightData.departure?.code }}</div>
            <div class="text-xs text-text-secondary">{{ flightData.departure?.city }}</div>
        </div>
        <div class="flex-grow mx-4 h-px bg-gray-200 relative">
           <svg class="absolute left-1/2 top-1/2 transform -translate-x-1/2 -translate-y-1/2 h-5 w-5 text-primary" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 12 3.269 3.125A59.769 59.769 0 0 1 21.485 12 59.768 59.768 0 0 1 3.27 20.875L5.999 12Zm0 0h7.5" />
            </svg>
        </div>
        <div class="text-center">
            <div class="text-lg font-semibold text-text-primary">{{ flightData.arrival?.code }}</div>
             <div class="text-xs text-text-secondary">{{ flightData.arrival?.city }}</div>
        </div>
    </div>

    <!-- Details Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-x-8 gap-y-6">
      <!-- Departure Info -->
      <div class="space-y-1">
        <h3 class="text-base font-medium text-text-secondary mb-1 border-b pb-1">出發資訊</h3>
        <p class="text-sm"><strong class="font-medium text-text-primary">機場:</strong> {{ flightData.departure?.name }} ({{ flightData.departure?.code }})</p>
        <p class="text-sm"><strong class="font-medium text-text-primary">城市:</strong> {{ flightData.departure?.city }}, {{ flightData.departure?.country }}</p>
        <p class="text-sm"><strong class="font-medium text-text-primary">計劃時間:</strong> {{ formatDateTime(flightData.departure?.scheduled_time) }}</p>
        <p v-if="currentActualDepartureTime" class="text-sm text-green-700">
          <strong class="font-medium text-green-700">實際時間:</strong> {{ formatDateTime(currentActualDepartureTime) }}
        </p>
         <p class="text-sm"><strong class="font-medium text-text-primary">航廈/登機門:</strong> {{ formatTerminalGate(currentTerminal || flightData.departure?.terminal, currentGate || flightData.departure?.gate) }}</p>
      </div>

      <!-- Arrival Info -->
       <div class="space-y-1">
        <h3 class="text-base font-medium text-text-secondary mb-1 border-b pb-1">抵達資訊</h3>
        <p class="text-sm"><strong class="font-medium text-text-primary">機場:</strong> {{ flightData.arrival?.name }} ({{ flightData.arrival?.code }})</p>
        <p class="text-sm"><strong class="font-medium text-text-primary">城市:</strong> {{ flightData.arrival?.city }}, {{ flightData.arrival?.country }}</p>
        <p class="text-sm"><strong class="font-medium text-text-primary">計劃時間:</strong> {{ formatDateTime(flightData.arrival?.scheduled_time) }}</p>
         <p v-if="currentActualArrivalTime" class="text-sm text-green-700">
            <strong class="font-medium text-green-700">實際時間:</strong> {{ formatDateTime(currentActualArrivalTime) }}
         </p>
         <p class="text-sm"><strong class="font-medium text-text-primary">航廈/登機門:</strong> {{ formatTerminalGate(currentTerminal || flightData.arrival?.terminal, currentGate || flightData.arrival?.gate) }} </p>
      </div>

      <!-- Flight Info -->
       <div class="space-y-1">
        <h3 class="text-base font-medium text-text-secondary mb-1 border-b pb-1">航班資訊</h3>
        <p class="text-sm"><strong class="font-medium text-text-primary">飛行時間:</strong> {{ formatDuration(flightData.duration_minutes) }}</p>
        <p class="text-sm"><strong class="font-medium text-text-primary">機型:</strong> {{ flightData.aircraft || 'N/A' }}</p>
        <p class="text-sm"><strong class="font-medium text-text-primary">類型:</strong> {{ flightData.is_domestic ? '國內線' : '國際線' }}</p>
      </div>
    </div>

    <!-- Prices -->
    <div class="mt-8 pt-6 border-t border-gray-200">
      <h3 class="text-lg font-semibold text-text-primary mb-3">票價資訊</h3>
      <div v-if="flightData.prices && flightData.prices.length > 0" class="space-y-2">
        <div v-for="(price, index) in flightData.prices" :key="index"
             class="flex justify-between items-center text-sm p-3 rounded-md bg-gray-50 border border-gray-100">
          <span class="font-medium text-text-secondary">{{ price.class_type }}</span>
          <span class="font-semibold text-lg text-primary">{{ price.currency }} {{ price.price?.toLocaleString() }}</span>
          <span class="text-xs text-gray-500">剩餘 {{ price.available_seats }} 位</span>
        </div>
      </div>
      <p v-else class="text-sm text-text-secondary">暫無可用票價資訊。</p>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, reactive, watch } from 'vue';
import flightService from '@/api/services/flightService'; // 確保路徑正確
import defaultLogo from '@/assets/images/default-airline.png'; // 確保你有預設圖片

const props = defineProps({
  initialFlight: {
    type: Object,
    required: true
  }
});

// 使用 reactive 來存儲航班數據，這樣可以方便地更新整個對象
// 但對於需要單獨更新的狀態（如 status, actual times），使用 ref 更清晰
const flightData = reactive({ ...props.initialFlight });

// 使用 ref 來管理會被刷新的狀態
const currentStatus = ref(props.initialFlight.status);
const currentStatusEn = ref(props.initialFlight.status_en); // 存儲英文狀態用於樣式計算
const currentActualDepartureTime = ref(props.initialFlight.departure?.actual_time);
const currentActualArrivalTime = ref(props.initialFlight.arrival?.actual_time);
const currentGate = ref(props.initialFlight.departure?.gate || props.initialFlight.arrival?.gate); // 注意：Gate/Terminal 可能不同
const currentTerminal = ref(props.initialFlight.departure?.terminal || props.initialFlight.arrival?.terminal);

const isRefreshing = ref(false);
const refreshError = ref(null);
const lastRefreshedAt = ref(null);
const refreshSource = ref('');

// 監聽 initialFlight prop 的變化
watch(() => props.initialFlight, (newFlight) => {
  console.log('[FlightDetailCard] Prop updated:', newFlight);
  // 更新整個 flightData (如果需要顯示其他不變信息)
  Object.assign(flightData, newFlight);
  // 更新可刷新的狀態
  currentStatus.value = newFlight.status;
  currentStatusEn.value = newFlight.status_en;
  currentActualDepartureTime.value = newFlight.departure?.actual_time;
  currentActualArrivalTime.value = newFlight.arrival?.actual_time;
  currentGate.value = newFlight.departure?.gate || newFlight.arrival?.gate; // 或更複雜的邏輯
  currentTerminal.value = newFlight.departure?.terminal || newFlight.arrival?.terminal;

  // 重置刷新相關狀態
  isRefreshing.value = false;
  refreshError.value = null;
  lastRefreshedAt.value = null;
  refreshSource.value = '';
}, { deep: true });

const handleRefreshStatus = async () => {
  if (!flightData.flight_id) {
    refreshError.value = '缺少航班 ID，無法刷新';
    return;
  }
  isRefreshing.value = true;
  refreshError.value = null;
  try {
    console.log(`[FlightDetailCard] Refreshing status for flight ID: ${flightData.flight_id}`);
    const updatedStatusInfo = await flightService.refreshFlightStatus(flightData.flight_id);
    console.log('[FlightDetailCard] Received refreshed status:', updatedStatusInfo);

    // 更新本地狀態
    currentStatus.value = updatedStatusInfo.status;
    currentStatusEn.value = updatedStatusInfo.status_en;
    currentActualDepartureTime.value = updatedStatusInfo.actual_departure_time;
    currentActualArrivalTime.value = updatedStatusInfo.actual_arrival_time;
    // 刷新時可能需要更智能地決定更新哪個 gate/terminal
    // 這裡簡單地用刷新結果覆蓋，可能不完全準確
    currentGate.value = updatedStatusInfo.gate;
    currentTerminal.value = updatedStatusInfo.terminal;
    lastRefreshedAt.value = updatedStatusInfo.retrieved_at;
    refreshSource.value = updatedStatusInfo.source;

  } catch (err) {
    console.error("[FlightDetailCard] 刷新航班狀態失敗:", err);
    refreshError.value = err?.response?.data?.message || err?.message || '刷新時發生未知錯誤';
  } finally {
    isRefreshing.value = false;
  }
};

// --- Helper Functions ---
const formatDateTime = (dateTimeString) => {
  if (!dateTimeString) return '--:--'; // 返回佔位符而非 N/A
  try {
    const dt = new Date(dateTimeString);
    return dt.toLocaleString('zh-TW', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false }).replace(/\//g, '-');
  } catch (e) {
    return '日期無效';
  }
};

const formatDuration = (minutes) => {
  if (minutes === null || minutes === undefined || isNaN(minutes)) return '--';
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return `${h}小時 ${m}分鐘`;
};

const formatTerminalGate = (terminal, gate) => {
    const t = terminal || '--';
    const g = gate || '--';
    return `${t} / ${g}`;
}

// 計算狀態顯示樣式
const statusClass = computed(() => {
  // 使用 currentStatusEn (英文狀態碼) 來決定樣式
  const status = currentStatusEn.value?.toUpperCase();
  switch (status) {
    case 'L': // Arrived
    case 'A': // Departed/In Air
      return 'bg-green-100 text-green-800 border border-green-200';
    case 'D': // Delayed
    case 'DN':
    case 'R': // Redirected
      return 'bg-yellow-100 text-yellow-800 border border-yellow-200';
    case 'C': // Cancelled
    case 'NO': // Not Operational
      return 'bg-red-100 text-red-800 border border-red-200';
    case 'S': // Scheduled
    case 'U': // Unknown
    default:
      return 'bg-blue-100 text-blue-800 border border-blue-200';
  }
});

</script>

<style scoped>
/* Structured Journey Minimalism: Primarily use Tailwind utilities. */
/* Add minor custom styles only if absolutely necessary. */
</style>
