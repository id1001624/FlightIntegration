<template>
  <div class="price-range-selector-container">
    <h3 class="selector-title">{{ title }}</h3>
    <div class="slider-histogram-wrapper">
      <div class="histogram-background" ref="histogramArea">
        <div
          v-for="(bar, index) in histogramBars"
          :key="index"
          class="histogram-bar"
          :style="{ height: bar.height + 
'%', left: bar.left + 
'%', width: bar.width + 
'%' }"
        ></div>
        <div v-if="showAveragePrice && averagePricePosition !== null"
             class="average-price-line"
             :style="{ left: averagePricePosition + '%' }"
        >
          <span class="average-price-label">平均</span>
        </div>
      </div>
      <div class="price-slider-track" ref="sliderTrack">
        <div class="slider-range" :style="{ left: leftHandlePosition + '%', right: (100 - rightHandlePosition) + '%' }"></div>
        <div 
          class="slider-handle min-handle"
          :style="{ left: leftHandlePosition + '%' }"
          @mousedown="startDrag($event, 'min')"
          @touchstart="startDrag($event, 'min')"
          tabindex="0"
          role="slider"
          :aria-valuemin="minPriceLimit"
          :aria-valuemax="maxPriceLimit"
          :aria-valuenow="currentMinPrice"
          aria-label="最低價格滑塊"
        ></div>
        <div 
          class="slider-handle max-handle"
          :style="{ left: rightHandlePosition + '%' }"
          @mousedown="startDrag($event, 'max')"
          @touchstart="startDrag($event, 'max')"
          tabindex="0"
          role="slider"
          :aria-valuemin="minPriceLimit"
          :aria-valuemax="maxPriceLimit"
          :aria-valuenow="currentMaxPrice"
          aria-label="最高價格滑塊"
        ></div>
      </div>
    </div>
    <div class="price-inputs">
      <div class="input-group min-input-group">
        <span v-if="currencySymbol" class="currency-symbol">{{ currencySymbol }}</span>
        <input 
          type="number" 
          class="price-input min-price" 
          :min="minPriceLimit" 
          :max="currentMaxPrice - step" 
          v-model.number="editableMinPrice"
          @change="updateSliderFromInput('min')"
          @blur="validateInput('min')"
          aria-label="最低價格輸入"
        />
      </div>
      <span class="separator">–</span>
      <div class="input-group max-input-group">
        <span v-if="currencySymbol" class="currency-symbol">{{ currencySymbol }}</span>
        <input 
          type="number" 
          class="price-input max-price" 
          :min="currentMinPrice + step" 
          :max="maxPriceLimit" 
          v-model.number="editableMaxPrice"
          @change="updateSliderFromInput('max')"
          @blur="validateInput('max')"
          aria-label="最高價格輸入"
        />
      </div>
      <button v-if="showClearButton" @click="resetPrices" class="clear-button text-button">清除</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, toRefs } from 'vue';

const props = defineProps({
  title: {
    type: String,
    default: '價格範圍'
  },
  minPriceLimit: {
    type: Number,
    default: 0
  },
  maxPriceLimit: {
    type: Number,
    default: 10000
  },
  initialMinPrice: {
    type: Number,
    default: 1000
  },
  initialMaxPrice: {
    type: Number,
    default: 7000
  },
  step: {
    type: Number,
    default: 100
  },
  currencySymbol: {
    type: String,
    default: 'NT$'
  },
  histogramData: { // Array of objects: [{rangeMin, rangeMax, count}, ...]
    type: Array,
    default: () => []
  },
  showAveragePrice: {
    type: Boolean,
    default: true
  },
  averagePrice: {
    type: Number,
    default: null // Calculated if not provided, or can be passed in
  },
  showClearButton: {
    type: Boolean,
    default: true
  }
});

const emit = defineEmits(['update:priceRange']);

const currentMinPrice = ref(props.initialMinPrice);
const currentMaxPrice = ref(props.initialMaxPrice);
const editableMinPrice = ref(props.initialMinPrice);
const editableMaxPrice = ref(props.initialMaxPrice);

const sliderTrack = ref(null);
const histogramArea = ref(null);
const activeHandle = ref(null);

