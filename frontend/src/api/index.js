import axios from 'axios';

// 創建axios實例
const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
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
