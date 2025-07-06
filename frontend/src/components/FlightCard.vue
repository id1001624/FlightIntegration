<template>
  <div class="flight-card" @click="toggleDetails">
    <!-- 航空公司品牌條 -->
    <div class="airline-brand-bar">
            <div class="airline-info">
        <img 
          v-if="flight.airline?.logo_path" 
          :src="getAirlineLogo(flight.airline.logo_path)"
          :alt="flight.airline.name_zh"
          class="airline-logo"
        />
        <div class="airline-text">
          <span class="airline-name">{{ flight.airline?.name_zh || flight.airline?.name_en }}</span>
          <span class="flight-number">{{ flight.flight_number }}</span>
        </div>
      </div>
      <div class="flight-status-indicator"></div>
    </div>

    <!-- 主要航班資訊 - Typography-driven Layout -->
    <div class="flight-main-info">
      <!-- 時間與機場資訊 -->
      <div class="flight-route">
        <!-- 出發資訊 -->
        <div class="airport-block departure-block">
          <div class="time-display">{{ formatTime(flight.scheduled_departure) }}</div>
          <div class="airport-code">{{ flight.departure_airport?.iata_code }}</div>
          <div class="airport-name">{{ flight.departure_airport?.name_zh || flight.departure_airport?.name_en }}</div>
          <div class="city-name">{{ flight.departure_airport?.city_zh || flight.departure_airport?.city_en }}</div>
        </div>

        <!-- 飛行軌跡視覺化 -->
        <div class="flight-trajectory">
          <div class="trajectory-header">
            <span class="duration-text">{{ calculateDuration() }}</span>
            <span class="flight-type">{{ flight.stops > 0 ? `${flight.stops}停` : '直飛' }}</span>
                </div>
          
          <div class="trajectory-visual">
            <div class="departure-point"></div>
            <div class="flight-path">
              <div class="path-line"></div>
              <div class="aircraft-icon">
                <div class="aircraft-shape"></div>
              </div>
              <div v-if="flight.stops > 0" class="stop-indicators">
                <div v-for="stop in flight.stops" :key="stop" class="stop-point"></div>
              </div>
            </div>
            <div class="arrival-point"></div>
          </div>
          
          <div class="trajectory-footer">
            <span class="aircraft-type">{{ flight.aircraft_type || 'B737' }}</span>
          </div>
        </div>

        <!-- 到達資訊 -->
        <div class="airport-block arrival-block">
          <div class="time-display">{{ formatTime(flight.scheduled_arrival) }}</div>
          <div class="airport-code">{{ flight.arrival_airport?.iata_code }}</div>
          <div class="airport-name">{{ flight.arrival_airport?.name_zh || flight.arrival_airport?.name_en }}</div>
          <div class="city-name">{{ flight.arrival_airport?.city_zh || flight.arrival_airport?.city_en }}</div>
        </div>
      </div>
    </div>

    <!-- 價格與艙等資訊 -->
    <div class="pricing-section">
      <div class="cabin-classes">
        <div v-if="flight.ticket_prices?.economy_price" class="price-option economy">
          <span class="cabin-label">經濟艙</span>
          <span class="price-value">NT$ {{ flight.ticket_prices.economy_price.toLocaleString() }}</span>
        </div>
        
        <div v-if="flight.ticket_prices?.business_price" class="price-option business">
          <span class="cabin-label">商務艙</span>
          <span class="price-value">NT$ {{ flight.ticket_prices.business_price.toLocaleString() }}</span>
        </div>
        
        <div v-if="flight.ticket_prices?.first_price" class="price-option first">
          <span class="cabin-label">頭等艙</span>
          <span class="price-value">NT$ {{ flight.ticket_prices.first_price.toLocaleString() }}</span>
        </div>
      </div>
      
      <!-- 操作按鈕 -->
      <div class="action-buttons">
        <button class="details-btn" :class="{ expanded: showDetails }">
          <span class="btn-text">{{ showDetails ? '收起詳情' : '查看詳情' }}</span>
          <div class="btn-arrow" :class="{ rotated: showDetails }"></div>
        </button>
      </div>
    </div>

    <!-- 展開的詳細資訊 -->
    <transition name="details-expand">
      <div v-if="showDetails" class="flight-details-expanded">
        <div class="details-grid">
          <!-- 航班詳細資訊 -->
          <div class="detail-section">
            <h4 class="detail-title">航班資訊</h4>
            <div class="detail-items">
              <div class="detail-item">
                <span class="item-label">機型</span>
                <span class="item-value">{{ flight.aircraft_type || 'Boeing 737-800' }}</span>
              </div>
              <div class="detail-item">
                <span class="item-label">機齡</span>
                <span class="item-value">{{ flight.aircraft_age || '5.2' }} 年</span>
              </div>
              <div class="detail-item">
                <span class="item-label">座位配置</span>
                <span class="item-value">{{ flight.seat_configuration || '3-3' }}</span>
              </div>
            </div>
          </div>

          <!-- 服務特色 -->
          <div class="detail-section">
            <h4 class="detail-title">服務特色</h4>
            <div class="service-features">
              <div class="feature-item">
                <span class="feature-text">機上餐食</span>
                <div class="feature-indicator available"></div>
              </div>
              <div class="feature-item">
                <span class="feature-text">機上娛樂</span>
                <div class="feature-indicator available"></div>
              </div>
              <div class="feature-item">
                <span class="feature-text">WiFi網路</span>
                <div class="feature-indicator" :class="flight.has_wifi ? 'available' : 'unavailable'"></div>
              </div>
              <div class="feature-item">
                <span class="feature-text">電源插座</span>
                <div class="feature-indicator available"></div>
              </div>
            </div>
          </div>

          <!-- 行李資訊 -->
          <div class="detail-section">
            <h4 class="detail-title">行李額度</h4>
            <div class="baggage-info">
              <div class="baggage-item">
                <span class="baggage-type">隨身行李</span>
                <span class="baggage-allowance">7kg / 56x36x23cm</span>
              </div>
              <div class="baggage-item">
                <span class="baggage-type">托運行李</span>
                <span class="baggage-allowance">20kg (經濟艙)</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 操作區域 -->
        <div class="details-actions">
          <button class="action-btn compare-btn">
            <span class="btn-text">比較航班</span>
          </button>
          <button class="action-btn select-btn">
            <span class="btn-text">選擇此航班</span>
            <div class="btn-highlight"></div>
          </button>
        </div>
      </div>
    </transition>
  </div>