const valueToPosition = (value) => {
  const range = props.maxPriceLimit - props.minPriceLimit;
  if (range === 0) return 0;
  return ((value - props.minPriceLimit) / range) * 100;
};

const positionToValue = (position) => {
  const range = props.maxPriceLimit - props.minPriceLimit;
  const value = (position / 100) * range + props.minPriceLimit;
  return Math.round(value / props.step) * props.step;
};

const leftHandlePosition = computed(() => valueToPosition(currentMinPrice.value));
const rightHandlePosition = computed(() => valueToPosition(currentMaxPrice.value));

const updatePrices = () => {
  editableMinPrice.value = currentMinPrice.value;
  editableMaxPrice.value = currentMaxPrice.value;
  emit('update:priceRange', { min: currentMinPrice.value, max: currentMaxPrice.value });
};

watch(currentMinPrice, updatePrices);
watch(currentMaxPrice, updatePrices);

const startDrag = (event, handle) => {
  event.preventDefault();
  activeHandle.value = handle;
  document.addEventListener('mousemove', onDrag);
  document.addEventListener('mouseup', stopDrag);
  document.addEventListener('touchmove', onDrag, { passive: false });
  document.addEventListener('touchend', stopDrag);
};

const onDrag = (event) => {
  if (!activeHandle.value || !sliderTrack.value) return;
  event.preventDefault();

  const trackRect = sliderTrack.value.getBoundingClientRect();
  const clientX = event.touches ? event.touches[0].clientX : event.clientX;
  let newPosition = ((clientX - trackRect.left) / trackRect.width) * 100;
  newPosition = Math.max(0, Math.min(100, newPosition));
  let newValue = positionToValue(newPosition);

  if (activeHandle.value === 'min') {
    newValue = Math.min(newValue, currentMaxPrice.value - props.step);
    currentMinPrice.value = Math.max(props.minPriceLimit, newValue);
  } else if (activeHandle.value === 'max') {
    newValue = Math.max(newValue, currentMinPrice.value + props.step);
    currentMaxPrice.value = Math.min(props.maxPriceLimit, newValue);
  }
};

const stopDrag = () => {
  activeHandle.value = null;
  document.removeEventListener('mousemove', onDrag);
  document.removeEventListener('mouseup', stopDrag);
  document.removeEventListener('touchmove', onDrag);
  document.removeEventListener('touchend', stopDrag);
};

const updateSliderFromInput = (handleType) => {
  if (handleType === 'min') {
    let newMin = Math.max(props.minPriceLimit, Math.min(editableMinPrice.value, currentMaxPrice.value - props.step));
    newMin = Math.round(newMin / props.step) * props.step;
    currentMinPrice.value = newMin;
    editableMinPrice.value = newMin; 
  } else if (handleType === 'max') {
    let newMax = Math.min(props.maxPriceLimit, Math.max(editableMaxPrice.value, currentMinPrice.value + props.step));
    newMax = Math.round(newMax / props.step) * props.step;
    currentMaxPrice.value = newMax;
    editableMaxPrice.value = newMax;
  }
};

const validateInput = (handleType) => {
    // Ensure inputs reflect the actual slider values after potential adjustments
    editableMinPrice.value = currentMinPrice.value;
    editableMaxPrice.value = currentMaxPrice.value;
}

const resetPrices = () => {
  currentMinPrice.value = props.initialMinPrice;
  currentMaxPrice.value = props.initialMaxPrice;
  editableMinPrice.value = props.initialMinPrice;
  editableMaxPrice.value = props.initialMaxPrice;
};

const histogramBars = computed(() => {
  if (!props.histogramData || props.histogramData.length === 0) return [];
  const maxCount = Math.max(...props.histogramData.map(d => d.count), 0);
  if (maxCount === 0) return [];

  return props.histogramData.map(data => {
    const barLeft = valueToPosition(data.rangeMin);
    const barRight = valueToPosition(data.rangeMax);
    return {
      height: (data.count / maxCount) * 100, // Percentage height
      left: barLeft,
      width: barRight - barLeft,
    };
  });
});

