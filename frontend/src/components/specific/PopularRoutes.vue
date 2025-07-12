<template>
  <section class="popular-routes">
    <div class="routes-container">
      <!-- Typography-driven 標題 -->
      <div class="section-header">
        <div class="header-content">
          <h2 class="section-title">熱門航線</h2>
          <p class="section-subtitle">
            探索最受歡迎的目的地，開始您的專業旅程
          </p>
          </div>
          
        <!-- 分類篩選 - 無 icons 的按鈕設計 -->
        <div class="category-filters">
            <button 
            v-for="category in routeCategories"
            :key="category.id"
            :class="['filter-btn', { active: activeCategory === category.id }]"
            @click="setActiveCategory(category.id)"
          >
            <span class="btn-text">{{ category.name }}</span>
            <div class="btn-accent"></div>
            </button>
          </div>
        </div>
        
      <!-- 路線網格 -->
      <div class="routes-grid" :class="gridLayoutClass">
        <div
          v-for="route in filteredRoutes"
          :key="`${route.fromCode}-${route.toCode}`"
          class="route-card"
          @click="handleRouteClick(route)"
        >
          <!-- 卡片背景圖片 -->
          <div class="card-background">
            <img
              :src="route.image"
              :alt="`${route.to} 風景`"
              class="background-image"
            />
            <div class="image-overlay"></div>
          </div>

          <!-- 卡片內容 - Typography-driven -->
          <div class="card-content">
            <div class="content-background">
              <!-- 路線資訊 -->
              <div class="route-info">
                <div class="route-path">
                  <span class="departure-city">{{ route.from }}</span>
                  <div class="route-line">
                    <div class="line-graphic"></div>
                    <div class="route-direction"></div>
              </div>
                  <span class="arrival-city">{{ route.to }}</span>
                </div>
                
                <div class="route-codes">
                  <span class="airport-code departure-code">{{ route.fromCode }}</span>
                  <span class="airport-code arrival-code">{{ route.toCode }}</span>
                </div>
              </div>

              <!-- 航班詳情 -->
              <div class="flight-details">
                <div class="detail-item">
                  <span class="detail-label">飛行時間</span>
                  <span class="detail-value">{{ route.duration }}</span>
        </div>

                <div class="detail-item">
                  <span class="detail-label">每日航班</span>
                  <span class="detail-value">{{ route.flightCount }} 班/日</span>
          </div>
              </div>

              <!-- 價格與標籤 -->
              <div class="card-bottom">
                <div class="price-section">
                  <span class="price-label">起價</span>
                  <span class="price-value">NT$ {{ route.price.toLocaleString() }}</span>
                </div>
                
                <div class="route-badges">
                  <span v-if="route.isDirect" class="badge direct-badge">直飛</span>
                  <span v-if="route.bestPrice" class="badge price-badge">最優價</span>
                  <span v-if="route.isPopular" class="badge popular-badge">熱門</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 懸停效果 -->
          <div class="card-hover-effect"></div>
        </div>
      </div>

      <!-- 空狀態 -->
      <div v-if="filteredRoutes.length === 0" class="empty-state">
        <div class="empty-content">
          <h3 class="empty-title">暫無航線資料</h3>
          <p class="empty-description">請嘗試其他分類或稍後再試</p>
        </div>
      </div>
    </div>
  </section>
</template>

<script>
import { ref, computed, onMounted } from 'vue'

