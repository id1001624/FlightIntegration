<template>
  <section class="popular-routes py-16">
    <div class="w-full mx-auto px-4 sm:px-6 md:px-8 lg:px-10 xl:max-w-screen-xl 2xl:max-w-screen-2xl">
      <h2 class="text-center text-3xl font-bold text-primary mb-3">熱門航線推薦</h2>
      <p class="text-center text-gray-600 mb-12 max-w-2xl mx-auto">探索我們精選的熱門目的地，享受便捷直飛與優惠票價</p>
      
      <div class="grid grid-cols-1 md:grid-cols-3 gap-x-4 gap-y-8">
        <!-- Card 1: 台北 → 東京 -->
        <div class="route-card rounded-xl shadow-lg overflow-hidden bg-white group flex flex-col">
          <!-- Image Section -->
          <div class="relative overflow-hidden">
            <img src="@/assets/images/cities/tokyo.png" alt="東京" class="w-full h-44 object-cover">
            <div class="absolute inset-0 bg-gradient-to-b from-transparent to-black/70 transform transition-transform duration-500 translate-y-0 group-hover:translate-y-1"></div>
            <div class="absolute bottom-0 left-0 right-0 p-3 sm:p-4 transition-all duration-500 transform group-hover:translate-y-0">
              <span class="inline-block px-3 py-1 bg-white/30 backdrop-blur-sm rounded-full text-white text-xs font-semibold mb-1.5">熱門景點</span>
              <h3 class="text-xl sm:text-2xl font-bold text-white">台北 → 東京</h3>
            </div>
          </div>
          
          <!-- Content Section -->
          <div class="p-4 sm:p-5 flex flex-col flex-grow relative">
            <div class="flex-grow">
              <div class="flex items-center mb-3 sm:mb-4 route-visual">
                <div class="route-dot"></div>
                <div class="route-line"></div>
                <div class="route-dot"></div>
              </div>
              <div class="flex justify-between items-start mb-3 sm:mb-4">
                <div>
                  <p class="text-gray-700 font-medium text-sm mb-0.5">直飛航線</p>
                  <p class="text-gray-500 text-xs">飛行時間約3小時</p>
                </div>
                <div class="text-right shrink-0 ml-2">
                  <p class="text-xs text-gray-500 mb-0.5">起價</p>
                  <p class="text-xl sm:text-2xl font-bold text-primary">NT$ 8,500</p>
                </div>
              </div>
            </div>
            <button 
              @click="goToSearch('TPE', 'NRT')" 
              class="absolute left-0 bottom-0 py-2 px-4 bg-primary text-white rounded-md hover:bg-primary-dark transition-all duration-200 text-xs font-medium flex items-center group focus:outline-none focus:ring-2 focus:ring-primary focus:ring-opacity-50">
              查看航班
              <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3 ml-1 transform group-hover:translate-x-0.5 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
              </svg>
            </button>
          </div>
        </div>
        
        <!-- Card 2: 高雄 → 香港 -->
        <div class="route-card rounded-xl shadow-lg overflow-hidden bg-white group flex flex-col">
          <div class="relative overflow-hidden">
            <img src="@/assets/images/cities/hongkong.png" alt="香港" class="w-full h-44 object-cover">
            <div class="absolute inset-0 bg-gradient-to-b from-transparent to-black/70 transform transition-transform duration-500 translate-y-0 group-hover:translate-y-1"></div>
            <div class="absolute bottom-0 left-0 right-0 p-3 sm:p-4 transition-all duration-500 transform group-hover:translate-y-0">
              <span class="inline-block px-3 py-1 bg-white/30 backdrop-blur-sm rounded-full text-white text-xs font-semibold mb-1.5">商務首選</span>
              <h3 class="text-xl sm:text-2xl font-bold text-white">高雄 → 香港</h3>
            </div>
          </div>
          <div class="p-4 sm:p-5 flex flex-col flex-grow relative">
            <div class="flex-grow">
              <div class="flex items-center mb-3 sm:mb-4 route-visual">
                <div class="route-dot"></div>
                <div class="route-line"></div>
                <div class="route-dot"></div>
              </div>
              <div class="flex justify-between items-start mb-3 sm:mb-4">
                <div>
                  <p class="text-gray-700 font-medium text-sm mb-0.5">直飛航線</p>
                  <p class="text-gray-500 text-xs">飛行時間約1.5小時</p>
                </div>
                <div class="text-right shrink-0 ml-2">
                  <p class="text-xs text-gray-500 mb-0.5">起價</p>
                  <p class="text-xl sm:text-2xl font-bold text-primary">NT$ 6,000</p>
                </div>
              </div>
            </div>
            <button 
              @click="goToSearch('KHH', 'HKG')" 
              class="absolute left-0 bottom-0 py-2 px-4 bg-primary text-white rounded-md hover:bg-primary-dark transition-all duration-200 text-xs font-medium flex items-center group focus:outline-none focus:ring-2 focus:ring-primary focus:ring-opacity-50">
              查看航班
              <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3 ml-1 transform group-hover:translate-x-0.5 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Card 3: 台中 → 澳門 -->
        <div class="route-card rounded-xl shadow-lg overflow-hidden bg-white group flex flex-col">
          <div class="relative overflow-hidden">
            <img src="@/assets/images/cities/macau.png" alt="澳門" class="w-full h-44 object-cover">
            <div class="absolute inset-0 bg-gradient-to-b from-transparent to-black/70 transform transition-transform duration-500 translate-y-0 group-hover:translate-y-1"></div>
            <div class="absolute bottom-0 left-0 right-0 p-3 sm:p-4 transition-all duration-500 transform group-hover:translate-y-0">
              <span class="inline-block px-3 py-1 bg-white/30 backdrop-blur-sm rounded-full text-white text-xs font-semibold mb-1.5">度假勝地</span>
              <h3 class="text-xl sm:text-2xl font-bold text-white">台中 → 澳門</h3>
            </div>
          </div>
          <div class="p-4 sm:p-5 flex flex-col flex-grow relative">
            <div class="flex-grow">
              <div class="flex items-center mb-3 sm:mb-4 route-visual">
                <div class="route-dot"></div>
                <div class="route-line"></div>
                <div class="route-dot"></div>
              </div>
              <div class="flex justify-between items-start mb-3 sm:mb-4">
                <div>
                  <p class="text-gray-700 font-medium text-sm mb-0.5">直飛航線</p>
                  <p class="text-gray-500 text-xs">飛行時間約2小時</p>
                </div>
                <div class="text-right shrink-0 ml-2">
                  <p class="text-xs text-gray-500 mb-0.5">起價</p>
                  <p class="text-xl sm:text-2xl font-bold text-primary">NT$ 5,800</p>
                </div>
              </div>
            </div>
            <button 
              @click="goToSearch('RMQ', 'MFM')" 
              class="absolute left-0 bottom-0 py-2 px-4 bg-primary text-white rounded-md hover:bg-primary-dark transition-all duration-200 text-xs font-medium flex items-center group focus:outline-none focus:ring-2 focus:ring-primary focus:ring-opacity-50">
              查看航班
              <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3 ml-1 transform group-hover:translate-x-0.5 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script>
