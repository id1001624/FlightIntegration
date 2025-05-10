<template>
  <div class="flex items-center justify-between py-2">
    <div>
      <p class="text-base font-medium text-gray-700">{{ label }}</p>
      <p v-if="description" class="text-xs text-gray-500">{{ description }}</p>
    </div>
    <div class="flex items-center space-x-3">
      <button 
        @click="decrement"
        :disabled="count <= localMinCount" 
        class="p-1 rounded-full text-gray-600 hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-teal-500 transition-colors"
        type="button"
        aria-label="減少數量"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 12H4"></path></svg>
      </button>
      <span class="text-lg font-medium text-gray-800 w-8 text-center tabular-nums">{{ count }}</span>
      <button 
        @click="increment" 
        class="p-1 rounded-full text-gray-600 hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-teal-500 transition-colors"
        type="button"
        aria-label="增加數量"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path></svg>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps({
  label: {
    type: String,
    required: true,
  },
  description: {
    type: String,
    default: ''
  },
  count: {
    type: Number,
    required: true,
  },
  minCount: {
    type: Number,
    default: 0,
  },
  // 可選的最大計數，例如嬰兒不能超過成人
  maxCount: {
    type: Number,
    default: Infinity
  }
});

const emit = defineEmits(['update:count']);

// 確保 minCount 不會是負數，並且至少是0
const localMinCount = computed(() => Math.max(0, props.minCount));

const increment = () => {
  if (props.count < props.maxCount) {
    emit('update:count', props.count + 1);
  }
};

const decrement = () => {
  if (props.count > localMinCount.value) {
    emit('update:count', props.count - 1);
  }
};
</script>

<style scoped>
/* 使用 Tailwind，此處無需額外樣式 */
</style> 