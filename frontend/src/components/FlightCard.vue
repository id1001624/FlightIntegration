<template>
  <div class="card card-hover mb-4 overflow-hidden">
    <div class="p-4">
      <!-- 卡片頭部：航空公司 Logo, 名稱, 航班號 -->
      <div class="flex items-center justify-between mb-3">
        <div class="flex items-center space-x-3">
          <img v-if="airlineLogoUrl" :src="airlineLogoUrl" :alt="airlineName" class="h-8 w-8 object-contain rounded-full bg-gray-100 border border-gray-200" />
          <div v-else class="h-8 w-8 rounded-full bg-gray-100 border border-gray-200 flex items-center justify-center text-xs text-gray-400">
            ? <!-- Placeholder for missing logo -->
          </div>
          <div>
            <p class="text-sm font-medium text-text-primary">{{ airlineName }}</p>
            <p class="text-xs text-text-secondary">{{ flightNumber }}</p>
          </div>
        </div>
        <div class="text-right">
          <p class="text-lg font-semibold text-primary">NT$ {{ displayPrice }}</p>
          <p class="text-xs text-text-secondary">{{ flightClassType }}</p>
        </div>
      </div>
      
      <!-- 行程視覺化 -->
      <div class="flex items-center my-4">
        <!-- 出發資訊 -->
        <div class="text-center w-1/3">
          <p class="text-lg font-semibold text-text-primary">{{ formattedDepartureTime }}</p>
          <p class="text-sm text-text-secondary">{{ getDepartureAirportCode }}</p>
        </div>

        <!-- 旅程線條與時長 -->
        <div class="flex-grow text-center px-2">
          <p class="text-xs text-text-secondary mb-1">{{ flightDuration }}</p>
          <div class="relative h-1 bg-gray-200 rounded-full">
            <div class="absolute left-0 top-0 h-1 bg-primary rounded-full" style="width: 100%;"></div>
            <div class="absolute left-0 top-1/2 transform -translate-y-1/2 h-3 w-3 rounded-full bg-primary"></div>
            <div class="absolute right-0 top-1/2 transform -translate-y-1/2 h-3 w-3 rounded-full bg-primary"></div>
          </div>
        </div>

        <!-- 到達資訊 -->
        <div class="text-center w-1/3">
          <p class="text-lg font-semibold text-text-primary">{{ formattedArrivalTime }}</p>
          <p class="text-sm text-text-secondary">{{ getArrivalAirportCode }}</p>
        </div>
      </div>

      <!-- 可選：顯示更多資訊的區域 -->
      <div class="text-xs text-text-secondary flex justify-between items-center pt-2 border-t border-gray-100">
        <span>{{ formattedDepartureDate }}</span>
        <span :class="statusClass">{{ flightStatusText }}</span>
      </div>

    </div>
    <!-- 底部操作區 -->
    <div class="bg-gray-50 px-4 py-2 text-right">
      <button class="btn-primary text-sm py-1 px-3" @click="selectFlight">選擇</button>
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
        if (status.includes('delayed')) return 'text-orange-600 font-medium';
        if (status.includes('cancelled')) return 'text-red-600 font-medium';
        if (status.includes('active') || status.includes('en-route') || status.includes('in air')) return 'text-blue-600 font-medium';
        if (status.includes('landed') || status.includes('arrived')) return 'text-green-600 font-medium';
        return 'text-text-secondary'; // 準時或預定
    });

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
      selectFlight,
    };
  }
}
</script>

<!-- Removed scoped styles --> 