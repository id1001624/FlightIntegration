<template>
  <div class="route-selection">
    <div class="route-inputs">
      <!-- 出發地 -->
      <div class="input-group departure-group">
        <label class="input-label">
          <span class="label-text">出發地</span>
          <span class="label-icon">✈</span>
        </label>
        <AirportSelector 
          :model-value="departureAirport"
          placeholder="選擇出發機場"
          :airports="taiwanAirports"
          :loading="loadingTaiwanAirports"
          :error="departureError"
          :is-departure="true"
          class="airport-input departure-input"
          @update:model-value="$emit('update:departureAirport', $event)"
          @change="$emit('departure-change', $event)"
          @select-recent-route="$emit('select-recent-route', $event)"
        />
      </div>
      
      <!-- 路線交換按鈕 -->
      <div class="route-swap">
        <button 
          type="button" 
          class="swap-button"
          @click="$emit('swap')"
          title="交換出發地與目的地"
        >
          <div class="swap-icon">
            <div class="swap-arrow swap-arrow-1"></div>
            <div class="swap-arrow swap-arrow-2"></div>
          </div>
        </button>
      </div>

      <!-- 目的地 -->
      <div class="input-group destination-group">
        <label class="input-label">
          <span class="label-text">目的地</span>
          <span class="label-icon">🎯</span>
        </label>
        <AirportSelector 
          :model-value="arrivalAirport"
          placeholder="選擇目的地機場"
          :airports="destinationAirports"
          :loading="loadingDestinations"
          :error="arrivalError"
          class="airport-input destination-input"
          @update:model-value="$emit('update:arrivalAirport', $event)"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import AirportSelector from '@/components/AirportSelector.vue';

defineProps({
  departureAirport: Object,
  arrivalAirport: Object,
  taiwanAirports: Array,
  destinationAirports: Array,
  loadingTaiwanAirports: Boolean,
  loadingDestinations: Boolean,
  departureError: String,
  arrivalError: String,
});

defineEmits([
  'update:departureAirport',
  'update:arrivalAirport',
  'swap',
  'departure-change',
  'select-recent-route'
]);
</script>

<style scoped>
.route-selection {
  position: relative;
}

.route-inputs {
  display: grid;
  grid-template-columns: 5fr 1fr 5fr;
  align-items: center;
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

.route-swap {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-top: 1.75rem; /* Aligns with input fields */
}

.swap-button {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background-color: #F1F5F9;
  border: 1px solid #E2E8F0;
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  transition: all 0.3s ease;
}

.swap-button:hover {
  transform: rotate(180deg) scale(1.1);
  background-color: #E0F2F1;
  border-color: #00796B;
}

.swap-icon {
  position: relative;
  width: 20px;
  height: 20px;
}

.swap-arrow {
  position: absolute;
  height: 2px;
  width: 14px;
  background-color: #00796B;
  border-radius: 1px;
  transition: transform 0.3s ease;
}

.swap-arrow-1 {
  top: 6px;
  left: 3px;
  transform: rotate(45deg);
}

.swap-button:hover .swap-arrow-1 {
  transform: rotate(225deg);
}

.swap-arrow-2 {
  bottom: 6px;
  left: 3px;
  transform: rotate(-45deg);
}

.swap-button:hover .swap-arrow-2 {
  transform: rotate(135deg);
}


@media (max-width: 768px) {
  .route-inputs {
    grid-template-columns: 1fr;
    gap: 1rem;
  }
  .route-swap {
    transform: rotate(90deg);
    margin: -0.5rem 0;
  }
}
</style> 