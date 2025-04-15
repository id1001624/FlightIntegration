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
      <!-- Tailwind doesn't have a default spinner, use a simple one or a library -->
      <div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
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
</style>
