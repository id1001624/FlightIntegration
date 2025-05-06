<template>
  <div class="container mx-auto px-4 py-8">
    <router-link to="/flight-search" class="text-primary hover:text-primary-dark mb-6 inline-flex items-center text-sm">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1" viewBox="0 0 20 20" fill="currentColor">
        <path fill-rule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clip-rule="evenodd" />
      </svg>
      返回搜索結果
    </router-link>

    <h1 class="text-2xl font-bold mb-6 text-text-primary">航班詳情</h1>
    
    <div v-if="loading" class="flex justify-center items-center h-64">
      <div class="flight-detail-loader">
        <div class="journey-visual">
          <div class="skeleton departure"></div>
          <div class="skeleton arrival"></div>
          
          <div class="flight-path">
            <div class="departure-dot"></div>
            <div class="path-line">
              <div class="path-progress"></div>
            </div>
            <div class="arrival-dot"></div>
          </div>
          
          <div class="skeleton depart-info"></div>
          <div class="skeleton arrive-info"></div>
        </div>
        <p class="loader-text">載入航班詳情...</p>
      </div>
    </div>
    
    <div v-else-if="error" class="text-center py-10 bg-red-50 border border-red-200 rounded-lg">
      <p class="text-red-700 font-semibold">加載航班詳情失敗</p>
      <p class="text-red-600 mt-2">{{ error }}</p>
      <router-link to="/flight-search" class="mt-4 inline-block px-4 py-2 bg-primary text-white rounded hover:bg-primary-dark text-sm">
        重新搜索
      </router-link>
    </div>
    
    <div v-else-if="flight">
      <FlightDetailCard :initial-flight="flight" />
    </div>
    
    <div v-else class="text-center py-10 bg-gray-50 border border-gray-200 rounded-lg">
      <p class="text-text-secondary">找不到您請求的航班信息。</p>
      <router-link to="/flight-search" class="mt-4 inline-block px-4 py-2 bg-primary text-white rounded hover:bg-primary-dark text-sm">
        返回搜索
      </router-link>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import flightService from '@/api/services/flightService'; // 確保路徑正確
import FlightDetailCard from '@/components/specific/FlightDetailCard.vue'; // 確保路徑正確

const route = useRoute();
const router = useRouter(); 
const flightId = ref(route.params.flight_id);
const flight = ref(null);
const loading = ref(true);
const error = ref(null);

const fetchFlightDetails = async (id) => {
  loading.value = true;
  error.value = null;
  flight.value = null; // 重置 flight
  try {
    console.log(`[FlightDetail] Fetching details for flight ID: ${id}`);
    const data = await flightService.getFlightDetails(id);
    flight.value = data; // 後端直接返回 data 對象
    if (!flight.value) {
      throw new Error('從服務器返回的航班數據無效');
    }
    console.log('[FlightDetail] Successfully fetched flight details:', flight.value);
  } catch (err) {
    console.error("[FlightDetail] 獲取航班詳情出錯:", err);
    // 嘗試從錯誤對象中提取後端返回的消息
    error.value = err?.response?.data?.message || err?.message || '加載航班數據時發生未知錯誤';
    // 如果是 404 錯誤，可以考慮跳轉回列表或顯示特定消息
    if (err?.response?.status === 404) {
       error.value = '找不到指定的航班信息。';
       // 可以選擇在這裡導航回上一頁或搜索頁
       // setTimeout(() => router.push('/flight-search'), 3000);
    }
  } finally {
    loading.value = false;
  }
};

// 組件掛載時獲取數據
onMounted(() => {
  if (flightId.value) { // 確保 flightId 存在
    fetchFlightDetails(flightId.value);
  } else {
      console.error('[FlightDetail] Missing flight_id in route params');
      error.value = '缺少航班 ID';
      loading.value = false;
  }
});

// 監聽路由參數變化 (如果用戶在詳情頁之間跳轉)
watch(() => route.params.flight_id, (newId) => {
  if (newId) {
    flightId.value = newId;
    fetchFlightDetails(newId);
  }
});
</script>

<style scoped>
/* Structured Journey Minimalism: Use Tailwind utilities, avoid custom scoped styles unless necessary */
.container {
  max-width: 960px; /* Limit content width for readability */
}

/* 航班詳情加載動畫 */
.flight-detail-loader {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2rem;
  padding: 3rem 0;
}

.journey-visual {
  position: relative;
  width: 12rem;
  height: 4rem;
}

.skeleton {
  position: absolute;
  height: 1rem;
  background-color: #e5e7eb;
  border-radius: 0.25rem;
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

.departure {
  top: 0;
  left: 0;
  width: 3rem;
}

.arrival {
  top: 0;
  right: 0;
  width: 3rem;
}

.depart-info {
  bottom: 0;
  left: 0;
  width: 4rem;
}

.arrive-info {
  bottom: 0;
  right: 0;
  width: 4rem;
}

.flight-path {
  position: absolute;
  top: 50%;
  left: 0;
  width: 100%;
  display: flex;
  align-items: center;
}

.departure-dot {
  width: 1.5rem;
  height: 1.5rem;
  background-color: #005F73;
  border-radius: 9999px;
  animation: bounce 1.5s infinite;
}

.path-line {
  flex: 1;
  height: 1px;
  background-color: #d1d5db;
  margin: 0 0.5rem;
  position: relative;
  overflow: hidden;
}

.path-progress {
  position: absolute;
  top: 0;
  bottom: 0;
  background-color: #005F73;
  width: 30%;
  animation: progress 1.5s infinite;
}

.arrival-dot {
  width: 1.5rem;
  height: 1.5rem;
  background-color: #F4A261;
  border-radius: 9999px;
  animation: bounce 1.5s infinite 0.3s;
}

.loader-text {
  color: #6C757D;
  font-weight: 500;
  font-size: 0.875rem;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-4px); }
}

@keyframes progress {
  0% { left: -33%; width: 30%; }
  100% { left: 100%; width: 10%; }
}
</style>
