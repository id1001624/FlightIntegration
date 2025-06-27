<template>
  <div class="mb-6" :class="{ 'opacity-60 pointer-events-none': disabled }">
    <label v-if="label" :for="id" class="label mb-2">{{ label }}</label>
    <div class="flex flex-wrap gap-2 border border-gray-300 p-2">
      <div
        v-for="option in classOptions"
        :key="option.value"
        :class="[
          'flex-1 min-w-[100px] text-center px-4 py-2 cursor-pointer transition-all duration-200 ease-in-out',
          modelValue === option.value
            ? 'bg-primary text-white font-medium'
            : 'bg-gray-100 text-text-secondary hover:bg-gray-200'
        ]"
        @click="selectClass(option.value)"
      >
        {{ option.label }}
      </div>
    </div>
    <p v-if="error" class="mt-2 text-red-600 text-sm">{{ error }}</p>
  </div>
</template>

<script>
import { ref } from 'vue'

export default {
  name: 'ClassTypeSelector',
  props: {
    id: {
      type: String,
      default: 'class-type'
    },
    label: {
      type: String,
      default: '座艙等級'
    },
    modelValue: {
      type: String,
      default: 'Economy'
    },
    disabled: {
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
    const classOptions = ref([
      { value: 'Economy', label: '經濟艙' },
      { value: 'Premium Economy', label: '優質經濟艙' },
      { value: 'Business', label: '商務艙' },
      { value: 'First', label: '頭等艙' }
    ]);

    const selectClass = (classType) => {
      if (props.disabled) return;
      
      emit('update:modelValue', classType);
      emit('change', classType);
    };

    return {
      classOptions,
      selectClass
    };
  }
}
</script>

<style scoped>
.label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #212529;
}
</style> 