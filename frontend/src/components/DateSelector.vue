<template>
  <div class="date-selector">
    <label v-if="label" :for="id" class="selector-label">{{ label }}</label>
    <input 
      type="date" 
      :id="id" 
      class="date-input"
      :value="modelValue"
      @input="onChange"
      :min="minDate"
      :max="maxDate"
      :disabled="disabled" 
    />
    <p v-if="error" class="error-message">{{ error }}</p>
  </div>
</template>

<script>
export default {
  name: 'DateSelector',
  props: {
    id: {
      type: String,
      default: 'date-selector'
    },
    label: {
      type: String,
      default: ''
    },
    modelValue: {
      type: String,
      default: ''
    },
    minDate: {
      type: String,
      default: () => new Date().toISOString().split('T')[0]
    },
    maxDate: {
      type: String,
      default: () => {
        const date = new Date();
        date.setDate(date.getDate() + 30);
        return date.toISOString().split('T')[0];
      }
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
    const onChange = (event) => {
      emit('update:modelValue', event.target.value);
      emit('change', event.target.value);
    };

    return {
      onChange
    };
  }
}
</script>

<style scoped>
.date-selector {
  margin-bottom: 1rem;
}

.selector-label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #333;
}

.date-input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
  color: #333;
}

.date-input:focus {
  outline: none;
  border-color: #4a90e2;
  box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.1);
}

.date-input:disabled {
  background-color: #f5f5f5;
  cursor: not-allowed;
}

.error-message {
  margin-top: 0.5rem;
  color: #e74c3c;
  font-size: 0.85rem;
}
</style> 