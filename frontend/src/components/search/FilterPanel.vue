<template>
  <div class="card p-6">
    <div class="flex justify-between items-center mb-6">
      <h3 class="text-lg font-semibold text-text-primary">篩選結果</h3>
      <button @click="resetFilters" class="btn-secondary text-sm" v-if="hasActiveFilters">重置篩選</button>
    </div>
    
    <AirlineFilter 
      :airlines="flights" 
      v-model="selectedAirlines"
    />
    
    <PriceRangeSlider 
      :min="minMaxPrices.min"
      :max="minMaxPrices.max"
      v-model="priceRange"
    />
  </div>
</template>

<script>
import AirlineFilter from '../AirlineFilter.vue';
import PriceRangeSlider from '../PriceRangeSlider.vue';
import { computed, ref, watch } from 'vue';

export default {
  name: 'FilterPanel',
  components: {
    AirlineFilter,
    PriceRangeSlider
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
    const priceRange = ref({
      min: 0,
      max: 50000
    });
    const defaultPriceRange = ref({
      min: 0,
      max: 50000
    });

    // 計算所有航班中的最低和最高價格
    const minMaxPrices = computed(() => {
      if (!props.flights || props.flights.length === 0) {
        return { min: 0, max: 50000 };
      }
      
      let min = Number.MAX_SAFE_INTEGER;
      let max = 0;
      
      props.flights.forEach(flight => {
        const price = parseFloat(flight.price) || parseFloat(flight.ticket_price) || 0;
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
      
      return { min, max };
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

    // 當選擇的航空公司變化時通知父組件
    watch(selectedAirlines, () => {
      emitFilterChange();
    });

    // 當價格範圍變化時通知父組件
    watch(priceRange, () => {
      emitFilterChange();
    }, { deep: true });
    
    // 當航班數據變化時重置價格範圍
    watch(minMaxPrices, (newValue) => {
      if (newValue && (
        priceRange.value.min === defaultPriceRange.value.min || 
        priceRange.value.max === defaultPriceRange.value.max
      )) {
        priceRange.value = { ...newValue };
      }
    });
    
    // 初始化時設置價格範圍
    watch(() => props.flights, (newFlights) => {
      if (newFlights && newFlights.length > 0) {
        // 設置初始價格範圍
        priceRange.value = { ...minMaxPrices.value };
        defaultPriceRange.value = { ...minMaxPrices.value };
      }
    }, { immediate: true });

    return {
      selectedAirlines,
      priceRange,
      minMaxPrices,
      hasActiveFilters,
      resetFilters
    };
  }
};
</script> 