</template>

<script>
import { ref } from 'vue'

export default {
  name: 'FlightCard',
  props: {
    flight: {
      type: Object,
      required: true
    }
  },
  setup(props) {
    const showDetails = ref(false)

    const toggleDetails = () => {
      showDetails.value = !showDetails.value
    }

    const formatTime = (datetime) => {
      if (!datetime) return '--:--'
      return new Date(datetime).toLocaleTimeString('zh-TW', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
      })
    }

    const calculateDuration = () => {
      if (!props.flight.scheduled_departure || !props.flight.scheduled_arrival) {
        return '-- 小時 -- 分'
      }
      
      const departure = new Date(props.flight.scheduled_departure)
      const arrival = new Date(props.flight.scheduled_arrival)
      const diffMs = arrival - departure
      const hours = Math.floor(diffMs / (1000 * 60 * 60))
      const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60))
      
      return `${hours} 小時 ${minutes} 分`
    }

    const getAirlineLogo = (logoPath) => {
      if (logoPath && logoPath.startsWith('http')) {
        return logoPath
      }
      return `/src/assets/images/logos/${logoPath}`
    }

    return {
      showDetails,
      toggleDetails,
      formatTime,
      calculateDuration,
      getAirlineLogo
    }
  }
}
</script>

<style scoped>
/* === 基礎變量 === */
:root {
  --primary-color: #005F73;
  --secondary-color: #F4A261;
  --accent-orange: #E76F51;
  --text-dark: #1A1A1A;
  --text-medium: #4A4A4A;
  --text-light: #7A7A7A;
  --background-light: #FAFAFA;
  --border-light: #E0E0E0;
  --white: #FFFFFF;
  --success-green: #2ECC71;
  --warning-yellow: #F39C12;
}

/* === 主卡片容器 === */
.flight-card {
  background: var(--white);
  border-radius: 20px;
  box-shadow: 
    0 4px 20px rgba(0, 0, 0, 0.08),
    0 1px 4px rgba(0, 0, 0, 0.04);
  border: 1px solid var(--border-light);
  cursor: pointer;
  transition: all 0.3s ease;
  overflow: hidden;
  margin-bottom: 1.5rem;
}

