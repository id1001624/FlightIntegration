<template>
  <div class="flight-card-wrapper relative">
    <router-link 
      v-if="flight && flight.flight_id" 
      :to="detailLinkTarget"             
      :event="detailLinkTarget ? 'click' : ''" 
      :class="{
        'flight-card-active': isActive,
        'cursor-default': !detailLinkTarget,
        'pointer-events-none': !detailLinkTarget
      }"
      class="flight-card-link" 
      @click.prevent="selectFlight" 
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
            <button 
              @click.stop.prevent="toggleDetails"
              class="details-button"
              title="查看詳細資訊"
              ref="detailsButtonRef" 
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </router-link>

    <!-- 詳細資訊小卡片 (疊加層) -->
    <transition name="details-fade">
      <div v-if="showDetails" class="details-overlay card" ref="detailsOverlayRef">
        <h5 class="details-title">航班資訊</h5>
        <div class="details-content">
          <p><span class="details-label">機型:</span> {{ flight.aircraft || 'N/A' }}</p>
          <p><span class="details-label">出發航廈:</span> {{ flight.departure?.terminal || '--' }}</p>
          <p><span class="details-label">抵達航廈:</span> {{ flight.arrival?.terminal || '--' }}</p>
        </div>
        <button @click="showDetails = false" class="details-close-button" title="關閉">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </transition>
  </div>
</template>

<script>
import { computed, ref, onMounted, onUnmounted } from 'vue';
import { RouterLink, useRouter } from 'vue-router';

