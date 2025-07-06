<template>
  <div class="flight-search-loader-overlay">
    <div class="loader-container">
      <!-- 主要動畫區域 -->
      <div class="flight-animation-stage">
        <!-- 飛機軌跡動畫 -->
        <div class="flight-path">
          <div class="departure-point">
            <div class="airport-dot departure-dot">
              <div class="airport-ring"></div>
              <div class="airport-pulse"></div>
            </div>
            <span class="airport-label">{{ departureCode || 'TPE' }}</span>
          </div>
          
          <!-- 飛行軌跡線 -->
          <div class="flight-trajectory">
            <div class="trajectory-line">
              <div class="trajectory-progress"></div>
            </div>
            
            <!-- 飛機圖標 -->
            <div class="flight-icon" ref="flightIcon">
              <svg class="airplane-svg" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
                <defs>
                  <linearGradient id="planeGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:#005F73;stop-opacity:1" />
                    <stop offset="100%" style="stop-color:#0A9396;stop-opacity:1" />
                  </linearGradient>
                </defs>
                <path d="M50,15 L85,35 L85,45 L50,35 L15,45 L15,35 Z M50,35 L50,75 L45,85 L55,85 Z" 
                      fill="url(#planeGradient)" class="plane-body"/>
                <path d="M30,40 L50,35 L70,40 L65,50 L50,45 L35,50 Z" 
                      fill="url(#planeGradient)" class="plane-wing"/>
              </svg>
              
              <!-- 飛機尾跡 -->
              <div class="plane-trail">
                <div class="trail-particle" v-for="i in 5" :key="i" :style="{ animationDelay: `${i * 0.1}s` }"></div>
              </div>
            </div>
            
            <!-- 路徑上的雲朵 -->
            <div class="flight-clouds">
              <div class="cloud cloud-1">☁</div>
              <div class="cloud cloud-2">☁</div>
              <div class="cloud cloud-3">☁</div>
            </div>
          </div>
          
          <div class="arrival-point">
            <div class="airport-dot arrival-dot">
              <div class="airport-ring"></div>
              <div class="airport-pulse"></div>
            </div>
            <span class="airport-label">{{ arrivalCode || 'NRT' }}</span>
          </div>
        </div>
        
        <!-- 搜尋進度指示器 -->
        <div class="search-progress">
          <div class="progress-steps">
            <div class="step" :class="{ active: currentStep >= 1, completed: currentStep > 1 }">
              <div class="step-dot">
                <span v-if="currentStep > 1">✓</span>
                <div v-else class="step-loader"></div>
              </div>
              <span class="step-label">連接航空公司</span>
            </div>
            
            <div class="progress-connector" :class="{ active: currentStep >= 2 }"></div>
            
            <div class="step" :class="{ active: currentStep >= 2, completed: currentStep > 2 }">
              <div class="step-dot">
                <span v-if="currentStep > 2">✓</span>
                <div v-else class="step-loader"></div>
              </div>
              <span class="step-label">查詢航班</span>
            </div>
            
            <div class="progress-connector" :class="{ active: currentStep >= 3 }"></div>
            
            <div class="step" :class="{ active: currentStep >= 3, completed: currentStep > 3 }">
              <div class="step-dot">
                <span v-if="currentStep > 3">✓</span>
                <div v-else class="step-loader"></div>
              </div>
              <span class="step-label">比較票價</span>
            </div>
            
            <div class="progress-connector" :class="{ active: currentStep >= 4 }"></div>
            
            <div class="step" :class="{ active: currentStep >= 4, completed: currentStep > 4 }">
              <div class="step-dot">
                <span v-if="currentStep > 4">✓</span>
                <div v-else class="step-loader"></div>
              </div>
              <span class="step-label">整理結果</span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 搜尋狀態信息 -->
      <div class="search-status">
        <h3 class="status-title">{{ currentStatusTitle }}</h3>
        <p class="status-description">{{ currentStatusDescription }}</p>
        
        <!-- 搜尋統計 -->
        <div class="search-stats">
          <div class="stat-item">
            <span class="stat-number">{{ searchedAirlines }}</span>
            <span class="stat-label">航空公司</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <span class="stat-number">{{ foundFlights }}</span>
            <span class="stat-label">找到航班</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <span class="stat-number">{{ searchDuration }}s</span>
            <span class="stat-label">搜尋時間</span>
          </div>
        </div>
      </div>
      
      <!-- 取消按鈕 -->
      <button class="cancel-search-btn" @click="$emit('cancel')" v-if="showCancelButton">
        取消搜尋
      </button>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue';

