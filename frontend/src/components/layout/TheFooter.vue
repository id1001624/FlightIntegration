<template>
  <footer class="main-footer bg-journey-gradient text-white py-12 mt-16 relative z-15">
    <div class="footer-container mx-auto px-4">
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
        <!-- Column 1: 關於 -->
        <div>
          <h4 class="text-lg font-semibold mb-4 text-white">關於 Flight Integration</h4>
          <ul class="space-y-2">
            <li><a href="#" class="text-gray-100 hover:text-white hover:translate-x-1 transition-all duration-200 text-sm">關於我們</a></li>
            <li><a href="#" class="text-gray-100 hover:text-white hover:translate-x-1 transition-all duration-200 text-sm">媒體中心</a></li>
            <li><a href="#" class="text-gray-100 hover:text-white hover:translate-x-1 transition-all duration-200 text-sm">人才招募</a></li>
            <li><a href="#" class="text-gray-100 hover:text-white hover:translate-x-1 transition-all duration-200 text-sm">合作夥伴</a></li>
          </ul>
        </div>

        <!-- Column 2: 條款與政策 -->
        <div>
          <h4 class="text-lg font-semibold mb-4 text-white">條款與政策</h4>
          <ul class="space-y-2">
            <li><a href="#" class="text-gray-100 hover:text-white hover:translate-x-1 transition-all duration-200 text-sm">服務條款</a></li>
            <li><a href="#" class="text-gray-100 hover:text-white hover:translate-x-1 transition-all duration-200 text-sm">隱私權保護政策</a></li>
            <li><a href="#" class="text-gray-100 hover:text-white hover:translate-x-1 transition-all duration-200 text-sm">Cookie 使用政策</a></li>
            <li><a href="#" class="text-gray-100 hover:text-white hover:translate-x-1 transition-all duration-200 text-sm">智慧財產權</a></li>
          </ul>
        </div>

        <!-- Column 3: 相關連結 -->
        <div>
          <h4 class="text-lg font-semibold mb-4 text-white">相關連結</h4>
          <ul class="space-y-2">
            <li><a href="#" class="text-gray-100 hover:text-white hover:translate-x-1 transition-all duration-200 text-sm">常見問題</a></li>
            <li><a href="#" class="text-gray-100 hover:text-white hover:translate-x-1 transition-all duration-200 text-sm">網站導覽</a></li>
            <li><a href="#" class="text-gray-100 hover:text-white hover:translate-x-1 transition-all duration-200 text-sm">航班動態 (僅示意)</a></li>
            <li><a href="#" class="text-gray-100 hover:text-white hover:translate-x-1 transition-all duration-200 text-sm">API 文件 (僅示意)</a></li>
          </ul>
        </div>

        <!-- Column 4: 追蹤我們 -->
        <div>
          <h4 class="text-lg font-semibold mb-4 text-white">追蹤我們</h4>
          <div class="flex space-x-3">
            <a href="#" class="w-12 h-12 bg-white/20 hover:bg-secondary text-white flex items-center justify-center rounded-full transition-all duration-200 hover:scale-110 p-2" aria-label="Facebook">
              <svg viewBox="0 0 24 24" fill="currentColor" class="w-8 h-8">
                <path d="M12 2.04C6.5 2.04 2 6.53 2 12.06C2 17.06 5.66 21.21 10.44 21.96V14.96H7.9V12.06H10.44V9.81C10.44 7.31 11.93 5.96 14.22 5.96C15.31 5.96 16.45 6.15 16.45 6.15V8.62H15.19C13.95 8.62 13.56 9.39 13.56 10.18V12.06H16.34L15.89 14.96H13.56V21.96C18.34 21.21 22 17.06 22 12.06C22 6.53 17.5 2.04 12 2.04Z"/>
              </svg>
            </a>
            <a href="#" class="w-12 h-12 bg-white/20 hover:bg-secondary text-white flex items-center justify-center rounded-full transition-all duration-200 hover:scale-110 p-2" aria-label="Instagram">
              <svg viewBox="0 0 24 24" fill="currentColor" class="w-8 h-8">
                <path d="M7.8,2H16.2C19.4,2 22,4.6 22,7.8V16.2A5.8,5.8 0 0,1 16.2,22H7.8C4.6,22 2,19.4 2,16.2V7.8A5.8,5.8 0 0,1 7.8,2M7.6,4A3.6,3.6 0 0,0 4,7.6V16.4C4,18.39 5.61,20 7.6,20H16.4A3.6,3.6 0 0,0 20,16.4V7.6C20,5.61 18.39,4 16.4,4H7.6M17.25,5.5A1.25,1.25 0 0,1 18.5,6.75A1.25,1.25 0 0,1 17.25,8A1.25,1.25 0 0,1 16,6.75A1.25,1.25 0 0,1 17.25,5.5M12,7A5,5 0 0,1 17,12A5,5 0 0,1 12,17A5,5 0 0,1 7,12A5,5 0 0,1 12,7M12,9A3,3 0 0,0 9,12A3,3 0 0,0 12,15A3,3 0 0,0 15,12A3,3 0 0,0 12,9Z"/>
              </svg>
            </a>
            <a href="#" class="w-12 h-12 bg-white/20 hover:bg-secondary text-white flex items-center justify-center rounded-full transition-all duration-200 hover:scale-110 p-2 line-icon-container" aria-label="Line">
              <svg viewBox="0 0 40 40" class="w-8 h-8" xmlns="http://www.w3.org/2000/svg">
                <defs>
                  <mask id="lineTextMaskSvg">
                    <rect width="100%" height="100%" fill="white" />
                    <text
                      x="20"
                      y="18"
                      text-anchor="middle"
                      font-family="Arial Black, Arial, sans-serif"
                      font-size="11"
                      font-weight="900"
                      dominant-baseline="middle"
                      letter-spacing="-0.5"
                      fill="black"
                    >LINE</text>
                  </mask>
                </defs>
                <path
                  d="M20 2C10 2 3 8 3 16.5C3 24 9 30 19 31C19.4 31.1 19.7 31.4 19.8 31.8C19.9 32.2 19.8 32.7 19.7 33.2L19.3 35C19.2 35.3 19 36 20 35.5C21 35 24.5 32.5 26.4 30.8C31 27 37 22 37 16.5C37 8 30 2 20 2Z"
                  fill="white"
                  mask="url(#lineTextMaskSvg)"
                />
              </svg>
            </a>
          </div>
          <div class="mt-6">
            <p class="text-sm text-gray-100">© 2024 Flight Integration. 版權所有。</p>
          </div>
        </div>
      </div>
    </div>
  </footer>
