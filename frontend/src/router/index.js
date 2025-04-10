import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import FlightSearch from '../views/FlightSearch.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/flight-search',
    name: 'FlightSearch',
    component: FlightSearch
  }
  // 其他路由...
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL || '/'),
  routes
})

export default router