import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import FlightSearch from '../views/FlightSearch.vue'
import TDXManager from '../views/admin/TDXManager.vue'
import Test from '../views/Test.vue'

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
  },
  {
    path: '/admin/tdx-manager',
    name: 'TDXManager',
    component: TDXManager
  },
  {
    path: '/test',
    name: 'Test',
    component: Test
  }
  // 其他路由...
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL || '/'),
  routes
})

export default router