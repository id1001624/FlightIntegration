<template>
  <footer class="main-footer bg-[#333] text-gray-300 py-12 mt-16">
    <div class="container mx-auto px-4">
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
        <!-- Column 1: 關於 -->
        <div>
          <h4 class="text-lg font-semibold mb-4 text-white">關於 Flight Integration</h4>
          <ul class="space-y-2">
            <li><a href="#" class="footer-link">關於我們</a></li>
            <li><a href="#" class="footer-link">媒體中心</a></li>
            <li><a href="#" class="footer-link">人才招募</a></li>
            <li><a href="#" class="footer-link">合作夥伴</a></li>
          </ul>
        </div>

        <!-- Column 2: 條款與政策 -->
        <div>
          <h4 class="text-lg font-semibold mb-4 text-white">條款與政策</h4>
          <ul class="space-y-2">
            <li><a href="#" class="footer-link">服務條款</a></li>
            <li><a href="#" class="footer-link">隱私權保護政策</a></li>
            <li><a href="#" class="footer-link">Cookie 使用政策</a></li>
            <li><a href="#" class="footer-link">智慧財產權</a></li>
          </ul>
        </div>

        <!-- Column 3: 相關連結 -->
        <div>
          <h4 class="text-lg font-semibold mb-4 text-white">相關連結</h4>
          <ul class="space-y-2">
            <li><a href="#" class="footer-link">常見問題</a></li>
            <li><a href="#" class="footer-link">網站導覽</a></li>
            <li><a href="#" class="footer-link">航班動態 (僅示意)</a></li>
            <li><a href="#" class="footer-link">API 文件 (僅示意)</a></li>
          </ul>
        </div>

        <!-- Column 4: 追蹤我們 -->
        <div>
          <h4 class="text-lg font-semibold mb-4 text-white">追蹤我們</h4>
          <div class="flex space-x-4">
            <a href="#" class="social-icon" aria-label="Facebook">
              <!-- Placeholder for Facebook Icon --> F
            </a>
            <a href="#" class="social-icon" aria-label="Line">
              <!-- Placeholder for Line Icon --> L
            </a>
            <a href="#" class="social-icon" aria-label="Instagram">
              <!-- Placeholder for Instagram Icon --> I
            </a>
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
.footer-link {
  @apply text-gray-400 hover:text-white transition-colors duration-200 text-sm;
}

.social-icon {
  @apply w-8 h-8 bg-gray-600 hover:bg-primary text-white flex items-center justify-center rounded-full transition-colors duration-200 text-sm font-bold;
}

/* 確保容器在不同斷點下的最大寬度 */
.container {
  max-width: 1280px;
}
</style> 