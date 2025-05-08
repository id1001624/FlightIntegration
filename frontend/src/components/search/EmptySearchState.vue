<template>
  <div class="empty-search-state" ref="emptyStateContainer">
    <div class="background-gradient"></div>
    
    <div class="content-container">
      <div class="illustration-container">
        <div class="sky-animation">
          <div class="plane-container" :class="{ 'animate-plane': isVisible }">
            <div class="plane-light-effect"></div>
            <img src="@/assets/images/sky-views/flighticon.png" alt="Flight Icon" class="plane-icon-img" />
            <div class="engine-animation"></div>
          </div>
          <div class="clouds">
            <div class="cloud cloud-1"></div>
            <div class="cloud cloud-2"></div>
            <div class="cloud cloud-3"></div>
            <div class="cloud cloud-4"></div>
            <div class="cloud cloud-5"></div>
          </div>
        </div>
      </div>
      
      <div class="text-content">
        <h2 class="title">探索你的下一段旅程</h2>
        <p class="subtitle">利用我們的航班搜索引擎，尋找最佳航班選擇</p>
        
        <div class="features">
          <div class="feature">
            <div class="feature-icon price-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M18 7H22V9H18V13H16V9H12V7H16V3H18V7Z" fill="#F4A261"/>
                <path d="M2 7H10V9H2V7Z" fill="#F4A261"/>
                <path d="M6 11H10V13H6V11Z" fill="#F4A261"/>
                <path d="M2 11H4V13H2V11Z" fill="#F4A261"/>
                <path d="M2 15H10V17H2V15Z" fill="#F4A261"/>
                <path d="M14 15H16V17H14V15Z" fill="#F4A261"/>
                <path d="M18 15H22V17H18V15Z" fill="#F4A261"/>
                <path d="M10 19V21H8V19H10Z" fill="#F4A261"/>
                <path d="M14 19V21H12V19H14Z" fill="#F4A261"/>
                <path d="M18 19V21H16V19H18Z" fill="#F4A261"/>
                <path d="M22 19V21H20V19H22Z" fill="#F4A261"/>
                <path d="M6 19V21H4V19H6Z" fill="#F4A261"/>
                <path d="M2 19V21H0V19H2Z" fill="#F4A261"/>
              </svg>
            </div>
            <div class="feature-text">
              <h3>價格比較</h3>
              <p>輕鬆比較不同航空公司的價格</p>
            </div>
          </div>
          
          <div class="feature">
            <div class="feature-icon time-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M11.99 2C6.47 2 2 6.48 2 12C2 17.52 6.47 22 11.99 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 11.99 2ZM12 20C7.58 20 4 16.42 4 12C4 7.58 7.58 4 12 4C16.42 4 20 7.58 20 12C20 16.42 16.42 20 12 20ZM12.5 7H11V13L16.25 16.15L17 14.92L12.5 12.25V7Z" fill="#005F73"/>
              </svg>
            </div>
            <div class="feature-text">
              <h3>即時航班資訊</h3>
              <p>獲取最新的航班狀態和時間</p>
            </div>
          </div>
          
          <div class="feature">
            <div class="feature-icon location-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2C8.13 2 5 5.13 5 9C5 14.25 12 22 12 22C12 22 19 14.25 19 9C19 5.13 15.87 2 12 2ZM12 11.5C10.62 11.5 9.5 10.38 9.5 9C9.5 7.62 10.62 6.5 12 6.5C13.38 6.5 14.5 7.62 14.5 9C14.5 10.38 13.38 11.5 12 11.5Z" fill="#2A9D8F"/>
              </svg>
            </div>
            <div class="feature-text">
              <h3>全球航線</h3>
              <p>搜尋全台灣往返全球目的地的航班</p>
            </div>
          </div>
        </div>
        
        <div class="search-instructions">
          <div class="instruction-arrow">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M20 12L4 12" stroke="#F4A261" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M10 18L4 12L10 6" stroke="#F4A261" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <p class="instruction-text">請使用上方的搜索表單<br>填寫出發地、目的地和日期開始搜索</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';

const emptyStateContainer = ref(null);
const isVisible = ref(false);

let observer = null;

onMounted(() => {
  // 使用 Intersection Observer API 監視元素可見性
  observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        isVisible.value = true;
        // 一旦觸發動畫，可以停止觀察
        if (observer) {
          observer.disconnect();
        }
      }
    });
  }, {
    threshold: 0.3 // 當30%的元素可見時觸發
  });
  
  if (emptyStateContainer.value) {
    observer.observe(emptyStateContainer.value);
  }
});

onUnmounted(() => {
  // 組件銷毀時清理觀察者
  if (observer) {
    observer.disconnect();
  }
});
</script>

