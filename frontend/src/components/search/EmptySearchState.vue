<template>
  <div class="empty-search-state">
    <div class="background-gradient"></div>
    
    <div class="content-container">
      <div class="illustration-container">
        <div class="sky-animation">
          <div class="plane-container">
            <svg class="plane" viewBox="0 0 24 24" width="60" height="60">
              <path d="M22,16.21V14.67L12,9V3.5A1.5,1.5,0,0,0,10.5,2h0A1.5,1.5,0,0,0,9,3.5V9L1.46,13.67v1.55l7.54-1.34V21l-2,1.5v1.77L11.56,23l4.56,1.27V22.5L14,21V13.89Z" fill="#005F73"/>
              <path d="M10.58,4.2h0a.76.76,0,0,1,.76.76V9a.27.27,0,0,1-.16.24L5.17,12.12a.25.25,0,0,1-.33-.33l5-7.35A.74.74,0,0,1,10.58,4.2Z" fill="#e0f2f1"/>
            </svg>
          </div>
          <div class="clouds">
            <div class="cloud cloud-1"></div>
            <div class="cloud cloud-2"></div>
            <div class="cloud cloud-3"></div>
          </div>
        </div>
      </div>
      
      <div class="text-content">
        <h2 class="title">探索你的下一段旅程</h2>
        <p class="subtitle">利用我們的航班搜索引擎，尋找最佳航班選擇</p>
        
        <div class="features">
          <div class="feature">
            <div class="feature-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2ZM13.41 18.09V20H10.74V18.07C9.03 17.71 7.58 16.61 7.05 14.9L9.17 14C9.55 15.09 10.43 15.97 12 15.97C13.95 15.97 15.15 14.63 15.15 13.11C15.15 11.79 14.29 10.86 12.53 10.37L11.46 10.08C10.34 9.78 9.94 9.36 9.94 8.71C9.94 7.93 10.55 7.4 11.56 7.4C12.69 7.4 13.31 8.05 13.59 8.9L15.59 8.07C15.08 6.58 13.93 5.69 12.03 5.51V4H9.36V5.51C7.79 5.84 6.47 7.05 6.47 8.77C6.47 10.4 7.58 11.5 9.44 12.03L10.4 12.29C11.85 12.65 12.35 13.13 12.35 13.88C12.35 14.69 11.74 15.27 10.58 15.27C9.35 15.27 8.39 14.67 8.04 13.67L6 14.5C6.54 16.29 7.86 17.4 10.74 17.95V18.09H13.41Z" fill="#005F73"/>
              </svg>
            </div>
            <div class="feature-text">
              <h3>價格比較</h3>
              <p>輕鬆比較不同航空公司的價格</p>
            </div>
          </div>
          
          <div class="feature">
            <div class="feature-icon">
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
            <div class="feature-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2C8.13 2 5 5.13 5 9C5 14.25 12 22 12 22C12 22 19 14.25 19 9C19 5.13 15.87 2 12 2ZM12 11.5C10.62 11.5 9.5 10.38 9.5 9C9.5 7.62 10.62 6.5 12 6.5C13.38 6.5 14.5 7.62 14.5 9C14.5 10.38 13.38 11.5 12 11.5Z" fill="#005F73"/>
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
              <path d="M20 12L4 12" stroke="#005F73" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M10 18L4 12L10 6" stroke="#005F73" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <p class="instruction-text">請使用上方的搜索表單<br>填寫出發地、目的地和日期開始搜索</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
// 無需額外的腳本邏輯
</script>

<style scoped>
.empty-search-state {
  position: relative;
  width: 100%;
  max-width: 1160px;
  margin: 0 auto;
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
  background: linear-gradient(180deg, rgba(0, 95, 115, 0.05) 0%, rgba(255, 255, 255, 0) 100%);
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
  left: 20%;
  transform: translateY(-50%);
  z-index: 10;
  filter: drop-shadow(0 4px 6px rgba(0, 0, 0, 0.1));
  animation: flyAndTilt 12s ease-in-out infinite;
}

.plane {
  transform-origin: center;
}

.clouds {
  position: absolute;
  width: 100%;
  height: 100%;
}

.cloud {
  position: absolute;
  background-color: rgba(255, 255, 255, 0.9);
  border-radius: 50px;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
}

.cloud::before,
.cloud::after {
  content: '';
  position: absolute;
  background-color: rgba(255, 255, 255, 0.9);
  border-radius: 50%;
}

.cloud-1 {
  width: 100px;
  height: 30px;
  top: 30%;
  left: 10%;
  animation: moveCloud 20s linear infinite;
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
  left: 35%;
  animation: moveCloud 25s linear infinite;
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
  left: 65%;
  animation: moveCloud 22s linear infinite;
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

@keyframes flyAndTilt {
  0% {
    transform: translate(-5%, -50%) rotate(-2deg);
  }
  25% {
    transform: translate(25%, -45%) rotate(3deg);
  }
  50% {
    transform: translate(60%, -50%) rotate(-1deg);
  }
  75% {
    transform: translate(25%, -55%) rotate(2deg);
  }
  100% {
    transform: translate(-5%, -50%) rotate(-2deg);
  }
}

@keyframes moveCloud {
  0% {
    transform: translateX(0);
  }
  100% {
    transform: translateX(-100vw);
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
  background-color: rgba(0, 95, 115, 0.05);
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

/* 響應式設計 */
@media (max-width: 768px) {
  .empty-search-state {
    min-height: 700px;
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
}
</style> 