export default {
  name: 'PopularRoutes',
  setup() {
    const activeCategory = ref('all')

    // 路線分類 - 移除國內
    const routeCategories = ref([
      { id: 'all', name: '全部' },
      { id: 'asia', name: '亞洲' },
      { id: 'international', name: '國際' }
    ])

    // 熱門路線數據 - 高質量圖片
    const popularRoutes = ref([
      {
        from: '台北',
        fromCode: 'TPE',
        to: '東京',
        toCode: 'NRT',
        category: 'asia',
        price: 12500,
        flightCount: '25-35',
        duration: '3小時20分',
        image: 'https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
        isPopular: true,
        isDirect: true,
        bestPrice: false
      },
      {
        from: '高雄',
        fromCode: 'KHH',
        to: '香港',
        toCode: 'HKG',
        category: 'asia',
        price: 8900,
        flightCount: '12-18',
        duration: '1小時45分',
        image: 'https://images.unsplash.com/photo-1536599018102-9f803c140fc1?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
        isPopular: true,
        isDirect: true,
        bestPrice: true
      },
      {
        from: '台北',
        fromCode: 'TPE',
        to: '澳門',
        toCode: 'MFM',
        category: 'asia',
        price: 9200,
        flightCount: '10-15',
        duration: '1小時30分',
        image: 'https://images.unsplash.com/photo-1556629538-fc3eba61504e?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
        isPopular: false,
        isDirect: true,
        bestPrice: false
      },
      {
        from: '台北',
        fromCode: 'TPE',
        to: '首爾',
        toCode: 'ICN',
        category: 'asia',
        price: 15800,
        flightCount: '18-26',
        duration: '2小時45分',
        image: 'https://images.unsplash.com/photo-1517154421773-0529f29ea451?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
        isPopular: true,
        isDirect: true,
        bestPrice: false
      },
      {
        from: '台北',
        fromCode: 'TPE',
        to: '洛杉磯',
        toCode: 'LAX',
        category: 'international',
        price: 28500,
        flightCount: '6-12',
        duration: '12小時30分',
        image: 'https://images.unsplash.com/photo-1580655653885-65763b2597d0?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
        isPopular: false,
        isDirect: true,
        bestPrice: false
      },
      {
        from: '台北',
        fromCode: 'TPE',
        to: '新加坡',
        toCode: 'SIN',
        category: 'asia',
        price: 18200,
        flightCount: '15-22',
        duration: '3小時45分',
        image: 'https://images.unsplash.com/photo-1525625293386-3f8f99389edd?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
        isPopular: true,
        isDirect: true,
        bestPrice: false
      }
    ])

    // 計算過濾後的路線
    const filteredRoutes = computed(() => {
      if (activeCategory.value === 'all') {
        return popularRoutes.value
      }
      return popularRoutes.value.filter(route => route.category === activeCategory.value)
    })

    // 計算網格佈局類別
    const gridLayoutClass = computed(() => {
      const count = filteredRoutes.value.length
      if (count === 1) {
        return 'single-card'
      } else if (count === 2) {
        return 'two-cards'
      }
      return ''
    })

    // 設置活躍分類
    const setActiveCategory = (categoryId) => {
      activeCategory.value = categoryId
    }

    // 處理路線點擊
    const handleRouteClick = (route) => {
      console.log('選擇路線:', route)
      // 這裡可以觸發搜索或導航到搜索結果
    }
    
    return {
      activeCategory,
      routeCategories,
      popularRoutes,
      filteredRoutes,
      gridLayoutClass,
      setActiveCategory,
      handleRouteClick
    }
  }
}
</script>

<style scoped>
/* === 基礎變量 === */
:root {
  --primary-color: #005F73;
  --secondary-color: #F4A261;
  --accent-orange: #E76F51;
  --text-dark: #1A1A1A;
  --text-medium: #4A4A4A;
  --text-light: #7A7A7A;
  --background-light: #FAFAFA;
  --border-light: #E0E0E0;
  --white: #FFFFFF;
  --success-green: #2ECC71;
}

