<template>
  <div id="app" class="app-container">
    <!-- 旅程背景層 -->
    <div class="journey-background"></div>
    
    <!-- 內容層 -->
    <div class="content-container">
      <!-- 頂部導航 -->
      <header class="header">
        <div class="logo-container">
          <router-link to="/" class="logo">
            <img src="@/assets/images/logo/logo.png" alt="Logo" class="logo-image">
            <span class="logo-text">Flight Integration</span>
          </router-link>
        </div>
        <nav class="main-nav">
          <router-link to="/" class="nav-link" exact>首頁</router-link>
          <router-link to="/flight-search" class="nav-link">航班查詢</router-link>
          <router-link to="/member/register" class="nav-link">會員註冊/登入</router-link>
          <router-link to="/social" class="nav-link">社群</router-link>
        </nav>
        <!-- 移動版漢堡選單 -->
        <button class="mobile-menu-btn" @click="toggleMobileMenu">
          <span class="mobile-menu-icon"></span>
        </button>
      </header>

      <!-- 移動版選單 -->
      <div class="mobile-menu" :class="{'mobile-menu-open': mobileMenuOpen}">
        <router-link to="/" class="mobile-nav-link" exact @click="closeMobileMenu">首頁</router-link>
        <router-link to="/flight-search" class="mobile-nav-link" @click="closeMobileMenu">航班查詢</router-link>
        <router-link to="/member/register" class="mobile-nav-link" @click="closeMobileMenu">會員註冊/登入</router-link>
        <router-link to="/social" class="mobile-nav-link" @click="closeMobileMenu">社群</router-link>
      </div>

      <!-- 主要內容區 -->
      <main class="main-content">
        <router-view v-slot="{ Component }">
          <transition name="page-transition" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>

      <!-- 新的詳細頁腳 -->
      <TheFooter />

      <!-- 原有的簡單頁腳 (版權信息) -->
      <footer class="footer">
        <div class="footer-content">
          <p>© 2025 Flight Integration System. All rights reserved.</p>
        </div>
      </footer>
    </div>
  </div>
</template>

<script>
import TheFooter from '@/components/layout/TheFooter.vue';

export default {
  name: 'App',
  components: {
    TheFooter
  },
  data() {
    return {
      mobileMenuOpen: false
    }
  },
  methods: {
    toggleMobileMenu() {
      this.mobileMenuOpen = !this.mobileMenuOpen;
      // 切換時禁止/恢復背景滾動
      document.body.style.overflow = this.mobileMenuOpen ? 'hidden' : '';
    },
    closeMobileMenu() {
      this.mobileMenuOpen = false;
      document.body.style.overflow = '';
    }
  },
  watch: {
    $route() {
      // 路由變更時關閉移動選單
      this.closeMobileMenu();
    }
  }
}
</script>

<style>
/* 全局重置 */
*, *::before, *::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

/* 根變量 - 與Tailwind配置保持一致 */
:root {
  /* 主要顏色 */
  --color-base: #FFFFFF;
  --color-background: #F8F9FA;
  
  --color-primary: #005F73;
  --color-primary-light: #0A9396;
  --color-primary-dark: #033F4D;
  
  --color-secondary: #F4A261;
  --color-secondary-light: #F8BC8A;
  --color-secondary-dark: #E07A38;
  
  /* 功能色彩 */
  --color-success: #38B000;
  --color-warning: #FFB703;
  --color-danger: #DC2F02;
  --color-info: #219EBC;
  
  /* 中性色 */
  --color-border: #DEE2E6;
  
  /* 文字顏色 */
  --color-text-primary: #212529;
  --color-text-secondary: #6C757D;
  --color-text-muted: #ADB5BD;

  /* 字體 */
  --font-family: 'Inter', 'Noto Sans TC', 'Microsoft JhengHei', Arial, sans-serif;
  
  /* 間距 */
  --spacing-xs: 0.25rem;  /* 4px */
  --spacing-sm: 0.5rem;   /* 8px */
  --spacing-md: 1rem;     /* 16px */
  --spacing-lg: 1.5rem;   /* 24px */
  --spacing-xl: 2rem;     /* 32px */
  
  /* 陰影 */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.05);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.05);
  
  /* 過渡 */
  --transition-fast: 150ms ease-in-out;
  --transition-normal: 250ms ease-in-out;
  
  /* 圓角 */
  --radius-sm: 0.25rem;
  --radius-md: 0.5rem;
  --radius-lg: 1rem;
}

