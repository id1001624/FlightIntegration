<template>
  <div class="home-container">
    <!-- 英雄區塊 -->
    <section class="hero-section">
      <div class="hero-content">
        <h1 class="hero-title">探索無限旅程</h1>
        <p class="hero-subtitle">整合台灣國內、離島、國際直飛航線，輕鬆規劃您的行程</p>
        <div class="hero-cta">
          <router-link to="/flight-search" class="primary-btn">立即搜尋航班</router-link>
          <a href="#features" class="secondary-btn">了解更多</a>
        </div>
      </div>
      <div class="hero-visual">
        <div class="visual-element">
          <img src="@/assets/images/sky-views/3gzzr6tf.png" alt="航空視圖" class="hero-image">
        </div>
      </div>
    </section>

    <!-- 特色區塊 -->
    <section id="features" class="features-section">
      <h2 class="section-title">優質服務特色</h2>
      <div class="features-grid">
        <div class="feature-card">
          <div class="feature-icon">✈</div>
          <h3 class="feature-title">多元航線整合</h3>
          <p class="feature-description">整合台灣國內、離島及國際航線資訊，一站式查詢比較</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">🔍</div>
          <h3 class="feature-title">精準篩選功能</h3>
          <p class="feature-description">依時間、價格、航空公司等條件快速篩選最適合的航班</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">📊</div>
          <h3 class="feature-title">即時價格監控</h3>
          <p class="feature-description">持續追蹤機票價格變化，把握最佳購票時機</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">🌟</div>
          <h3 class="feature-title">專業資訊服務</h3>
          <p class="feature-description">提供航班延遲、取消等即時資訊及旅遊建議</p>
        </div>
      </div>
    </section>

    <!-- 熱門航線區塊 -->
    <section class="trending-section">
      <h2 class="section-title">熱門航線推薦</h2>
      <div class="trending-grid">
        <div class="trending-card">
          <div class="destination-image taipei"></div>
          <div class="destination-info">
            <h3 class="destination-name">台北 → 東京</h3>
            <p class="destination-description">直飛航線，飛行時間約3小時</p>
            <p class="destination-price">NT$ 8,500 起</p>
          </div>
          <router-link to="/flight-search" class="destination-link">查看航班</router-link>
        </div>
        <div class="trending-card">
          <div class="destination-image kaohsiung"></div>
          <div class="destination-info">
            <h3 class="destination-name">高雄 → 香港</h3>
            <p class="destination-description">直飛航線，飛行時間約1.5小時</p>
            <p class="destination-price">NT$ 6,000 起</p>
          </div>
          <router-link to="/flight-search" class="destination-link">查看航班</router-link>
        </div>
        <div class="trending-card">
          <div class="destination-image taichung"></div>
          <div class="destination-info">
            <h3 class="destination-name">台中 → 澳門</h3>
            <p class="destination-description">直飛航線，飛行時間約2小時</p>
            <p class="destination-price">NT$ 5,800 起</p>
          </div>
          <router-link to="/flight-search" class="destination-link">查看航班</router-link>
        </div>
      </div>
    </section>

    <!-- 合作夥伴區塊 -->
    <section class="partners-section">
      <h2 class="section-title">合作航空公司</h2>
      <div class="partners-grid">
        <div class="partner-logo">中華航空</div>
        <div class="partner-logo">長榮航空</div>
        <div class="partner-logo">立榮航空</div>
        <div class="partner-logo">華信航空</div>
        <div class="partner-logo">星宇航空</div>
      </div>
    </section>
  </div>
</template>

<script>
export default {
  name: 'HomeView',
}
</script>

<style scoped>
.home-container {
  width: 100%;
}

/* 英雄區塊 */
.hero-section {
  display: flex;
  align-items: center;
  padding: var(--spacing-xl) 0;
  gap: var(--spacing-xl);
  position: relative;
  min-height: 500px;
}

.hero-content {
  flex: 1;
  max-width: 600px;
}