/* === 主容器 === */
.popular-routes {
  padding: 0 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

.routes-container {
  background: rgba(255, 255, 255, 0.95);
  padding: 4rem 3rem;
  border-radius: 24px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  max-width: 1200px;
  width: 100%;
  min-height: 800px;
  margin: 0 auto;
}

/* === Typography-driven Header === */
.section-header {
  text-align: center;
  margin-bottom: 3rem;
  padding-top: 0.5rem;
}

.header-content {
  margin-bottom: 1.5rem;
  text-align: center;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.section-title {
  font-size: 2.5rem;
  font-weight: 700;
  color: var(--color-primary, #005F73);
  margin: 0 0 0.75rem 0;
  letter-spacing: -0.02em;
  line-height: 1.2;
  text-align: center;
  position: relative;
  display: block;
  width: 100%;
  clear: both;
}

.section-title::after {
  content: '';
  position: absolute;
  bottom: -10px;
  left: 50%;
  transform: translateX(-50%);
  width: 60px;
  height: 3px;
  background: linear-gradient(90deg, var(--color-primary, #005F73) 0%, var(--color-secondary, #F4A261) 100%);
}

.section-subtitle {
  font-size: 1.125rem;
  color: var(--color-text-secondary, #6C757D);
  font-weight: 400;
  max-width: 500px;
  margin: 0 auto 0.5rem auto;
  line-height: 1.6;
  text-align: center;
  display: block;
  width: auto;
  clear: both;
}

/* === 分類篩選器 - 無 Icons 設計 === */
.category-filters {
  display: flex;
  justify-content: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.filter-btn {
  background: transparent;
  border: 2px solid var(--border-light);
  color: var(--text-medium);
  padding: 0.75rem 1.5rem;
  border-radius: 12px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
  min-width: 80px;
}

.filter-btn:hover {
  background: rgba(0, 95, 115, 0.05);
  border-color: var(--color-primary, #005F73);
  color: var(--color-primary, #005F73);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 95, 115, 0.15);
}

.filter-btn:hover {
  border-color: var(--primary-color);
  color: var(--primary-color);
}

.filter-btn.active {
  background: var(--color-primary-light, #0A9396);
  border-color: var(--color-primary-light, #0A9396);
  color: var(--white, #FFFFFF);
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(10, 147, 150, 0.25);
}

.filter-btn.active:hover {
  background: var(--color-primary, #005F73);
  border-color: var(--color-primary, #005F73);
  color: var(--white, #FFFFFF);
  transform: translateY(-3px);
  box-shadow: 0 8px 20px rgba(0, 95, 115, 0.3);
}

.btn-text {
  position: relative;
  z-index: 2;
}

.btn-accent {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--secondary-color);
  transform: scaleX(0);
  transition: transform 0.3s ease;
  transform-origin: center;
}

.filter-btn:hover .btn-accent {
  transform: scaleX(1);
}

.filter-btn.active .btn-accent {
  transform: scaleX(0);
}

/* === 路線網格 - 響應式佈局 === */
.routes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
  gap: 2rem;
  margin-bottom: 2rem;
  max-width: 1200px;
  margin-left: auto;
  margin-right: auto;
  justify-content: center;
}

/* 單張卡片時的特殊佈局 */
.routes-grid.single-card {
  grid-template-columns: minmax(340px, 1200px);
  justify-content: center;
}

/* 可選的其他寬度選項（註解保留供參考）
選項1 - 與其他區塊完全一致: minmax(340px, 1200px)
選項2 - 稍微保守一些: minmax(340px, 1000px)
選項3 - 填滿整個容器: 1fr
選項4 - 固定大尺寸: minmax(340px, 1100px)
*/

/* 兩張卡片時的特殊佈局 */
.routes-grid.two-cards {
  grid-template-columns: repeat(2, minmax(340px, 500px));
  justify-content: center;
}

/* === 路線卡片 - 一致性設計 === */
.route-card {
  background: var(--white);
  border-radius: 20px;
  overflow: hidden;
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.08),
    0 2px 8px rgba(0, 0, 0, 0.04);
  cursor: pointer;
  position: relative;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  height: 420px; /* 統一高度 */
  display: flex;
  flex-direction: column;
  border: 1px solid rgba(229, 231, 235, 0.6);
}

.route-card:hover {
  transform: translateY(-12px) scale(1.02);
  box-shadow:
    0 20px 60px rgba(0, 95, 115, 0.15),
    0 8px 16px rgba(0, 0, 0, 0.08);
  border-color: rgba(0, 95, 115, 0.2);
}

/* === 卡片背景 === */
.card-background {
  position: relative;
  height: 200px;
  overflow: hidden;
}

.background-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.4s ease;
}

.route-card:hover .background-image {
  transform: scale(1.05);
}

.image-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(
    135deg,
    rgba(0, 95, 115, 0.3) 0%,
    rgba(244, 162, 97, 0.2) 100%
  );
}

/* === 卡片內容 === */
.card-content {
  padding: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.content-background {
  background: var(--white);
  padding: 1.5rem;
  border-radius: 0 0 20px 20px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.1);
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

/* === 路線資訊 - Typography-driven === */
.route-info {
  margin-bottom: 1rem;
}

.route-path {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}

.departure-city,
.arrival-city {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text-dark);
}

.route-line {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 1rem;
  position: relative;
}

.line-graphic {
  width: 60px;
  height: 2px;
  background: linear-gradient(90deg, var(--secondary-color), var(--primary-color));
  border-radius: 1px;
}

.route-direction {
  position: absolute;
  right: -6px;
  width: 0;
  height: 0;
  border-left: 6px solid var(--primary-color);
  border-top: 4px solid transparent;
  border-bottom: 4px solid transparent;
}

.route-codes {
  display: flex;
  justify-content: space-between;
}

.airport-code {
  font-size: 0.875rem;
  font-weight: 700;
  padding: 0.25rem 0.5rem;
  border-radius: 6px;
  color: var(--white);
}

.departure-code {
  background: var(--secondary-color);
}

.arrival-code {
  background: var(--primary-color);
}

/* === 航班詳情 === */
.flight-details {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-bottom: 1rem;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.detail-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-light);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.detail-value {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text-dark);
}

/* === 卡片底部 === */
.card-bottom {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  flex-wrap: wrap;
  gap: 1rem;
}

.price-section {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.price-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-light);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.price-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--accent-orange);
}

/* === 標籤 - 無 Icons 的設計 === */
.route-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.badge {
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.direct-badge {
  background: var(--success-green);
  color: var(--white);
}

.price-badge {
  background: var(--accent-orange);
  color: var(--white);
}

.popular-badge {
  background: var(--secondary-color);
  color: var(--white);
}

/* === 懸停效果 === */
.card-hover-effect {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(
    135deg,
    rgba(0, 95, 115, 0.05) 0%,
    rgba(244, 162, 97, 0.05) 100%
  );
  opacity: 0;
  transition: opacity 0.3s ease;
  pointer-events: none;
}

.route-card:hover .card-hover-effect {
  opacity: 1;
}

/* === 空狀態 === */
.empty-state {
  text-align: center;
  padding: 3rem 1rem;
  background: var(--background-light);
  border-radius: 20px;
  border: 2px dashed var(--border-light);
}

.empty-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-medium);
  margin-bottom: 0.5rem;
}

.empty-description {
  color: var(--text-light);
  font-size: 1rem;
}

/* === 響應式設計 === */
@media (max-width: 1024px) {
  .popular-routes {
    padding: 3rem 1.5rem;
}

  .routes-grid {
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1.5rem;
  }
}

@media (max-width: 768px) {
  .popular-routes {
    padding: 2rem 1rem;
  }
  
  .section-title {
    font-size: 2rem;
  }
  
  .routes-grid {
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }
  
  .route-card {
    height: auto;
    min-height: 350px;
  }
  
  .card-background {
    height: 160px;
  }
  
  .route-path {
    flex-direction: column;
    gap: 0.5rem;
    text-align: center;
  }
  
  .route-line {
    margin: 0.5rem 0;
  }
  
  .flight-details {
    grid-template-columns: 1fr;
    gap: 0.75rem;
  }
  
  .card-bottom {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  
  .route-badges {
    align-self: stretch;
    justify-content: flex-start;
  }
}

@media (max-width: 480px) {
  .category-filters {
    gap: 0.25rem;
  }
  
  .filter-btn {
    padding: 0.5rem 1rem;
    font-size: 0.8rem;
    min-width: 70px;
  }
  
  .route-path {
    gap: 0.75rem;
  }
  
  .departure-city,
  .arrival-city {
    font-size: 1.1rem;
  }
  
  .line-graphic {
    width: 40px;
  }
}
</style> 