<style scoped>
.empty-search-state {
  position: relative;
  width: 100%;
  max-width: 100%; /* 適應父容器寬度 */
  margin-left: auto;
  margin-right: auto;
  min-height: 520px;
  background-color: #FFFFFF;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
  border: 1px solid #E9ECEF;
}

.background-gradient {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 250px;
  background: linear-gradient(180deg, rgba(244, 162, 97, 0.25) 0%, rgba(255, 255, 255, 0) 100%); /* 增加不透明度 */
  z-index: 0;
}

.content-container {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 2rem;
  height: 100%;
}

.illustration-container {
  width: 100%;
  height: 180px;
  position: relative;
  margin-bottom: 2.5rem;
}

.sky-animation {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.plane-container {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  left: -80px;
  z-index: 10;
  filter: drop-shadow(0 4px 6px rgba(0, 0, 0, 0.1));
  /* 移除原本的動畫，等待觸發 */
  opacity: 0;
  transition: opacity 0.5s ease;
}

.animate-plane {
  animation: flyInAndHover 8s ease-out forwards;
  opacity: 1;
}

.plane-light-effect {
  position: absolute;
  width: 8px;
  height: 8px;
  top: 30%;
  right: 10%;
  background-color: rgba(255, 255, 255, 0.9);
  border-radius: 50%;
  box-shadow: 0 0 8px 2px rgba(255, 255, 255, 0.8);
  animation: blinkLight 2s infinite;
  z-index: 1;
}

.engine-animation {
  position: absolute;
  width: 10px;
  height: 6px;
  bottom: 35%;
  right: 35%;
  background-color: rgba(240, 240, 240, 0.7);
  filter: blur(1px);
  border-radius: 3px;
  animation: engineVibration 0.2s infinite;
  z-index: 0;
}

.plane-icon-img {
  width: 120px; /* 放大飛機圖片 */
  height: 120px; /* 放大飛機圖片 */
  object-fit: contain;
  position: relative;
  z-index: 2;
}

.clouds {
  position: absolute;
  width: 100%;
  height: 100%;
}

.cloud {
  position: absolute;
  background-color: rgba(255, 255, 255, 0.9); /* 提高不透明度 */
  border-radius: 50px;
  box-shadow: 0 3px 6px rgba(0, 0, 0, 0.05); /* 加強陰影 */
}

.cloud::before,
.cloud::after {
  content: '';
  position: absolute;
  background-color: rgba(255, 255, 255, 0.9); /* 提高不透明度 */
  border-radius: 50%;
}

.cloud-1 {
  width: 100px;
  height: 30px;
  top: 30%;
  left: 110%;
  animation: moveCloud 20s linear infinite;
  animation-delay: 0s;
}

.cloud-1::before {
  width: 45px;
  height: 45px;
  top: -25px;
  left: 10px;
}

.cloud-1::after {
  width: 60px;
  height: 60px;
  top: -35px;
  left: 40px;
}

.cloud-2 {
  width: 140px;
  height: 30px;
  top: 60%;
  left: 110%;
  animation: moveCloud 25s linear infinite;
  animation-delay: 5s;
}

.cloud-2::before {
  width: 50px;
  height: 50px;
  top: -30px;
  left: 20px;
}

.cloud-2::after {
  width: 70px;
  height: 70px;
  top: -40px;
  left: 60px;
}

.cloud-3 {
  width: 120px;
  height: 25px;
  top: 40%;
  left: 110%;
  animation: moveCloud 22s linear infinite;
  animation-delay: 10s;
}

.cloud-3::before {
  width: 40px;
  height: 40px;
  top: -20px;
  left: 15px;
}

.cloud-3::after {
  width: 55px;
  height: 55px;
  top: -30px;
  left: 50px;
}

.cloud-4 {
  width: 85px;
  height: 22px;
  top: 20%;
  left: 110%;
  animation: moveCloud 19s linear infinite;
  animation-delay: 7s;
}

.cloud-4::before {
  width: 35px;
  height: 35px;
  top: -18px;
  left: 12px;
}

.cloud-4::after {
  width: 48px;
  height: 48px;
  top: -25px;
  left: 35px;
}

.cloud-5 {
  width: 110px;
  height: 24px;
  top: 70%;
  left: 110%;
  animation: moveCloud 23s linear infinite;
  animation-delay: 15s;
}

.cloud-5::before {
  width: 38px;
  height: 38px;
  top: -20px;
  left: 15px;
}

.cloud-5::after {
  width: 52px;
  height: 52px;
  top: -28px;
  left: 45px;
}

@keyframes flyInAndHover {
  0% {
    left: -80px;
    transform: translateY(-50%) rotate(0deg);
  }
  25% {
    left: 45%;
    transform: translateY(-50%) rotate(0deg);
  }
  30% { transform: translateY(-52%) rotate(1deg); }
  35% { transform: translateY(-50%) rotate(-1deg); }
  40% { transform: translateY(-51%) rotate(0.5deg); }
  45% { transform: translateY(-49%) rotate(-0.5deg); }
  50% { transform: translateY(-50%) rotate(0deg); }
  55% { transform: translateY(-51%) rotate(0.7deg); }
  60% { transform: translateY(-49%) rotate(-0.7deg); }
  65% { transform: translateY(-50%) rotate(0.3deg); }
  70% { transform: translateY(-50%) rotate(-0.3deg); }
  75% { transform: translateY(-51%) rotate(0.5deg); }
  80% { transform: translateY(-49%) rotate(-0.5deg); }
  85% { transform: translateY(-50%) rotate(0.2deg); }
  90% { transform: translateY(-50%) rotate(-0.2deg); }
  95% { transform: translateY(-50.5%) rotate(0.1deg); }
  100% { 
    left: 45%;
    transform: translateY(-50%) rotate(0deg);
  }
}

@keyframes blinkLight {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 1; }
}

