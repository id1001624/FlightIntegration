// 引入 Vue 核心庫
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'  // 假設您的 router/index.js 已配置好
import axios from 'axios'  // 如果使用 axios 進行 API 請求

// 配置 axios
axios.defaults.baseURL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api'

// 創建 Vue 應用實例
const app = createApp(App)

// 全局屬性
app.config.globalProperties.$http = axios

// 關閉生產環境提示
app.config.productionTip = false

// 掛載路由和渲染到DOM
app.use(router)
app.mount('#app')