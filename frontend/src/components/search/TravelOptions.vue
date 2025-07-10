<template>
  <div class="travel-options">
    <!-- 日期選擇 -->
    <div class="date-selection">
      <div class="input-group date-group">
        <label class="input-label">
          <span class="label-text">出發日期</span>
          <span class="label-icon">📅</span>
        </label>
        <DateSelector 
          :model-value="departureDate"
          :error="departureDateError"
          class="date-input"
          @update:model-value="$emit('update:departureDate', $event)"
          @change="$emit('departure-date-change', $event)"
        />
      </div>
      
      <div class="input-group date-group">
        <label class="input-label">
          <span class="label-text">回程日期</span>
          <span class="label-icon optional-icon">📅</span>
          <span class="optional-tag">選填</span>
        </label>
        <DateSelector 
          :model-value="returnDate"
          :error="returnDateError"
          :min-date="departureDate"
          class="date-input"
          placeholder="單程票請留空"
          @update:model-value="$emit('update:returnDate', $event)"
        />
      </div>
    </div>
    
    <!-- 乘客與艙等 -->
    <div class="passenger-cabin-selection">
      <div class="input-group passenger-group">
        <label class="input-label">
          <span class="label-text">乘客與艙等</span>
          <span class="label-icon">👥</span>
        </label>
        <button 
          type="button"
          @click="$emit('open-passenger-modal')"
          class="passenger-selector"
        >
          <div class="passenger-display">
            <span class="passenger-text">{{ passengerCabinDisplay }}</span>
            <span class="dropdown-arrow">▼</span>
          </div>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import DateSelector from '@/components/DateSelector.vue';

defineProps({
  departureDate: String,
  returnDate: String,
  departureDateError: String,
  returnDateError: String,
  passengerCabinDisplay: {
    type: String,
    required: true,
  },
});

defineEmits([
  'update:departureDate',
  'update:returnDate',
  'open-passenger-modal',
  'departure-date-change'
]);
</script>

<style scoped>
.travel-options {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 1.5rem;
  align-items: flex-end;
}

.date-selection {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.input-group {
  position: relative;
}

.input-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: #4A5568;
  margin-bottom: 0.5rem;
}

.label-icon {
  font-size: 1rem;
}

.optional-tag {
  font-size: 0.75rem;
  color: #718096;
  background-color: #F1F5F9;
  padding: 0.1rem 0.4rem;
  border-radius: 4px;
}

.passenger-selector {
  width: 100%;
  background-color: #FFFFFF;
  border: 1px solid #CBD5E1;
  border-radius: 0.5rem;
  padding: 0.75rem 1rem;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s ease;
  height: 44px; /* Match DateSelector height */
}

.passenger-selector:hover {
  border-color: #00796B;
}

.passenger-display {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.passenger-text {
  font-weight: 500;
  color: #1E293B;
}

.dropdown-arrow {
  color: #94A3B8;
  transition: transform 0.2s ease;
}

.passenger-selector:hover .dropdown-arrow {
  transform: translateY(2px);
}


@media (max-width: 992px) {
  .travel-options {
    grid-template-columns: 1fr;
    gap: 1rem;
  }
}
</style> 