export default {
  name: 'FlightSearchLoader',
  props: {
    departureCode: {
      type: String,
      default: 'TPE'
    },
    arrivalCode: {
      type: String,  
      default: 'NRT'
    },
    showCancelButton: {
      type: Boolean,
      default: true
    }
  },
  emits: ['cancel'],
  setup() {
    const currentStep = ref(1);
    const searchedAirlines = ref(0);
    const foundFlights = ref(0);
    const searchDuration = ref(0);
    
    let stepInterval = null;
    let statsInterval = null;
    let durationInterval = null;
    
    const statusSteps = [
      {
        title: '連接航空公司...',
        description: '正在建立與各大航空公司的連接，取得最新航班資訊'
      },
      {
        title: '查詢可用航班...',
        description: '搜尋您指定日期和路線的所有可用航班'
      },
      {
        title: '比較票價...',
        description: '分析不同航空公司的價格和服務，為您找到最佳選擇'
      },
      {
        title: '整理搜尋結果...',
        description: '正在整理和排序搜尋結果，即將為您呈現最佳航班選項'
      },
      {
        title: '搜尋完成！',
        description: '已找到最適合您的航班選項，正在載入結果...'
      }
    ];
    
    const currentStatusTitle = computed(() => {
      return statusSteps[currentStep.value - 1]?.title || '搜尋中...';
    });
    
    const currentStatusDescription = computed(() => {
      return statusSteps[currentStep.value - 1]?.description || '正在處理您的搜尋請求...';
    });
    
    onMounted(() => {
      // 步驟進度動畫
      stepInterval = setInterval(() => {
        if (currentStep.value < 5) {
          currentStep.value++;
        }
      }, 3000);
      
      // 統計數據動畫
      statsInterval = setInterval(() => {
        if (searchedAirlines.value < 12) {
          searchedAirlines.value++;
        }
        if (foundFlights.value < 156 && Math.random() > 0.7) {
          foundFlights.value += Math.floor(Math.random() * 8) + 1;
        }
      }, 800);
      
      // 搜尋時間計數器
      durationInterval = setInterval(() => {
        searchDuration.value++;
      }, 1000);
    });
    
    onBeforeUnmount(() => {
      if (stepInterval) clearInterval(stepInterval);
      if (statsInterval) clearInterval(statsInterval);
      if (durationInterval) clearInterval(durationInterval);
    });
    
    return {
      currentStep,
      currentStatusTitle,
      currentStatusDescription,
      searchedAirlines,
      foundFlights,
      searchDuration
    };
  }
};
</script>

<style scoped>
.flight-search-loader-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, 
    rgba(0, 95, 115, 0.95) 0%, 
    rgba(10, 147, 150, 0.92) 50%,
    rgba(0, 95, 115, 0.95) 100%
  );
  backdrop-filter: blur(20px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  animation: fadeIn 0.5s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.loader-container {
  max-width: 800px;
  width: 90%;
  text-align: center;
  color: white;
}

/* 飛行動畫舞台 */
.flight-animation-stage {
  background: rgba(255, 255, 255, 0.08);
  border-radius: 24px;
  padding: 3rem 2rem;
  margin-bottom: 2rem;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.flight-path {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 3rem;
  position: relative;
}

/* 機場點 */
.airport-dot {
  position: relative;
  width: 20px;
  height: 20px;
  background: #F4A261;
  border-radius: 50%;
  box-shadow: 0 0 20px rgba(244, 162, 97, 0.6);
}

.airport-ring {
  position: absolute;
  top: -10px;
  left: -10px;
  width: 40px;
  height: 40px;
  border: 2px solid rgba(244, 162, 97, 0.4);
  border-radius: 50%;
  animation: airportPulse 2s ease-in-out infinite;
}

.airport-pulse {
  position: absolute;
  top: -5px;
  left: -5px;
  width: 30px;
  height: 30px;
  background: radial-gradient(circle, rgba(244, 162, 97, 0.3) 0%, transparent 70%);
  border-radius: 50%;
  animation: airportPulse 2s ease-in-out infinite 0.5s;
}

@keyframes airportPulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.5); opacity: 0.3; }
}

