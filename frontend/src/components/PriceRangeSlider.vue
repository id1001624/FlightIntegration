<template>
  <div class="price-range-slider">
    <div class="slider-header">
      <h4 class="slider-title">價格範圍</h4>
      <div class="price-values">
        <span>NT$ {{ formatPrice(selectedRange.min) }}</span>
        <span>NT$ {{ formatPrice(selectedRange.max) }}</span>
      </div>
    </div>
    
    <div class="slider-container">
      <div class="slider-background"></div>
      <div 
        class="slider-progress"
        :style="{
          left: `${minPercent}%`,
          width: `${rangePercent}%`
        }"
      ></div>
      
      <input
        type="range"
        :min="min"
        :max="max"
        :value="selectedRange.min"
        @input="updateMinPrice"
        class="slider-thumb min-thumb"
        :style="{ zIndex: selectedRange.min > max - 100 ? 5 : 3 }"
      />
      
      <input
        type="range"
        :min="min"
        :max="max"
        :value="selectedRange.max"
        @input="updateMaxPrice"
        class="slider-thumb max-thumb"
      />
    </div>
  </div>
</template>

<script>
import { computed } from 'vue';

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
  setup(props, { emit }) {
    const selectedRange = computed(() => props.modelValue);

    const minPercent = computed(() => {
      return ((selectedRange.value.min - props.min) / (props.max - props.min)) * 100;
    });

    const rangePercent = computed(() => {
      return ((selectedRange.value.max - selectedRange.value.min) / (props.max - props.min)) * 100;
    });

    const updateMinPrice = (event) => {
      const newMin = Number(event.target.value);
      const currentMax = selectedRange.value.max;
      
      // 防止最小值超過最大值
      if (newMin <= currentMax) {
        emit('update:modelValue', { min: newMin, max: currentMax });
      } else {
        // 如果超過，將最小值設為最大值
        event.target.value = currentMax; // Reset the slider position visually
        emit('update:modelValue', { min: currentMax, max: currentMax });
      }
    };

    const updateMaxPrice = (event) => {
      const newMax = Number(event.target.value);
      const currentMin = selectedRange.value.min;

      // 防止最大值小於最小值
      if (newMax >= currentMin) {
        emit('update:modelValue', { min: currentMin, max: newMax });
      } else {
        // 如果小於，將最大值設為最小值
        event.target.value = currentMin; // Reset the slider position visually
        emit('update:modelValue', { min: currentMin, max: currentMin });
      }
    };

    const formatPrice = (price) => {
      if (price == null) return '0';
      return Number(price).toLocaleString('zh-TW');
    };

    return {
      selectedRange,
      minPercent,
      rangePercent,
      updateMinPrice,
      updateMaxPrice,
      formatPrice
    };
  }
}
</script>

<style>
.price-range-slider {
  @apply mb-8;
}

.slider-header {
  @apply mb-4;
}

.slider-title {
  @apply text-base font-medium text-gray-800 mb-2;
}

.price-values {
  @apply flex justify-between text-sm text-gray-500;
}

.slider-container {
  @apply relative h-10 flex items-center;
}

.slider-background {
  @apply absolute bg-gray-200 h-1.5 w-full rounded-full;
}

.slider-progress {
  @apply absolute bg-primary h-1.5 rounded-full;
}

.slider-thumb {
  @apply absolute w-full h-1.5 appearance-none bg-transparent pointer-events-none z-10;
}

.slider-thumb::-webkit-slider-thumb {
  @apply appearance-none h-5 w-5 rounded-full shadow-md cursor-pointer pointer-events-auto;
  background: linear-gradient(135deg, theme('colors.primary.DEFAULT') 0%, theme('colors.primary.dark') 100%);
  border: 2px solid white;
}

.slider-thumb::-moz-range-thumb {
  @apply appearance-none h-5 w-5 rounded-full shadow-md cursor-pointer pointer-events-auto border-0;
  background: linear-gradient(135deg, theme('colors.primary.DEFAULT') 0%, theme('colors.primary.dark') 100%);
  border: 2px solid white;
}

.slider-thumb:focus {
  @apply outline-none;
}

/* Add a subtle effect on focus/active if desired */
.slider-thumb:focus::-webkit-slider-thumb {
   @apply ring-2 ring-primary-light/50;
}
.slider-thumb:focus::-moz-range-thumb {
   @apply ring-2 ring-primary-light/50; /* May need adjustment for Firefox */
}

.min-thumb::-webkit-slider-thumb {
  /* Optional: Slight offset if thumbs overlap too much */
}

.max-thumb::-webkit-slider-thumb {
  /* Optional: Slight offset if thumbs overlap too much */
}

.min-thumb::-moz-range-thumb {
  /* Optional: Slight offset for Firefox */
}

.max-thumb::-moz-range-thumb {
  /* Optional: Slight offset for Firefox */
}

</style> 