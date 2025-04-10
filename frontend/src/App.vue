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
            <span class="logo-icon">✈</span>
            <span class="logo-text">Flight Integration</span>
          </router-link>
        </div>
        <nav class="main-nav">
          <router-link to="/" class="nav-link" exact>首頁</router-link>
          <router-link to="/flight-search" class="nav-link">航班查詢</router-link>
          <router-link to="/admin/tdx-manager" class="nav-link">航班資料管理</router-link>
          <router-link to="/test" class="nav-link">測試頁面</router-link>
        </nav>
      </header>

      <!-- 主要內容區 -->
      <main class="main-content">
        <router-view/>
      </main>

      <!-- 頁腳 -->
      <footer class="footer">
        <div class="footer-content">
          <p>© 2025 Flight Integration System. All rights reserved.</p>
        </div>
      </footer>
    </div>
  </div>
</template>

<script>
export default {
  name: 'App'
}
</script>

<style>
/* 全局重置 */
*, *::before, *::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

/* 根變量 */
:root {
  /* 主要顏色 */
  --color-primary: #005F73;      /* 深青色 - 主色調 */
  --color-secondary: #0A9396;    /* 淺青色 - 次要色調 */
  --color-accent: #94D2BD;       /* 薄荷綠 - 強調色 */
  --color-highlight: #E9D8A6;    /* 淺黃 - 高亮色 */
  --color-warning: #EE9B00;      /* 橙色 - 警告色 */
  --color-danger: #CA6702;       /* 深橙 - 危險色 */
  --color-error: #BB3E03;        /* 紅棕 - 錯誤色 */
  
  /* 中性色 */
  --color-white: #FFFFFF;
  --color-background: #F8F9FA;
  --color-border: #DEE2E6;
  --color-text-primary: #212529;
  --color-text-secondary: #495057;
  --color-text-muted: #6C757D;

  /* 字體 */
  --font-family: 'Noto Sans TC', 'Microsoft JhengHei', Arial, sans-serif;
  
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
}

/* 全局樣式 */
html, body {
  height: 100%;
  font-family: var(--font-family);
  font-size: 16px;
  line-height: 1.5;
  color: var(--color-text-primary);
  background-color: var(--color-white);
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
  background-image: url('/src/assets/images/vista-wei-xYNC73QAqc8-unsplash.jpg');
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  opacity: 0.15;
  z-index: 0;
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
  font-size: 1.5rem;
}

.logo-icon {
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
  transition: color var(--transition-fast);
  position: relative;
}

.nav-link:hover {
  color: var(--color-primary);
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

/* 媒體查詢 */
@media (max-width: 768px) {
  .header {
    flex-direction: column;
    gap: var(--spacing-md);
  }
  
  .main-nav {
    flex-wrap: wrap;
    justify-content: center;
    gap: var(--spacing-sm);
  }
}
</style>