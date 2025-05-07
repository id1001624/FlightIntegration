<template>
  <div class="empty-search-state">
    <div class="background-gradient"></div>
    
    <div class="content-container">
      <div class="illustration-container">
        <div class="airplane-animation">
          <div class="airplane">
            <svg width="50" height="50" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M21 16V14L13 9V3.5C13 2.67 12.33 2 11.5 2C10.67 2 10 2.67 10 3.5V9L2 14V16L10 13.5V19L8 20.5V22L11.5 21L15 22V20.5L13 19V13.5L21 16Z" fill="#F4A261"/>
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
// 無需額外的腳本邏輯
</script>

<style scoped>
.empty-search-state {
  position: relative;
  height: 500px;
  width: 100%;
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
  height: 200px;
  background: linear-gradient(180deg, rgba(244, 162, 97, 0.15) 0%, rgba(255, 255, 255, 0) 100%);
  z-index: 0;
}

.content-container {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  height: 100%;
}

.illustration-container {
  width: 100%;
  height: 150px;
  position: relative;
  margin-bottom: 2rem;
}

.airplane-animation {
  position: relative;
  width: 100%;
  height: 100%;
}

.airplane {
  position: absolute;
  left: 10%;
  top: 50%;
  transform: translateY(-50%);
  animation: fly 20s linear infinite;
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

.cloud-1 {
  width: 80px;
  height: 20px;
  top: 40%;
  left: 20%;
  animation: moveCloud 25s linear infinite;
}

.cloud-2 {
  width: 120px;
  height: 30px;
  top: 30%;
  left: 50%;
  animation: moveCloud 30s linear infinite;
}

.cloud-3 {
  width: 60px;
  height: 15px;
  top: 60%;
  left: 70%;
  animation: moveCloud 22s linear infinite;
}

@keyframes fly {
  0% {
    left: -5%;
    transform: translateY(-50%) rotate(5deg);
  }
  50% {
    left: 105%;
    transform: translateY(-50%) rotate(-5deg);
  }
  50.01% {
    left: -5%;
    transform: translateY(-50%) rotate(5deg);
  }
  100% {
    left: 105%;
    transform: translateY(-50%) rotate(-5deg);
  }
}

@keyframes moveCloud {
  0% {
    transform: translateX(0);
  }
  100% {
    transform: translateX(-400%);
  }
}

.text-content {
  text-align: center;
  max-width: 600px;
}

.title {
  font-size: 1.75rem;
  font-weight: 700;
  color: #212529;
  margin-bottom: 0.5rem;
}

.subtitle {
  font-size: 1rem;
  color: #6C757D;
  margin-bottom: 2rem;
}

.features {
  display: flex;
  justify-content: space-around;
  margin-bottom: 2rem;
  width: 100%;
}

.feature {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 30%;
}

.feature-icon {
  margin-bottom: 0.5rem;
}

.feature-text h3 {
  font-size: 1rem;
  font-weight: 600;
  color: #212529;
  margin-bottom: 0.25rem;
}

.feature-text p {
  font-size: 0.875rem;
  color: #6C757D;
}

.search-instructions {
  display: flex;
  align-items: center;
  margin-top: 1rem;
}

.instruction-arrow {
  margin-right: 1rem;
  animation: pointUp 2s ease-in-out infinite;
}

.instruction-text {
  font-size: 0.875rem;
  color: #6C757D;
  text-align: left;
  font-weight: 500;
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
  .features {
    flex-direction: column;
    align-items: center;
  }
  
  .feature {
    width: 100%;
    margin-bottom: 1.5rem;
  }
  
  .search-instructions {
    flex-direction: column;
  }
  
  .instruction-arrow {
    margin-right: 0;
    margin-bottom: 0.5rem;
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