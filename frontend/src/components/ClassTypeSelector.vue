<template>
  <div class="class-type-selector" :class="{ 'disabled': disabled }">
    <label v-if="label" :for="id" class="selector-label">{{ label }}</label>
    <div class="selector-options">
      <div 
        v-for="option in classOptions" 
        :key="option.value"
        :class="['option', { 'selected': modelValue === option.value }]"
        @click="selectClass(option.value)"
      >
        {{ option.label }}
      </div>
    </div>
    <p v-if="error" class="error-message">{{ error }}</p>
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
      default: 'economy'
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
      { value: 'economy', label: '經濟艙' },
      { value: 'premium_economy', label: '豪華經濟艙' },
      { value: 'business', label: '商務艙' },
      { value: 'first', label: '頭等艙' }
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
.class-type-selector {
  margin-bottom: 1.5rem;
}

.selector-label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #333;
}

.selector-options {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 0.5rem;
}

.option {
  padding: 0.5rem 1rem;
  border-radius: 4px;
  background-color: #f5f5f5;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: center;
  flex: 1;
  min-width: 100px;
}

.option:hover {
  background-color: #e9e9e9;
}

.option.selected {
  background-color: #4a90e2;
  color: white;
  font-weight: 500;
}

.error-message {
  margin-top: 0.5rem;
  color: #e74c3c;
  font-size: 0.85rem;
}

.class-type-selector.disabled .option {
  opacity: 0.6;
  cursor: not-allowed;
}
</style> 