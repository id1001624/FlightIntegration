<template>
  <div class="mb-6">
    <h4 class="text-base font-medium text-text-primary mb-3">價格範圍</h4>
    <div class="flex justify-between text-sm text-text-secondary mb-2">
      <span>NT$ {{ formatPrice(selectedRange.min) }}</span>
      <span>NT$ {{ formatPrice(selectedRange.max) }}</span>
    </div>
    <div class="relative h-5 flex items-center">
      <div class="absolute bg-gray-200 h-1 w-full rounded"></div>
      <div
        class="absolute bg-primary h-1 rounded"
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
        class="absolute w-full h-1 appearance-none bg-transparent pointer-events-none z-10 slider-thumb"
        :style="{ zIndex: selectedRange.min > max - 100 ? 5 : 3 }"
      />
      <input
        type="range"
        :min="min"
        :max="max"
        :value="selectedRange.max"
        @input="updateMaxPrice"
        class="absolute w-full h-1 appearance-none bg-transparent pointer-events-none z-10 slider-thumb"
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
        event.target.value = currentMax;
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
        event.target.value = currentMin;
        emit('update:modelValue', { min: currentMin, max: currentMin });
      }
    };

    const formatPrice = (price) => {
      if (price == null) return '0';
      return price.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
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
  input[type=range]::-webkit-slider-thumb {
    @apply appearance-none h-4 w-4 bg-primary rounded-full cursor-pointer pointer-events-auto;
  }
  input[type=range]::-moz-range-thumb {
    @apply appearance-none h-4 w-4 bg-primary rounded-full cursor-pointer pointer-events-auto border-none;
  }
</style> 