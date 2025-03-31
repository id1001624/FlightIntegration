<template>
    <div id="app">
      <nav>
        <router-link to="/">首頁</router-link> |
        <router-link to="/flight-search">航班查詢</router-link> |
        <router-link to="/admin/tdx-manager">航班資料管理</router-link> |
        <router-link to="/test">測試頁面</router-link>
      </nav>
      <router-view/>
    </div>
  </template>
  
  <script>
  export default {
    name: 'App'
  }
  </script>
  
  <style>
  #app {
    font-family: 'Microsoft JhengHei', Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    color: #2c3e50;
  }
  
  nav {
    padding: 30px;
    text-align: center;
  }
  
  nav a {
    font-weight: bold;
    color: #2c3e50;
    text-decoration: none;
    margin: 0 10px;
  }
  
  nav a.router-link-active {
    color: #42b983;
  }
  </style>