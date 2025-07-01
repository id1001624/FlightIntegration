import axios from 'axios';

// 使用環境變數或默認值作為baseURL
// 在開發環境中默認使用本地服務器
// 在生產環境中將使用Vercel環境變數中配置的API URL
const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5000/api';

// 創建axios實例
const api = axios.create({
  baseURL: baseURL,
  timeout: 60000, // 增加到 60 秒以處理 Amadeus API 的慢響應
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
});

// 請求攔截器
api.interceptors.request.use(
  config => {
    console.log(`API請求: ${config.method.toUpperCase()} ${config.url}`, config.params || config.data);
    return config;
  },
  error => {
    return Promise.reject(error);
  }
);

// 響應攔截器
api.interceptors.response.use(
  response => {
    console.log(`API響應: ${response.config.url}`, response.data);
    return response.data;
  },
  error => {
    console.error('API錯誤:', error);
    
    // 如果是超時錯誤，提供更明確的錯誤信息
    if (error.code === 'ECONNABORTED' && error.message.includes('timeout')) {
      console.error('API請求超時，後端服務可能運行緩慢或未啟動');
    }
    
    return Promise.reject(error);
  }
);

export default api;