.airport-label {
  position: absolute;
  top: 35px;
  left: 50%;
  transform: translateX(-50%);
  font-weight: 600;
  font-size: 0.875rem;
  white-space: nowrap;
}

/* 飛行軌跡 */
.flight-trajectory {
  flex: 1;
  position: relative;
  margin: 0 2rem;
}

.trajectory-line {
  height: 2px;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 1px;
  position: relative;
  overflow: hidden;
}

.trajectory-progress {
  height: 100%;
  background: linear-gradient(90deg, #F4A261 0%, #E76F51 100%);
  border-radius: 1px;
  animation: flightProgress 8s ease-in-out infinite;
  position: relative;
}

.trajectory-progress::after {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  width: 20px;
  height: 100%;
  background: linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.8) 100%);
  animation: progressGlow 2s ease-in-out infinite;
}

@keyframes flightProgress {
  0% { width: 0%; }
  50% { width: 75%; }
  100% { width: 100%; }
}

@keyframes progressGlow {
  0%, 100% { opacity: 0; }
  50% { opacity: 1; }
}

/* 飛機圖標 */
.flight-icon {
  position: absolute;
  top: -15px;
  left: 20%;
  width: 32px;
  height: 32px;
  animation: flightMovement 8s ease-in-out infinite;
}

.airplane-svg {
  width: 100%;
  height: 100%;
  filter: drop-shadow(0 2px 8px rgba(0, 0, 0, 0.3));
}

.plane-body, .plane-wing {
  animation: planeGlow 2s ease-in-out infinite alternate;
}

@keyframes planeGlow {
  from { filter: brightness(1); }
  to { filter: brightness(1.2); }
}

@keyframes flightMovement {
  0% { left: 0%; transform: translateX(0) rotate(0deg); }
  25% { transform: translateX(0) rotate(5deg); }
  50% { left: 50%; transform: translateX(-50%) rotate(0deg); }
  75% { transform: translateX(-50%) rotate(-5deg); }
  100% { left: 100%; transform: translateX(-100%) rotate(0deg); }
}

/* 飛機尾跡 */
.plane-trail {
  position: absolute;
  top: 50%;
  left: -20px;
  width: 20px;
  height: 2px;
}

.trail-particle {
  position: absolute;
  width: 4px;
  height: 1px;
  background: rgba(244, 162, 97, 0.6);
  border-radius: 50%;
  animation: trailFade 1s ease-out infinite;
}

@keyframes trailFade {
  0% { opacity: 1; transform: translateX(0) scale(1); }
  100% { opacity: 0; transform: translateX(-20px) scale(0.5); }
}

/* 雲朵動畫 */
.flight-clouds {
  position: absolute;
  top: -30px;
  left: 0;
  right: 0;
  height: 60px;
  pointer-events: none;
}

.cloud {
  position: absolute;
  font-size: 1.5rem;
  opacity: 0.6;
  animation: cloudFloat 12s ease-in-out infinite;
}

.cloud-1 {
  left: 20%;
  animation-delay: 0s;
}

.cloud-2 {
  left: 50%;
  animation-delay: 4s;
}

.cloud-3 {
  left: 80%;
  animation-delay: 8s;
}

@keyframes cloudFloat {
  0%, 100% { transform: translateY(0) scale(1); opacity: 0.4; }
  50% { transform: translateY(-10px) scale(1.1); opacity: 0.8; }
}

