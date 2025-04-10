<template>
  <div class="flight-card">
    <!-- 卡片上部分 -->
    <div class="card-content">
      <!-- 航空公司資訊 -->
      <div class="airline-info">
        <div class="airline-logo-container">
          <img v-if="airlineLogoUrl" :src="airlineLogoUrl" :alt="airlineName" class="airline-logo" />
          <div v-else class="airline-logo-placeholder">
            {{ getAirlineInitial }}
          </div>
        </div>
        <div class="airline-details">
          <h3 class="airline-name">{{ airlineName }}</h3>
          <p class="flight-number">{{ flightNumber }}</p>
      </div>
    </div>
    
      <!-- 行程資訊 -->
      <div class="journey-info">
        <!-- 出發資訊 -->
        <div class="terminal-info departure">
          <time class="time">{{ formattedDepartureTime }}</time>
          <div class="airport-code">{{ getDepartureAirportCode }}</div>
        </div>
        
        <!-- 飛行時間圖示 -->
        <div class="flight-duration">
          <div class="duration-text">{{ flightDuration }}</div>
          <div class="flight-path">
            <div class="path-line"></div>
            <div class="plane-icon">
              <svg class="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                <path d="M21,16V14L13,9V3.5A1.5,1.5,0 0,0 11.5,2A1.5,1.5,0 0,0 10,3.5V9L2,14V16L10,13.5V19L8,20.5V22L11.5,21L15,22V20.5L13,19V13.5L21,16Z" />
              </svg>
            </div>
          </div>
        </div>
        
        <!-- 到達資訊 -->
        <div class="terminal-info arrival">
          <time class="time">{{ formattedArrivalTime }}</time>
          <div class="airport-code">{{ getArrivalAirportCode }}</div>
        </div>
      </div>
      
      <!-- 價格與選擇按鈕 -->
      <div class="price-action">
        <div class="price-info">
          <p class="price-amount">NT$ {{ displayPrice }}</p>
          <p class="seat-class">{{ flightClassType }}</p>
        </div>
        <button class="select-button" @click="selectFlight">
          選擇
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="w-4 h-4 ml-1">
            <path fill-rule="evenodd" d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z" clip-rule="evenodd" />
          </svg>
        </button>
      </div>
        </div>

    <!-- 卡片底部資訊 -->
    <div class="card-footer">
      <div class="flight-details">
        <div class="detail-item">
          <span class="detail-label">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="w-4 h-4 text-gray-400"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clip-rule="evenodd" /></svg>
            飛行日期
          </span>
          <span class="detail-value">{{ formattedDepartureDate }}</span>
        </div>
        <div class="detail-divider"></div>
        <div class="detail-item">
          <span class="detail-label">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="w-4 h-4 text-gray-400"><path d="M9 6a3 3 0 11-6 0 3 3 0 016 0zM17 6a3 3 0 11-6 0 3 3 0 016 0zM12.93 17c.046-.327.07-.66.07-1a6.97 6.97 0 00-1.5-4.33A5 5 0 0119 16v1h-6.07zM6 11a5 5 0 015 5v1H1v-1a5 5 0 015-5z" /></svg>
            艙位狀態
          </span>
          <span :class="['detail-value', statusClass]">{{ flightStatusText }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue';

export default {
  name: 'FlightCard',
  props: {
    flight: {
      type: Object,
      required: true
    }
  },
  emits: ['select-flight'],
  setup(props, { emit }) {
    // --- Logo Mapping ---
    const airlineLogos = {
      'CI': '/src/assets/images/airlines/中華航空.png',
      'BR': '/src/assets/images/airlines/長榮航空.png',
      'AE': '/src/assets/images/airlines/華信航空.png',
      'B7': '/src/assets/images/airlines/立榮航空.png',
      'JX': '/src/assets/images/airlines/星宇航空.png',
      'DA': '/src/assets/images/airlines/德安航空.png',
      'JL': '/src/assets/images/airlines/日本航空.png',
      'CX': '/src/assets/images/airlines/國泰航空.png',
      'OZ': '/src/assets/images/airlines/韓亞航空.png',
      'IT': '/src/assets/images/airlines/台灣虎行.png',
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

    // --- Formatting Functions ---
    const formatTime = (dateTimeString) => {
      if (!dateTimeString) return '--:--';
      try {
        // Assuming dateTimeString includes date, extract time
        const date = new Date(dateTimeString);
        if (isNaN(date.getTime())) {
          // If only time string like HH:MM is provided
          if (/^\d{1,2}:\d{1,2}$/.test(dateTimeString)) return dateTimeString;
          return '--:--';
        }
        return date.toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit', hour12: false });
      } catch (e) { return '--:--'; }
    };

    const formatDate = (dateTimeString) => {
      if (!dateTimeString) return '--/--';
      try {
        const date = new Date(dateTimeString);
        if (isNaN(date.getTime())) return '--/--';
        return date.toLocaleDateString('zh-TW', { month: '2-digit', day: '2-digit' });
      } catch (e) { return '--/--'; }
    };

    const formatPrice = (price) => {
      if (price == null || isNaN(price)) return '--';
      return Number(price).toLocaleString('zh-TW');
    };

    const formatDuration = (durationMinutes) => {
      if (durationMinutes == null || isNaN(durationMinutes)) return '--時--分';
      const hours = Math.floor(durationMinutes / 60);
      const minutes = durationMinutes % 60;
      return `${hours}時${minutes > 0 ? minutes+'分' : ''}`; // More concise format
    };

    const formatClassType = (classType) => {
      if (!classType) return '經濟艙';
      const lower = classType.toLowerCase();
      if (lower.includes('business') || lower.includes('商務')) return '商務艙';
      if (lower.includes('first') || lower.includes('頭等')) return '頭等艙';
      return '經濟艙';
    };
    // --- End Formatting Functions ---

    // --- Computed Properties ---
    const formattedDepartureTime = computed(() => formatTime(props.flight.departure_time || props.flight.scheduled_departure));
    const formattedArrivalTime = computed(() => formatTime(props.flight.arrival_time || props.flight.scheduled_arrival));
    const formattedDepartureDate = computed(() => formatDate(props.flight.departure_time || props.flight.scheduled_departure));

    const getDepartureAirportCode = computed(() => props.flight.departure_airport_code || props.flight.departure_airport || 'N/A');
    const getArrivalAirportCode = computed(() => props.flight.arrival_airport_code || props.flight.arrival_airport || 'N/A');

    const airlineName = computed(() => props.flight.airline_name || (props.flight.airline ? props.flight.airline.name : '未知航空'));
    const flightNumber = computed(() => props.flight.flight_number || 'N/A');

    const displayPrice = computed(() => {
      const price = props.flight.price ?? props.flight.ticket_price;
      return price != null ? formatPrice(price) : '洽詢';
    });

    const flightClassType = computed(() => formatClassType(props.flight.class_type));

    const flightDuration = computed(() => {
      if (props.flight.duration && typeof props.flight.duration === 'number') {
        return formatDuration(props.flight.duration);
      }
      const departure = props.flight.departure_time || props.flight.scheduled_departure;
      const arrival = props.flight.arrival_time || props.flight.scheduled_arrival;
      if (departure && arrival) {
        try {
          const diff = new Date(arrival) - new Date(departure);
          if (!isNaN(diff) && diff > 0) return formatDuration(Math.round(diff / 60000));
        } catch (e) { /* ignore */ }
      }
      return '--時--分';
    });

    const flightStatusText = computed(() => {
      const status = props.flight.status?.toLowerCase() || 'scheduled';
      if (status.includes('delayed')) return '延遲';
      if (status.includes('cancelled')) return '取消';
      if (status.includes('landed') || status.includes('arrived')) return '已抵達';
      if (status.includes('active') || status.includes('en-route') || status.includes('in air')) return '飛行中';
          return '準時';
    });

    const statusClass = computed(() => {
      const status = props.flight.status?.toLowerCase() || 'scheduled';
      if (status.includes('delayed')) return 'text-orange-500';
      if (status.includes('cancelled')) return 'text-red-600';
      if (status.includes('active') || status.includes('en-route') || status.includes('in air')) return 'text-blue-600';
      if (status.includes('landed') || status.includes('arrived')) return 'text-green-600';
      return 'text-secondary';
    });

    const getAirlineInitial = computed(() => {
      return airlineName.value ? airlineName.value.charAt(0) : '?';
    });
    // --- End Computed Properties ---

    const selectFlight = () => {
      emit('select-flight', props.flight);
    };

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
      getAirlineInitial,
      selectFlight,
    };
  }
}
</script>

<style scoped>
.flight-card {
  @apply bg-white rounded-xl overflow-hidden transition-all duration-300 mb-6;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
}

.flight-card:hover {
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.card-content {
  @apply p-6 grid grid-cols-12 gap-4 items-center;
}

.airline-info {
  @apply col-span-3 flex items-center space-x-3;
}

.airline-logo-container {
  @apply flex-shrink-0 w-12 h-12 bg-gray-50 rounded-full flex items-center justify-center overflow-hidden border border-gray-200;
}

.airline-logo {
  @apply w-10 h-10 object-contain;
}

.airline-logo-placeholder {
  @apply flex items-center justify-center w-full h-full text-lg font-semibold text-gray-500;
}

.airline-details {
  @apply flex flex-col overflow-hidden;
  min-width: 0; /* Fix for flex item overflow */
}

.airline-name {
  @apply text-sm font-medium text-gray-900 truncate;
}

.flight-number {
  @apply text-xs text-gray-500;
}

.journey-info {
  @apply col-span-6 grid grid-cols-3 items-center;
}

.terminal-info {
  @apply flex flex-col items-center;
}

.terminal-info.departure {
  @apply items-center md:items-start;
}

.terminal-info.arrival {
  @apply items-center md:items-end;
}

.time {
  @apply text-xl font-bold text-gray-900 mb-0.5;
}

.airport-code {
  @apply text-sm font-medium text-gray-600;
}

.flight-duration {
  @apply flex flex-col items-center justify-center px-2;
}

.duration-text {
  @apply text-xs text-gray-500 mb-2 whitespace-nowrap;
}

.flight-path {
  @apply relative w-full h-6 flex items-center justify-center;
}

.path-line {
  @apply absolute w-full h-px bg-gray-300;
}

.path-line:before, .path-line:after {
  content: '';
  @apply absolute top-1/2 w-1.5 h-1.5 rounded-full bg-gray-300 transform -translate-y-1/2;
}

.path-line:before {
  @apply left-0;
}

.path-line:after {
  @apply right-0;
}

.plane-icon {
  @apply relative z-10 bg-white text-primary p-0.5 rounded-full;
  /* removed animation for cleaner look, can be added back */
  /* animation: pulse-gentle 2s infinite; */
}

.price-action {
  @apply col-span-3 flex flex-col items-end justify-center space-y-3;
}

.price-info {
  @apply text-right;
}

.price-amount {
  @apply text-xl font-bold text-primary;
}

.seat-class {
  @apply text-xs text-gray-500;
}

.select-button {
  @apply flex items-center justify-center px-4 py-2 text-white text-sm font-medium rounded-lg transition-colors duration-200;
  background: linear-gradient(135deg, theme('colors.primary.DEFAULT') 0%, theme('colors.primary.dark') 100%);
}

.select-button:hover {
  background: linear-gradient(135deg, theme('colors.primary.dark') 0%, theme('colors.primary.dark') 100%);
  box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}

.card-footer {
  @apply px-6 py-3 bg-gray-50 border-t border-gray-100;
}

.flight-details {
  @apply flex items-center justify-between;
}

.detail-item {
  @apply flex items-center;
}

.detail-label {
  @apply flex items-center text-xs text-gray-500 mr-1.5;
}

.detail-label svg {
  @apply mr-1;
}

.detail-value {
  @apply text-xs font-medium text-gray-700;
}

.detail-divider {
  @apply h-4 w-px bg-gray-300 mx-4;
}

/* Ensure status colors defined in tailwind.config.js are used */
.detail-value.text-orange-500 { @apply text-orange-500; }
.detail-value.text-red-600 { @apply text-red-600; }
.detail-value.text-blue-600 { @apply text-blue-600; }
.detail-value.text-green-600 { @apply text-green-600; }
.detail-value.text-secondary { @apply text-secondary; }

/* Optional: Add responsive adjustments if needed */
@media (max-width: 1024px) { /* Example breakpoint */
  .card-content {
    @apply grid-cols-1 gap-y-6;
  }
  .airline-info, .journey-info, .price-action {
    @apply col-span-1;
  }
  .journey-info {
     @apply order-3;
  }
  .price-action {
     @apply order-2 flex-row items-center justify-between w-full;
  }
}

@media (max-width: 640px) {
  .terminal-info.departure {
     @apply items-center;
  }
  .terminal-info.arrival {
     @apply items-center;
  }
  .time {
    @apply text-lg;
  }
  .price-amount {
    @apply text-lg;
  }
  .flight-details {
    @apply flex-col items-start gap-1;
  }
  .detail-divider {
    @apply hidden;
  }
}

</style> 