// **讀取環境變數並移除 /api**
const backendUrl = import.meta.env.VITE_API_BASE_URL.replace('/api', '');

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
    const router = useRouter();
    const isActive = ref(props.active);
    const journeyLine = ref(null);
    const airplaneIcon = ref(null);
    let animationFrame = null;
    const showDetails = ref(false);
    const detailsOverlayRef = ref(null);
    const detailsButtonRef = ref(null);
    
    // --- 移除 Logo Mapping ---
    // const airlineLogos = {
    //   // ... 原來的硬編碼內容 ...
    // };

    // --- 移除 getAirlineCode，因為我們直接用 logo_path ---
    // const getAirlineCode = computed(() => {
    //     // ... 原來的邏輯 ...
    // });

    // --- 修改 airlineLogoUrl 以使用 logo_path ---
    const airlineLogoUrl = computed(() => {
        const logoPath = props.flight?.airline?.logo_path;
        // 確保 logoPath 存在且不為空
        if (logoPath && typeof logoPath === 'string' && logoPath.trim() !== '') {
            // 檢查 logoPath 是否已經是完整的 URL (雖然我們的 API 返回相對路徑)
            if (logoPath.startsWith('http://') || logoPath.startsWith('https://')) {
                return logoPath;
            }
            // 為相對路徑添加後端基礎 URL
            // 確保路徑以 '/' 開頭，避免 //
            const correctedPath = logoPath.startsWith('/') ? logoPath : `/${logoPath}`;
            return `${backendUrl}${correctedPath}`;
        }
        return null; // 如果沒有 logo_path，返回 null
    });
    // --- End Logo Path Logic ---

    const formatTime = (dateTimeString) => {
      console.log(`[FlightCard] formatTime called with: ${dateTimeString}`);
      if (!dateTimeString) return '--:--';
      try {
        const date = new Date(dateTimeString);
        if (isNaN(date.getTime())) {
          console.warn(`[FlightCard] Invalid date string for time: ${dateTimeString}`);
          return '--:--';
        }
        return date.toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit', hour12: false });
      } catch (e) {
        console.error(`[FlightCard] Error formatting time: ${dateTimeString}`, e);
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

    const formattedDepartureTime = computed(() => formatTime(props.flight.departure?.time));
    const formattedArrivalTime = computed(() => formatTime(props.flight.arrival?.time));
    const formattedDepartureDate = computed(() => {
        const dateStr = props.flight.departure?.time;
        console.log(`[FlightCard] formattedDepartureDate computed with: ${dateStr}`);
        if (!dateStr) return '--/--';
        try {
            const date = new Date(dateStr);
            if (isNaN(date.getTime())) {
              console.warn(`[FlightCard] Invalid date string for date: ${dateStr}`);
              return '--/--';
            }
            return date.toLocaleDateString('zh-TW', { month: '2-digit', day: '2-digit' });
        } catch (e) { 
            console.error(`[FlightCard] Error formatting date: ${dateStr}`, e);
            return '--/--'; 
        }
    });

    const getDepartureAirportCode = computed(() => props.flight.departure?.code || 'N/A');
    const getArrivalAirportCode = computed(() => props.flight.arrival?.code || 'N/A');

    const airlineName = computed(() => props.flight.airline?.name_zh || props.flight.airline?.name || '未知航空');
    const flightNumber = computed(() => props.flight.flight_number || 'N/A');

    const displayPrice = computed(() => {
      if (props.flight.price?.amount !== null && typeof props.flight.price?.amount === 'number') {
        return formatPrice(props.flight.price.amount);
      } 
      // 可以保留其他備用邏輯，但主要應該讀取 amount
      // if (props.flight.ticket_price) {
      //     return formatPrice(props.flight.ticket_price);
      // }
      return '洽詢';
    });

    const flightClassType = computed(() => formatClassType(props.flight.price?.cabin_class));

    const flightDuration = computed(() => {
      if (props.flight.duration_minutes != null) {
        return formatDuration(props.flight.duration_minutes);
      }
      // 其次嘗試計算時間差
      const departure = props.flight.scheduled_departure;
      const arrival = props.flight.scheduled_arrival;
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

    const detailLinkTarget = computed(() => {
      if (props.flight && props.flight.flight_id) {
        return { name: 'FlightDetail', params: { flight_id: props.flight.flight_id } };
      }
      // 如果 flight_id 無效，返回 null，阻止 router-link 生成有效 href
      return null; 
    });

    const selectFlight = () => {
      if (props.flight && props.flight.flight_id) {
          router.push({ name: 'FlightDetail', params: { flight_id: props.flight.flight_id } });
      } else {
          console.error('Flight ID is missing, cannot navigate to details.', props.flight);
      }
      emit('select-flight', props.flight);
    };
    
    const toggleDetails = (event) => {
      if (event) {
        event.stopPropagation();
        event.preventDefault();
      }
      showDetails.value = !showDetails.value;
    };

    // Click outside handler
    const handleClickOutside = (event) => {
      // Check if the overlay exists and is visible
      if (showDetails.value && detailsOverlayRef.value) {
        // Check if the click target is inside the overlay or on the button
        const clickedInsideOverlay = detailsOverlayRef.value.contains(event.target);
        const clickedOnButton = detailsButtonRef.value?.contains(event.target); // Use optional chaining

        if (!clickedInsideOverlay && !clickedOnButton) {
          console.log('[FlightCard] Clicked outside, closing details.');
          showDetails.value = false; // Close the overlay
        }
      }
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
      
      // Add click outside listener
      document.addEventListener('click', handleClickOutside, true); // Use capture phase
    });
    
    onUnmounted(() => {
      // 清理動畫
      if (animationFrame) {
        cancelAnimationFrame(animationFrame);
      }
      // Remove click outside listener
      document.removeEventListener('click', handleClickOutside, true);
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
      isActive,
      showDetails,
      toggleDetails,
      selectFlight,
      journeyLine,
      airplaneIcon,
      detailLinkTarget,
      detailsOverlayRef,
      detailsButtonRef
    };
  }
}
</script>

<style scoped>
.flight-card-wrapper {
  position: relative;
}

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
  align-items: center;
  font-size: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px solid #f0f0f0;
}

.flight-date {
  color: var(--color-text-secondary);
}

/* 詳細資訊按鈕樣式 */
.details-button {
  background: none;
  border: none;
  padding: 0.25rem;
  cursor: pointer;
  color: var(--color-text-secondary);
  transition: color var(--transition-fast);
}
.details-button:hover {
  color: var(--color-primary);
}

/* 詳細資訊疊加層樣式 */
.details-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background-color: var(--color-background);
  border: 1px solid var(--color-border);
  border-top: 2px solid var(--color-primary);
  padding: 0.75rem 1rem;
  z-index: 10;
  font-size: 0.8rem;
  box-shadow: var(--shadow-lg);
  border-radius: 0 0 0.5rem 0.5rem;
  transform: translateY(100%);
  transition: transform 0.3s ease-out, opacity 0.3s ease-out;
  opacity: 0;
}

/* 過渡效果 */
.details-fade-enter-active,
.details-fade-leave-active {
  transition: transform 0.3s ease-out, opacity 0.3s ease-out;
}

.details-fade-enter-from,
.details-fade-leave-to {
  transform: translateY(100%);
  opacity: 0;
}
.details-fade-enter-to,
.details-fade-leave-from {
  transform: translateY(0);
  opacity: 1;
}

.details-title {
  font-weight: 600;
  color: var(--color-primary);
  margin-bottom: 0.5rem;
  font-size: 0.85rem;
}

.details-content p {
  margin-bottom: 0.3rem;
  color: var(--color-text-primary);
}

.details-label {
  font-weight: 500;
  color: var(--color-text-secondary);
  margin-right: 0.25rem;
}

.details-close-button {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  background: none;
  border: none;
  padding: 0.25rem;
  cursor: pointer;
  color: var(--color-text-secondary);
}
.details-close-button:hover {
  color: var(--color-danger);
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