<template>
  <div class="home-container">
    <!-- 英雄區塊 -->
    <section class="hero-section">
      <div class="hero-content">
        <h1 class="hero-title animate-fade-in">探索無限旅程</h1>
        <p class="hero-subtitle animate-fade-in">整合台灣國內、離島、國際直飛航線，輕鬆規劃您的行程</p>
        <div class="hero-cta animate-fade-in animate-delay-1">
          <router-link to="/flight-search" class="primary-btn">
            <span>立即搜尋航班</span>
            <svg xmlns="http://www.w3.org/2000/svg" class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          </router-link>
          <a href="#features" class="secondary-btn">了解更多</a>
        </div>
      </div>
      <div class="hero-visual animate-fade-in animate-delay-2">
        <div class="journey-elements">
          <!-- 飛機飛行路徑元素 -->
          <div class="journey-path">
            <svg class="journey-path-line" width="100%" height="100%" viewBox="0 0 300 200" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M20,100 C70,50 130,180 280,80" stroke="currentColor" stroke-width="2" stroke-dasharray="5,5" />
            </svg>
            <div class="journey-airplane">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                <path d="M21 16v-2l-8-5V3.5c0-.83-.67-1.5-1.5-1.5S10 2.67 10 3.5V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5l8 2.5z"/>
              </svg>
            </div>
          </div>
          <!-- 雲朵漂浮元素 -->
          <div class="floating-clouds">
            <div class="cloud cloud-1"></div>
            <div class="cloud cloud-2"></div>
            <div class="cloud cloud-3"></div>
          </div>
          <!-- 主視覺圖片 -->
          <div class="visual-element">
            <img src="@/assets/images/sky-views/3gzzr6tf.png" alt="航空視圖" class="hero-image">
          </div>
        </div>
      </div>
    </section>

    <!-- 特色區塊 -->
    <section id="features" class="features-section">
      <h2 class="section-title">優質服務特色</h2>
      <div class="features-grid">
        <div class="feature-card animate-on-scroll">
          <div class="feature-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M17.8 19.2L16 11l3.5-3.5C21 6 21.5 4 21 3c-1-.5-3 0-4.5 1.5L13 8 4.8 6.2c-.5-.1-.9.1-1.1.5l-.3.5c-.2.5-.1 1 .3 1.3L9 12l-2 3H4l-1 1 3 2 2 3 1-1v-3l3-2 3.5 5.3c.3.4.8.5 1.3.3l.5-.2c.4-.3.6-.7.5-1.2z"></path>
            </svg>
          </div>
          <h3 class="feature-title">多元航線整合</h3>
          <p class="feature-description">整合台灣國內、離島及國際航線資訊，一站式查詢比較</p>
        </div>
        <div class="feature-card animate-on-scroll">
          <div class="feature-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="11" cy="11" r="8"></circle>
              <path d="M21 21l-4.35-4.35"></path>
              <path d="M8 11h6"></path>
              <path d="M11 8v6"></path>
            </svg>
          </div>
          <h3 class="feature-title">精準篩選功能</h3>
          <p class="feature-description">依時間、價格、航空公司等條件快速篩選最適合的航班</p>
        </div>
        <div class="feature-card animate-on-scroll">
          <div class="feature-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 20v-6M6 20V10M18 20V4"></path>
            </svg>
          </div>
          <h3 class="feature-title">即時價格監控</h3>
          <p class="feature-description">持續追蹤機票價格變化，把握最佳購票時機</p>
        </div>
        <div class="feature-card animate-on-scroll">
          <div class="feature-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path>
            </svg>
          </div>
          <h3 class="feature-title">專業資訊服務</h3>
          <p class="feature-description">提供航班延遲、取消等即時資訊及旅遊建議</p>
        </div>
      </div>
    </section>

    <!-- 熱門航線區塊 -->
    <section class="trending-section">
      <h2 class="section-title">熱門航線推薦</h2>
      <div class="trending-grid">
        <div class="trending-card animate-on-scroll">
          <div class="destination-image taipei"></div>
          <div class="destination-info">
            <h3 class="destination-name">台北 → 東京</h3>
            <div class="journey-line">
              <span class="journey-dot start"></span>
              <span class="journey-path-mini"></span>
              <span class="journey-dot end"></span>
            </div>
            <p class="destination-description">直飛航線，飛行時間約3小時</p>
            <p class="destination-price">NT$ 8,500 起</p>
          </div>
          <router-link to="/flight-search" class="destination-link">查看航班</router-link>
        </div>
        <div class="trending-card animate-on-scroll">
          <div class="destination-image kaohsiung"></div>
          <div class="destination-info">
            <h3 class="destination-name">高雄 → 香港</h3>
            <div class="journey-line">
              <span class="journey-dot start"></span>
              <span class="journey-path-mini"></span>
              <span class="journey-dot end"></span>
            </div>
            <p class="destination-description">直飛航線，飛行時間約1.5小時</p>
            <p class="destination-price">NT$ 6,000 起</p>
          </div>
          <router-link to="/flight-search" class="destination-link">查看航班</router-link>
        </div>
        <div class="trending-card animate-on-scroll">
          <div class="destination-image taichung"></div>
          <div class="destination-info">
            <h3 class="destination-name">台中 → 澳門</h3>
            <div class="journey-line">
              <span class="journey-dot start"></span>
              <span class="journey-path-mini"></span>
              <span class="journey-dot end"></span>
            </div>
            <p class="destination-description">直飛航線，飛行時間約2小時</p>
            <p class="destination-price">NT$ 5,800 起</p>
          </div>
          <router-link to="/flight-search" class="destination-link">查看航班</router-link>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