.flight-card:hover {
  transform: translateY(-4px);
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.12),
    0 2px 8px rgba(0, 0, 0, 0.08);
}

/* === 航空公司品牌條 === */
.airline-brand-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  background: linear-gradient(135deg, var(--background-light) 0%, var(--white) 100%);
  border-bottom: 1px solid var(--border-light);
}

.airline-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.airline-logo {
  width: 32px;
  height: 32px;
  object-fit: contain;
  border-radius: 6px;
}

.airline-text {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}

.airline-name {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-dark);
}

.flight-number {
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--text-light);
}

.flight-status-indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--success-green);
  box-shadow: 0 0 0 3px rgba(46, 204, 113, 0.2);
}

/* === 主要航班資訊 === */
.flight-main-info {
  padding: 1.5rem;
}

/* === 航班路線 === */
.flight-route {
  display: grid;
  grid-template-columns: 1fr 2fr 1fr;
  gap: 1.5rem;
  align-items: center;
}

/* === 機場資訊塊 === */
.airport-block {
  text-align: center;
}

.time-display {
  font-size: 2rem;
  font-weight: 700;
  color: var(--text-dark);
  margin-bottom: 0.5rem;
  line-height: 1;
}

.airport-code {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--primary-color);
  margin-bottom: 0.25rem;
}

.airport-name {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-medium);
  margin-bottom: 0.125rem;
}

.city-name {
  font-size: 0.75rem;
  color: var(--text-light);
}

.departure-block .airport-code {
  color: var(--secondary-color);
}

.arrival-block .airport-code {
  color: var(--primary-color);
}

/* === 飛行軌跡視覺化 === */
.flight-trajectory {
  text-align: center;
  padding: 0 1rem;
}

.trajectory-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.duration-text {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-dark);
}

.flight-type {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-light);
  background: var(--background-light);
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
}

.trajectory-visual {
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  margin: 1rem 0;
}

.departure-point,
.arrival-point {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  position: relative;
}

.departure-point {
  background: var(--secondary-color);
  box-shadow: 0 0 0 4px rgba(244, 162, 97, 0.2);
}

.arrival-point {
  background: var(--primary-color);
  box-shadow: 0 0 0 4px rgba(0, 95, 115, 0.2);
}

.flight-path {
  flex: 1;
  height: 2px;
  margin: 0 1rem;
  position: relative;
  display: flex;
  align-items: center;
}

.path-line {
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, var(--secondary-color), var(--primary-color));
  border-radius: 1px;
}

.aircraft-icon {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 2;
}

.aircraft-shape {
  width: 16px;
  height: 16px;
  background: var(--text-dark);
  border-radius: 50% 0 50% 50%;
  transform: rotate(45deg);
}

.stop-indicators {
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  display: flex;
  justify-content: space-evenly;
  transform: translateY(-50%);
}

.stop-point {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--warning-yellow);
}

.trajectory-footer {
  margin-top: 0.75rem;
}

.aircraft-type {
  font-size: 0.75rem;
  color: var(--text-light);
  font-weight: 500;
}

/* === 價格區域 === */
.pricing-section {
  padding: 1.5rem;
  border-top: 1px solid var(--border-light);
  background: var(--background-light);
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.cabin-classes {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.price-option {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding: 0.75rem 1rem;
  border-radius: 12px;
  background: var(--white);
  border: 2px solid var(--border-light);
  transition: all 0.2s ease;
  min-width: 120px;
}

.price-option:hover {
  border-color: var(--primary-color);
}

.price-option.economy:hover {
  border-color: var(--success-green);
}

.price-option.business:hover {
  border-color: var(--warning-yellow);
}

.price-option.first:hover {
  border-color: var(--accent-orange);
}

.cabin-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-medium);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.price-value {
  font-size: 1.125rem;
  font-weight: 700;
  color: var(--text-dark);
}

/* === 操作按鈕 === */
.action-buttons {
  display: flex;
  gap: 0.75rem;
}

.details-btn {
  background: var(--primary-color);
  color: var(--white);
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 12px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.3s ease;
}

.details-btn:hover {
  background: var(--text-dark);
}

.btn-arrow {
  width: 0;
  height: 0;
  border-left: 4px solid transparent;
  border-right: 4px solid transparent;
  border-top: 6px solid currentColor;
  transition: transform 0.3s ease;
}

.btn-arrow.rotated {
  transform: rotate(180deg);
}

/* === 展開的詳細資訊 === */
.flight-details-expanded {
  border-top: 1px solid var(--border-light);
  background: var(--white);
  padding: 2rem 1.5rem;
}

.details-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 2rem;
  margin-bottom: 2rem;
}

