import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import FlightSearch from '../views/FlightSearch.vue'
import FlightDetail from '../views/FlightDetail.vue'
import PopularFlights from '../views/PopularFlights.vue'
import FromTaiwanFlights from '../views/FromTaiwanFlights.vue'
import FAQ from '../views/FAQ.vue'

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
    path: '/flights/:flight_id',
    name: 'FlightDetail',
    component: FlightDetail,
    props: true
  },
  {
    path: '/flights/popular',
    name: 'PopularFlights',
    component: PopularFlights
  },
  {
    path: '/flights/from-taiwan',
    name: 'FromTaiwanFlights',
    component: FromTaiwanFlights
  },
  {
    path: '/faq',
    name: 'FAQ',
    component: FAQ
  }
  // 其他路由...
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL || '/'),
  routes
})

export default router