export default {
  name: 'HomeView',
  mounted() {
    // 監聽滾動事件，啟用滾動觸發動畫
    this.setupScrollAnimations();
  },
  methods: {
    setupScrollAnimations() {
      const animateElements = document.querySelectorAll('.animate-on-scroll');
      
      const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.classList.add('animate-visible');
            // 避免重複觸發動畫
            observer.unobserve(entry.target);
          }
        });
      }, {
        root: null, // 視口
        threshold: 0.1, // 當10%的元素可見時觸發
        rootMargin: '0px 0px -50px 0px' // 觸發位置調整
      });
      
      animateElements.forEach(element => {
        observer.observe(element);
      });
    }
  }
}
</script>

<style scoped>
/* 基本容器 */
.home-container {
  width: 100%;
}

/* 動畫類 */
.animate-fade-in {
  opacity: 0;
  animation: fadeIn 0.8s ease-out forwards;
}

.animate-delay-1 {
  animation-delay: 0.2s;
}

.animate-delay-2 {
  animation-delay: 0.4s;
}

.animate-on-scroll {
  opacity: 0;
  transform: translateY(20px);
  transition: opacity 0.6s ease-out, transform 0.6s ease-out;
}

.animate-visible {
  opacity: 1;
  transform: translateY(0);
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 英雄區塊 */
.hero-section {
  display: flex;
  align-items: center;
  padding: var(--spacing-xl) 0;
  gap: var(--spacing-xl);
  position: relative;
  min-height: 550px;
  overflow: hidden;
}

.hero-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.45);
  z-index: 0;
}

.hero-content {
  flex: 1;
  max-width: 550px;
  position: relative;
  z-index: 2;
}

.hero-title {
  font-size: 3.5rem;
  font-weight: 700;
  line-height: 1.1;
  margin-bottom: var(--spacing-md);
  color: var(--color-primary);
  position: relative;
}

.hero-title::after {
  content: '';
  position: absolute;
  bottom: -10px;
  left: 0;
  width: 60px;
  height: 3px;
  background-color: var(--color-secondary);
}

.hero-subtitle {
  font-size: 1.25rem;
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-lg);
  line-height: 1.5;
}

.hero-cta {
  display: flex;
  gap: var(--spacing-md);
}

.primary-btn {
  display: inline-flex;
  align-items: center;
  padding: var(--spacing-md) var(--spacing-lg);
  background-color: var(--color-primary);
  color: white;
  font-weight: 500;
  text-decoration: none;
  border-radius: 4px;
  transition: all var(--transition-fast);
}

