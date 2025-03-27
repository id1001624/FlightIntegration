<template>
    <div class="home">
      <h1>台灣航班整合系統</h1>
      <div class="welcome-section">
        <p>歡迎使用台灣航班整合系統！我們提供台灣國內、離島及國際航班的整合資訊。</p>
        <router-link to="/flight-search" class="search-button">
          立即查詢航班
        </router-link>
      </div>
      
      <div class="features">
        <div class="feature-card">
          <h3>國內航班</h3>
          <p>查詢連接台灣主要城市的國內航班</p>
        </div>
        
        <div class="feature-card">
          <h3>離島航班</h3>
          <p>查詢往返澎湖、金門、馬祖等離島的航班</p>
        </div>
        
        <div class="feature-card">
          <h3>國際航班</h3>
          <p>查詢從台灣出發的國際航班</p>
        </div>
      </div>
    </div>
  </template>
  
  <script>
  export default {
    name: 'Home'
  }
  </script>
  
  <style scoped>
  .home {
    max-width: 1000px;
    margin: 0 auto;
    padding: 20px;
  }
  
  .welcome-section {
    text-align: center;
    margin: 40px 0;
  }
  
  .search-button {
    display: inline-block;
    margin-top: 15px;
    padding: 12px 24px;
    background-color: #4CAF50;
    color: white;
    text-decoration: none;
    border-radius: 4px;
    font-weight: bold;
  }
  
  .features {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
    margin-top: 40px;
  }
  
  .feature-card {
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    text-align: center;
  }
  
  @media (max-width: 768px) {
    .features {
      grid-template-columns: 1fr;
    }
  }
  </style>