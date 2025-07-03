<template>
  <div class="card p-6">
    <div class="flex justify-between items-center mb-6">
      <h3 class="text-lg font-semibold text-text-primary">篩選結果</h3>
      <button @click="resetFilters" class="border border-primary text-primary text-sm px-2 py-1" v-if="hasActiveFilters">重置篩選</button>
    </div>
    
    <AirlineFilter 
      :airlines="allAirlines"
      :flights="flights"
      v-model="selectedAirlines"
    />
    
    <PriceRangeSelector
      :min-price-limit="minMaxPrices.min"
      :max-price-limit="minMaxPrices.max"
      :initial-min-price="priceRange.min"
      :initial-max-price="priceRange.max"
      @update:price-range="updatePriceRange"
      :histogram-data="priceHistogramData" 
      :average-price="averageFlightPrice"
    />
  </div>
</template>

<script>
import AirlineFilter from '../AirlineFilter.vue';
import PriceRangeSelector from './PriceRangeSelector.vue';
import { computed, ref, watch, onMounted } from 'vue';
import flightService from '../../api/services/flightService';

export default {
  name: 'FilterPanel',
  components: {
    AirlineFilter,
    PriceRangeSelector
  },
  props: {
    flights: {
      type: Array,
      default: () => []
    }
  },
  emits: ['filter-change'],
  setup(props, { emit }) {
    const selectedAirlines = ref([]);
    const allAirlines = ref([]);
    const priceRange = ref({
      min: 0,
      max: 50000
    });
    const defaultPriceRange = ref({
      min: 0,
      max: 50000
    });

    // 獲取所有航空公司列表
    const loadAllAirlines = async () => {
      try {
        const airlines = await flightService.getAirlines();
        console.log('獲取到的所有航空公司:', airlines);
        
        // 轉換數據格式以符合AirlineFilter的期望
        allAirlines.value = airlines.map(airline => ({
          code: airline.airline_id,
          name: airline.name_zh || airline.name_en || airline.airline_id,
          name_zh: airline.name_zh,
          name_en: airline.name_en,
          logo_path: airline.logo_path,
          is_domestic: airline.is_domestic
        }));
        
        console.log('轉換後的航空公司數據:', allAirlines.value);
      } catch (error) {
        console.error('獲取航空公司列表失敗:', error);
        allAirlines.value = [];
      }
    };

    // 組件掛載時獲取航空公司列表
    onMounted(() => {
      loadAllAirlines();
    });

    // 計算所有航班中的最低和最高價格
    const minMaxPrices = computed(() => {
      if (!props.flights || props.flights.length === 0) {
        return { min: 0, max: 50000 };
      }
      
      let min = Number.MAX_SAFE_INTEGER;
      let max = 0;
      
      props.flights.forEach(flight => {
        const price = flight.price?.amount ? parseFloat(flight.price.amount) : 0;
        
        if (price > 0) {
          min = Math.min(min, price);
          max = Math.max(max, price);
        }
      });
      
      // 如果沒有有效價格，使用默認值
      if (min === Number.MAX_SAFE_INTEGER) {
        min = 0;
      }
      
      // 為最大值添加一點緩衝
      max = Math.ceil(max / 1000) * 1000;
      if (max === 0 && min === 0 && props.flights.length > 0) { // 如果所有價格都是0或無效，但有航班數據
        max = 50000; // 設置一個默認最大值
      }
      
      // 確保最小值不大於最大值 (如果 max 緩衝後仍為 0)
      if (min > max) {
        min = 0; // 或者設置為 max? 取決於業務邏輯，這裡設為0
      }
      
      console.log(`[FilterPanel] Calculated minMaxPrices: min=${min}, max=${max}`);
      return { min, max };
    });
    
    const averageFlightPrice = computed(() => {
      if (!props.flights || props.flights.length === 0) return null;
      let total = 0;
      let count = 0;
      props.flights.forEach(flight => {
        const price = flight.price?.amount ? parseFloat(flight.price.amount) : 0;
        if (price > 0) {
          total += price;
          count++;
        }
      });
      return count > 0 ? Math.round(total / count) : null;
    });

    const priceHistogramData = computed(() => {
      if (!props.flights || props.flights.length === 0 || minMaxPrices.value.max === 0) return [];
      const numBuckets = 20; // 可以調整柱狀圖的精細度
      const bucketSize = (minMaxPrices.value.max - minMaxPrices.value.min) / numBuckets;
      if (bucketSize <= 0) return []; // 防止除以零或負數

      const buckets = Array(numBuckets).fill(0).map((_, i) => {
        return {
          rangeMin: minMaxPrices.value.min + i * bucketSize,
          rangeMax: minMaxPrices.value.min + (i + 1) * bucketSize,
          count: 0
        };
      });

      props.flights.forEach(flight => {
        const price = flight.price?.amount ? parseFloat(flight.price.amount) : 0;
        if (price > 0) {
          const bucketIndex = Math.min(Math.floor((price - minMaxPrices.value.min) / bucketSize), numBuckets - 1);
          if (bucketIndex >= 0 && bucketIndex < numBuckets) {
             buckets[bucketIndex].count++;
          }
        }
      });
      return buckets;
    });
    
    // 檢查是否有任何活動的過濾條件
    const hasActiveFilters = computed(() => {
      return (
        selectedAirlines.value.length > 0 ||
        priceRange.value.min !== minMaxPrices.value.min ||
        priceRange.value.max !== minMaxPrices.value.max
      );
    });

    const resetFilters = () => {
      selectedAirlines.value = [];
      priceRange.value = {
        min: minMaxPrices.value.min,
        max: minMaxPrices.value.max
      };
      
      // 通知父組件過濾條件已重置
      emitFilterChange();
    };
    
    const emitFilterChange = () => {
      emit('filter-change', {
        airlines: selectedAirlines.value,
        priceRange: priceRange.value
      });
    };

    // 新增一個方法來處理新組件的事件
    const updatePriceRange = (newRange) => {
      priceRange.value = { ...newRange };
    };

    // 當選擇的航空公司變化時通知父組件
    watch(selectedAirlines, () => {
      emitFilterChange();
    });

    // 當價格範圍變化時通知父組件
    watch(priceRange, () => {
      emitFilterChange();
    }, { deep: true });
    
    // 當計算出的價格範圍變化時，更新本地的選定範圍
    watch(minMaxPrices, (newValue) => {
        console.log('[FilterPanel] minMaxPrices changed, resetting priceRange ref to full range:', newValue);
        // 直接將 priceRange 重置為新的完整範圍
        priceRange.value = { min: newValue.min, max: newValue.max };
        defaultPriceRange.value = { ...newValue }; // 更新 defaultPriceRange 以供可能的重置邏輯使用
    }, { immediate: true }); // immediate 確保初始計算完成後立即設置

    return {
      selectedAirlines,
      priceRange,
      minMaxPrices,
      hasActiveFilters,
      resetFilters,
      updatePriceRange,
      priceHistogramData,
      averageFlightPrice,
      allAirlines
    };
  }
};
</script>

<style scoped>
.card {
  border: 1px solid #dee2e6;
  background-color: #fff;
}
</style> 