.primary-btn:hover {
  background-color: var(--color-primary-dark);
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 95, 115, 0.2);
}

.primary-btn .btn-icon {
  width: 18px;
  height: 18px;
  margin-left: 8px;
  transition: transform var(--transition-fast);
}

.primary-btn:hover .btn-icon {
  transform: translateX(4px);
}

.secondary-btn {
  display: inline-block;
  padding: var(--spacing-md) var(--spacing-lg);
  background-color: transparent;
  color: var(--color-primary);
  font-weight: 500;
  text-decoration: none;
  border: 1px solid var(--color-primary);
  border-radius: 4px;
  transition: all var(--transition-fast);
}

.secondary-btn:hover {
  background-color: rgba(0, 95, 115, 0.05);
  transform: translateY(-2px);
}

.hero-visual {
  flex: 1;
  position: relative;
  min-height: 400px;
}

.journey-elements {
  position: relative;
  width: 100%;
  height: 100%;
}

.visual-element {
  width: 100%;
  max-width: 500px;
  aspect-ratio: 4/3;
  position: relative;
  overflow: hidden;
  border-radius: 8px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  transform: perspective(1000px) rotateY(-5deg) rotateX(5deg);
  transition: all 0.5s ease;
}

.visual-element:hover {
  transform: perspective(1000px) rotateY(0deg) rotateX(0deg);
}

.hero-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.5s ease;
}

.visual-element:hover .hero-image {
  transform: scale(1.05);
}

/* 飛機飛行路徑動畫 */
.journey-path {
  position: absolute;
  width: 300px;
  height: 200px;
  top: -80px;
  left: -40px;
  z-index: 1;
  color: var(--color-primary-light);
  opacity: 0.6;
}

.journey-path-line {
  stroke-dasharray: 400;
  stroke-dashoffset: 400;
  animation: drawPath 3s forwards;
}

.journey-airplane {
  position: absolute;
  width: 24px;
  height: 24px;
  color: var(--color-primary);
  top: 0;
  left: 0;
  animation: flyPlane 3s forwards;
  filter: drop-shadow(0 2px 3px rgba(0, 0, 0, 0.2));
}

@keyframes drawPath {
  to {
    stroke-dashoffset: 0;
  }
}

@keyframes flyPlane {
  0% {
    transform: translate(20px, 100px) rotate(0deg);
    opacity: 0;
  }
  10% {
    opacity: 1;
  }
  100% {
    transform: translate(280px, 80px) rotate(-15deg);
  }
}

/* 漂浮雲朵 */
.floating-clouds {
  position: absolute;
  width: 100%;
  height: 100%;
  top: 0;
  left: 0;
  pointer-events: none;
}

.cloud {
  position: absolute;
  background-color: white;
  border-radius: 50%;
  opacity: 0.7;
  z-index: 0;
  filter: blur(4px);
}

.cloud-1 {
  width: 100px;
  height: 40px;
  top: 30%;
  left: 10%;
  animation: floatCloud 15s infinite ease-in-out;
}

.cloud-2 {
  width: 80px;
  height: 30px;
  top: 60%;
  right: 20%;
  animation: floatCloud 12s infinite ease-in-out reverse;
}

.cloud-3 {
  width: 120px;
  height: 45px;
  bottom: 20%;
  left: 25%;
  animation: floatCloud 20s infinite ease-in-out;
}

@keyframes floatCloud {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(30px, -15px);
  }
}

/* 特色區塊 */
.features-section {
  padding: var(--spacing-xl) 0;
  background-color: var(--color-background);
  margin: var(--spacing-xl) 0;
  border-radius: 16px;
}

.section-title {
  font-size: 2rem;
  text-align: center;
  margin-bottom: var(--spacing-xl);
  color: var(--color-primary);
  position: relative;
}

.section-title::after {
  content: '';
  position: absolute;
  bottom: -10px;
  left: 50%;
  transform: translateX(-50%);
  width: 60px;
  height: 3px;
  background-color: var(--color-primary);
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: var(--spacing-lg);
  padding: 0 var(--spacing-lg);
}