const calculatedAveragePrice = computed(() => {
  if (props.averagePrice !== null) return props.averagePrice;
  if (!props.histogramData || props.histogramData.length === 0) return null;
  let totalValue = 0;
  let totalCount = 0;
  props.histogramData.forEach(d => {
    totalValue += ((d.rangeMin + d.rangeMax) / 2) * d.count;
    totalCount += d.count;
  });
  return totalCount > 0 ? totalValue / totalCount : null;
});

const averagePricePosition = computed(() => {
  if (!props.showAveragePrice || calculatedAveragePrice.value === null) return null;
  return valueToPosition(calculatedAveragePrice.value);
});

// Watch for external changes to initial prices
watch(() => [props.initialMinPrice, props.initialMaxPrice], ([newInitialMin, newInitialMax]) => {
  currentMinPrice.value = newInitialMin;
  currentMaxPrice.value = newInitialMax;
  editableMinPrice.value = newInitialMin;
  editableMaxPrice.value = newInitialMax;
});

// Watch for external changes to limits
watch(() => [props.minPriceLimit, props.maxPriceLimit], ([newMinLimit, newMaxLimit]) => {
  // Adjust current values if they are outside new limits
  currentMinPrice.value = Math.max(newMinLimit, Math.min(currentMinPrice.value, newMaxLimit - props.step));
  currentMaxPrice.value = Math.min(newMaxLimit, Math.max(currentMaxPrice.value, newMinLimit + props.step));
  editableMinPrice.value = currentMinPrice.value;
  editableMaxPrice.value = currentMaxPrice.value;
});

onMounted(() => {
  // Initial setup
  currentMinPrice.value = Math.max(props.minPriceLimit, Math.min(props.initialMinPrice, props.maxPriceLimit - props.step));
  currentMaxPrice.value = Math.min(props.maxPriceLimit, Math.max(props.initialMaxPrice, props.minPriceLimit + props.step));
  editableMinPrice.value = currentMinPrice.value;
  editableMaxPrice.value = currentMaxPrice.value;

  // Ensure handles are not overlapping initially if possible
  if (currentMinPrice.value > currentMaxPrice.value - props.step) {
    currentMinPrice.value = currentMaxPrice.value - props.step;
    if (currentMinPrice.value < props.minPriceLimit) {
       currentMinPrice.value = props.minPriceLimit;
       currentMaxPrice.value = props.minPriceLimit + props.step;
       if (currentMaxPrice.value > props.maxPriceLimit) {
         currentMaxPrice.value = props.maxPriceLimit;
         currentMinPrice.value = props.maxPriceLimit - props.step;
         if (currentMinPrice.value < props.minPriceLimit) currentMinPrice.value = props.minPriceLimit;
       }
    }
    editableMinPrice.value = currentMinPrice.value;
    editableMaxPrice.value = currentMaxPrice.value;
  }
});

onBeforeUnmount(() => {
  document.removeEventListener('mousemove', onDrag);
  document.removeEventListener('mouseup', stopDrag);
  document.removeEventListener('touchmove', onDrag);
  document.removeEventListener('touchend', stopDrag);
});

</script>

