<template>
  <footer class="main-footer bg-journey-gradient text-white py-12 mt-16">
    <div class="container mx-auto px-4">
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
        <!-- Column 1: 關於 -->
        <div>
          <h4 class="text-lg font-semibold mb-4 text-white">關於 Flight Integration</h4>
          <ul class="space-y-2">
            <li><a href="#" class="text-gray-100 hover:text-white hover:translate-x-1 transition-all duration-200 flex items-center text-sm"><span class="mr-1">›</span> 關於我們</a></li>
            <li><a href="#" class="text-gray-100 hover:text-white hover:translate-x-1 transition-all duration-200 flex items-center text-sm"><span class="mr-1">›</span> 媒體中心</a></li>
            <li><a href="#" class="text-gray-100 hover:text-white hover:translate-x-1 transition-all duration-200 flex items-center text-sm"><span class="mr-1">›</span> 人才招募</a></li>
            <li><a href="#" class="text-gray-100 hover:text-white hover:translate-x-1 transition-all duration-200 flex items-center text-sm"><span class="mr-1">›</span> 合作夥伴</a></li>
          </ul>
        </div>

        <!-- Column 2: 條款與政策 -->
        <div>
          <h4 class="text-lg font-semibold mb-4 text-white">條款與政策</h4>
          <ul class="space-y-2">
            <li><a href="#" class="text-gray-100 hover:text-white hover:translate-x-1 transition-all duration-200 flex items-center text-sm"><span class="mr-1">›</span> 服務條款</a></li>
            <li><a href="#" class="text-gray-100 hover:text-white hover:translate-x-1 transition-all duration-200 flex items-center text-sm"><span class="mr-1">›</span> 隱私權保護政策</a></li>
            <li><a href="#" class="text-gray-100 hover:text-white hover:translate-x-1 transition-all duration-200 flex items-center text-sm"><span class="mr-1">›</span> Cookie 使用政策</a></li>
            <li><a href="#" class="text-gray-100 hover:text-white hover:translate-x-1 transition-all duration-200 flex items-center text-sm"><span class="mr-1">›</span> 智慧財產權</a></li>
          </ul>
        </div>

        <!-- Column 3: 相關連結 -->
        <div>
          <h4 class="text-lg font-semibold mb-4 text-white">相關連結</h4>
          <ul class="space-y-2">
            <li><a href="#" class="text-gray-100 hover:text-white hover:translate-x-1 transition-all duration-200 flex items-center text-sm"><span class="mr-1">›</span> 常見問題</a></li>
            <li><a href="#" class="text-gray-100 hover:text-white hover:translate-x-1 transition-all duration-200 flex items-center text-sm"><span class="mr-1">›</span> 網站導覽</a></li>
            <li><a href="#" class="text-gray-100 hover:text-white hover:translate-x-1 transition-all duration-200 flex items-center text-sm"><span class="mr-1">›</span> 航班動態 (僅示意)</a></li>
            <li><a href="#" class="text-gray-100 hover:text-white hover:translate-x-1 transition-all duration-200 flex items-center text-sm"><span class="mr-1">›</span> API 文件 (僅示意)</a></li>
          </ul>
        </div>

        <!-- Column 4: 追蹤我們 -->
        <div>
          <h4 class="text-lg font-semibold mb-4 text-white">追蹤我們</h4>
          <div class="flex space-x-3">
            <a href="#" class="w-10 h-10 bg-white/20 hover:bg-secondary text-white flex items-center justify-center rounded-full transition-all duration-200 hover:scale-110 p-2" aria-label="Facebook">
              <svg viewBox="0 0 24 24" fill="currentColor" class="w-5 h-5">
                <path d="M12 2.04C6.5 2.04 2 6.53 2 12.06C2 17.06 5.66 21.21 10.44 21.96V14.96H7.9V12.06H10.44V9.81C10.44 7.31 11.93 5.96 14.22 5.96C15.31 5.96 16.45 6.15 16.45 6.15V8.62H15.19C13.95 8.62 13.56 9.39 13.56 10.18V12.06H16.34L15.89 14.96H13.56V21.96C18.34 21.21 22 17.06 22 12.06C22 6.53 17.5 2.04 12 2.04Z"/>
              </svg>
            </a>
            <a href="#" class="w-10 h-10 bg-white/20 hover:bg-secondary text-white flex items-center justify-center rounded-full transition-all duration-200 hover:scale-110 p-2" aria-label="Instagram">
              <svg viewBox="0 0 24 24" fill="currentColor" class="w-5 h-5">
                <path d="M7.8,2H16.2C19.4,2 22,4.6 22,7.8V16.2A5.8,5.8 0 0,1 16.2,22H7.8C4.6,22 2,19.4 2,16.2V7.8A5.8,5.8 0 0,1 7.8,2M7.6,4A3.6,3.6 0 0,0 4,7.6V16.4C4,18.39 5.61,20 7.6,20H16.4A3.6,3.6 0 0,0 20,16.4V7.6C20,5.61 18.39,4 16.4,4H7.6M17.25,5.5A1.25,1.25 0 0,1 18.5,6.75A1.25,1.25 0 0,1 17.25,8A1.25,1.25 0 0,1 16,6.75A1.25,1.25 0 0,1 17.25,5.5M12,7A5,5 0 0,1 17,12A5,5 0 0,1 12,17A5,5 0 0,1 7,12A5,5 0 0,1 12,7M12,9A3,3 0 0,0 9,12A3,3 0 0,0 12,15A3,3 0 0,0 15,12A3,3 0 0,0 12,9Z"/>
              </svg>
            </a>
            <a href="#" class="w-10 h-10 bg-white/20 hover:bg-secondary text-white flex items-center justify-center rounded-full transition-all duration-200 hover:scale-110 p-2" aria-label="Line">
              <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" class="w-5 h-5">
                <!-- 對話泡泡圓形部分 -->
                <circle cx="12" cy="9" r="7" fill="white" />
                <!-- 對話泡泡尖角 -->
                <polygon points="9,16 15,16 12,20" fill="white" />
                <!-- LINE 文字 -->
                <text x="12" y="9" fill="#005F73" font-size="6" font-weight="bold" text-anchor="middle" dominant-baseline="middle" font-family="sans-serif">
                  LINE
                </text>
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
/* .footer-link 用 class 直接定義在模板中 */
/* .social-icon 用 class 直接定義在模板中 */

.social-icon svg {
  fill: currentColor; /* 原 @apply fill-current; */
}

/* 確保容器在不同斷點下的最大寬度 */
.container {
  max-width: 1280px;
}
</style> 