.feature-card {
  background-color: var(--color-base);
  padding: var(--spacing-lg);
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  border-radius: 8px;
  box-shadow: var(--shadow-sm);
  transition: all var(--transition-normal);
}

.feature-card:hover {
  transform: translateY(-5px);
  box-shadow: var(--shadow-md);
}

.feature-icon {
  font-size: 2.5rem;
  margin-bottom: var(--spacing-md);
  color: var(--color-primary);
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(0, 95, 115, 0.1);
  border-radius: 50%;
  margin-bottom: var(--spacing-md);
}

.feature-title {
  font-size: 1.25rem;
  margin-bottom: var(--spacing-sm);
  color: var(--color-text-primary);
  font-weight: 600;
}

.feature-description {
  color: var(--color-text-secondary);
  line-height: 1.5;
}

/* 熱門航線區塊 */
.trending-section {
  padding: var(--spacing-xl) 0;
}

.trending-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: var(--spacing-lg);
  padding: 0 var(--spacing-lg);
}

.trending-card {
  background-color: var(--color-base);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: var(--shadow-sm);
  transition: all var(--transition-normal);
}

.trending-card:hover {
  transform: translateY(-5px);
  box-shadow: var(--shadow-md);
}

.destination-image {
  height: 180px;
  background-size: cover;
  background-position: center;
  position: relative;
}

.destination-image::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 40%;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.6), transparent);
}

.taipei {
  background-image: url('@/assets/images/cities/tokyo.png');
}

.kaohsiung {
  background-image: url('@/assets/images/cities/hongkong.png');
}

.taichung {
  background-image: url('@/assets/images/cities/macau.png');
}

.destination-info {
  padding: var(--spacing-lg);
  position: relative;
}

.destination-name {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0 0 var(--spacing-sm) 0;
  color: var(--color-text-primary);
}

/* 旅程小線條 */
.journey-line {
  display: flex;
  align-items: center;
  margin: var(--spacing-sm) 0;
  width: 80px;
}

.journey-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: var(--color-primary);
}

.journey-dot.start {
  background-color: var(--color-primary);
}

.journey-dot.end {
  background-color: var(--color-secondary);
}

.journey-path-mini {
  flex-grow: 1;
  height: 2px;
  background: linear-gradient(to right, var(--color-primary), var(--color-secondary));
  margin: 0 4px;
}

.destination-description {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  margin: var(--spacing-sm) 0;
}

.destination-price {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--color-primary);
  margin: var(--spacing-sm) 0 var(--spacing-md) 0;
}

.destination-link {
  display: inline-block;
  padding: var(--spacing-sm) var(--spacing-md);
  background-color: var(--color-primary);
  color: white;
  text-decoration: none;
  border-radius: 4px;
  font-size: 0.875rem;
  font-weight: 500;
  transition: all var(--transition-fast);
}

.destination-link:hover {
  background-color: var(--color-primary-dark);
}

/* 響應式調整 */
@media (max-width: 768px) {
  .hero-section {
    flex-direction: column;
    text-align: center;
    padding: var(--spacing-lg) var(--spacing-md);
  }
  
  .hero-content {
    max-width: 100%;
  }
  
  .hero-title {
    font-size: 2.5rem;
  }
  
  .hero-title::after {
    left: 50%;
    transform: translateX(-50%);
  }
  
  .hero-cta {
    justify-content: center;
  }
  
  .journey-path {
    display: none;
  }
  
  .visual-element {
    transform: none;
    margin: 0 auto;
  }
  
  .floating-clouds {
    display: none;
  }
}

@media (max-width: 640px) {
  .trending-grid,
  .features-grid {
    grid-template-columns: 1fr;
  }
  
  .section-title {
    font-size: 1.75rem;
  }
  
  .hero-cta {
    flex-direction: column;
    gap: var(--spacing-sm);
  }
  
  .primary-btn, .secondary-btn {
    width: 100%;
  }
}
</style>