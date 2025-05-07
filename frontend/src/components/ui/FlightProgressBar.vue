<template>
  <div class="flight-progress-bar-container" @mouseover="showTooltip = true" @mouseleave="showTooltip = false" :aria-label="`航班進度：${formattedProgress}%`">
    <div class="journey-visualization">
      <div class="departure-info">
        <p class="time">{{ departureTime }}</p>
        <p class="airport-code">{{ departureCode }}</p>
      </div>
      
      <div class="journey-content">
        <div class="flight-duration">{{ totalDuration }}</div>
        <div class="route-track">
          <div class="completed-path" :style="{ width: progressPercentage + '%' }"></div>
          <div class="progress-indicator" :style="{ left: progressPercentage + '%' }">
            <div class="indicator-head"></div>
            <div class="indicator-tail-1"></div>
            <div class="indicator-tail-2"></div>
            <div class="indicator-tail-3"></div>
          </div>
          <div v-if="showOriginDestinationMarkers" class="origin-marker"></div>
          <div v-if="showOriginDestinationMarkers" class="destination-marker"></div>
        </div>
        <div class="progress-tooltip" v-if="showTooltip" :style="{ left: tooltipPosition + '%' }">
          已飛行: {{ flownDuration }} ({{ formattedProgress }}%)
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
import { ref, computed, toRefs } from 'vue';

const props = defineProps({
  currentProgress: {
    type: Number, // e.g., minutes flown
    required: true,
    default: 0
  },
  totalFlightTime: {
    type: Number, // e.g., total minutes for flight
    required: true,
    default: 100
  },
  showOriginDestinationMarkers: {
    type: Boolean,
    default: false // As per design, these are optional
  },
  departureCode: {
    type: String,
    default: 'DEP'
  },
  arrivalCode: {
    type: String,
    default: 'ARR'
  },
  departureTime: {
    type: String,
    default: '--:--'
  },
  arrivalTime: {
    type: String,
    default: '--:--'
  }
});

const { currentProgress, totalFlightTime } = toRefs(props);
const showTooltip = ref(false);

const progressPercentage = computed(() => {
  if (totalFlightTime.value <= 0) return 0;
  const percentage = (currentProgress.value / totalFlightTime.value) * 100;
  return Math.min(Math.max(percentage, 0), 100); // Clamp between 0 and 100
});

const formattedProgress = computed(() => {
  return progressPercentage.value.toFixed(0);
});

const formatDuration = (minutes) => {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  let formatted = '';
  if (h > 0) formatted += `${h}時`;
  formatted += `${m}分`;
  return formatted.trim();
};

const totalDuration = computed(() => {
  return formatDuration(totalFlightTime.value);
});

const flownDuration = computed(() => {
  return formatDuration(currentProgress.value);
});

const tooltipPosition = computed(() => {
  // Adjust tooltip position to be centered above the indicator, 
  // but prevent it from going off-screen.
  const basePosition = progressPercentage.value;
  // This is a simplified calculation. In a real scenario, you might need to measure tooltip width.
  if (basePosition < 10) return 10;
  if (basePosition > 90) return 90;
  return basePosition;
});

</script>

<style scoped>
.flight-progress-bar-container {
  position: relative;
  padding: 12px 0;
  width: 100%;
  cursor: default; /* Indicate it's not a clickable progress bar unless specified */
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
  margin-bottom: 6px;
  font-weight: 400;
  transition: color 0.3s ease;
}

.route-track {
  position: relative;
  width: 100%;
  height: 2.5px; /* Slightly thicker for better visibility */
  background-color: #E9ECEF; /*邊框色*/
  border-radius: 1.25px;
}

.completed-path {
  position: absolute;
  height: 100%;
  background-color: #005F73; /*主強調色*/
  border-radius: 1.25px;
  transition: width 0.5s ease-out; /* Smooth progress animation */
}

.progress-indicator {
  position: absolute;
  top: 50%;
  transform: translate(-50%, -50%); /* Center the indicator on the line */
  display: flex;
  align-items: center;
  transition: left 0.5s ease-out; /* Smooth movement */
}

.indicator-head {
  width: 7px;
  height: 7px;
  background-color: #005F73; /*主強調色*/
  border-radius: 50%;
  z-index: 2;
  transition: transform 0.3s ease;
}

.indicator-tail-1, .indicator-tail-2, .indicator-tail-3 {
  width: 4px;
  height: 4px;
  background-color: #005F73; /*主強調色*/
  border-radius: 50%;
  margin-left: -2px; /* Overlap for a connected look */
  opacity: 0.7;
  animation: flowParticle 1.2s infinite ease-in-out;
  z-index: 1;
}

.indicator-tail-2 {
  width: 3px;
  height: 3px;
  opacity: 0.5;
  animation-delay: 0.2s;
}

.indicator-tail-3 {
  width: 2px;
  height: 2px;
  opacity: 0.3;
  animation-delay: 0.4s;
}

@keyframes flowParticle {
  0%, 100% {
    transform: translateX(0) scale(1);
    opacity: 0.3;
  }
  50% {
    transform: translateX(-3px) scale(0.8);
    opacity: 0.7;
  }
}

.origin-marker, .destination-marker {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 5px;
  height: 5px;
  border-radius: 50%;
  z-index: 0;
}

.origin-marker {
  left: 0;
  background-color: #F4A261; /*次強調色*/
}

.destination-marker {
  right: 0;
  background-color: #B0BEC5; /* A lighter shade of grey or a muted version of primary */
}

.progress-tooltip {
  position: absolute;
  bottom: calc(100% + 5px); /* Position above the progress bar */
  transform: translateX(-50%);
  padding: 6px 10px;
  background-color: #F8F9FA; /*淺灰*/
  border: 1px solid #E9ECEF; /*邊框色*/
  border-radius: 4px; /*遵循指南*/
  box-shadow: 0 2px 4px rgba(0,0,0,0.05); /*遵循指南*/
  font-size: 0.875rem; /* 14px */
  color: #212529; /*文字主色*/
  white-space: nowrap;
  z-index: 10;
  transition: opacity 0.2s ease, transform 0.2s ease;
  opacity: 0;
  pointer-events: none;
}

.flight-progress-bar-container:hover .indicator-head {
  transform: scale(1.3);
}

.flight-progress-bar-container:hover .flight-duration {
  color: #212529; /*文字主色*/
}

.flight-progress-bar-container:hover .progress-tooltip {
  opacity: 1;
  transform: translateX(-50%) translateY(-5px); /* Slight upward movement on hover */
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