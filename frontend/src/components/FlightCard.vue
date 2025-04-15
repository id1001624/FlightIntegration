<template>
  <router-link 
    :to="{ name: 'FlightDetail', params: { id: flight.id } }" 
    class="flight-card-link" 
    :class="{'flight-card-active': isActive}"
  >
    <div class="flight-card" >
      <div class="flight-card-inner">
        <!-- 卡片頭部：航空公司 Logo, 名稱, 航班號 -->
        <div class="flight-card-header">
          <div class="airline-info">
            <div class="airline-logo-container">
              <img v-if="airlineLogoUrl" :src="airlineLogoUrl" :alt="airlineName" class="airline-logo" />
              <div v-else class="airline-logo-placeholder">
                <span>{{ airlineName.charAt(0) }}</span>
              </div>
            </div>
            <div class="airline-details">
              <h3 class="airline-name">{{ airlineName }}</h3>
              <p class="flight-number">{{ flightNumber }}</p>
            </div>
          </div>
          <div class="flight-price">
            <p class="price-amount">NT$ {{ displayPrice }}</p>
            <p class="cabin-type">{{ flightClassType }}</p>
          </div>
        </div>
        
        <!-- 行程視覺化 -->
        <div class="journey-visualization">
          <!-- 出發資訊 -->
          <div class="departure-info">
            <p class="time">{{ formattedDepartureTime }}</p>
            <p class="airport-code">{{ getDepartureAirportCode }}</p>
          </div>

          <!-- 旅程線條與時長 -->
          <div class="journey-line-container">
            <p class="flight-duration">{{ flightDuration }}</p>
            <div class="journey-line-wrapper">
              <div class="journey-line" ref="journeyLine"></div>
              <div class="airplane-icon" ref="airplaneIcon"></div>
              <div class="departure-dot"></div>
              <div class="arrival-dot"></div>
            </div>
          </div>

          <!-- 到達資訊 -->
          <div class="arrival-info">
            <p class="time">{{ formattedArrivalTime }}</p>
            <p class="airport-code">{{ getArrivalAirportCode }}</p>
          </div>
        </div>

        <!-- 額外資訊 -->
        <div class="flight-meta">
          <span class="flight-date">{{ formattedDepartureDate }}</span>
          <span class="flight-status" :class="statusClass">{{ flightStatusText }}</span>
        </div>

      </div>
    </div>
  </router-link>
</template>

<script>
import { computed, ref, onMounted, onUnmounted } from 'vue';
import { RouterLink } from 'vue-router';

