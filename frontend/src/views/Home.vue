<template>
  <div class="home-container">
    <!-- 英雄區塊 -->
    <section class="hero-section">
      <div class="container hero-container-flex">
        <div class="hero-content">
          <h1 class="hero-title animate-fade-in">探索無限旅程</h1>
          <p class="hero-subtitle animate-fade-in">整合台灣國內、離島、國際直飛航線，輕鬆規劃您的行程</p>
          <div class="hero-cta animate-fade-in animate-delay-1">
            <button @click="startSearch" class="primary-btn">
              <span>立即搜尋航班</span>
              <svg xmlns="http://www.w3.org/2000/svg" class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M5 12h14M12 5l7 7-7 7" />
              </svg>
            </button>
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
            <!-- 漂浮雲朵 -->
            <div class="floating-clouds">
              <div class="cloud cloud-1"></div>
              <div class="cloud cloud-2"></div>
              <div class="cloud cloud-3"></div>
            </div>
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
/* 全局容器和佈局 */
.home-container {
  background-color: #F0F4F8;
  color: #333;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1.5rem;
}

/* 英雄區塊 */
.hero-section {
  background: linear-gradient(135deg, #E0F7FA 0%, #B2EBF2 100%);
  padding: 6rem 0;
  overflow: hidden;
  position: relative;
}

.hero-container-flex {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 2rem;
}

.hero-content {
  flex-basis: 50%;
  z-index: 10;
}

.hero-title {
  font-size: 3.5rem;
  font-weight: bold;
  color: #004D40;
  margin-bottom: 1rem;
  line-height: 1.2;
}

.hero-subtitle {
  font-size: 1.25rem;
  color: #00796B;
  margin-bottom: 2.5rem;
}

.hero-cta {
  display: flex;
  gap: 1.5rem;
}

.primary-btn, .secondary-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.8rem 1.8rem;
  border-radius: 50px;
  font-weight: 600;
  text-decoration: none;
  transition: all 0.3s ease;
  cursor: pointer;
}

.primary-btn {
  background-color: #00796B;
  color: white;
  border: 2px solid #00796B;
}

.primary-btn:hover {
  background-color: #004D40;
  border-color: #004D40;
  transform: translateY(-3px);
  box-shadow: 0 8px 20px rgba(0, 77, 64, 0.25);
}

.btn-icon {
  transition: transform 0.3s ease;
}

.primary-btn:hover .btn-icon {
  transform: translateX(4px);
}

.secondary-btn {
  background-color: transparent;
  color: #00796B;
  border: 2px solid #00796B;
}

.secondary-btn:hover {
  background-color: #00796B;
  color: white;
  transform: translateY(-3px);
  box-shadow: 0 8px 20px rgba(0, 121, 107, 0.2);
}

/* 視覺動畫區塊 */
.hero-visual {
  flex-basis: 50%;
  position: relative;
  min-height: 300px;
}

.journey-elements {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 100%;
  height: 100%;
}

/* 飛行路徑動畫 */
.journey-path {
  position: absolute;
  width: 100%;
  height: 100%;
  color: #00796B;
}

.journey-path-line path {
  stroke-dasharray: 410;
  stroke-dashoffset: 410;
  animation: drawPath 4s ease-in-out 1s forwards;
}

@keyframes drawPath {
  to {
    stroke-dashoffset: 0;
  }
}

.journey-airplane {
  position: absolute;
  color: #D32F2F;
  offset-path: path('M20,100 C70,50 130,180 280,80');
  animation: flyPlane 4s ease-in-out 1s forwards;
  opacity: 0;
}

@keyframes flyPlane {
  0% {
    offset-distance: 0%;
    opacity: 1;
  }
  100% {
    offset-distance: 100%;
    opacity: 1;
  }
}

/* 漂浮雲朵動畫 */
.floating-clouds {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: -1;
}

.cloud {
  position: absolute;
  background: white;
  border-radius: 50px;
  opacity: 0.6;
  animation: floatCloud 20s linear infinite;
}

.cloud-1 {
  width: 120px;
  height: 40px;
  top: 20%;
  left: -150px;
  animation-duration: 25s;
  animation-delay: -5s;
}

.cloud-2 {
  width: 80px;
  height: 30px;
  top: 40%;
  left: -100px;
  animation-duration: 20s;
  animation-delay: 0s;
}

.cloud-3 {
  width: 100px;
  height: 35px;
  top: 70%;
  left: -120px;
  animation-duration: 18s;
  animation-delay: -10s;
}

@keyframes floatCloud {
  from {
    transform: translateX(0);
  }
  to {
    transform: translateX(calc(1200px + 150px));
  }
}


/* 通用淡入動畫 */
.animate-fade-in {
  opacity: 0;
  animation: fadeIn 0.8s ease-out forwards;
}

@keyframes fadeIn {
  to {
    opacity: 1;
  }
}

.animate-delay-1 { animation-delay: 0.3s; }
.animate-delay-2 { animation-delay: 0.6s; }


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
  .hero-container-flex {
    flex-direction: column;
    text-align: center;
  }

  .hero-content {
    margin-bottom: 4rem;
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
    padding: 4rem 0;
  }

  .hero-title {
    font-size: 2.5rem;
  }

  .section-title {
    font-size: 2rem;
  }
}
</style>