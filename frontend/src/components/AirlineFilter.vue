<template>
  <div class="airline-filter">
    <h4 class="filter-title">航空公司</h4>
    <div class="loading" v-if="loading">載入中...</div>
    <div v-else-if="airlines.length === 0" class="no-data">無可用航空公司</div>
    <div v-else class="airlines-list">
      <div 
        v-for="airline in airlines" 
        :key="airline.code" 
        class="airline-option"
      >
        <label class="airline-checkbox">
          <input 
            type="checkbox" 
            :value="airline.code" 
            :checked="isSelected(airline.code)"
            @change="toggleAirline(airline.code)" 
          />
          <span class="airline-name">{{ airline.name }} ({{ airline.code }})</span>
        </label>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AirlineFilter',
  props: {
    airlines: {
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
  methods: {
    isSelected(airlineCode) {
      return this.modelValue.includes(airlineCode);
    },
    toggleAirline(airlineCode) {
      const selected = [...this.modelValue];
      const index = selected.indexOf(airlineCode);
      
      if (index === -1) {
        selected.push(airlineCode);
      } else {
        selected.splice(index, 1);
      }
      
      this.$emit('update:modelValue', selected);
    }
  }
}
</script>

<style scoped>
.airline-filter {
  margin-bottom: 2rem;
}

.filter-title {
  margin-top: 0;
  margin-bottom: 1rem;
  font-size: 1rem;
  color: #333;
}

.airlines-list {
  max-height: 200px;
  overflow-y: auto;
}

.airline-option {
  margin-bottom: 0.5rem;
}

.airline-checkbox {
  display: flex;
  align-items: center;
  cursor: pointer;
}

.airline-checkbox input {
  margin-right: 0.5rem;
}

.airline-name {
  font-size: 0.9rem;
}

.loading, .no-data {
  font-size: 0.9rem;
  color: #666;
  padding: 0.5rem 0;
}
</style> 