/* 搜尋進度 */
.search-progress {
  margin-top: 2rem;
}

.progress-steps {
  display: flex;
  align-items: center;
  justify-content: space-between;
  max-width: 600px;
  margin: 0 auto;
}

.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  opacity: 0.5;
  transition: all 0.3s ease;
}

.step.active {
  opacity: 1;
}

.step.completed {
  opacity: 0.8;
}

.step-dot {
  width: 40px;
  height: 40px;
  border: 2px solid rgba(255, 255, 255, 0.5);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.1);
  font-weight: bold;
  transition: all 0.3s ease;
}

.step.active .step-dot {
  border-color: #F4A261;
  background: rgba(244, 162, 97, 0.2);
  box-shadow: 0 0 20px rgba(244, 162, 97, 0.4);
}

.step.completed .step-dot {
  border-color: #4ADE80;
  background: rgba(74, 222, 128, 0.2);
  color: #4ADE80;
}

.step-loader {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(244, 162, 97, 0.3);
  border-top: 2px solid #F4A261;
  border-radius: 50%;
  animation: stepSpin 1s linear infinite;
}

@keyframes stepSpin {
  to { transform: rotate(360deg); }
}

.step-label {
  font-size: 0.75rem;
  font-weight: 500;
  text-align: center;
  max-width: 80px;
  line-height: 1.2;
}

.progress-connector {
  flex: 1;
  height: 2px;
  background: rgba(255, 255, 255, 0.3);
  margin: 0 1rem;
  position: relative;
  overflow: hidden;
}

.progress-connector.active::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  background: linear-gradient(90deg, #F4A261 0%, #E76F51 100%);
  animation: connectorProgress 0.5s ease-out forwards;
}

@keyframes connectorProgress {
  from { width: 0%; }
  to { width: 100%; }
}

/* 搜尋狀態 */
.search-status {
  background: rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  padding: 2rem;
  margin-bottom: 2rem;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.status-title {
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: white;
}

.status-description {
  font-size: 1rem;
  opacity: 0.9;
  margin-bottom: 2rem;
  line-height: 1.5;
}

/* 搜尋統計 */
.search-stats {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 2rem;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
}

.stat-number {
  font-size: 2rem;
  font-weight: 700;
  color: #F4A261;
  line-height: 1;
}

.stat-label {
  font-size: 0.875rem;
  opacity: 0.8;
}

.stat-divider {
  width: 1px;
  height: 40px;
  background: rgba(255, 255, 255, 0.3);
}

/* 取消按鈕 */
.cancel-search-btn {
  padding: 0.75rem 2rem;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 12px;
  color: white;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  backdrop-filter: blur(10px);
}

.cancel-search-btn:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: translateY(-1px);
}

/* 響應式設計 */
@media (max-width: 768px) {
  .flight-animation-stage {
    padding: 2rem 1rem;
  }
  
  .flight-path {
    flex-direction: column;
    gap: 3rem;
    align-items: center;
  }
  
  .flight-trajectory {
    width: 200px;
    margin: 0;
    transform: rotate(90deg);
  }
  
  .flight-icon {
    animation: flightMovementVertical 8s ease-in-out infinite;
  }
  
  .progress-steps {
    flex-direction: column;
    gap: 1.5rem;
  }
  
  .progress-connector {
    width: 2px;
    height: 30px;
    margin: 0;
  }
  
  .search-stats {
    flex-direction: column;
    gap: 1rem;
  }
  
  .stat-divider {
    width: 40px;
    height: 1px;
  }
}

@keyframes flightMovementVertical {
  0% { top: -15px; transform: translateY(0) rotate(90deg); }
  25% { transform: translateY(0) rotate(95deg); }
  50% { top: calc(50% - 15px); transform: translateY(0) rotate(90deg); }
  75% { transform: translateY(0) rotate(85deg); }
  100% { top: calc(100% - 15px); transform: translateY(0) rotate(90deg); }
}
</style> 