export default {
  name: 'FlightCard',
  props: {
    flight: {
      type: Object,
      required: true
    },
    active: {
      type: Boolean,
      default: false
    }
  },
  emits: ['select-flight'],
  setup(props, { emit }) {
    const isActive = ref(props.active);
    const journeyLine = ref(null);
    const airplaneIcon = ref(null);
    let animationFrame = null;
    
    // --- Logo Mapping ---
    const airlineLogos = {
      // IATA Code: Logo Path
      'CI': '/assets/images/airlines/中華航空.png',
      'BR': '/assets/images/airlines/長榮航空.png',
      'AE': '/assets/images/airlines/華信航空.png',
      'B7': '/assets/images/airlines/立榮航空.png',
      'JX': '/assets/images/airlines/星宇航空.png',
      'DA': '/assets/images/airlines/德安航空.png',
      'JL': '/assets/images/airlines/日本航空.png',
      'CX': '/assets/images/airlines/國泰航空.png',
      'OZ': '/assets/images/airlines/韓亞航空.png',
      'IT': '/assets/images/airlines/台灣虎行.png',
      // Add more airlines as needed
    };

    const getAirlineCode = computed(() => {
        if (props.flight.airline && typeof props.flight.airline === 'object') {
            return props.flight.airline.code || props.flight.airline.iata_code;
        }
        return props.flight.airline_code || (props.flight.flight_number ? props.flight.flight_number.substring(0, 2) : null);
    });

    const airlineLogoUrl = computed(() => {
        const code = getAirlineCode.value;
        return code ? airlineLogos[code] : null;
    });
    // --- End Logo Mapping ---

    const formatTime = (dateTimeString) => {
      if (!dateTimeString) return '--:--';
      try {
        const date = new Date(dateTimeString);
        return date.toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit', hour12: false });
      } catch (e) {
        return '--:--';
      }
    };

    const formatDate = (dateTimeString) => {
      if (!dateTimeString) return '--/--';
      try {
        const date = new Date(dateTimeString);
        return date.toLocaleDateString('zh-TW', { month: '2-digit', day: '2-digit' });
      } catch (e) {
        return '--/--';
      }
    };

    const formatPrice = (price) => {
      if (price == null) return '--';
      return price.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    };

    const formatDuration = (durationMinutes) => {
      if (durationMinutes == null || isNaN(durationMinutes)) return '--時--分';
      const hours = Math.floor(durationMinutes / 60);
      const minutes = durationMinutes % 60;
      return `${hours}時${minutes}分`;
    };

    const formatClassType = (classType) => {
      if (!classType) return '經濟艙';
      const lowerCaseType = classType.toLowerCase();
      if (lowerCaseType.includes('business') || lowerCaseType.includes('商務')) return '商務艙';
      if (lowerCaseType.includes('first') || lowerCaseType.includes('頭等')) return '頭等艙';
      return '經濟艙';
    };

    const formattedDepartureTime = computed(() => formatTime(props.flight.departure_time || props.flight.scheduled_departure));
    const formattedArrivalTime = computed(() => formatTime(props.flight.arrival_time || props.flight.scheduled_arrival));
    const formattedDepartureDate = computed(() => formatDate(props.flight.departure_time || props.flight.scheduled_departure));

    const getDepartureAirportCode = computed(() => props.flight.departure_airport_code || props.flight.departure_airport || 'N/A');
    const getArrivalAirportCode = computed(() => props.flight.arrival_airport_code || props.flight.arrival_airport || 'N/A');

    const airlineName = computed(() => props.flight.airline_name || (props.flight.airline ? props.flight.airline.name : '未知航空'));
    const flightNumber = computed(() => props.flight.flight_number || 'N/A');

    const displayPrice = computed(() => {
      if (props.flight.price && typeof props.flight.price === 'number') {
        return formatPrice(props.flight.price);
      }
      if (props.flight.ticket_price) {
          return formatPrice(props.flight.ticket_price);
      }
      return '洽詢';
    });

    const flightClassType = computed(() => formatClassType(props.flight.class_type));

    const flightDuration = computed(() => {
      // 優先使用已有的 duration 屬性 (假設是分鐘)
      if (props.flight.duration && typeof props.flight.duration === 'number') {
        return formatDuration(props.flight.duration);
      }
      // 其次嘗試計算時間差
      const departure = props.flight.departure_time || props.flight.scheduled_departure;
      const arrival = props.flight.arrival_time || props.flight.scheduled_arrival;
      if (departure && arrival) {
        try {
          const diff = new Date(arrival) - new Date(departure);
          if (!isNaN(diff) && diff > 0) {
            return formatDuration(Math.round(diff / (1000 * 60)));
          }
        } catch (e) { /* 計算失敗 */ }
      }
      return '--時--分';
    });

    // 航班狀態處理
    const flightStatusText = computed(() => {
        const status = props.flight.status ? props.flight.status.toLowerCase() : 'scheduled';
        if (status.includes('delayed')) return '延遲';
        if (status.includes('cancelled')) return '取消';
        if (status.includes('landed') || status.includes('arrived')) return '已抵達';
        if (status.includes('active') || status.includes('en-route') || status.includes('in air')) return '飛行中';
        return '準時'; // 默認
    });

    const statusClass = computed(() => {
        const status = props.flight.status ? props.flight.status.toLowerCase() : 'scheduled';
        if (status.includes('delayed')) return 'status-delayed';
        if (status.includes('cancelled')) return 'status-cancelled';
        if (status.includes('active') || status.includes('en-route') || status.includes('in air')) return 'status-in-air';
        if (status.includes('landed') || status.includes('arrived')) return 'status-arrived';
        return 'status-on-time'; // 準時或預定
    });

    const selectFlight = () => {
      emit('select-flight', props.flight);
    };
    
    // 旅程線條動畫
    const animateJourneyLine = () => {
      if (!journeyLine.value || !airplaneIcon.value) return;
      
      // 初始化線條寬度為0%
      journeyLine.value.style.width = '0%';
      
      // 觸發重排以確保動畫效果
      void journeyLine.value.offsetWidth;
      
      // 開始動畫
      journeyLine.value.style.width = '100%';
      
      // 飛機圖標動畫
      animationFrame = requestAnimationFrame(function animate() {
        const progress = parseFloat(journeyLine.value.style.width) || 0;
        if (progress < 100) {
          airplaneIcon.value.style.left = `${progress}%`;
          animationFrame = requestAnimationFrame(animate);
        } else {
          airplaneIcon.value.style.left = '100%';
        }
      });
    };

    onMounted(() => {
      // 啟動旅程線條動畫
      setTimeout(animateJourneyLine, 300); // 稍微延遲以確保DOM已渲染
    });
    
    onUnmounted(() => {
      // 清理動畫
      if (animationFrame) {
        cancelAnimationFrame(animationFrame);
      }
    });

    return {
      formattedDepartureTime,
      formattedArrivalTime,
      formattedDepartureDate,
      getDepartureAirportCode,
      getArrivalAirportCode,
      airlineName,
      airlineLogoUrl,
      flightNumber,
      displayPrice,
      flightClassType,
      flightDuration,
      flightStatusText,
      statusClass,
      selectFlight,
      isActive,
      journeyLine,
      airplaneIcon
    };
  }
}
</script>

