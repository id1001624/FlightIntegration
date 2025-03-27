<template>
  <div class="tdx-manager">
    <h1>TDX航班資料管理</h1>
    
    <div class="card">
      <h2>資料同步與初始化</h2>
      <div class="button-group">
        <button @click="testConnection" :disabled="isLoading.test">
          {{ isLoading.test ? '測試中...' : '測試TDX連線' }}
        </button>
        
        <button @click="initializeBaseData" :disabled="isLoading.init" class="primary">
          {{ isLoading.init ? '初始化中...' : '初始化基礎資料' }}
        </button>
        
        <button @click="syncFlights" :disabled="isLoading.sync">
          {{ isLoading.sync ? '同步中...' : '同步航班資料' }}
        </button>
      </div>
      
      <div v-if="results.test" class="result-box" :class="{ success: results.test.success, error: !results.test.success }">
        <h3>連線測試結果</h3>
        <p>{{ results.test.message || (results.test.success ? '連線成功' : '連線失敗') }}</p>
        <div v-if="results.test.success && results.test.data" class="data-sample">
          <p>收到 {{ results.test.data.length }} 筆航班資料</p>
        </div>
      </div>
      
      <div v-if="results.init" class="result-box" :class="{ success: results.init.success, error: !results.init.success }">
        <h3>初始化結果</h3>
        <p v-if="results.init.airlines">{{ results.init.airlines }}</p>
        <p v-if="results.init.airports">{{ results.init.airports }}</p>
      </div>
      
      <div v-if="results.sync" class="result-box" :class="{ success: results.sync.success, error: !results.sync.success }">
        <h3>同步結果</h3>
        <p>{{ results.sync.message }}</p>
      </div>
    </div>
    
    <div class="card">
      <h2>排程設定說明</h2>
      <div class="schedule-info">
        <p>系統已設定以下自動同步排程：</p>
        <ul>
          <li><strong>月初同步：</strong>每月1號凌晨2點</li>
          <li><strong>月中同步：</strong>每月15號凌晨2點</li>
          <li><strong>月底同步：</strong>每月最後一天凌晨2點</li>
        </ul>
        <p>您也可以使用上方的「同步航班資料」按鈕手動進行同步。</p>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      isLoading: {
        test: false,
        init: false,
        sync: false
      },
      results: {
        test: null,
        init: null,
        sync: null
      }
    }
  },
  methods: {
    async testConnection() {
      this.isLoading.test = true;
      try {
        const response = await axios.get('http://localhost:5000/api/tdx/test');
        this.results.test = response.data;
      } catch (error) {
        this.results.test = {
          success: false,
          message: `發生錯誤: ${error.message}`
        };
      } finally {
        this.isLoading.test = false;
      }
    },
    
    async initializeBaseData() {
      this.isLoading.init = true;
      try {
        const response = await axios.post('http://localhost:5000/api/admin/initialize-base-data');
        this.results.init = response.data;
      } catch (error) {
        this.results.init = {
          success: false,
          message: `發生錯誤: ${error.message}`
        };
      } finally {
        this.isLoading.init = false;
      }
    },
    
    async syncFlights() {
      this.isLoading.sync = true;
      try {
        const response = await axios.post('http://localhost:5000/api/admin/sync-tdx-flights');
        this.results.sync = response.data;
      } catch (error) {
        this.results.sync = {
          success: false,
          message: `發生錯誤: ${error.message}`
        };
      } finally {
        this.isLoading.sync = false;
      }
    }
  }
}
</script>

<style scoped>
.tdx-manager {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.card {
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  padding: 20px;
  margin-bottom: 20px;
}

.button-group {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

button {
  background-color: #4CAF50;
  border: none;
  color: white;
  padding: 10px 20px;
  text-align: center;
  text-decoration: none;
  display: inline-block;
  font-size: 16px;
  cursor: pointer;
  border-radius: 4px;
  transition: background-color 0.3s;
}

button:hover {
  background-color: #45a049;
}

button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

button.primary {
  background-color: #1976d2;
}

button.primary:hover {
  background-color: #1565c0;
}

.result-box {
  margin-top: 15px;
  padding: 15px;
  border-radius: 4px;
}

.success {
  background-color: #e8f5e9;
  border-left: 5px solid #4CAF50;
}

.error {
  background-color: #ffebee;
  border-left: 5px solid #f44336;
}

.data-sample {
  margin-top: 10px;
  background-color: #f5f5f5;
  padding: 10px;
  border-radius: 4px;
  font-family: monospace;
}

.schedule-info {
  background-color: #e3f2fd;
  padding: 15px;
  border-radius: 4px;
}

.schedule-info ul {
  margin-left: 20px;
}
</style>