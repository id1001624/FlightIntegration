import { ref, watch } from 'vue';
import { getAirports, getDestinations } from '@/api/services/flightService';

export function useAirportManagement(searchParams) {
  const taiwanAirports = ref([]);
  const destinationAirports = ref([]);
  const loadingTaiwanAirports = ref(false);
  const loadingDestinations = ref(false);

  // 獲取台灣機場列表
  const fetchTaiwanAirports = async () => {
    if (taiwanAirports.value.length > 0) return;
    loadingTaiwanAirports.value = true;
    try {
      // 在我們的專案中，getAirports()會返回所有機場，我們在前端過濾
      const allAirports = await getAirports();
      taiwanAirports.value = allAirports.filter(a => a.country === 'Taiwan');
    } catch (error) {
      console.error('獲取台灣機場失敗:', error);
    } finally {
      loadingTaiwanAirports.value = false;
    }
  };

  // 根據出發地獲取目的地機場列表
  const fetchDestinations = async (departureCode) => {
    if (!departureCode) {
      destinationAirports.value = [];
      return;
    }
    loadingDestinations.value = true;
    destinationAirports.value = [];
    try {
      const destinations = await getDestinations(departureCode);
      // 確保目的地不包含出發地
      destinationAirports.value = destinations.filter(d => d.code !== departureCode);
    } catch (error) {
      console.error(`獲取 ${departureCode} 的目的地失敗:`, error);
      destinationAirports.value = []; // 失敗時清空
    } finally {
      loadingDestinations.value = false;
    }
  };

  // 監聽出發機場的變化
  watch(() => searchParams?.value?.departureAirport, (newDepartureAirport) => {
    if (newDepartureAirport && newDepartureAirport.code) {
      fetchDestinations(newDepartureAirport.code);
    } else {
      destinationAirports.value = [];
    }
  });
  
  return {
    taiwanAirports,
    destinationAirports,
    loadingTaiwanAirports,
    loadingDestinations,
    fetchTaiwanAirports,
    fetchDestinations,
  };
} 