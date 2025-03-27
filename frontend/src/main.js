// 引入 Vue 核心庫
import Vue from 'vue'
import App from './App.vue'
import router from './router'  // 假設您的 router/index.js 已配置好

// 可能需要的其他引入
import axios from 'axios'  // 如果使用 axios 進行 API 請求

// 配置 axios (選用)
axios.defaults.baseURL = process.env.VUE_APP_API_URL || 'http://localhost:5000/api'
Vue.prototype.$http = axios

// 關閉生產環境提示
Vue.config.productionTip = false

// 創建 Vue 實例
new Vue({
  router,           // 掛載路由
  render: h => h(App)  // 渲染 App 根組件
}).$mount('#app')   // 掛載到 HTML 中 id="app" 的元素