@keyframes engineVibration {
  0%, 100% { transform: translate(0px, 0px); }
  25% { transform: translate(0.5px, 0.2px); }
  50% { transform: translate(0px, -0.2px); }
  75% { transform: translate(-0.5px, 0.2px); }
}

@keyframes moveCloud {
  0% {
    left: 110%;
    opacity: 0.3; /* 提高初始透明度 */
  }
  10% {
    opacity: 0.7; /* 提高移動中透明度 */
  }
  90% {
    opacity: 0.7; /* 提高移動中透明度 */
  }
  100% {
    left: -20%;
    opacity: 0.3; /* 提高結束透明度 */
  }
}

.text-content {
  text-align: center;
  max-width: 700px;
}

.title {
  font-size: 2rem;
  font-weight: 700;
  color: #212529;
  margin-bottom: 0.5rem;
}

.subtitle {
  font-size: 1.125rem;
  color: #6C757D;
  margin-bottom: 2.5rem;
}

.features {
  display: flex;
  justify-content: space-around;
  margin-bottom: 2.5rem;
  width: 100%;
}

.feature {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 30%;
}

.feature-icon {
  margin-bottom: 0.75rem;
  transform: scale(1.2);
  transition: transform 0.3s ease;
}

.feature:hover .feature-icon {
  transform: scale(1.3);
}

.price-icon {
  filter: drop-shadow(0 2px 4px rgba(244, 162, 97, 0.2));
}

.time-icon {
  filter: drop-shadow(0 2px 4px rgba(0, 95, 115, 0.2));
}

.location-icon {
  filter: drop-shadow(0 2px 4px rgba(42, 157, 143, 0.2));
}

.feature-text h3 {
  font-size: 1.125rem;
  font-weight: 600;
  color: #212529;
  margin-bottom: 0.5rem;
}

.feature-text p {
  font-size: 0.925rem;
  color: #6C757D;
  line-height: 1.4;
}

.search-instructions {
  display: flex;
  align-items: center;
  margin-top: 1.5rem;
  padding: 1rem;
  background-color: rgba(244, 162, 97, 0.05); /* 修改為 #F4A261 顏色 */
  border-radius: 8px;
}

.instruction-arrow {
  margin-right: 1.5rem;
  animation: pointUp 2s ease-in-out infinite;
}

.instruction-text {
  font-size: 1rem;
  color: #495057;
  text-align: left;
  font-weight: 500;
  line-height: 1.5;
}

@keyframes pointUp {
  0%, 100% {
    transform: translateX(0);
  }
  50% {
    transform: translateX(-5px);
  }
}

@media (max-width: 768px) {
  .empty-search-state {
    min-height: 520px;
    height: auto; /* 自適應高度 */
    max-height: none; /* 移除最大高度限制 */
    overflow: visible; /* 確保內容可見 */
  }

  .content-container {
    height: auto; /* 讓容器高度由內容決定 */
    min-height: unset; /* 移除最小高度 */
  }

  .features {
    flex-direction: column;
    align-items: center;
  }
  
  .feature {
    width: 100%;
    margin-bottom: 2rem;
  }
  
  .search-instructions {
    flex-direction: column;
    padding: 1.5rem;
  }
  
  .instruction-arrow {
    margin-right: 0;
    margin-bottom: 1rem;
    transform: rotate(90deg);
  }
  
  .instruction-text {
    text-align: center;
  }
  
  @keyframes pointUp {
    0%, 100% {
      transform: rotate(90deg) translateX(0);
    }
    50% {
      transform: rotate(90deg) translateX(-5px);
    }
  }
  
  @keyframes flyInAndHover {
    0% {
      left: -80px;
      transform: translateY(-50%) rotate(0deg);
    }
    25% {
      left: 40%;
      transform: translateY(-50%) rotate(0deg);
    }
    30% { transform: translateY(-52%) rotate(1deg); }
    100% { 
      left: 40%;
      transform: translateY(-50%) rotate(0deg);
    }
  }
}
</style> 