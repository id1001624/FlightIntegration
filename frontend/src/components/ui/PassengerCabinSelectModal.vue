<template>
  <AnimatePresence>
    <motion.div
      v-if="visible"
      :initial="{ opacity: 0, y: 50, scale: 0.9 }"
      :animate="{ opacity: 1, y: 0, scale: 1 }"
      :exit="{ opacity: 0, y: 30, scale: 0.95 }"
      :transition="{ type: 'spring', stiffness: 350, damping: 25, mass: 0.8 }"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
      @click.self="emitClose"
    >
      <motion.div
        :initial="{ opacity: 0, scale: 0.8 }"
        :animate="{ opacity: 1, scale: 1 }"
        :transition="{ type: 'spring', stiffness: 300, damping: 20, delay: 0.1 }"
        class="bg-white rounded-lg shadow-xl w-full max-w-md p-6 space-y-6"
      >
        <!-- 標題 -->
        <div class="text-center">
          <h2 class="text-2xl font-semibold text-gray-800">選擇旅客與艙等</h2>
        </div>

        <!-- 旅客選擇區域 -->
        <div class="space-y-4">
          <h3 class="text-lg font-medium text-gray-700 border-b pb-2">旅客人數</h3>
          <!-- 成人 -->
          <PassengerCounter
            label="成人"
            description="12歲或以上"
            :count="selectedPassengers.adults"
            @update:count="(count) => updatePassengerCount('adults', count)"
            :min-count="1"
          ></PassengerCounter>
          <!-- 兒童 -->
          <PassengerCounter
            label="兒童"
            description="2-11歲"
            :count="selectedPassengers.children"
            @update:count="(count) => updatePassengerCount('children', count)"
            :max-count="9"
          ></PassengerCounter>
          <!-- 嬰兒 -->
          <PassengerCounter
            label="嬰兒 (不佔位)"
            description="0-1歲"
            :count="selectedPassengers.infants"
            @update:count="(count) => updatePassengerCount('infants', count)"
            :max-count="selectedPassengers.adults"
          ></PassengerCounter>
        </div>

        <!-- 艙等選擇區域 -->
        <div class="space-y-3">
          <h3 class="text-lg font-medium text-gray-700 border-b pb-2">選擇艙等</h3>
          <select
            v-model="selectedCabinClass"
            class="w-full p-3 border border-gray-300 rounded-md shadow-sm focus:ring-teal-500 focus:border-teal-500 transition duration-150 ease-in-out"
          >
            <option v-for="cabin in cabinClasses" :key="cabin.value" :value="cabin.value">
              {{ cabin.text }}
            </option>
          </select>
        </div>

        <!-- 操作按鈕 -->
        <div class="flex justify-end space-x-3 pt-4">
          <button
            @click="emitClose"
            class="px-6 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 transition duration-150 ease-in-out"
          >
            取消
          </button>
          <button
            @click="handleConfirm"
            class="px-6 py-2 text-sm font-medium text-white bg-teal-600 rounded-md hover:bg-teal-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-teal-500 transition duration-150 ease-in-out"
          >
            確認
          </button>
        </div>
      </motion.div>
    </motion.div>
  </AnimatePresence>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue';
import { motion, AnimatePresence } from 'motion-v';
import PassengerCounter from './PassengerCounter.vue'; // 導入獨立的組件

// Props
const props = defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
  initialPassengers: {
    type: Object,
    default: () => ({ adults: 1, children: 0, infants: 0 }),
  },
  initialCabinClass: {
    type: String,
    default: 'Economy', 
  },
});

// Emits
const emit = defineEmits(['close', 'confirm']);

// 內部狀態
const selectedPassengers = reactive({ ...props.initialPassengers });
const selectedCabinClass = ref(props.initialCabinClass);

// 監聽 props 變化以更新內部狀態
watch(() => props.initialPassengers, (newVal) => {
  Object.assign(selectedPassengers, newVal);
}, { deep: true });

watch(() => props.initialCabinClass, (newVal) => {
  selectedCabinClass.value = newVal;
});

// 艙等選項
const cabinClasses = ref([
  { value: 'Economy', text: '經濟艙' },
  { value: 'Premium Economy', text: '優質經濟艙' },
  { value: 'Business', text: '商務艙' },
  { value: 'First', text: '頭等艙' },
]);

// 更新乘客數量的方法
const updatePassengerCount = (type: 'adults' | 'children' | 'infants', count: number) => {
  const currentAdults = selectedPassengers.adults;
  
  if (type === 'adults') {
    selectedPassengers.adults = Math.max(1, count); // 成人至少為1
    // 如果成人數量減少，確保嬰兒數量不超過新的成人數量
    if (selectedPassengers.infants > selectedPassengers.adults) {
      selectedPassengers.infants = selectedPassengers.adults;
    }
  } else if (type === 'children') {
    selectedPassengers.children = Math.max(0, Math.min(count, 9)); // 兒童 0-9
  } else if (type === 'infants') {
    selectedPassengers.infants = Math.max(0, Math.min(count, currentAdults)); // 嬰兒 0 - 成人數
  }
};

const emitClose = () => {
  emit('close');
};

const handleConfirm = () => {
  emit('confirm', {
    passengers: { ...selectedPassengers },
    cabinClass: selectedCabinClass.value,
  });
  emitClose(); 
};

</script>

<style scoped>
.fixed.inset-0 {
  overscroll-behavior: contain; 
}
</style> 