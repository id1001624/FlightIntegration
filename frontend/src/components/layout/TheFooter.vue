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
              <svg width="24" height="24" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" class="w-5 h-5">
                <circle cx="24" cy="24" r="20" fill="#005F73"/>
                <path d="M39.3 23.3394C39.3 15.5731 32.3926 9.30004 24 9.30004C15.6074 9.30004 8.7 15.5731 8.7 23.3394C8.7 30.2729 14.3557 36.0381 21.8373 37.2221C22.5179 37.3807 23.5288 37.7077 23.7628 38.302C23.9757 38.8388 23.9104 39.682 23.8456 40.1722C23.8456 40.1722 23.6748 41.3132 23.6212 41.5942C23.5347 42.0289 23.2251 43.3669 24 42.7301C24.7857 42.0825 30.4374 38.3238 33.0661 35.9949C34.8708 34.3697 39.3 30.0033 39.3 23.3394Z" fill="#F4A261"/>
                <path d="M20.2578 19.6313H19.4834C19.2818 19.6313 19.1182 19.7948 19.1182 19.9964V26.5221C19.1182 26.7237 19.2818 26.8872 19.4834 26.8872H20.2578C20.4594 26.8872 20.623 26.7237 20.623 26.5221V19.9964C20.623 19.7948 20.4594 19.6313 20.2578 19.6313Z" fill="#F4A261"/>
                <path d="M29.2655 19.6313H28.491C28.2894 19.6313 28.1259 19.7948 28.1259 19.9964V24.4125L24.8239 19.7737C24.8071 19.7484 24.7876 19.7254 24.7659 19.7052C24.7659 19.7052 24.7585 19.6991 24.7555 19.6967C24.7427 19.6839 24.7288 19.6725 24.7141 19.6621C24.7035 19.6555 24.6926 19.6494 24.6814 19.6439C24.6686 19.6378 24.6556 19.6325 24.6423 19.6273C24.6299 19.6228 24.6175 19.6191 24.6048 19.6154C24.5925 19.6121 24.5798 19.6094 24.5672 19.6073C24.5536 19.6046 24.5396 19.6031 24.5257 19.6015C24.5139 19.6007 24.5022 19.6003 24.4902 19.6H24.4871H23.7121C23.5105 19.6 23.3469 19.7635 23.3469 19.9651V26.4908C23.3469 26.6923 23.5105 26.8559 23.7121 26.8559H24.4871C24.6886 26.8559 24.8522 26.6923 24.8522 26.4908V22.0752L28.1573 26.7196C28.1817 26.7527 28.2109 26.7818 28.2441 26.8046C28.2441 26.8046 28.2502 26.8089 28.2517 26.8101C28.2636 26.8187 28.2759 26.8262 28.2889 26.833C28.303 26.8412 28.3176 26.8481 28.3326 26.8538C28.3427 26.8572 28.3528 26.8602 28.3631 26.8626C28.3788 26.8667 28.3947 26.8697 28.4112 26.8715C28.422 26.8726 28.4329 26.873 28.4437 26.8735C28.457 26.8741 28.4703 26.8741 28.4835 26.8735H29.2661C29.4677 26.8735 29.6312 26.71 29.6312 26.5084V19.9828C29.63 19.7942 29.4665 19.6313 29.2655 19.6313Z" fill="#F4A261"/>
                <path d="M18.3748 25.3823H15.6323V19.9963C15.6323 19.7947 15.4687 19.6311 15.2671 19.6311H14.4928C14.2912 19.6311 14.1276 19.7947 14.1276 19.9963V26.5219C14.1276 26.6213 14.1669 26.7166 14.2367 26.7869C14.307 26.8572 14.4024 26.8959 14.5017 26.8959H14.5022H18.3754C18.577 26.8959 18.7406 26.7324 18.7406 26.5308V26.5219V25.7474C18.7395 25.5458 18.5765 25.3823 18.3748 25.3823Z" fill="#F4A261"/>
                <path d="M34.3683 21.1365C34.57 21.1365 34.7336 20.9729 34.7336 20.7714V19.9969C34.7336 19.7953 34.57 19.6318 34.3683 19.6318H30.4952C30.3958 19.6318 30.3005 19.6711 30.2302 19.7408C30.1599 19.8111 30.1211 19.9065 30.1211 20.0058V20.0064V26.5225C30.1211 26.6219 30.1599 26.7172 30.2302 26.7875C30.3005 26.8579 30.3958 26.8966 30.4952 26.8966H30.4957H34.3683C34.57 26.8966 34.7336 26.733 34.7336 26.5314V25.7569C34.7336 25.5553 34.57 25.3918 34.3683 25.3918H31.6259V24.1166H34.3683C34.57 24.1166 34.7336 23.953 34.7336 23.7514V22.977C34.7336 22.7754 34.57 22.6118 34.3683 22.6118H31.6259V21.1371H34.3683V21.1365Z" fill="#F4A261"/>
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