import Vue from 'vue'
import VueRouter from 'vue-router'
import Home from '../views/Home.vue'
import FlightSearch from '../views/FlightSearch.vue'
import TDXManager from '@/views/admin/TDXManager.vue'

Vue.use(VueRouter)

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
  }
  // 其他路由...
]

const router = new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  routes
})

export default router