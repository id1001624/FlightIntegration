<template>
  <div class="price-range-slider">
    <h4 class="filter-title">價格範圍</h4>
    <div class="price-display">
      <span>NT$ {{ formatPrice(selectedRange.min) }}</span>
      <span>NT$ {{ formatPrice(selectedRange.max) }}</span>
    </div>
    <div class="slider-container">
      <div class="slider-track"></div>
      <div 
        class="slider-track-highlight" 
        :style="{
          left: `${((selectedRange.min - min) / (max - min)) * 100}%`,
          width: `${((selectedRange.max - selectedRange.min) / (max - min)) * 100}%`
        }"
      ></div>
      <input 
        type="range" 
        class="slider min-slider" 
        :min="min" 
        :max="max" 
        :value="selectedRange.min" 
        @input="updateMinPrice" 
      />
      <input 
        type="range" 
        class="slider max-slider" 
        :min="min" 
        :max="max" 
        :value="selectedRange.max" 
        @input="updateMaxPrice" 
      />
    </div>
  </div>
</template>

<script>
export default {
  name: 'PriceRangeSlider',
  props: {
    min: {
      type: Number,
      default: 0
    },
    max: {
      type: Number,
      default: 50000
    },
    modelValue: {
      type: Object,
      default: () => ({
        min: 0,
        max: 50000
      })
    }
  },
  emits: ['update:modelValue'],
  computed: {
    selectedRange() {
      return this.modelValue;
    }
  },
  methods: {
    updateMinPrice(event) {
      const newMin = Number(event.target.value);
      if (newMin <= this.selectedRange.max) {
        this.$emit('update:modelValue', {
          min: newMin,
          max: this.selectedRange.max
        });
      } else {
        event.target.value = this.selectedRange.max;
        this.$emit('update:modelValue', {
          min: this.selectedRange.max,
          max: this.selectedRange.max
        });
      }
    },
    updateMaxPrice(event) {
      const newMax = Number(event.target.value);
      if (newMax >= this.selectedRange.min) {
        this.$emit('update:modelValue', {
          min: this.selectedRange.min,
          max: newMax
        });
      } else {
        event.target.value = this.selectedRange.min;
        this.$emit('update:modelValue', {
          min: this.selectedRange.min,
          max: this.selectedRange.min
        });
      }
    },
    formatPrice(price) {
      return price.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    }
  }
}
</script>

<style scoped>
.price-range-slider {
  margin-bottom: 2rem;
}

.filter-title {
  margin-top: 0;
  margin-bottom: 1rem;
  font-size: 1rem;
  color: #333;
}

.price-display {
  display: flex;
  justify-content: space-between;
  margin-bottom: 1rem;
  font-size: 0.9rem;
  color: #666;
}

.slider-container {
  position: relative;
  height: 20px;
  margin: 20px 0;
}

.slider {
  position: absolute;
  width: 100%;
  height: 5px;
  top: 0;
  background: none;
  pointer-events: none;
  -webkit-appearance: none;
  appearance: none;
  outline: none;
  z-index: 3;
}

.slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #4a90e2;
  cursor: pointer;
  pointer-events: auto;
}

.slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #4a90e2;
  cursor: pointer;
  pointer-events: auto;
}

.min-slider, .max-slider {
  top: 7px;
}

.min-slider::-webkit-slider-thumb, .max-slider::-webkit-slider-thumb {
  z-index: 4;
  position: relative;
}

.min-slider::-moz-range-thumb, .max-slider::-moz-range-thumb {
  z-index: 4;
  position: relative;
}

.min-slider::-webkit-slider-thumb {
  background: #3498db;
}

.max-slider::-webkit-slider-thumb {
  background: #3498db;
}

.min-slider::-moz-range-thumb {
  background: #3498db;
}

.max-slider::-moz-range-thumb {
  background: #3498db;
}

.slider-track {
  position: absolute;
  width: 100%;
  height: 5px;
  background-color: #e0e0e0;
  border-radius: 3px;
  top: 7px;
  z-index: 1;
}

.slider-track-highlight {
  position: absolute;
  height: 5px;
  background-color: #4a90e2;
  border-radius: 3px;
  top: 7px;
  z-index: 2;
}
</style> 