<template>
  <section class="popular-routes py-12">
    <div class="container mx-auto px-4">
      <h2 class="text-center text-2xl font-bold text-primary mb-8">熱門航線推薦</h2>
      
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <!-- 台北 → 東京 -->
        <div class="route-card rounded-lg shadow-md overflow-hidden bg-white">
          <img src="@/assets/images/cities/tokyo.png" alt="東京" class="w-full h-48 object-cover">
          <div class="p-4">
            <h3 class="text-xl font-bold">台北 → 東京</h3>
            <div class="flex items-center my-3">
              <div class="h-1 w-1 bg-primary rounded-full"></div>
              <div class="h-0.5 flex-grow bg-gradient-to-r from-primary to-secondary"></div>
              <div class="h-1 w-1 bg-secondary rounded-full"></div>
            </div>
            <p class="text-gray-600 text-sm">直飛航線，飛行時間約3小時</p>
            <p class="text-xl font-bold text-primary mt-4">NT$ 8,500 起</p>
            <button 
              @click="goToSearch('TPE', 'NRT')" 
              class="mt-4 w-full py-2 bg-primary text-white rounded-md hover:bg-primary-dark transition-all duration-200"
            >
              查看航班
            </button>
          </div>
        </div>
        
        <!-- 高雄 → 香港 -->
        <div class="route-card rounded-lg shadow-md overflow-hidden bg-white">
          <img src="@/assets/images/cities/hongkong.png" alt="香港" class="w-full h-48 object-cover">
          <div class="p-4">
            <h3 class="text-xl font-bold">高雄 → 香港</h3>
            <div class="flex items-center my-3">
              <div class="h-1 w-1 bg-primary rounded-full"></div>
              <div class="h-0.5 flex-grow bg-gradient-to-r from-primary to-secondary"></div>
              <div class="h-1 w-1 bg-secondary rounded-full"></div>
            </div>
            <p class="text-gray-600 text-sm">直飛航線，飛行時間約1.5小時</p>
            <p class="text-xl font-bold text-primary mt-4">NT$ 6,000 起</p>
            <button 
              @click="goToSearch('KHH', 'HKG')" 
              class="mt-4 w-full py-2 bg-primary text-white rounded-md hover:bg-primary-dark transition-all duration-200"
            >
              查看航班
            </button>
          </div>
        </div>
        
        <!-- 台中 → 澳門 -->
        <div class="route-card rounded-lg shadow-md overflow-hidden bg-white">
          <img src="@/assets/images/cities/macau.png" alt="澳門" class="w-full h-48 object-cover">
          <div class="p-4">
            <h3 class="text-xl font-bold">台中 → 澳門</h3>
            <div class="flex items-center my-3">
              <div class="h-1 w-1 bg-primary rounded-full"></div>
              <div class="h-0.5 flex-grow bg-gradient-to-r from-primary to-secondary"></div>
              <div class="h-1 w-1 bg-secondary rounded-full"></div>
            </div>
            <p class="text-gray-600 text-sm">直飛航線，飛行時間約2小時</p>
            <p class="text-xl font-bold text-primary mt-4">NT$ 5,800 起</p>
            <button 
              @click="goToSearch('RMQ', 'MFM')" 
              class="mt-4 w-full py-2 bg-primary text-white rounded-md hover:bg-primary-dark transition-all duration-200"
            >
              查看航班
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
    
    // 導航到搜索頁面，並傳遞出發地和目的地參數
    const goToSearch = (fromCode, toCode) => {
      router.push({
        path: '/search', // 請確保這與您的搜索頁面路由匹配
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
  background-color: #f5f7f9;
}

.route-card {
  transition: transform 0.3s ease;
}

.route-card:hover {
  transform: translateY(-5px);
}
</style> 