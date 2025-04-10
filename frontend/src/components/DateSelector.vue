<template>
  <div class="mb-4">
    <label v-if="label" :for="id" class="label">{{ label }}</label>
    <input
      type="date"
      :id="id"
      :value="modelValue"
      @input="onChange"
      :min="minDate"
      :max="maxDate"
      :disabled="disabled"
      class="input w-full"
      :class="{ 'border-red-500': error, 'opacity-50 cursor-not-allowed': disabled }"
    />
    <p v-if="error" class="mt-1 text-xs text-red-600">{{ error }}</p>
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
      // Default to one year from now
      default: () => {
        const date = new Date();
        date.setFullYear(date.getFullYear() + 1);
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