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
            <svg class="journey-path-line" width="100%" height="100%" viewBox="0 0 200 120" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M10,70 C50,30 90,90 180,40" stroke="#005F73" stroke-width="2" stroke-dasharray="5,5" />
            </svg>
            <div class="journey-airplane">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
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
      <div class="features-container">
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
  padding: 3rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 4rem;
  min-height: 100vh;
}

/* 統一區塊寬度 */
.hero-section,
.features-section,
.popular-routes-section {
  max-width: 1200px;
  margin: 0 auto;
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
  background: rgba(255, 255, 255, 0.95);
  border-radius: 24px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4rem 3rem;
  gap: 3rem;
  position: relative;
  min-height: 500px;
}

.hero-content {
  flex: 1;
  max-width: 550px;
  position: relative;
  z-index: 2;
  text-align: left;
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
  left: 0;
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
  justify-content: flex-start;
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

/* 飛機飛行路徑動畫 - 修復定位到左上角 */
.journey-path {
  position: absolute;
  width: 200px;
  height: 120px;
  top: 5%;
  left: 5%;
  z-index: 2;
  opacity: 0.8;
}

.journey-path-line {
  width: 100%;
  height: 100%;
}

.journey-path-line path {
  stroke: #005F73;
  stroke-width: 2;
  stroke-dasharray: 300;
  stroke-dashoffset: 300;
  animation: drawPath 3s ease-out forwards;
}

.journey-airplane {
  position: absolute;
  width: 20px;
  height: 20px;
  color: var(--color-primary, #005F73);
  top: 60%;
  left: 5%;
  transform: translateY(-50%);
  animation: flyPlane 4s ease-in-out forwards;
  filter: drop-shadow(0 2px 6px rgba(0, 95, 115, 0.4));
}

@keyframes drawPath {
  0% {
    stroke-dashoffset: 300;
    opacity: 0.3;
  }
  100% {
    stroke-dashoffset: 0;
    opacity: 1;
  }
}

@keyframes flyPlane {
  0% {
    transform: translate(0, 0) rotate(0deg);
    opacity: 0;
  }
  20% {
    opacity: 1;
  }
  100% {
    transform: translate(160px, -20px) rotate(-8deg);
    opacity: 0.9;
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
  padding: 0 2rem;
  position: relative;
}

.features-container {
  background: rgba(255, 255, 255, 0.95);
  padding: 4rem 3rem;
  border-radius: 24px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.section-title {
  text-align: center;
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 3rem;
  color: var(--color-primary, #005F73);
  position: relative;
}

.section-title::after {
  content: '';
  position: absolute;
  bottom: -1rem;
  left: 50%;
  transform: translateX(-50%);
  width: 80px;
  height: 4px;
  background: linear-gradient(90deg, var(--color-primary, #005F73), var(--color-secondary, #F4A261));
  border-radius: 2px;
}

/* 移除標題裝飾線條以保持簡潔設計 */

.features-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1.5rem;
  width: 100%;
}

.feature-card {
  background: #FFFFFF !important;
  padding: 3rem 2rem;
  border-radius: 20px !important;
  text-align: center;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid rgba(229, 231, 235, 0.6) !important;
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.08) !important,
    0 2px 8px rgba(0, 0, 0, 0.04) !important;
  position: relative;
  overflow: hidden !important;
  min-height: 340px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  cursor: pointer;
}

/* 移除卡片頂部裝飾條以保持簡潔設計 */

.feature-card:hover {
  transform: translateY(-12px) scale(1.02);
  box-shadow:
    0 20px 60px rgba(0, 95, 115, 0.15) !important,
    0 8px 16px rgba(0, 0, 0, 0.08) !important;
  border-color: rgba(0, 95, 115, 0.2) !important;
}

.feature-icon {
  margin-bottom: 1.5rem;
  color: var(--color-primary, #005F73);
  transition: all 0.3s ease;
}

.feature-card:hover .feature-icon {
  transform: scale(1.1);
  color: var(--color-secondary, #F4A261);
}

.feature-title {
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 1rem;
  color: var(--color-primary, #005F73);
  transition: color 0.3s ease;
}

.feature-description {
  font-size: 1rem;
  color: #64748b;
  line-height: 1.6;
  transition: color 0.3s ease;
}

/* 強制圓角樣式 - 參考 PopularRoutes 成功實現 */
.features-section .feature-card {
  border-radius: 20px !important;
  -webkit-border-radius: 20px !important;
  -moz-border-radius: 20px !important;
  -ms-border-radius: 20px !important;
  -o-border-radius: 20px !important;
  box-sizing: border-box !important;
  overflow: hidden !important;
}

/* 覆蓋可能的 Tailwind 樣式 */
.features-section .feature-card.card {
  border-radius: 20px !important;
}

/* 偽元素已移除，無需額外圓角設定 */

/* 響應式設計 */
@media (max-width: 1200px) {
  .home-container {
    padding: 2rem 1rem;
    gap: 3rem;
  }

  .hero-section,
  .features-section,
  .popular-routes-section {
    margin: 0 1rem;
  }

  .hero-section {
    padding: 3rem 2rem;
    min-height: 400px;
  }

  .features-section {
    padding: 3rem 2rem;
  }

  .features-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 1.5rem;
  }

  .feature-card {
    padding: 2rem 1.5rem;
    min-height: 260px;
  }
}

@media (max-width: 992px) {
  .home-container {
    gap: 2.5rem;
  }

  .hero-section {
    flex-direction: column;
    text-align: center;
    gap: 2rem;
    padding: 3rem 2rem;
    min-height: 350px;
  }

  .hero-content {
    margin-bottom: 2rem;
    text-align: center;
  }

  .hero-title::after {
    left: 50%;
    transform: translateX(-50%);
  }

  .hero-cta {
    justify-content: center;
  }

  .features-section {
    padding: 2.5rem 2rem;
  }

  .hero-title {
    font-size: 3rem;
  }

  .features-container {
    padding: 0 1rem;
  }

  .features-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 1.5rem;
  }

  .journey-path {
    width: 150px;
    height: 100px;
    top: 8%;
    left: 8%;
  }

  .journey-airplane {
    width: 18px;
    height: 18px;
  }
}

@media (max-width: 768px) {
  .hero-section {
    padding: 3rem 1rem;
  }

  .features-section {
    padding: 2rem 1rem;
  }

  .features-container {
    padding: 2rem;
  }

  .hero-title {
    font-size: 2.5rem;
  }

  .section-title {
    font-size: 2rem;
    margin-bottom: 3rem;
  }

  .hero-cta {
    flex-direction: column;
    align-items: center;
    gap: 1rem;
  }

  .features-grid {
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }

  .feature-card {
    padding: 2rem 1.5rem;
    margin: 0 auto;
    max-width: 100%;
    min-height: 240px;
    border-radius: 20px !important;
  }

  .journey-path {
    display: none; /* 在小螢幕隱藏動畫避免干擾 */
  }
}

@media (max-width: 768px) {
  .home-container {
    padding: 1.5rem 0.5rem;
    gap: 2rem;
  }

  .hero-section,
  .features-section,
  .popular-routes-section {
    margin: 0 0.5rem;
  }

  .hero-section {
    padding: 2.5rem 1.5rem;
    min-height: 300px;
  }

  .features-section {
    padding: 2.5rem 1.5rem;
  }

  .features-grid {
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }
}

@media (max-width: 480px) {
  .home-container {
    padding: 1rem 0.25rem;
    gap: 1.5rem;
  }

  .hero-section,
  .features-section,
  .popular-routes-section {
    margin: 0 0.25rem;
  }

  .hero-section {
    padding: 2rem 1rem;
    min-height: 250px;
  }

  .features-section {
    padding: 2rem 1rem;
  }

  .feature-card {
    padding: 1.5rem 1rem;
    min-height: 200px;
  }

  .feature-title {
    font-size: 1.25rem;
  }

  .feature-description {
    font-size: 0.9rem;
  }
}
</style>