<template>
  <div class="mb-6">
    <h4 class="text-base font-medium text-text-primary mb-3">航空公司</h4>
    <div class="text-sm text-text-secondary py-2" v-if="loading">載入中...</div>
    <div class="text-sm text-text-secondary py-2" v-else-if="availableAirlines.length === 0">沒有可用的航空公司</div>
    <div v-else class="max-h-48 overflow-y-auto space-y-2 pr-2">
      <div
        v-for="airline in availableAirlines"
        :key="airline.code"
      >
        <label class="flex items-center cursor-pointer text-sm">
          <input
            type="checkbox"
            :value="airline.code"
            :checked="isSelected(airline.code)"
            @change="toggleAirline(airline.code)"
            class="mr-2 h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
          />
          <span class="text-text-primary">{{ airline.name }} ({{ airline.code }})</span>
        </label>
      </div>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue';

export default {
  name: 'AirlineFilter',
  props: {
    airlines: { // 原始傳入的航班列表
      type: Array,
      default: () => []
    },
    modelValue: {
      type: Array,
      default: () => []
    },
    loading: {
      type: Boolean,
      default: false
    }
  },
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    // 從航班列表中提取不重複的航空公司資訊
    const availableAirlines = computed(() => {
      if (!props.airlines) return [];
      const seenCodes = new Set();
      const uniqueAirlines = [];
      props.airlines.forEach(flight => {
        const airlineCode = flight.airline_code || (flight.airline ? flight.airline.code : null);
        const airlineName = flight.airline_name || (flight.airline ? flight.airline.name : '未知航空公司');
        if (airlineCode && !seenCodes.has(airlineCode)) {
          seenCodes.add(airlineCode);
          uniqueAirlines.push({ code: airlineCode, name: airlineName });
        }
      });
      // 根據航空公司名稱排序
      return uniqueAirlines.sort((a, b) => a.name.localeCompare(b.name));
    });

    const isSelected = (airlineCode) => {
      return props.modelValue.includes(airlineCode);
    };

    const toggleAirline = (airlineCode) => {
      const selected = [...props.modelValue];
      const index = selected.indexOf(airlineCode);

      if (index === -1) {
        selected.push(airlineCode);
      } else {
        selected.splice(index, 1);
      }

      emit('update:modelValue', selected);
    };

    return {
      availableAirlines,
      isSelected,
      toggleAirline
    };
  }
}
</script> 