.detail-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.detail-title {
  font-size: 1rem;
  font-weight: 700;
  color: var(--text-dark);
  margin: 0;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid var(--border-light);
}

/* === 詳細項目 === */
.detail-items {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.item-label {
  font-size: 0.875rem;
  color: var(--text-medium);
  font-weight: 500;
}

.item-value {
  font-size: 0.875rem;
  color: var(--text-dark);
  font-weight: 600;
}

/* === 服務特色 === */
.service-features {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.feature-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.feature-text {
  font-size: 0.875rem;
  color: var(--text-medium);
  font-weight: 500;
}

.feature-indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.feature-indicator.available {
  background: var(--success-green);
}

.feature-indicator.unavailable {
  background: var(--text-light);
}

/* === 行李資訊 === */
.baggage-info {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.baggage-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding: 0.75rem;
  background: var(--background-light);
  border-radius: 8px;
}

.baggage-type {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-dark);
}

.baggage-allowance {
  font-size: 0.75rem;
  color: var(--text-medium);
}

/* === 詳情操作區 === */
.details-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  padding-top: 1rem;
  border-top: 1px solid var(--border-light);
}

.action-btn {
  padding: 0.875rem 1.5rem;
  border-radius: 12px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.compare-btn {
  background: var(--white);
  color: var(--primary-color);
  border: 2px solid var(--primary-color);
}

.compare-btn:hover {
  background: var(--primary-color);
  color: var(--white);
}

.select-btn {
  background: var(--accent-orange);
  color: var(--white);
  border: 2px solid var(--accent-orange);
}

.select-btn:hover {
  background: var(--text-dark);
  border-color: var(--text-dark);
}

.btn-highlight {
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s ease;
}

.select-btn:hover .btn-highlight {
  left: 100%;
}

/* === 展開動畫 === */
.details-expand-enter-active,
.details-expand-leave-active {
  transition: all 0.3s ease;
  overflow: hidden;
}

.details-expand-enter-from,
.details-expand-leave-to {
  max-height: 0;
  opacity: 0;
}

.details-expand-enter-to,
.details-expand-leave-from {
  max-height: 500px;
  opacity: 1;
}

/* === 響應式設計 === */
@media (max-width: 1024px) {
  .flight-route {
    gap: 1rem;
  }
  
  .pricing-section {
    flex-direction: column;
    align-items: stretch;
    gap: 1rem;
  }
  
  .cabin-classes {
    justify-content: space-between;
  }
  
  .details-grid {
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }
}

@media (max-width: 768px) {
  .flight-card {
    border-radius: 16px;
    margin-bottom: 1rem;
  }
  
  .airline-brand-bar {
    padding: 1rem;
  }
  
  .flight-main-info {
    padding: 1rem;
  }
  
  .flight-route {
    grid-template-columns: 1fr;
    gap: 1.5rem;
    text-align: center;
  }
  
  .trajectory-visual {
    margin: 0.75rem 0;
  }
  
  .flight-path {
    transform: rotate(90deg);
    width: 60px;
    margin: 1rem 0;
  }
  
  .pricing-section {
    padding: 1rem;
  }
  
  .cabin-classes {
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .price-option {
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
    min-width: auto;
  }
  
  .details-actions {
    flex-direction: column;
    gap: 0.75rem;
  }
  
  .action-btn {
    width: 100%;
    text-align: center;
  }
}

@media (max-width: 480px) {
  .airline-brand-bar {
    padding: 0.75rem;
  }
  
  .flight-main-info {
    padding: 0.75rem;
  }
  
  .time-display {
    font-size: 1.5rem;
  }
  
  .airport-code {
    font-size: 1rem;
  }
  
  .trajectory-header {
    flex-direction: column;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
  }
  
  .pricing-section {
    padding: 0.75rem;
  }
  
  .flight-details-expanded {
    padding: 1rem;
  }
}
</style> 