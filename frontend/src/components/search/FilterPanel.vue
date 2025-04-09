<template>
  <div class="filter-panel">
    <div class="filter-header">
      <h3>篩選結果</h3>
      <button @click="resetFilters" class="reset-btn" v-if="hasActiveFilters">重置篩選</button>
    </div>
    
    <div class="filter-section">
      <h4>航空公司</h4>
      <div class="airline-filter-container" v-if="airlines.length > 0">
        <AirlineFilter 
          :airlines="airlines" 
          v-model="selectedAirlines"
        />
      </div>
      <p v-else class="no-data">沒有可用的航空公司</p>
    </div>
    
    <div class="filter-section">
      <h4>價格範圍</h4>
      <div class="price-filter-container">
        <PriceRangeSlider 
          v-model:min="priceRange.min" 
          v-model:max="priceRange.max"
          :floor="minMaxPrices.min"
          :ceiling="minMaxPrices.max"
          @change="onPriceChange"
        />
        <div class="price-display">
          <span>{{ priceRange.min }} TWD</span>
          <span>{{ priceRange.max }} TWD</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import AirlineFilter from '../AirlineFilter.vue';
import PriceRangeSlider from '../PriceRangeSlider.vue';

export default {
  name: 'FilterPanel',
  components: {
    AirlineFilter,
    PriceRangeSlider
  },
  props: {
    // 從父組件傳入的所有航班數據
    flights: {
      type: Array,
      default: () => []
    }
  },
  data() {
    return {
      selectedAirlines: [],
      priceRange: {
        min: 0,
        max: 50000
      },
      defaultPriceRange: {
        min: 0,
        max: 50000
      }
    };
  },
  computed: {
    // 從所有航班中提取不重複的航空公司
    airlines() {
      if (!this.flights || this.flights.length === 0) {
        return [];
      }
      
      const uniqueAirlines = new Map();
      
      this.flights.forEach(flight => {
        if (flight.airline && flight.airline.code) {
          uniqueAirlines.set(flight.airline.code, {
            code: flight.airline.code,
            name: flight.airline.name || '未知航空公司',
            logo: flight.airline.logo || ''
          });
        }
      });
      
      return Array.from(uniqueAirlines.values());
    },
    
    // 計算所有航班中的最低和最高價格
    minMaxPrices() {
      if (!this.flights || this.flights.length === 0) {
        return { min: 0, max: 50000 };
      }
      
      let min = Number.MAX_SAFE_INTEGER;
      let max = 0;
      
      this.flights.forEach(flight => {
        const price = parseFloat(flight.price) || 0;
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
    },
    
    // 檢查是否有任何活動的過濾條件
    hasActiveFilters() {
      return (
        this.selectedAirlines.length > 0 ||
        this.priceRange.min !== this.minMaxPrices.min ||
        this.priceRange.max !== this.minMaxPrices.max
      );
    }
  },
  methods: {
    resetFilters() {
      this.selectedAirlines = [];
      this.priceRange = {
        min: this.minMaxPrices.min,
        max: this.minMaxPrices.max
      };
      
      // 通知父組件過濾條件已重置
      this.emitFilterChange();
    },
    
    onPriceChange() {
      this.emitFilterChange();
    },
    
    emitFilterChange() {
      this.$emit('filter-change', {
        airlines: this.selectedAirlines,
        priceRange: this.priceRange
      });
    }
  },
  watch: {
    // 當選擇的航空公司變化時通知父組件
    selectedAirlines() {
      this.emitFilterChange();
    },
    
    // 當航班數據變化時重置價格範圍
    minMaxPrices(newValue) {
      if (newValue && (
        this.priceRange.min === this.defaultPriceRange.min || 
        this.priceRange.max === this.defaultPriceRange.max
      )) {
        this.priceRange = { ...newValue };
      }
    },
    
    // 初始化時設置價格範圍
    flights: {
      immediate: true,
      handler(newFlights) {
        if (newFlights && newFlights.length > 0) {
          // 設置初始價格範圍
          this.priceRange = { ...this.minMaxPrices };
          this.defaultPriceRange = { ...this.minMaxPrices };
        }
      }
    }
  }
};
</script>

<style scoped>
.filter-panel {
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  padding: 1.5rem;
  height: fit-content;
}

.filter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.filter-header h3 {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 600;
}

.reset-btn {
  background: none;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 0.3rem 0.7rem;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.reset-btn:hover {
  background-color: #f5f5f5;
}

.filter-section {
  margin-bottom: 1.5rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid #eee;
}

.filter-section:last-child {
  margin-bottom: 0;
  padding-bottom: 0;
  border-bottom: none;
}

.filter-section h4 {
  margin: 0 0 1rem 0;
  font-size: 1rem;
  font-weight: 500;
  color: #444;
}

.no-data {
  color: #999;
  font-size: 0.9rem;
  font-style: italic;
}

.price-display {
  display: flex;
  justify-content: space-between;
  margin-top: 1rem;
  font-size: 0.9rem;
  color: #666;
}

@media (max-width: 768px) {
  .filter-panel {
    margin-bottom: 1.5rem;
  }
}
</style> 