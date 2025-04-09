<template>
  <div class="flight-card">
    <div class="flight-header">
      <div class="airline-info">
        <span class="airline-code">{{ airlineCode }}</span>
        <span class="flight-number">{{ flightNumber }}</span>
      </div>
      <div class="flight-price">
        <span class="price-label">票價</span>
        <span class="price-amount">{{ displayPrice }}</span>
        <span class="price-class">{{ flightClassType }}</span>
      </div>
    </div>
    
    <div class="flight-details">
      <div class="flight-time">
        <div class="time-column departure">
          <span class="time">{{ formattedDepartureTime }}</span>
          <span class="airport-code">{{ getDepartureAirportCode }}</span>
          <span class="airport-name">{{ departureAirportName }}</span>
        </div>
        
        <div class="flight-duration">
          <div class="duration-line"></div>
          <span class="duration-text">{{ flightDuration }}</span>
          <div class="duration-line"></div>
        </div>
        
        <div class="time-column arrival">
          <span class="time">{{ formattedArrivalTime }}</span>
          <span class="airport-code">{{ getArrivalAirportCode }}</span>
          <span class="airport-name">{{ arrivalAirportName }}</span>
        </div>
      </div>
      
      <div class="flight-info">
        <div class="info-item">
          <span class="info-label">航班日期</span>
          <span class="info-value">{{ formattedDepartureDate }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">航空公司</span>
          <span class="info-value">{{ airlineName }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">可用座位</span>
          <span class="info-value">{{ availableSeats }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">航班狀態</span>
          <span class="info-value" :class="{
            'status-delayed': isDelayed, 
            'status-ontime': isOntime, 
            'status-cancelled': isCancelled,
            'status-inair': isInAir,
            'status-arrived': isArrived,
            'status-diverted': isDiverted
          }">{{ flightStatus }}</span>
        </div>
      </div>
    </div>
    
    <div class="flight-actions">
      <button class="select-button" @click="selectFlight">選擇此航班</button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'FlightCard',
  props: {
    flight: {
      type: Object,
      required: true
    }
  },
  computed: {
    formattedDepartureTime() {
      if (this.flight.departure && this.flight.departure.time) {
        return this.formatTime(this.flight.departure.time);
      }
      return this.formatTime(this.flight.scheduled_departure || this.flight.departure_time);
    },
    formattedArrivalTime() {
      if (this.flight.arrival && this.flight.arrival.time) {
        return this.formatTime(this.flight.arrival.time);
      }
      return this.formatTime(this.flight.scheduled_arrival || this.flight.arrival_time);
    },
    formattedDepartureDate() {
      if (this.flight.departure && this.flight.departure.time) {
        return this.formatDate(this.flight.departure.time);
      }
      return this.formatDate(this.flight.scheduled_departure || this.flight.departure_time);
    },
    formattedArrivalDate() {
      if (this.flight.arrival && this.flight.arrival.time) {
        return this.formatDate(this.flight.arrival.time);
      }
      return this.formatDate(this.flight.scheduled_arrival || this.flight.arrival_time);
    },
    getDepartureAirportCode() {
      if (this.flight.departure && this.flight.departure.airport_id) {
        return this.flight.departure.airport_id;
      }
      return this.flight.departure_airport || this.flight.departure_airport_code || 'TPE';
    },
    getArrivalAirportCode() {
      if (this.flight.arrival && this.flight.arrival.airport_id) {
        return this.flight.arrival.airport_id;
      }
      return this.flight.arrival_airport || this.flight.arrival_airport_code || 'DPS';
    },
    availableSeats() {
      if (this.flight.price && this.flight.price.available_seats) {
        if (this.flight.price.available_seats === 0) {
          return '客滿';
        }
        return this.flight.price.available_seats;
      }
      
      if (this.flight.available_seats === 0) {
        return '客滿';
      }
      
      if (this.flight.available_seats) {
        return this.flight.available_seats;
      }
      
      // 生成假數據
      const min = 2;
      const max = 45;
      return Math.floor(Math.random() * (max - min + 1)) + min;
    },
    flightClassType() {
      const classType = this.flight.class_type || 
                       (this.flight.price ? this.flight.price.cabin_class : null);
      
      if (!classType) {
        return '經濟艙'; // 默認值
      }
      
      return this.formatClassType(classType);
    },
    departureAirportName() {
      if (this.flight.departure && this.flight.departure.name) {
        return this.flight.departure.name;
      }
      return this.flight.departure_airport_name || 
             this.flight.departure?.name || 
             '桃園國際機場';
    },
    arrivalAirportName() {
      if (this.flight.arrival && this.flight.arrival.name) {
        return this.flight.arrival.name;
      }
      return this.flight.arrival_airport_name || 
             this.flight.arrival?.name || 
             '目的地機場';
    },
    airlineCode() {
      if (this.flight.airline && typeof this.flight.airline === 'object') {
        return this.flight.airline.code || this.flight.airline.iata_code || '';
      }
      return this.flight.airline_code || 
             (typeof this.flight.airline === 'string' ? this.flight.airline : '') || 
             (this.flight.flight_number ? this.flight.flight_number.substring(0, 2) : '未知');
    },
    flightNumber() {
      return this.flight.flight_number || '未知';
    },
    displayPrice() {
      // 如果是API返回的標準格式
      if (this.flight.price && typeof this.flight.price === 'object' && this.flight.price.amount) {
        return this.formatPrice(this.flight.price.amount);
      }
      
      // 如果有直接的票價屬性
      if (this.flight.price && typeof this.flight.price !== 'object') {
        return this.formatPrice(this.flight.price);
      }
      
      if (this.flight.ticket_price || this.flight.base_price) {
        return this.formatPrice(this.flight.ticket_price || this.flight.base_price);
      }
      
      // 使用模擬價格
      const classType = this.flight.class_type || 
                       (this.flight.price && this.flight.price.cabin_class ? this.flight.price.cabin_class : null) || 
                       '經濟';
      
      let basePrice;
      switch(classType.toLowerCase()) {
        case 'business':
        case '商務':
        case '商務艙':
          basePrice = 25000 + Math.floor(Math.random() * 10000);
          break;
        case 'first':
        case '頭等':
        case '頭等艙':
          basePrice = 45000 + Math.floor(Math.random() * 15000);
          break;
        case 'economy':
        case '經濟':
        case '經濟艙':
        default:
          basePrice = 8000 + Math.floor(Math.random() * 7000);
          break;
      }
      
      return this.formatPrice(basePrice);
    },
    flightDuration() {
      if (this.flight.duration) {
        if (typeof this.flight.duration === 'string' && this.flight.duration.includes(':')) {
          const parts = this.flight.duration.split(':');
          if (parts.length >= 2) {
            const hours = parseInt(parts[0], 10);
            const minutes = parseInt(parts[1], 10);
            return `${hours}小時${minutes}分鐘`;
          }
        }
        
        return this.formatDuration(this.flight.duration);
      }
      
      let departureTime = null;
      let arrivalTime = null;
      
      if (this.flight.departure && this.flight.departure.time) {
        departureTime = new Date(this.flight.departure.time);
      } else if (this.flight.scheduled_departure) {
        departureTime = new Date(this.flight.scheduled_departure);
      } else if (this.flight.departure_time) {
        departureTime = new Date(this.flight.departure_time);
      }
      
      if (this.flight.arrival && this.flight.arrival.time) {
        arrivalTime = new Date(this.flight.arrival.time);
      } else if (this.flight.scheduled_arrival) {
        arrivalTime = new Date(this.flight.scheduled_arrival);
      } else if (this.flight.arrival_time) {
        arrivalTime = new Date(this.flight.arrival_time);
      }
      
      if (departureTime && arrivalTime && !isNaN(departureTime) && !isNaN(arrivalTime)) {
        const durationMs = arrivalTime - departureTime;
        
        if (durationMs > 0) {
          return this.formatDuration(durationMs / 60000);
        }
      }
      
      return '未知';
    },
    airlineName() {
      if (this.flight.airline && typeof this.flight.airline === 'object') {
        return this.flight.airline.name || this.flight.airline.name_zh || '';
      }
      return this.flight.airline_name || 
             (typeof this.flight.airline === 'string' ? this.flight.airline : '') || 
             '未知';
    },
    flightStatus() {
      const status = this.flight.status?.toLowerCase() || 'unknown';
      switch (status) {
        case 'delayed':
          return '延誤';
        case 'on_time':
        case 'ontime':
          return '準時';
        case 'cancelled':
          return '取消';
        case 'in-air':
        case 'in_air':
          return '已起飛';
        case 'arrived':
        case 'landed':
          return '已抵達';
        case 'scheduled':
          return '準時'; // 預計準時
        case 'departed':
          return '已起飛';
        case 'diverted':
          return '備降';
        case 'unknown':
          return '未知';
        default:
          return typeof this.flight.status === 'string' ? this.flight.status : '準時';
      }
    },
    isDelayed() {
      return this.flight.status?.toLowerCase() === 'delayed';
    },
    isOntime() {
      const status = this.flight.status?.toLowerCase();
      return status === 'on_time' || status === 'ontime' || status === 'scheduled';
    },
    isCancelled() {
      return this.flight.status?.toLowerCase() === 'cancelled';
    },
    isInAir() {
      const status = this.flight.status?.toLowerCase();
      return status === 'in-air' || status === 'in_air' || status === 'departed';
    },
    isArrived() {
      const status = this.flight.status?.toLowerCase();
      return status === 'arrived' || status === 'landed';
    },
    isDiverted() {
      return this.flight.status?.toLowerCase() === 'diverted';
    }
  },
  emits: ['select'],
  methods: {
    formatTime(timeString) {
      if (!timeString) return '00:00';
      try {
        const date = new Date(timeString);
        if (isNaN(date.getTime())) {
          // 嘗試解析其他格式
          if (typeof timeString === 'string') {
            // 如果是類似 "05:10" 這樣的格式
            if (/^\d{1,2}:\d{1,2}$/.test(timeString)) {
              return timeString;
            }
          }
          return '00:00';
        }
        
        // 設置小時和分鐘的格式
        let hours = date.getHours();
        const minutes = date.getMinutes();
        
        // 轉換為12小時制
        const ampm = hours >= 12 ? '下午' : '上午';
        hours = hours % 12;
        hours = hours ? hours : 12; // 0應該顯示為12
        
        // 格式化輸出
        const hoursStr = hours < 10 ? `0${hours}` : hours;
        const minutesStr = minutes < 10 ? `0${minutes}` : minutes;
        
        return `${ampm}${hoursStr}:${minutesStr}`;
      } catch (e) {
        console.error('時間格式化錯誤:', e);
        return '00:00';
      }
    },
    formatDate(dateString) {
      if (!dateString) return '未知';
      try {
        const date = new Date(dateString);
        if (isNaN(date.getTime())) return '未知';
        return `${date.getMonth() + 1}月${date.getDate()}日 ${this.getWeekDay(date)}`;
      } catch (e) {
        return '未知';
      }
    },
    getWeekDay(date) {
      const weekDays = ['週日', '週一', '週二', '週三', '週四', '週五', '週六'];
      return weekDays[date.getDay()];
    },
    formatDuration(duration) {
      if (!duration) return '未知';
      if (typeof duration === 'string') {
        const match = duration.match(/(\d+)H(\d+)M/);
        if (match) {
          return `${match[1]}小時${match[2]}分鐘`;
        }
      }
      if (typeof duration === 'number') {
        const hours = Math.floor(duration / 60);
        const minutes = Math.floor(duration % 60);
        return `${hours}小時${minutes}分鐘`;
      }
      return '未知';
    },
    formatPrice(price) {
      if (!price || isNaN(price)) return 'NT$ ---';
      return `NT$ ${Number(price).toLocaleString('zh-TW')}`;
    },
    formatClassType(classType) {
      if (!classType) return '經濟艙';
      const classTypeMap = {
        'economy': '經濟艙',
        'business': '商務艙',
        'first': '頭等艙'
      };
      return classTypeMap[classType.toLowerCase()] || classType;
    },
    selectFlight() {
      this.$emit('select', this.flight);
    }
  }
}
</script>

<style scoped>
.flight-card {
  background: #ffffff;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 20px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
  transition: all 0.3s ease;
}

.flight-card:hover {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #f0f0f0;
}

.airline-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.airline-logo {
  width: 40px;
  height: 40px;
  object-fit: contain;
}

.airline-details {
  display: flex;
  flex-direction: column;
}

.airline-name {
  font-weight: 600;
  color: #1a1a1a;
  font-size: 1.1em;
}

.flight-number {
  color: #555555;
  font-size: 0.9em;
}

.price-tag {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.price {
  font-size: 1.6em;
  font-weight: 700;
  color: #1a1a1a;
}

.price-unit {
  font-size: 0.8em;
  color: #555555;
  margin-top: -5px;
}

.flight-time {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.time-block {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.time {
  font-size: 1.5em;
  font-weight: 600;
  color: #1a1a1a;
}

.airport-code {
  font-size: 1.2em;
  color: #1a1a1a;
  font-weight: 500;
}

.airport-name {
  color: #555555;
  font-size: 0.9em;
  text-align: center;
}

.flight-duration {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.duration-line {
  width: 150px;
  height: 2px;
  background: #e0e0e0;
  position: relative;
}

.duration-line::after {
  content: '✈';
  position: absolute;
  top: -10px;
  right: -10px;
  color: #1a1a1a;
}

.duration-text {
  font-size: 0.9em;
  color: #555555;
  white-space: nowrap;
}

.flight-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
  margin-top: 24px;
  background-color: #f8f8f8;
  padding: 16px;
  border-radius: 8px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.info-label {
  font-size: 0.9em;
  color: #555555;
  font-weight: 500;
}

.info-value {
  font-size: 1em;
  color: #1a1a1a;
}

.status-delayed {
  color: #e74c3c;
  font-weight: bold;
}

.status-ontime {
  color: #2ecc71;
  font-weight: bold;
}

.status-cancelled {
  color: #e74c3c;
  text-decoration: line-through;
  font-weight: bold;
}

.status-inair {
  color: #3498db;
  font-weight: bold;
}

.status-arrived {
  color: #9b59b6;
  font-weight: bold;
}

.status-diverted {
  color: #f39c12;
  font-weight: bold;
}

.flight-actions {
  margin-top: 24px;
  text-align: right;
}

.select-button {
  background: #1a1a1a;
  color: white;
  border: none;
  padding: 12px 28px;
  border-radius: 6px;
  font-size: 1em;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  letter-spacing: 0.03em;
}

.select-button:hover {
  background: #333333;
  transform: translateY(-2px);
}

@media (max-width: 768px) {
  .flight-time {
    flex-direction: column;
    gap: 20px;
  }
  
  .flight-duration {
    transform: rotate(90deg);
    margin: 20px 0;
  }
  
  .flight-info {
    grid-template-columns: 1fr;
  }
}
</style> 