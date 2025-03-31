<template>
  <div class="airport-selector">
    <label v-if="label" :for="id" class="selector-label">{{ label }}</label>
    <div class="selector-wrapper">
      <select
        :id="id"
        :value="currentValue"
        @change="onChange"
        class="airport-select"
        :disabled="disabled"
      >
        <option value="" disabled selected>{{ placeholder }}</option>
        <option v-for="airport in airports" :key="airport.code" :value="airport.code">
          {{ airport.code }} - {{ airport.name }}
        </option>
      </select>
      <div v-if="loading" class="loading-spinner"></div>
    </div>
    <p v-if="error" class="error-message">{{ error }}</p>
  </div>
</template>

<script>
import { computed } from 'vue'

export default {
  name: 'AirportSelector',
  props: {
    id: {
      type: String,
      default: 'airport-selector'
    },
    label: {
      type: String,
      default: ''
    },
    placeholder: {
      type: String,
      default: '選擇機場'
    },
    airports: {
      type: Array,
      default: () => []
    },
    modelValue: {
      type: [Object, String],
      default: null
    },
    disabled: {
      type: Boolean,
      default: false
    },
    loading: {
      type: Boolean,
      default: false
    },
    error: {
      type: String,
      default: ''
    }
  },
  emits: ['update:modelValue', 'change'],
  setup(props, { emit }) {
    const onChange = (event) => {
      const selectedCode = event.target.value;
      const selectedAirport = props.airports.find(airport => airport.code === selectedCode);
      
      if (selectedAirport) {
        emit('update:modelValue', selectedAirport);
        emit('change', selectedCode);
      } else {
        emit('update:modelValue', null);
        emit('change', '');
      }
    };

    // 計算當前選中的機場代碼
    const currentValue = computed(() => {
      if (!props.modelValue) return '';
      if (typeof props.modelValue === 'string') return props.modelValue;
      return props.modelValue.code || '';
    });

    return {
      onChange,
      currentValue
    };
  }
}
</script>

<style scoped>
.airport-selector {
  margin-bottom: 1rem;
}

.selector-label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #1a1a1a;
  letter-spacing: 0.02em;
}

.selector-wrapper {
  position: relative;
}

.airport-select {
  width: 100%;
  padding: 0.85rem;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  background-color: white;
  font-size: 1rem;
  color: #1a1a1a;
  appearance: none;
  background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%231a1a1a' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e");
  background-repeat: no-repeat;
  background-position: right 1rem center;
  background-size: 1em;
  transition: all 0.2s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
}

.airport-select:focus {
  outline: none;
  border-color: #1a1a1a;
  box-shadow: 0 0 0 3px rgba(0, 0, 0, 0.05);
}

.airport-select:hover:not(:disabled) {
  border-color: #1a1a1a;
}

.airport-select:disabled {
  background-color: #f8f8f8;
  cursor: not-allowed;
  color: #999999;
}

.error-message {
  margin-top: 0.5rem;
  color: #e74c3c;
  font-size: 0.85rem;
}

.loading-spinner {
  position: absolute;
  top: 50%;
  right: 2.5rem;
  transform: translateY(-50%);
  width: 1.2rem;
  height: 1.2rem;
  border: 2px solid rgba(0, 0, 0, 0.05);
  border-top: 2px solid #1a1a1a;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  0% { transform: translateY(-50%) rotate(0deg); }
  100% { transform: translateY(-50%) rotate(360deg); }
}
</style> 