.hero-title {
  font-size: 3rem;
  font-weight: 700;
  line-height: 1.1;
  margin-bottom: var(--spacing-md);
  color: var(--color-primary);
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
  display: inline-block;
  padding: var(--spacing-md) var(--spacing-lg);
  background-color: var(--color-primary);
  color: white;
  font-weight: 500;
  text-decoration: none;
  transition: background-color var(--transition-fast);
}

.primary-btn:hover {
  background-color: var(--color-secondary);
}

.secondary-btn {
  display: inline-block;
  padding: var(--spacing-md) var(--spacing-lg);
  background-color: transparent;
  color: var(--color-primary);
  font-weight: 500;
  text-decoration: none;
  border: 1px solid var(--color-primary);
  transition: all var(--transition-fast);
}

.secondary-btn:hover {
  background-color: rgba(0, 95, 115, 0.05);
}

.hero-visual {
  flex: 1;
  display: flex;
  justify-content: flex-end;
  align-items: center;
}

.visual-element {
  width: 100%;
  max-width: 500px;
  aspect-ratio: 4/3;
  position: relative;
  overflow: hidden;
}

.hero-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 8px;
}

/* 特色區塊 */
.features-section {
  padding: var(--spacing-xl) 0;
  background-color: var(--color-background);
  margin: var(--spacing-xl) 0;
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
}

.feature-card {
  background-color: var(--color-white);
  padding: var(--spacing-lg);
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.feature-icon {
  font-size: 2.5rem;
  margin-bottom: var(--spacing-md);
  color: var(--color-primary);
}

.feature-title {
  font-size: 1.25rem;
  margin-bottom: var(--spacing-sm);
  color: var(--color-text-primary);
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
}

.trending-card {
  background-color: var(--color-white);
  overflow: hidden;
  position: relative;
}

.destination-image {
  width: 100%;
  height: 200px;
  background-size: cover;
  background-position: center;
}

.destination-image.taipei {
  background-image: url('/src/assets/images/taipei.jpg');
  background-color: var(--color-primary); /* 作為備用 */
}

.destination-image.kaohsiung {
  background-image: url('/src/assets/images/kaohsiung.jpg');
  background-color: var(--color-secondary); /* 作為備用 */
}

.destination-image.taichung {
  background-image: url('/src/assets/images/taichung.jpg');
  background-color: var(--color-accent); /* 作為備用 */
}

.destination-info {
  padding: var(--spacing-md);
}

.destination-name {
  font-size: 1.25rem;
  margin-bottom: var(--spacing-xs);
  font-weight: 600;
}

.destination-description {
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-sm);
  font-size: 0.9rem;
}

.destination-price {
  color: var(--color-primary);
  font-weight: 600;
  margin-bottom: var(--spacing-sm);
}

.destination-link {
  display: block;
  padding: var(--spacing-sm) var(--spacing-md);
  text-align: center;
  background-color: var(--color-primary);
  color: white;
  text-decoration: none;
  transition: background-color var(--transition-fast);
}

.destination-link:hover {
  background-color: var(--color-secondary);
}

/* 合作夥伴區塊 */
.partners-section {
  padding: var(--spacing-xl) 0;
  background-color: var(--color-background);
  margin-bottom: var(--spacing-xl);
}

.partners-grid {
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--spacing-lg);
}

.partner-logo {
  flex: 1;
  min-width: 150px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--color-white);
  color: var(--color-text-secondary);
  font-weight: 500;
}

/* 媒體查詢 */
@media (max-width: 992px) {
  .hero-section {
    flex-direction: column;
    text-align: center;
  }
  
  .hero-content {
    max-width: 100%;
  }
  
  .hero-cta {
    justify-content: center;
  }
  
  .visual-element {
    margin-top: var(--spacing-lg);
  }
  
  .partners-grid {
    justify-content: center;
  }
}

@media (max-width: 768px) {
  .hero-title {
    font-size: 2.5rem;
  }
  
  .hero-subtitle {
    font-size: 1.1rem;
  }
  
  .features-grid,
  .trending-grid {
    grid-template-columns: 1fr;
  }
}
</style>