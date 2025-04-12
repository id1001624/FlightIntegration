<template>
  <div class="skeleton-loader" :class="{ 'animated': animate }">
    <div v-if="type === 'flight-card'" class="skeleton-flight-card">
      <div class="skeleton-flight-card-inner">
        <!-- 卡片頭部 -->
        <div class="skeleton-flight-card-header">
          <div class="skeleton-airline-info">
            <div class="skeleton-logo"></div>
            <div class="skeleton-airline-details">
              <div class="skeleton-text skeleton-text-medium"></div>
              <div class="skeleton-text skeleton-text-small"></div>
            </div>
          </div>
          <div class="skeleton-price">
            <div class="skeleton-text skeleton-text-large"></div>
            <div class="skeleton-text skeleton-text-small"></div>
          </div>
        </div>
        
        <!-- 行程視覺化 -->
        <div class="skeleton-journey">
          <div class="skeleton-route-info">
            <div class="skeleton-text skeleton-text-large"></div>
            <div class="skeleton-text skeleton-text-small"></div>
          </div>
          
          <div class="skeleton-journey-line"></div>
          
          <div class="skeleton-route-info">
            <div class="skeleton-text skeleton-text-large"></div>
            <div class="skeleton-text skeleton-text-small"></div>
          </div>
        </div>
        
        <!-- 額外資訊 -->
        <div class="skeleton-meta">
          <div class="skeleton-text skeleton-text-small"></div>
          <div class="skeleton-text skeleton-text-small"></div>
        </div>
      </div>
      
      <!-- 底部 -->
      <div class="skeleton-flight-card-footer">
        <div class="skeleton-button"></div>
      </div>
    </div>
    
    <div v-else-if="type === 'search-form'" class="skeleton-search-form">
      <div class="skeleton-form-row">
        <div class="skeleton-input skeleton-input-large"></div>
      </div>
      <div class="skeleton-form-row">
        <div class="skeleton-input"></div>
        <div class="skeleton-input"></div>
      </div>
      <div class="skeleton-form-row">
        <div class="skeleton-input"></div>
        <div class="skeleton-input"></div>
        <div class="skeleton-button skeleton-button-primary"></div>
      </div>
    </div>
    
    <div v-else-if="type === 'filter'" class="skeleton-filter">
      <div class="skeleton-filter-header">
        <div class="skeleton-text skeleton-text-medium"></div>
      </div>
      <div class="skeleton-filter-options">
        <div class="skeleton-filter-option" v-for="i in 4" :key="i">
          <div class="skeleton-checkbox"></div>
          <div class="skeleton-text skeleton-text-medium"></div>
        </div>
      </div>
    </div>
    
    <div v-else class="skeleton-custom">
      <slot></slot>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SkeletonLoader',
  props: {
    type: {
      type: String,
      default: 'flight-card',
      validator: (value) => ['flight-card', 'search-form', 'filter', 'custom'].includes(value)
    },
    animate: {
      type: Boolean,
      default: true
    }
  }
}
</script>

<style scoped>
.skeleton-loader {
  width: 100%;
}

.skeleton-loader.animated .skeleton-text,
.skeleton-loader.animated .skeleton-logo,
.skeleton-loader.animated .skeleton-input,
.skeleton-loader.animated .skeleton-button,
.skeleton-loader.animated .skeleton-journey-line,
.skeleton-loader.animated .skeleton-checkbox {
  position: relative;
  overflow: hidden;
}

.skeleton-loader.animated .skeleton-text::after,
.skeleton-loader.animated .skeleton-logo::after,
.skeleton-loader.animated .skeleton-input::after,
.skeleton-loader.animated .skeleton-button::after,
.skeleton-loader.animated .skeleton-journey-line::after,
.skeleton-loader.animated .skeleton-checkbox::after {
  content: "";
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  background: linear-gradient(90deg, 
    rgba(255, 255, 255, 0) 0%, 
    rgba(255, 255, 255, 0.6) 50%, 
    rgba(255, 255, 255, 0) 100%);
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(100%);
  }
}

/* 通用骨架元素 */
.skeleton-text {
  background-color: #e9ecef;
  border-radius: 4px;
}

.skeleton-text-small {
  height: 10px;
  width: 60%;
  margin-top: 6px;
}

.skeleton-text-medium {
  height: 14px;
  width: 80%;
}

.skeleton-text-large {
  height: 20px;
  width: 70%;
}

/* 航班卡片骨架 */
.skeleton-flight-card {
  margin-bottom: 1rem;
  border-radius: 8px;
  overflow: hidden;
  background-color: white;
  border: 1px solid #dee2e6;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.skeleton-flight-card-inner {
  padding: 1.25rem;
}

.skeleton-flight-card-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 1.5rem;
}

.skeleton-airline-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.skeleton-logo {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 50%;
  background-color: #e9ecef;
}

.skeleton-airline-details {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.skeleton-price {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.375rem;
}

.skeleton-journey {
  display: flex;
  align-items: center;
  margin: 1.5rem 0;
}

.skeleton-route-info {
  width: 30%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.375rem;
}

.skeleton-journey-line {
  flex-grow: 1;
  height: 2px;
  margin: 0 1rem;
  background-color: #e9ecef;
}

.skeleton-meta {
  display: flex;
  justify-content: space-between;
  margin-top: 1.25rem;
  padding-top: 0.75rem;
  border-top: 1px solid #f0f0f0;
}

.skeleton-flight-card-footer {
  background-color: #f8f9fa;
  padding: 0.75rem 1.25rem;
  display: flex;
  justify-content: flex-end;
}

.skeleton-button {
  width: 4rem;
  height: 2rem;
  border-radius: 4px;
  background-color: #e9ecef;
}

.skeleton-button-primary {
  background-color: #cfe6e8;
  width: 6rem;
}

/* 搜索表單骨架 */
.skeleton-search-form {
  background-color: white;
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.skeleton-form-row {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
}

.skeleton-input {
  flex: 1;
  height: 3rem;
  background-color: #e9ecef;
  border-radius: 4px;
}

.skeleton-input-large {
  height: 4rem;
}

/* 篩選器骨架 */
.skeleton-filter {
  background-color: white;
  border-radius: 8px;
  padding: 1.25rem;
  margin-bottom: 1rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.skeleton-filter-header {
  margin-bottom: 1rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid #f0f0f0;
}

.skeleton-filter-options {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.skeleton-filter-option {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.skeleton-checkbox {
  width: 1.25rem;
  height: 1.25rem;
  border-radius: 4px;
  background-color: #e9ecef;
}

/* 響應式調整 */
@media (max-width: 640px) {
  .skeleton-journey {
    flex-direction: column;
    gap: 1rem;
  }
  
  .skeleton-route-info {
    width: 100%;
    flex-direction: row;
    justify-content: space-between;
  }
  
  .skeleton-journey-line {
    width: 100%;
    margin: 1rem 0;
  }
  
  .skeleton-flight-card-header {
    flex-direction: column;
    gap: 1rem;
  }
  
  .skeleton-price {
    width: 100%;
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
  }
  
  .skeleton-form-row {
    flex-direction: column;
  }
}
</style> 