</template>

<script>
export default {
  name: 'TheFooter'
}
</script>

<style scoped>
/* Fallback 樣式 - 確保即使 Tailwind 不工作時也能正常顯示 */
.main-footer {
  background: linear-gradient(120deg, #005F73 0%, #0A9396 100%);
  color: white;
  padding: 3rem 0;
  margin-top: 4rem;
  position: relative;
  z-index: 15;
  width: 100%;
}

.footer-container {
  max-width: 1440px;
  margin: 0 auto;
  padding: 0 1rem;
}

.grid {
  display: grid;
  gap: 2rem;
}

@media (min-width: 640px) {
  .grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 1024px) {
  .grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

h4 {
  font-size: 1.125rem;
  font-weight: 600;
  margin-bottom: 1rem;
  color: white;
}

ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

li {
  margin-bottom: 0.5rem;
}

a {
  color: #f1f3f5;
  text-decoration: none;
  font-size: 0.875rem;
  display: flex;
  align-items: center;
  transition: all 0.2s ease;
}

a:hover {
  color: white;
  transform: translateX(0.25rem);
}

.flex {
  display: flex;
}

.space-x-3 > * + * {
  margin-left: 0.75rem;
}

.w-12 {
  width: 3rem;
}

.h-12 {
  height: 3rem;
}

.bg-white\/20 {
  background-color: rgba(255, 255, 255, 0.2);
}

.rounded-full {
  border-radius: 9999px;
}

.items-center {
  align-items: center;
}

.justify-center {
  justify-content: center;
}

.transition-all {
  transition: all 0.2s ease;
}

.hover\:bg-secondary:hover {
  background-color: #F4A261;
}

.hover\:scale-110:hover {
  transform: scale(1.1);
}

.p-2 {
  padding: 0.5rem;
}

.w-8 {
  width: 2rem;
}

.h-8 {
  height: 2rem;
}

.mt-6 {
  margin-top: 1.5rem;
}

.text-sm {
  font-size: 0.875rem;
}

.text-gray-100 {
  color: #f1f3f5;
}

/* .footer-link 用 class 直接定義在模板中 */
/* .social-icon 用 class 直接定義在模板中 */

.social-icon svg {
  fill: currentColor; /* 原 @apply fill-current; */
}

/* LINE 文字顏色變化效果 */
.line-text {
  fill: #005F73;
  transition: fill 0.2s ease;
}

.line-icon-container:hover .line-text {
  fill: #F4A261;
}
</style> 