<style scoped>
.price-range-selector-container {
  padding: 0.75rem; /* Reduced padding */
  border: 1px solid var(--color-border, #e9ecef);
  border-radius: 0.375rem;
  background-color: var(--color-background-secondary, #fff);
  font-family: var(--font-family-sans);
  margin-bottom: 1rem;
}

.selector-title {
  font-size: 0.9rem; /* Reduced font size */
  font-weight: 600;
  color: var(--color-text-primary, #212529);
  margin-bottom: 0.8rem; /* Reduced margin */
}

.slider-histogram-wrapper {
  position: relative;
  margin-bottom: 1rem; /* Reduced margin */
  height: 60px; /* Fixed height for histogram + slider */
}

.histogram-background {
  position: absolute;
  bottom: 10px; /* Position above the slider track */
  width: 100%;
  height: 40px; /* Height for histogram bars */
  display: flex;
  align-items: flex-end;
}

.histogram-bar {
  position: absolute;
  bottom: 0;
  background-color: var(--color-primary-light, #a5d8ff);
  opacity: 0.6;
  border-top-left-radius: 2px;
  border-top-right-radius: 2px;
}

.average-price-line {
  position: absolute;
  bottom: 0;
  top: 0;
  width: 2px;
  background-color: var(--color-accent, #fd7e14);
  z-index: 1;
  display: flex;
  justify-content: center;
}

.average-price-label {
  position: absolute;
  top: -16px; /* Position above the line */
  transform: translateX(-50%);
  background-color: var(--color-background-secondary, #fff);
  color: var(--color-accent, #fd7e14);
  padding: 0 3px;
  font-size: 0.65rem; /* Smaller font */
  font-weight: 500;
  white-space: nowrap;
}

.price-slider-track {
  position: absolute;
  bottom: 0; /* Slider at the very bottom of wrapper */
  width: 100%;
  height: 6px;
  background-color: var(--color-border-light, #ced4da);
  border-radius: 3px;
  cursor: pointer;
}

.slider-range {
  position: absolute;
  height: 100%;
  background-color: var(--color-primary, #007bff);
  border-radius: 3px;
}

.slider-handle {
  position: absolute;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 14px; /* Smaller handle */
  height: 14px; /* Smaller handle */
  background-color: var(--color-background-secondary, #fff);
  border: 2px solid var(--color-primary, #007bff);
  border-radius: 50%;
  cursor: grab;
  z-index: 2;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.slider-handle:active {
  cursor: grabbing;
  box-shadow: 0 2px 5px rgba(0,0,0,0.2);
}

.price-inputs {
  display: flex;
  flex-wrap: wrap; /* Allow wrapping */
  align-items: center;
  gap: 0.5rem; /* Reduced gap */
  margin-top: 0.8rem; /* Reduced margin */
}

.input-group {
  display: flex;
  align-items: center;
  background-color: var(--color-background, #f8f9fa);
  border: 1px solid var(--color-border-light, #ced4da);
  border-radius: 0.25rem;
  padding: 0.3rem 0.5rem; /* Reduced padding */
  flex-grow: 1; /* Allow input groups to grow */
  min-width: 90px; /* Minimum width for input group */
}

.currency-symbol {
  font-size: 0.8rem; /* Reduced font size */
  color: var(--color-text-secondary, #6c757d);
  margin-right: 0.3rem;
}

.price-input {
  width: 100%; /* Make input take available space in group */
  border: none;
  background-color: transparent;
  font-size: 0.8rem; /* Reduced font size */
  color: var(--color-text-primary, #212529);
  text-align: right;
  -moz-appearance: textfield; /* Firefox */
  appearance: textfield; /* Standard property */
}

.price-input::-webkit-outer-spin-button,
.price-input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

.separator {
  font-size: 0.9rem;
  color: var(--color-text-secondary, #6c757d);
}

.clear-button {
  font-size: 0.8rem; /* Reduced font size */
  padding: 0.3rem 0.6rem; /* Reduced padding */
  color: var(--color-primary, #007bff);
  border: 1px solid var(--color-primary-light, #a5d8ff);
  background-color: transparent;
  border-radius: 0.25rem;
  cursor: pointer;
  transition: background-color 0.2s, color 0.2s;
  flex-shrink: 0; /* Prevent button from shrinking too much */
}

.clear-button:hover {
  background-color: var(--color-primary-light, #a5d8ff);
  color: var(--color-background-secondary, #fff);
}

/* Responsive adjustments */
@media (max-width: 480px) {
  .selector-title {
    font-size: 0.85rem;
  }

  .price-inputs {
    gap: 0.4rem;
  }
  
  .input-group {
    min-width: 80px; /* Further reduce min-width for very small screens */
    padding: 0.25rem 0.4rem;
  }

  .currency-symbol, .price-input, .clear-button {
    font-size: 0.75rem;
  }
  .clear-button {
    padding: 0.25rem 0.5rem;
    width: 100%; /* Make clear button full width on small screens */
    margin-top: 0.5rem; /* Add some space when it wraps */
  }
}

@media (max-width: 360px) {
  .slider-histogram-wrapper {
    height: 50px; /* Slightly reduce height */
  }
  .histogram-background {
     bottom: 8px;
     height: 32px;
  }
  .average-price-label {
    font-size: 0.6rem;
    top: -14px;
  }
   .input-group {
    min-width: 70px;
  }
  .currency-symbol, .price-input {
    font-size: 0.7rem;
  }
}

</style> 