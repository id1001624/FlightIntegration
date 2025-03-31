<template>
  <div class="home">
    <h1>台灣航班整合系統</h1>
    <div class="welcome-message">
      <p>歡迎使用台灣航班整合系統！這個系統提供台灣境內及國際航班的整合資訊。</p>
      <p>請點擊下方按鈕開始搜尋航班</p>
      <div class="action-buttons">
        <router-link to="/flight-search" class="action-button">
          開始搜尋航班
        </router-link>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Home',
  created() {
    console.log('Home頁面已加載');
  }
}
</script>

<style scoped>
.home {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  text-align: center;
}

h1 {
  margin-bottom: 40px;
  color: #2c3e50;
}

.welcome-message {
  margin-bottom: 40px;
}

.action-buttons {
  margin-top: 30px;
}

.action-button {
  display: inline-block;
  padding: 12px 24px;
  background-color: #4a90e2;
  color: white;
  text-decoration: none;
  border-radius: 4px;
  font-weight: bold;
  transition: background-color 0.3s;
}

.action-button:hover {
  background-color: #3a7bc8;
}
</style>