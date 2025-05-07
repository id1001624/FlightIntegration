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
             :style="{ left: averagePricePosition + 
'%' }"
        >
          <span class="average-price-label">平均</span>
        </div>
      </div>
      <div class="price-slider-track" ref="sliderTrack">
        <div class="slider-range" :style="{ left: leftHandlePosition + 
'%', right: (100 - rightHandlePosition) + 
'%' }"></div>
        <div 
          class="slider-handle min-handle"
          :style="{ left: leftHandlePosition + 
'%' }"
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
          :style="{ left: rightHandlePosition + 
'%' }"
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
      <div class="input-group">
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
      <div class="input-group">
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
  const avg = calculatedAveragePrice.value;
  if (avg === null) return null;
  return valueToPosition(avg);
});

onMounted(() => {
  // Initialize values
  currentMinPrice.value = Math.max(props.minPriceLimit, Math.min(props.initialMinPrice, props.maxPriceLimit - props.step));
  currentMaxPrice.value = Math.min(props.maxPriceLimit, Math.max(props.initialMaxPrice, props.minPriceLimit + props.step));
  if (currentMinPrice.value > currentMaxPrice.value - props.step) {
      currentMinPrice.value = currentMaxPrice.value - props.step;
  }
  editableMinPrice.value = currentMinPrice.value;
  editableMaxPrice.value = currentMaxPrice.value;
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
  font-family: 'Inter', 'Noto Sans TC', sans-serif;
  padding: 16px;
  background-color: #FFFFFF; /* Card background */
  border-radius: 8px; /* Card border radius */
  /* box-shadow: 0 2px 4px rgba(0,0,0,0.05); /* Card shadow */
}

.selector-title {
  font-size: 1.125rem; /* 18px, between h3 and basic text */
  font-weight: 600; /* As per design */
  color: #212529; /* 文字主色 */
  margin-bottom: 20px; /* Increased margin for spacing */
}

.slider-histogram-wrapper {
  position: relative;
  height: 50px; /* Adjusted height for histogram */
  margin-bottom: 20px;
}

.histogram-background {
  position: absolute;
  bottom: 12px; /* Align with slider track center */
  width: 100%;
  height: 30px; /* Histogram height */
  display: flex;
  align-items: flex-end;
  pointer-events: none; /* Allow clicks to pass through to slider */
}

.histogram-bar {
  background-color: rgba(244, 162, 97, 0.4); /* 次強調色 #F4A261 with transparency */
  transition: background-color 0.3s ease;
  border-top-left-radius: 2px;
  border-top-right-radius: 2px;
}

.average-price-line {
  position: absolute;
  bottom: 0;
  height: 100%;
  width: 1.5px;
  background-color: #6C757D; /* 文字次色 */
  display: flex;
  justify-content: center;
  color: #212529; /* 文字主色 */
  background-color: transparent;
  text-align: right;
  -moz-appearance: textfield; /* Firefox */
  appearance: textfield; /* Standard property */
}

.average-price-label {
  position: absolute;
  top: -18px; /* Position above the line */
  transform: translateX(-50%);
  font-size: 0.7rem; /* 11.2px */
  color: #6C757D;
  background-color: #FFFFFF;
  padding: 0 3px;
  white-space: nowrap;
}

.price-slider-track {
  position: absolute;
  bottom: 0; /* Aligns with histogram bottom visually */
  width: 100%;
  height: 6px;
  background-color: #E9ECEF; /* 邊框色 (淺灰) */
  border-radius: 3px;
  margin-top: 10px; /* Space between histogram and track */
}

.slider-range {
  position: absolute;
  height: 100%;
  background-color: #005F73; /* 主強調色 */
  border-radius: 3px;
}

.slider-handle {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 16px;
  height: 16px;
  background-color: #005F73; /* 主強調色 */
  border-radius: 50%;
  border: 2px solid #FFFFFF; /* White border for definition */
  box-shadow: 0 1px 3px rgba(0,0,0,0.15); /* Slightly more pronounced shadow */
  cursor: grab;
  z-index: 2;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.slider-handle:hover {
  transform: translateY(-50%) scale(1.15);
  box-shadow: 0 2px 5px rgba(0,0,0,0.2);
}

.slider-handle:active {
  cursor: grabbing;
  transform: translateY(-50%) scale(1.1);
  box-shadow: 0 1px 3px rgba(0,0,0,0.25);
}

.price-inputs {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 4px; /* Reduced from 16px to be closer to slider */
}

.input-group {
  display: flex;
  align-items: center;
  border: 1px solid #E9ECEF; /* 邊框色 */
  border-radius: 4px; /* 遵循指南 */
  padding: 0 8px;
  background-color: #FFFFFF;
  transition: border-color 0.3s ease;
}

.input-group:focus-within {
  border-color: #005F73; /* 主強調色 */
}

.currency-symbol {
  color: #6C757D; /* 文字次色 */
  font-size: 0.875rem; /* 14px */
  margin-right: 4px;
}

.price-input {
  border: none;
  outline: none;
  padding: 8px 2px;
  width: 70px; /* Adjusted width */
  font-size: 0.9375rem; /* 15px, slightly smaller than 1rem */
  color: #212529; /* 文字主色 */
  background-color: transparent;
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
  color: #6C757D; /* 文字次色 */
  font-size: 1rem;
}

.clear-button {
  color: #005F73; /* 主強調色 */
  background: none;
  border: none;
  cursor: pointer;
  padding: 8px;
  font-size: 0.875rem; /* 14px */
  font-weight: 500;
  margin-left: auto; /* Pushes clear button to the right */
  transition: color 0.3s ease;
}

.clear-button:hover {
  color: #004E5F; /* Darker primary for hover */
}
</style> 