import { useRouter } from 'vue-router';

export default {
  name: 'PopularRoutes',
  setup() {
    const router = useRouter();
    
    const goToSearch = (fromCode, toCode) => {
      router.push({
        path: '/flight-search',
        query: {
          from: fromCode,
          to: toCode
        }
      });
    };
    
    return {
      goToSearch
    };
  }
}
</script>

<style scoped>
.popular-routes {
  background-color: #f8fafc; /* Light gray background for the section */
}

.route-card {
  transition: all 0.35s ease;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.07), 0 2px 4px -2px rgba(0, 0, 0, 0.04);
  position: relative;
  z-index: 1;
}

.route-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 12px 20px -8px rgba(0, 0, 0, 0.15), 0 8px 16px -6px rgba(0, 0, 0, 0.1);
}

.route-card .relative img {
  transition: transform 0.7s, filter 0.5s;
}

.route-card:hover .relative img {
  transform: scale(1.08);
  filter: brightness(1.05);
}

.route-visual {
  position: relative; 
}

.route-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background-color: #005F73; /* Primary color */
  position: relative;
  z-index: 1; 
}

.route-dot:last-child {
  background-color: #F4A261; /* Secondary color */
}

.route-line {
  flex-grow: 1;
  height: 2.5px; 
  background: linear-gradient(to right, #005F73, #F4A261);
  margin: 0 1px; 
}

</style> 