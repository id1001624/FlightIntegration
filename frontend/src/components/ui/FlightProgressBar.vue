<template>
  <div class="flight-progress-bar-container">
    <div class="journey-visualization">
      <div class="departure-info">
        <p class="time">{{ departureTime }}</p>
        <p class="airport-code">{{ departureCode }}</p>
      </div>
      
      <div class="journey-content">
        <div class="flight-duration">{{ totalDuration }}</div>
        <div class="route-track">
          <div class="static-path"></div>
          <div class="origin-marker"></div>
          <div class="destination-marker"></div>
        </div>
      </div>
      
      <div class="arrival-info">
        <p class="time">{{ arrivalTime }}</p>
        <p class="airport-code">{{ arrivalCode }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  totalFlightTime: {
    type: Number, // 總飛行時間（分鐘）
    required: false,
    default: 120 // 默認2小時
  },
  departureCode: {
    type: String,
    default: 'TPE' // 默認為台北
  },
  arrivalCode: {
    type: String,
    default: 'HKG' // 默認為香港
  },
  departureTime: {
    type: String,
    default: '08:00' // 默認出發時間
  },
  arrivalTime: {
    type: String,
    default: '10:00' // 默認到達時間
  }
});

const formatDuration = (minutes) => {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  let formatted = '';
  if (h > 0) formatted += `${h}小時`;
  formatted += `${m}分`;
  return formatted.trim();
};

const totalDuration = computed(() => {
  return formatDuration(props.totalFlightTime);
});
</script>

<style scoped>
.flight-progress-bar-container {
  position: relative;
  padding: 12px 0;
  width: 100%;
}

.journey-visualization {
  display: flex;
  align-items: center;
  width: 100%;
}

.departure-info, .arrival-info {
  width: 80px;
  text-align: center;
}

.time {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--color-text-primary, #212529);
  margin: 0 0 0.25rem 0;
}

.airport-code {
  font-size: 0.875rem;
  color: var(--color-text-secondary, #6C757D);
  margin: 0;
  font-weight: 500;
}

.journey-content {
  flex: 1;
  padding: 0 10px;
  position: relative;
}

.flight-duration {
  text-align: center;
  font-size: 0.875rem; /* 14px */
  color: #6C757D; /*文字次色*/
  margin-bottom: 8px;
  font-weight: 500; /* 略微加粗 */
  letter-spacing: 0.01em; /* 輕微調整字間距 */
}

.route-track {
  position: relative;
  width: 100%;
  height: 2.5px;
  background-color: #E9ECEF; /*邊框色*/
  border-radius: 1.25px;
  overflow: visible; /* 允許標記顯示在軌道外 */
}

.static-path {
  position: absolute;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, #F4A261 0%, #005F73 100%); /* 漸變效果從出發到到達 */
  opacity: 0.7; /* 稍微提高不透明度 */
  border-radius: 1.25px;
  box-shadow: 0 0 5px rgba(0, 95, 115, 0.2); /* 極輕微的發光效果 */
}

.origin-marker, .destination-marker {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 8px; /* 放大一點 */
  height: 8px;
  border-radius: 50%;
  z-index: 2;
  box-shadow: 0 0 3px rgba(0, 0, 0, 0.1); /* 輕微陰影提升立體感 */
}

.origin-marker {
  left: -1px; /* 輕微調整位置，確保完全可見 */
  background-color: #F4A261; /*次強調色*/
}

.destination-marker {
  right: -1px; /* 輕微調整位置，確保完全可見 */
  background-color: #005F73; /*主強調色*/
}

/* 卡片懸停時的脈衝效果 */
.flight-progress-bar-container:hover .static-path {
  animation: pulse 1.5s infinite ease-in-out;
}

@keyframes pulse {
  0% { opacity: 0.7; }
  50% { opacity: 0.9; }
  100% { opacity: 0.7; }
}

/* 響應式設計 */
@media (max-width: 640px) {
  .journey-visualization {
    flex-direction: column;
  }
  
  .departure-info, .arrival-info {
    width: 100%;
    display: flex;
    justify-content: space-between;
    text-align: left;
    margin-bottom: 0.5rem;
  }
  
  .journey-content {
    width: 100%;
    padding: 1rem 0;
    order: 3;
  }
}
</style> 