/* 全局樣式 */
html, body {
  height: 100%;
  font-family: var(--font-family);
  font-size: 16px;
  line-height: 1.5;
  color: var(--color-text-primary);
  background-color: var(--color-base);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* 主容器 */
.app-container {
  min-height: 100vh;
  position: relative;
  overflow: hidden;
}

/* 旅程背景層 */
.journey-background {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: url('@/assets/images/sky-views/vista-wei-xYNC73QAqc8-unsplash.jpg');
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  opacity: 0.08; /* 降低不透明度使其更淡 */
  z-index: 0;
  filter: blur(1px); /* 輕微模糊 */
}

/* 內容容器 */
.content-container {
  position: relative;
  z-index: 1;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  max-width: 1440px;
  margin: 0 auto;
  padding: 0 var(--spacing-md);
}

/* 頭部 */
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-lg) 0;
  border-bottom: 1px solid var(--color-border);
}

.logo-container {
  display: flex;
  align-items: center;
}

.logo {
  display: flex;
  align-items: center;
  text-decoration: none;
  color: var(--color-primary);
  font-weight: 700;
  font-size: 2rem;
  transition: transform var(--transition-fast);
}

.logo:hover {
  transform: translateY(-1px);
}

.logo-image {
  height: 44px;
  width: auto;
  margin-right: var(--spacing-sm);
}

/* 導航 */
.main-nav {
  display: flex;
  gap: var(--spacing-lg);
}

.nav-link {
  color: var(--color-text-secondary);
  text-decoration: none;
  font-weight: 500;
  padding: var(--spacing-sm) var(--spacing-md);
  transition: color var(--transition-fast), transform var(--transition-fast);
  position: relative;
}

.nav-link:hover {
  color: var(--color-primary);
  transform: translateY(-1px);
}

.nav-link.router-link-active {
  color: var(--color-primary);
}

.nav-link.router-link-active::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  width: 100%;
  height: 2px;
  background-color: var(--color-primary);
  animation: journeyLine 0.3s ease-out forwards;
}

/* 移動版選單按鈕 */
.mobile-menu-btn {
  display: none; /* 預設隱藏 */
  background: transparent;
  border: none;
  padding: var(--spacing-sm);
  cursor: pointer;
  position: relative;
  width: 40px;
  height: 40px;
}

.mobile-menu-icon,
.mobile-menu-icon::before,
.mobile-menu-icon::after {
  content: '';
  display: block;
  width: 24px;
  height: 2px;
  background-color: var(--color-primary);
  position: absolute;
  left: 8px;
  transition: all var(--transition-normal);
}

.mobile-menu-icon {
  top: 19px;
}

.mobile-menu-icon::before {
  top: -8px;
}

.mobile-menu-icon::after {
  bottom: -8px;
}

/* 移動選單開啟狀態 */
.mobile-menu-open .mobile-menu-icon {
  background-color: transparent;
}

.mobile-menu-open .mobile-menu-icon::before {
  transform: rotate(45deg);
  top: 0;
}

.mobile-menu-open .mobile-menu-icon::after {
  transform: rotate(-45deg);
  bottom: 0;
}

/* 移動版導航選單 */
.mobile-menu {
  display: none;
  flex-direction: column;
  background-color: var(--color-base);
  position: fixed;
  top: 70px;
  left: 0;
  width: 100%;
  height: 0;
  overflow: hidden;
  z-index: 100;
  opacity: 0;
  transition: opacity var(--transition-normal), height var(--transition-normal);
  box-shadow: var(--shadow-md);
}

.mobile-menu-open {
  height: calc(100vh - 70px);
  opacity: 1;
}

.mobile-nav-link {
  padding: var(--spacing-lg);
  text-decoration: none;
  color: var(--color-text-primary);
  font-weight: 500;
  border-bottom: 1px solid var(--color-border);
  transition: background-color var(--transition-fast);
}

.mobile-nav-link:hover,
.mobile-nav-link.router-link-active {
  background-color: rgba(0, 95, 115, 0.05);
  color: var(--color-primary);
}

/* 主要內容 */
.main-content {
  flex: 1;
  padding: var(--spacing-xl) 0;
}

/* 頁腳 */
.footer {
  margin-top: auto;
  padding: var(--spacing-lg) 0;
  border-top: 1px solid var(--color-border);
}

.footer-content {
  text-align: center;
  color: var(--color-text-muted);
  font-size: 0.875rem;
}

/* 頁面切換動畫 */
.page-transition-enter-active,
.page-transition-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.page-transition-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.page-transition-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}

/* 動畫關鍵幀 */
@keyframes journeyLine {
  0% {
    width: 0%;
    opacity: 0.5;
  }
  100% {
    width: 100%;
    opacity: 1;
  }
}

/* 響應式樣式 */
@media (max-width: 768px) {
  .header {
    padding: var(--spacing-md) 0;
  }
  
  .main-nav {
    display: none; /* 在移動版隱藏 */
  }
  
  .mobile-menu-btn {
    display: block; /* 在移動版顯示 */
  }
  
  .mobile-menu {
    display: flex; /* 啟用彈出式選單 */
  }
  
  .content-container {
    padding: 0 var(--spacing-sm);
  }
}
</style>