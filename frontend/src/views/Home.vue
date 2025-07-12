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
              <path d="M20,100 C70,50 130,180 280,80" stroke="#005F73" stroke-width="2" stroke-dasharray="5,5" />
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
            <img src="@/assets/images/sky-views/3gzzr6tf.jpg" alt="航空視圖" class="hero-image">
          </div>
        </div>
      </div>
    </section>

    <!-- 特色區塊 -->
    <section id="features" class="features-section">
      <div class="container">
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
      </div>
    </section>

    <!-- 熱門航線區塊 -->
    <PopularRoutes />
  </div>
</template>

<script>
import PopularRoutes from '@/components/specific/PopularRoutes.vue';

export default {
  name: 'HomeView',
  components: {
    PopularRoutes
  },
  mounted() {
    this.setupScrollAnimations();
  },
  methods: {
    setupScrollAnimations() {
      const animateElements = document.querySelectorAll('.animate-on-scroll');
      
      const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.classList.add('animate-visible');
            observer.unobserve(entry.target);
          }
        });
      }, {
        root: null,
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
      });
      
      animateElements.forEach(element => {
        observer.observe(element);
      });
    },
    
    startSearch() {
      this.$router.push('/search');
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
  justify-content: center;
  text-align: center;
  padding: var(--spacing-xl, 6rem) 2rem;
  gap: var(--spacing-xl, 4rem);
  position: relative;
  min-height: 550px;
  overflow: hidden;
  background-color: #ffffff;
  max-width: 1200px;
  margin: 0 auto;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
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
  margin-bottom: var(--spacing-md, 1rem);
  color: var(--color-primary, #005F73);
  position: relative;
}

.hero-title::after {
  content: '';
  position: absolute;
  bottom: -10px;
  left: 50%;
  transform: translateX(-50%);
  width: 60px;
  height: 3px;
  background-color: var(--color-secondary, #F4A261);
}

.hero-subtitle {
  font-size: 1.25rem;
  color: var(--color-text-secondary, #555);
  margin-bottom: var(--spacing-lg, 1.5rem);
  line-height: 1.5;
}

.hero-cta {
  display: flex;
  justify-content: center;
  gap: var(--spacing-md, 1rem);
}

.primary-btn {
  display: inline-flex;
  align-items: center;
  padding: var(--spacing-md, 0.8rem) var(--spacing-lg, 1.8rem);
  background-color: var(--color-primary, #005F73);
  color: white;
  font-weight: 500;
  text-decoration: none;
  border-radius: 4px;
  transition: all var(--transition-fast, 0.2s);
}

.primary-btn:hover {
  background-color: var(--color-primary-dark, #004c5a);
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 95, 115, 0.2);
}

.primary-btn .btn-icon {
  width: 18px;
  height: 18px;
  margin-left: 8px;
  transition: transform var(--transition-fast, 0.2s);
}

.primary-btn:hover .btn-icon {
  transform: translateX(4px);
}

.secondary-btn {
  display: inline-block;
  padding: var(--spacing-md, 0.8rem) var(--spacing-lg, 1.8rem);
  background-color: transparent;
  color: var(--color-primary, #005F73);
  font-weight: 500;
  text-decoration: none;
  border: 1px solid var(--color-primary, #005F73);
  border-radius: 4px;
  transition: all var(--transition-fast, 0.2s);
}

.secondary-btn:hover {
  background-color: rgba(0, 95, 115, 0.05);
  transform: translateY(-2px);
}

.hero-visual {
  flex: 1;
  position: relative;
  min-height: 400px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.journey-elements {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
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

/* 飛機飛行路徑動畫 - 修復定位 */
.journey-path {
  position: absolute;
  width: 280px;
  height: 180px;
  top: 20%;
  left: 10%;
  z-index: 1;
  opacity: 0.7;
}

.journey-path-line {
  width: 100%;
  height: 100%;
}

.journey-path-line path {
  stroke: #005F73;
  stroke-width: 2;
  stroke-dasharray: 400;
  stroke-dashoffset: 400;
  animation: drawPath 3s forwards;
}

.journey-airplane {
  position: absolute;
  width: 24px;
  height: 24px;
  color: var(--color-primary, #005F73);
  top: 55%;
  left: 7%;
  transform: translateY(-50%);
  animation: flyPlane 4s ease-in-out forwards;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3));
}

@keyframes drawPath {
  to {
    stroke-dashoffset: 0;
  }
}

@keyframes flyPlane {
  0% {
    transform: translate(0, 0) rotate(0deg);
    opacity: 0;
  }
  15% {
    opacity: 1;
  }
  100% {
    transform: translate(240px, -30px) rotate(-10deg);
    opacity: 0.8;
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
  padding: 6rem 0;
  background-color: #FFFFFF;
}

.section-title {
  text-align: center;
  font-size: 2.5rem;
  font-weight: bold;
  margin-bottom: 4rem;
  color: #004D40;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 2rem;
}

.feature-card {
  background: #F8F9FA;
  padding: 2.5rem 2rem;
  border-radius: 12px;
  text-align: center;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  border: 1px solid #E0E0E0;
}

.feature-card:hover {
  transform: translateY(-10px);
  box-shadow: 0 15px 30px rgba(0, 0, 0, 0.08);
}

.feature-icon {
  margin-bottom: 1.5rem;
  color: #00796B;
}

.feature-title {
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 1rem;
  color: #004D40;
}

.feature-description {
  font-size: 1rem;
  color: #555;
  line-height: 1.6;
}

/* 響應式設計 */
@media (max-width: 992px) {
  .hero-section {
    flex-direction: column;
    text-align: center;
    gap: 2rem;
  }

  .hero-content {
    margin-bottom: 2rem;
  }
  
  .hero-cta {
    justify-content: center;
  }

  .hero-title {
    font-size: 3rem;
  }
}

@media (max-width: 768px) {
  .hero-section, .features-section {
    padding: 4rem 1rem;
  }

  .hero-title {
    font-size: 2.5rem;
  }

  .section-title {
    font-size: 2rem;
  }

  .hero-cta {
    flex-direction: column;
    align-items: center;
  }
}
</style>