<style scoped>
.flight-card-link {
  display: block;
  text-decoration: none;
  color: inherit;
}

.flight-card {
  margin-bottom: 1rem;
  border-radius: 0.5rem;
  overflow: hidden;
  background-color: var(--color-base);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-sm);
  transition: all var(--transition-normal);
}

.flight-card:hover {
  border-color: var(--color-primary-light);
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.flight-card-active {
  border-color: var(--color-primary);
  box-shadow: var(--shadow-md);
}

.flight-card-inner {
  padding: 1.25rem;
}

/* 卡片頭部 */
.flight-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.25rem;
}

.airline-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.airline-logo-container {
  width: 2.5rem;
  height: 2.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  overflow: hidden;
  background-color: var(--color-background);
  border: 1px solid var(--color-border);
}

.airline-logo {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.airline-logo-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  color: var(--color-primary);
  font-size: 1rem;
}

.airline-details {
  display: flex;
  flex-direction: column;
}

.airline-name {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-primary);
  margin: 0;
}

.flight-number {
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  margin: 0;
}

.flight-price {
  text-align: right;
}

.price-amount {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--color-primary);
  margin: 0 0 0.25rem 0;
}

.cabin-type {
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  margin: 0;
}

/* 旅程視覺化 */
.journey-visualization {
  display: flex;
  align-items: center;
  margin: 1.5rem 0;
}

.departure-info, .arrival-info {
  width: 30%;
  text-align: center;
}

.time {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 0.25rem 0;
}

.airport-code {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  margin: 0;
  font-weight: 500;
}

.journey-line-container {
  flex-grow: 1;
  padding: 0 0.75rem;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.flight-duration {
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  margin-bottom: 0.5rem;
  text-align: center;
}

.journey-line-wrapper {
  position: relative;
  width: 100%;
  height: 2px;
  background-color: #eaeaea;
  border-radius: 1px;
}

.journey-line {
  position: absolute;
  top: 0;
  left: 0;
  height: 2px;
  width: 0%;
  background-color: var(--color-primary);
  border-radius: 1px;
  transition: width 1.5s cubic-bezier(0.22, 1, 0.36, 1);
}

.departure-dot, .arrival-dot {
  position: absolute;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: var(--color-primary);
  top: 50%;
  transform: translateY(-50%);
}

.departure-dot {
  left: 0;
}

.arrival-dot {
  right: 0;
}

.airplane-icon {
  position: absolute;
  width: 16px;
  height: 16px;
  left: 0%;
  top: 50%;
  transform: translate(-50%, -50%);
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%23005F73'%3E%3Cpath d='M21 16v-2l-8-5V3.5c0-.83-.67-1.5-1.5-1.5S10 2.67 10 3.5V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5l8 2.5z'/%3E%3C/svg%3E");
  background-size: contain;
  background-repeat: no-repeat;
  transition: left 1.5s cubic-bezier(0.22, 1, 0.36, 1);
}

/* 航班狀態 */
.flight-meta {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px solid #f0f0f0;
}

.flight-date {
  color: var(--color-text-secondary);
}

.flight-status {
  font-weight: 500;
}

.status-delayed {
  color: var(--color-warning);
}

.status-cancelled {
  color: var(--color-danger);
}

.status-in-air {
  color: var(--color-info);
}

.status-arrived {
  color: var(--color-success);
}

.status-on-time {
  color: var(--color-text-secondary);
}

/* 響應式 */
@media (max-width: 640px) {
  .journey-visualization {
    flex-direction: column;
    margin: 1rem 0;
  }
  
  .departure-info, .arrival-info {
    width: 100%;
    display: flex;
    justify-content: space-between;
    text-align: left;
    margin-bottom: 0.5rem;
  }
  
  .journey-line-container {
    width: 100%;
    padding: 1rem 0;
    order: 3;
  }
  
  .flight-card-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .flight-price {
    width: 100%;
    display: flex;
    justify-content: space-between;
    text-align: left;
    margin-top: 0.75rem;
  }
}
</style> 