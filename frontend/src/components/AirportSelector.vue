<template>
  <div class="mb-4">
    <label v-if="label" :for="id" class="label">{{ label }}</label>
    <div class="relative">
      <select
        :id="id"
        :value="currentValue"
        @change="onChange"
        :disabled="disabled || loading"
        class="input w-full appearance-none pr-10"
        :class="{ 'border-red-500': error, 'opacity-50 cursor-not-allowed': disabled, 'pl-3': !loading, 'pl-8': loading }"
      >
        <option value="" disabled>{{ placeholder }}</option>
        <option v-for="airport in airports" :key="airport.code" :value="airport.code">
          {{ airport.code }} - {{ airport.name }}
        </option>
      </select>
      <!-- Loading Spinner -->
      <div v-if="loading" class="absolute inset-y-0 left-0 pl-2 flex items-center pointer-events-none">
        <div class="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-gray-400"></div>
      </div>
      <!-- Dropdown Arrow -->
      <div class="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
        <svg class="h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
          <path fill-rule="evenodd" d="M10 3a.75.75 0 01.53.22l3.75 3.75a.75.75 0 01-1.06 1.06L10 5.06l-3.22 3.22a.75.75 0 01-1.06-1.06l3.75-3.75A.75.75 0 0110 3zM10 17a.75.75 0 01-.53-.22l-3.75-3.75a.75.75 0 011.06-1.06L10 14.94l3.22-3.22a.75.75 0 011.06 1.06l-3.75 3.75A.75.75 0 0110 17z" clip-rule="evenodd" />
        </svg>
      </div>
    </div>
    <p v-if="error" class="mt-1 text-xs text-red-600">{{ error }}</p>
  </div>
</template>

<script>
import { computed } from 'vue'

export default {
  name: 'AirportSelector',
  props: {
    id: {
      type: String,
      default: 'airport-selector'
    },
    label: {
      type: String,
      default: ''
    },
    placeholder: {
      type: String,
      default: '選擇機場'
    },
    airports: {
      type: Array,
      default: () => []
    },
    modelValue: {
      type: [Object, String],
      default: null
    },
    disabled: {
      type: Boolean,
      default: false
    },
    loading: {
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
      const selectedCode = event.target.value;
      const selectedAirport = props.airports.find(airport => airport.code === selectedCode);

      if (selectedAirport) {
        emit('update:modelValue', selectedAirport);
        emit('change', selectedAirport); // Emit the full object for parent handling
      } else {
        emit('update:modelValue', null);
        emit('change', null);
      }
    };

    const currentValue = computed(() => {
      if (!props.modelValue) return '';
      if (typeof props.modelValue === 'string') return props.modelValue; // Handle initial string value if any
      return props.modelValue.code || '';
    });

    return {
      onChange,
      currentValue
    };
  }
}
</script> 