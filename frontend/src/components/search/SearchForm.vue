<template>
  <div class="search-form-container">
    <div class="search-form-wrapper">
      <!-- 主搜索卡片 -->
      <div class="search-card">
        <!-- 標題區域 - Typography-driven -->
        <div class="search-header">
          <h1 class="search-title">搜尋航班</h1>
          <div class="search-subtitle">找到您的完美航線</div>
        </div>

        <!-- 搜索表單 - 幾何布局 -->
        <form @submit.prevent="handleSearch" class="search-form">
          <!-- 航線選擇 - 雙欄布局 -->
          <div class="route-section">
            <div class="route-header">
              <span class="section-label">航線</span>
            </div>
            
            <div class="route-inputs">
              <!-- 出發地 -->
              <div class="input-group departure-group">
                <label class="input-label">出發</label>
                <div class="airport-input-wrapper">
                  <input
                    v-model="formData.departure"
                    type="text"
                    class="airport-input departure-input"
                    placeholder="台北 Taipei"
                    @input="handleDepartureInput"
                    @focus="handleDepartureFocus"
                    @click="handleDepartureFocus"
                    autocomplete="off"
                  />
                  <div class="input-accent departure-accent"></div>
                </div>
                
                <!-- 出發地下拉選單 -->
                <div v-if="isDepartureDropdownOpen && departureOptions.length" class="dropdown departure-dropdown">
                  <div class="dropdown-header">
                    <span class="dropdown-title">選擇出發地</span>
                  </div>
                  <div class="dropdown-content">
                    <div 
                      v-for="airport in departureOptions" 
                      :key="airport.airport_id"
                      class="dropdown-item"
                      @click="selectDeparture(airport)"
                    >
                      <div class="airport-info">
                        <span class="airport-code">{{ airport.iata_code }}</span>
                        <span class="airport-name">{{ airport.name_zh || airport.name_en }}</span>
                      </div>
                      <div class="airport-location">{{ airport.city_zh || airport.city_en }}</div>
                    </div>
                  </div>
                </div>
      </div>
        
              <!-- 目的地 -->
              <div class="input-group arrival-group">
                <label class="input-label">目的地</label>
                <div class="airport-input-wrapper">
                  <input
                    v-model="formData.arrival"
                    type="text"
                    class="airport-input arrival-input"
                    placeholder="東京 Tokyo"
                    @input="handleArrivalInput"
                    @focus="handleArrivalFocus"
                    @click="handleArrivalFocus"
                    autocomplete="off"
                  />
                  <div class="input-accent arrival-accent"></div>
                </div>
                
                <!-- 目的地下拉選單 -->
                <div v-if="isArrivalDropdownOpen && arrivalOptions.length" class="dropdown arrival-dropdown">
                  <div class="dropdown-header">
                    <span class="dropdown-title">選擇目的地</span>
                  </div>
                  <div class="dropdown-content">
                    <div 
                      v-for="airport in arrivalOptions" 
                      :key="airport.airport_id"
                      class="dropdown-item"
                      @click="selectArrival(airport)"
                    >
                      <div class="airport-info">
                        <span class="airport-code">{{ airport.iata_code }}</span>
                        <span class="airport-name">{{ airport.name_zh || airport.name_en }}</span>
                      </div>
                      <div class="airport-location">{{ airport.city_zh || airport.city_en }}</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
      </div>
      
          <!-- 日期與乘客選擇 - 三欄布局 -->
          <div class="details-section">
            <div class="section-label">詳細資訊</div>
            
            <div class="details-inputs">
              <!-- 出發日期 -->
              <div class="input-group date-group">
                <label class="input-label">出發日期</label>
                <input
          v-model="formData.departureDate"
                  type="date"
                  class="date-input"
                  :min="new Date().toISOString().split('T')[0]"
        />
      </div>
        
              <!-- 回程日期 -->
              <div class="input-group date-group">
                <label class="input-label">回程日期</label>
                <input
          v-model="formData.returnDate"
                  type="date"
                  class="date-input"
                  :min="formData.departureDate"
        />
      </div>
      
              <!-- 乘客與艙等 -->
              <div class="input-group passenger-group">
                <label class="input-label">乘客與艙等</label>
        <button 
                  type="button"
                  class="passenger-button"
          @click="openPassengerModal"
                >
                  <div class="passenger-info">
                    <span class="passenger-count">{{ getTotalPassengers() }} 位乘客</span>
                    <span class="cabin-class">{{ getCabinClassName() }}</span>
                  </div>
                  <div class="button-accent"></div>
        </button>
              </div>
            </div>
      </div>
        
          <!-- 搜索按鈕 - 強調設計 -->
          <div class="search-action">
            <button type="submit" class="search-submit-btn" :disabled="isLoading">
              <span v-if="!isLoading" class="btn-text">搜尋航班</span>
              <span v-else class="btn-text">搜尋中...</span>
              <div class="btn-background"></div>
        </button>
          </div>
        </form>
    </div>

      <!-- 乘客艙等選擇彈窗 -->
    <PassengerCabinSelectModal
        v-if="isPassengerModalVisible"
        :is-visible="isPassengerModalVisible"
        :passengers="formData.passengers"
        :cabin-class="formData.cabinClass"
      @close="closePassengerModal"
      @confirm="handlePassengerConfirm"
    />
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { getAirports, getTaiwanAirports, searchFlights } from '@/api/services/flightService'
import PassengerCabinSelectModal from '@/components/ui/PassengerCabinSelectModal.vue'

export default {
  name: 'SearchForm',
  components: {
    PassengerCabinSelectModal
  },
  setup() {
    // 表單數據
    const formData = reactive({
      departure: '',
      arrival: '',
      departureCode: '',
      arrivalCode: '',
        departureDate: '',
        returnDate: '',
      passengers: {
        adults: 1,
        children: 0,
        infants: 0
      },
      cabinClass: 'economy'
    })

    // 狀態管理
    const isLoading = ref(false)
    const isDepartureDropdownOpen = ref(false)
    const isArrivalDropdownOpen = ref(false)
    const isPassengerModalVisible = ref(false)
    
    // 機場選項
    const departureOptions = ref([])
    const arrivalOptions = ref([])
    const allAirports = ref([])

    // 生命週期
    onMounted(async () => {
      await loadAirports()
      setupClickOutside()
    })

    onUnmounted(() => {
      document.removeEventListener('click', handleClickOutside)
    })

    // 載入機場數據
    const loadAirports = async () => {
      try {
        const airports = await getAirports()
        allAirports.value = airports
      } catch (error) {
        console.error('載入機場失敗:', error)
      }
    }

    // 搜索邏輯
    const handleDepartureInput = (event) => {
      const query = event.target.value
      if (query.length >= 1) {
        departureOptions.value = filterAirports(query)
        isDepartureDropdownOpen.value = true
      } else {
        departureOptions.value = []
        isDepartureDropdownOpen.value = false
      }
    }

    const handleDepartureFocus = () => {
      // 點擊或聚焦時顯示所有台灣機場
      if (formData.departure === '') {
        departureOptions.value = allAirports.value.filter(airport => 
          airport.country === 'Taiwan' || airport.country === 'TW'
        ).slice(0, 10)
      } else {
        departureOptions.value = filterAirports(formData.departure)
      }
      isDepartureDropdownOpen.value = true
    }

    const handleArrivalInput = (event) => {
      const query = event.target.value
      if (query.length >= 1) {
        arrivalOptions.value = filterAirports(query)
        isArrivalDropdownOpen.value = true
      } else {
        arrivalOptions.value = []
        isArrivalDropdownOpen.value = false
      }
    }

    const handleArrivalFocus = () => {
      // 點擊或聚焦時顯示熱門目的地
      if (formData.arrival === '') {
        const popularDestinations = ['NRT', 'HKG', 'ICN', 'SIN', 'LAX', 'MFM']
        arrivalOptions.value = allAirports.value.filter(airport => 
          popularDestinations.includes(airport.iata_code)
        )
      } else {
        arrivalOptions.value = filterAirports(formData.arrival)
      }
      isArrivalDropdownOpen.value = true
    }

    const filterAirports = (query) => {
      return allAirports.value.filter(airport => 
        airport.name_zh?.includes(query) ||
        airport.name_en?.toLowerCase().includes(query.toLowerCase()) ||
        airport.city_zh?.includes(query) ||
        airport.city_en?.toLowerCase().includes(query.toLowerCase()) ||
        airport.iata_code?.toLowerCase().includes(query.toLowerCase())
      ).slice(0, 8)
    }

    // 選擇機場
    const selectDeparture = (airport) => {
      formData.departure = airport.name_zh || airport.name_en
      formData.departureCode = airport.iata_code
      isDepartureDropdownOpen.value = false
    }

    const selectArrival = (airport) => {
      formData.arrival = airport.name_zh || airport.name_en
      formData.arrivalCode = airport.iata_code
      isArrivalDropdownOpen.value = false
    }

    // 乘客相關
    const openPassengerModal = () => {
      isPassengerModalVisible.value = true
    }

    const closePassengerModal = () => {
      isPassengerModalVisible.value = false
    }

    const handlePassengerConfirm = (data) => {
      formData.passengers = { ...data.passengers }
      formData.cabinClass = data.cabinClass
      closePassengerModal()
    }

    const getTotalPassengers = () => {
      return formData.passengers.adults + formData.passengers.children + formData.passengers.infants
    }

    const getCabinClassName = () => {
      const classNames = {
        economy: '經濟艙',
        business: '商務艙',
        first: '頭等艙'
      }
      return classNames[formData.cabinClass] || '經濟艙'
    }

    // 表單提交
    const handleSearch = async () => {
      if (!validateForm()) return
      
      isLoading.value = true
      try {
        // 發送搜索事件給父組件
        // 這裡可以調用實際的搜索API
        console.log('搜索參數:', formData)
      } catch (error) {
        console.error('搜索失敗:', error)
      } finally {
        isLoading.value = false
      }
    }

    const validateForm = () => {
      if (!formData.departureCode || !formData.arrivalCode) {
        alert('請選擇出發地和目的地')
        return false
      }
      if (!formData.departureDate) {
        alert('請選擇出發日期')
        return false
      }
      return true
    }

    // 點擊外部關閉下拉選單
    const handleClickOutside = (event) => {
      const departureContainer = event.target.closest('.departure-group')
      const arrivalContainer = event.target.closest('.arrival-group')
      
      if (!departureContainer) {
        isDepartureDropdownOpen.value = false
      }
      if (!arrivalContainer) {
        isArrivalDropdownOpen.value = false
      }
    }

    const setupClickOutside = () => {
      document.addEventListener('click', handleClickOutside)
    }

    return {
      formData,
      isLoading,
      isDepartureDropdownOpen,
      isArrivalDropdownOpen,
      isPassengerModalVisible,
      departureOptions,
      arrivalOptions,
      handleDepartureInput,
      handleDepartureFocus,
      handleArrivalInput,
      handleArrivalFocus,
      selectDeparture,
      selectArrival,
      openPassengerModal,
      closePassengerModal,
      handlePassengerConfirm,
      getTotalPassengers,
      getCabinClassName,
      handleSearch
    }
  }
}
</script>

<style scoped>
/* === CSS 變數 === */
:root {
  --primary-color: #005F73;
  --secondary-color: #F4A261;
  --accent-color: #E76F51;
  --background-light: #F8FAFC;
  --white: #FFFFFF;
  --text-dark: #1A202C;
  --text-medium: #4A5568;
  --text-light: #718096;
  --border-light: #E2E8F0;
  --shadow-soft: 0 4px 16px rgba(0, 0, 0, 0.08);
  --shadow-medium: 0 8px 24px rgba(0, 0, 0, 0.12);
}

/* === 主容器 === */
.search-form-container {
  width: 100%;
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
  position: relative;
}

.search-form-wrapper {
  background: rgba(255, 255, 255, 0.95);
  padding: 3rem;
  border-radius: 24px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  max-width: 1200px;
  margin: 0 auto;
}

/* === 搜索卡片 === */
.search-card {
  background: transparent;
  border-radius: 0;
  padding: 0;
  box-shadow: none;
  border: none;
  backdrop-filter: none;
  position: relative;
  z-index: 10;
}

/* === 標題區域 === */
.search-header {
  text-align: center;
  margin-bottom: 3rem;
}

.search-title {
  font-size: 3rem;
  font-weight: 800;
  color: var(--primary-color);
  margin-bottom: 1rem;
  letter-spacing: -0.02em;
}

.search-subtitle {
  font-size: 1.125rem;
  color: var(--text-medium);
  font-weight: 500;
}

/* === 搜索表單 === */
.search-form {
  display: flex;
  flex-direction: column;
  gap: 2.5rem;
}

/* === 路線選擇區塊 === */
.route-section {
  position: relative;
}

.route-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.section-label {
  font-size: 1.125rem;
  font-weight: 700;
  color: var(--text-dark);
  letter-spacing: 0.025em;
}

.route-inputs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  position: relative;
}

/* === 輸入群組 === */
.input-group {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  position: relative;
}

.input-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-medium);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.airport-input-wrapper {
  position: relative;
}

.airport-input {
  width: 100%;
  padding: 1.25rem 1.5rem;
  border: 2px solid var(--border-light);
  border-radius: 16px;
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--text-dark);
  background: var(--white);
  transition: all 0.2s ease;
  position: relative;
  z-index: 2;
}

.airport-input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 4px rgba(0, 95, 115, 0.1);
}

.airport-input::placeholder {
  color: var(--text-light);
  font-weight: 500;
}

.input-accent {
  position: absolute;
  bottom: 0;
  left: 1.5rem;
  right: 1.5rem;
  height: 3px;
  border-radius: 1.5px;
  transform: scaleX(0);
  transition: transform 0.2s ease;
  transform-origin: left;
  z-index: 3;
}

.departure-accent {
  background: var(--secondary-color);
}

.arrival-accent {
  background: var(--primary-color);
}

.airport-input:focus + .input-accent {
  transform: scaleX(1);
}

/* === 下拉選單 === */
.dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: var(--white);
  border: 2px solid var(--border-light);
  border-top: none;
  border-radius: 0 0 12px 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  z-index: 1000;
  max-height: 320px;
  overflow-y: auto;
}

.dropdown-header {
  padding: 0.75rem 1.25rem;
  border-bottom: 1px solid var(--border-light);
  background: var(--background-light);
}

.dropdown-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-medium);
}

.dropdown-item {
  padding: 1rem 1.25rem;
  cursor: pointer;
  border-bottom: 1px solid var(--border-light);
  transition: background 0.2s ease;
}

.dropdown-item:hover {
  background: var(--background-light);
}

.dropdown-item:last-child {
  border-bottom: none;
}

.airport-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.25rem;
}

.airport-code {
  font-size: 0.875rem;
  font-weight: 700;
  color: var(--primary-color);
  padding: 0.25rem 0.5rem;
  background: rgba(0, 95, 115, 0.1);
  border-radius: 4px;
}

.airport-name {
  font-weight: 600;
  color: var(--text-dark);
}

.airport-location {
  font-size: 0.875rem;
  color: var(--text-light);
}

/* === 詳細資訊區塊 === */
.details-section {
  margin-bottom: 2.5rem;
}

.details-inputs {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 1.5rem;
}

.date-input {
  width: 100%;
  padding: 1rem 1.25rem;
  border: 2px solid var(--border-light);
  border-radius: 12px;
  font-size: 1rem;
  font-weight: 500;
  color: var(--text-dark);
  background: var(--white);
  transition: all 0.2s ease;
}

.date-input:focus {
  outline: none;
  border-color: var(--primary-color);
}

.passenger-button {
  width: 100%;
  padding: 1rem 1.25rem;
  border: 2px solid var(--border-light);
  border-radius: 12px;
  background: var(--white);
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: all 0.2s ease;
}

.passenger-button:hover {
  border-color: var(--primary-color);
}

.passenger-info {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.25rem;
}

.passenger-count {
  font-weight: 600;
  color: var(--text-dark);
}

.cabin-class {
  font-size: 0.875rem;
  color: var(--text-medium);
}

.button-accent {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--primary-color);
  transform: scaleX(0);
  transition: transform 0.2s ease;
  transform-origin: left;
}

.passenger-button:hover .button-accent {
  transform: scaleX(1);
}

/* === 搜索按鈕 === */
.search-action {
  display: flex;
  justify-content: center;
}

.search-submit-btn {
  background: var(--primary-color);
  color: var(--white);
  border: none;
  padding: 1.25rem 3rem;
  border-radius: 16px;
  font-size: 1.1rem;
  font-weight: 700;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
  min-width: 200px;
}

.search-submit-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 95, 115, 0.3);
}

.search-submit-btn:active {
  transform: translateY(0);
}

.search-submit-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
}

.btn-text {
  position: relative;
  z-index: 2;
}

.btn-background {
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s ease;
}

.search-submit-btn:hover .btn-background {
  left: 100%;
}

/* === 響應式設計 === */
@media (max-width: 768px) {
  .search-card {
    padding: 2rem 1.5rem;
  }
  
  .search-title {
    font-size: 2.5rem;
  }
  
  .route-inputs {
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }
  
  .details-inputs {
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }
}
</style> 
<template>
  <div class="journey-search-container">
    <!-- 搜尋標題區域 -->
    <div class="search-header">
      <h1 class="search-title">探索您的下一趟旅程</h1>
      <p class="search-subtitle">找到完美的航班，開始您的精彩旅程</p>
    </div>

    <!-- 主要搜尋表單 -->
    <div class="search-form-wrapper">
      <form @submit.prevent="submitSearch" class="journey-form">
        <!-- 航線選擇區域 -->
        <div class="route-selection">
          <div class="route-inputs">
            <!-- 出發地 -->
            <div class="input-group departure-group">
              <label class="input-label">
                <span class="label-text">出發地</span>
                <span class="label-icon">✈</span>
              </label>
        <AirportSelector 
                v-model="formData.departureAirport"
                placeholder="選擇出發機場"
          :airports="taiwanAirports"
          :loading="loadingTaiwanAirports"
          :error="errors.departureAirport"
          :isDeparture="true"
                class="airport-input departure-input"
          @change="onDepartureChange"
          @select-recent-route="handleRecentRouteSelected"
        />
      </div>
        
            <!-- 路線交換按鈕 -->
            <div class="route-swap">
              <button 
                type="button" 
                class="swap-button"
                @click="swapAirports"
                title="交換出發地與目的地"
              >
                <div class="swap-icon">
                  <div class="swap-arrow swap-arrow-1"></div>
                  <div class="swap-arrow swap-arrow-2"></div>
                </div>
              </button>
            </div>

            <!-- 目的地 -->
            <div class="input-group destination-group">
              <label class="input-label">
                <span class="label-text">目的地</span>
                <span class="label-icon">🎯</span>
              </label>
        <AirportSelector 
                v-model="formData.arrivalAirport"
                placeholder="選擇目的地機場"
          :airports="destinationAirports"
          :loading="loadingDestinations"
          :error="errors.arrivalAirport"
                class="airport-input destination-input"
        />
            </div>
          </div>
      </div>
      
        <!-- 日期與選項區域 -->
        <div class="travel-options">
          <!-- 日期選擇 -->
          <div class="date-selection">
            <div class="input-group date-group">
              <label class="input-label">
                <span class="label-text">出發日期</span>
                <span class="label-icon">📅</span>
              </label>
        <DateSelector 
          v-model="formData.departureDate"
          :error="errors.departureDate"
                class="date-input"
          @change="onDepartureDateChange"
        />
      </div>
        
            <div class="input-group date-group">
              <label class="input-label">
                <span class="label-text">回程日期</span>
                <span class="label-icon optional-icon">📅</span>
                <span class="optional-tag">選填</span>
              </label>
        <DateSelector 
          v-model="formData.returnDate"
          :error="errors.returnDate"
                :minDate="formData.departureDate"
                class="date-input"
                placeholder="單程票請留空"
        />
            </div>
      </div>
      
          <!-- 乘客與艙等 -->
          <div class="passenger-cabin-selection">
            <div class="input-group passenger-group">
              <label class="input-label">
                <span class="label-text">乘客與艙等</span>
                <span class="label-icon">👥</span>
              </label>
        <button 
                type="button"
          @click="openPassengerModal"
                class="passenger-selector"
              >
                <div class="passenger-display">
                  <span class="passenger-text">{{ passengerCabinDisplay }}</span>
                  <span class="dropdown-arrow">▼</span>
                </div>
        </button>
            </div>
          </div>
      </div>
        
        <!-- 搜尋按鈕區域 -->
        <div class="search-action">
        <button 
            type="submit" 
            class="search-button"
          :disabled="isSearching || loadingTaiwanAirports || loadingDestinations"
          >
            <div class="button-content">
              <span v-if="!isSearching" class="button-text">
                <span class="search-icon">🔍</span>
                搜尋航班
              </span>
              <div v-else class="searching-state">
                <div class="search-loader">
                  <div class="loader-ring"></div>
                  <div class="loader-dot"></div>
                </div>
                <span class="searching-text">搜尋中...</span>
              </div>
            </div>
          </button>
        </div>
      </form>

      <!-- 最近搜尋快捷方式 -->
      <div class="recent-searches" v-if="recentSearches.length > 0">
        <h3 class="recent-title">最近搜尋</h3>
        <div class="recent-routes">
          <button
            v-for="(route, index) in recentSearches.slice(0, 3)"
            :key="index"
            @click="handleRecentRouteSelected(route)"
            class="recent-route-chip"
          >
            <span class="route-text">
              {{ route.departureAirport?.name || route.departureAirport?.code }} 
              → 
              {{ route.arrivalAirport?.name || route.arrivalAirport?.code }}
            </span>
        </button>
        </div>
      </div>
    </div>

    <!-- 乘客艙等選擇彈窗 -->
    <PassengerCabinSelectModal
      v-if="isPassengerModalVisible"
      :passengers="formData.passengers"
      :cabinClass="formData.cabinClass"
      @close="closePassengerModal"
      @confirm="handlePassengerConfirm"
    />
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted, watch } from 'vue';
import { useSearchStore } from '@/store/modules/search';
import AirportSelector from '@/components/AirportSelector.vue';
import DateSelector from '@/components/DateSelector.vue';
import PassengerCabinSelectModal from '@/components/ui/PassengerCabinSelectModal.vue';
import { getAirports, getDestinations } from '@/api/services/flightService';

export default {
  name: 'SearchForm',
  components: {
    AirportSelector,
    DateSelector,
    PassengerCabinSelectModal
  },
  props: {
    isSearching: {
      type: Boolean,
      default: false
    }
  },
  emits: ['search'],
  setup(props, { emit }) {
    const searchStore = useSearchStore();
    
    // 響應式數據
    const taiwanAirports = ref([]);
    const destinationAirports = ref([]);
    const loadingTaiwanAirports = ref(false);
    const loadingDestinations = ref(false);
    const isPassengerModalVisible = ref(false);

    const formData = reactive({
      departureAirport: null,
      arrivalAirport: null,
      departureDate: '',
      returnDate: '',
      passengers: { adults: 1, children: 0, infants: 0 },
      cabinClass: 'ECONOMY'
    });

    const errors = reactive({
        departureAirport: '',
        arrivalAirport: '',
        departureDate: '',
      returnDate: ''
    });

    // 計算屬性
    const recentSearches = computed(() => searchStore.recentSearches);
    
    const passengerCabinDisplay = computed(() => {
      const total = formData.passengers.adults + formData.passengers.children + formData.passengers.infants;
      const cabinMap = {
        'ECONOMY': '經濟艙',
        'BUSINESS': '商務艙',
        'FIRST': '頭等艙'
      };
      return `${total} 位乘客, ${cabinMap[formData.cabinClass]}`;
    });

    // 方法
    const fetchTaiwanAirports = async () => {
      loadingTaiwanAirports.value = true;
      try {
        const response = await getAirports();
        if (response.success && response.data) {
          taiwanAirports.value = response.data.filter(airport => 
            airport.country === 'Taiwan'
          ).sort((a, b) => {
            const scoreA = Number(a.activity_score) || 0;
            const scoreB = Number(b.activity_score) || 0;
            return scoreB - scoreA;
          });
        }
      } catch (error) {
        console.error('獲取台灣機場失敗:', error);
      } finally {
        loadingTaiwanAirports.value = false;
      }
    };

    const onDepartureChange = async (airport) => {
      if (!airport || !airport.code) {
        destinationAirports.value = [];
        return;
      }

      loadingDestinations.value = true;
      try {
        const response = await getDestinations(airport.code);
        if (response.success && response.data) {
          destinationAirports.value = response.data.sort((a, b) => 
            (a.name || '').localeCompare(b.name || '')
          );
        } else {
          destinationAirports.value = [];
          errors.arrivalAirport = '此出發地無可用目的地';
        }
      } catch (error) {
        console.error('獲取目的地機場時出錯:', error);
        destinationAirports.value = [];
        errors.arrivalAirport = '載入目的地失敗';
      } finally {
        loadingDestinations.value = false;
      }
    };

    const swapAirports = () => {
      const temp = formData.departureAirport;
      formData.departureAirport = formData.arrivalAirport;
      formData.arrivalAirport = temp;
      
      if (formData.departureAirport && formData.departureAirport.code) {
        onDepartureChange(formData.departureAirport);
      }
    };

    const onDepartureDateChange = () => {
      if (formData.returnDate && new Date(formData.returnDate) < new Date(formData.departureDate)) {
        formData.returnDate = '';
      }
      if (formData.departureAirport && formData.departureAirport.code) {
        onDepartureChange(formData.departureAirport);
      }
    };

    const handleRecentRouteSelected = (route) => {
      if (route.departureAirport) {
        formData.departureAirport = {
          ...route.departureAirport,
          code: route.departureAirport.code || route.departureAirport.airport_id
        };
      }
      
      if (route.arrivalAirport) {
        formData.arrivalAirport = {
          ...route.arrivalAirport,
          code: route.arrivalAirport.code || route.arrivalAirport.airport_id
        };
      }
      
      if (formData.departureAirport && formData.departureAirport.code) {
        onDepartureChange(formData.departureAirport);
      }
    };

    const validateForm = () => {
      let isValid = true;
      Object.keys(errors).forEach(key => errors[key] = '');

      if (!formData.departureAirport || !formData.departureAirport.code) {
        errors.departureAirport = '請選擇出發機場';
        isValid = false;
      }
      
      if (!formData.arrivalAirport || !formData.arrivalAirport.code) {
        errors.arrivalAirport = '請選擇目的地機場';
        isValid = false;
      }
      
      if (!formData.departureDate) {
        errors.departureDate = '請選擇出發日期';
        isValid = false;
      }

      if (formData.returnDate) {
        const depDate = new Date(formData.departureDate);
        const retDate = new Date(formData.returnDate);
        if (retDate < depDate) {
          errors.returnDate = '回程日期必須在出發日期之後';
          isValid = false;
        }
      }

      return isValid;
    };

    const submitSearch = () => {
      if (!validateForm() || props.isSearching) return;
      
      const searchData = {
        departure: formData.departureAirport.code,
        arrival: formData.arrivalAirport.code,
        date: formData.departureDate,
        return_date: formData.returnDate || null,
        cabinClass: formData.cabinClass,
      };
      
      emit('search', searchData);
      
      // 保存搜尋參數和歷史
      searchStore.setSearchParams({ ...formData });
        searchStore.addRecentSearch({
          departureAirport: { ...formData.departureAirport },
          arrivalAirport: { ...formData.arrivalAirport }
        });
    };

    const openPassengerModal = () => {
      isPassengerModalVisible.value = true;
    };

    const closePassengerModal = () => {
      isPassengerModalVisible.value = false;
    };

    const handlePassengerConfirm = (data) => {
      formData.passengers = { ...data.passengers };
      formData.cabinClass = data.cabinClass;
      closePassengerModal();
    };

    onMounted(async () => {
      await fetchTaiwanAirports();
    });

    return {
      taiwanAirports,
      destinationAirports,
      loadingTaiwanAirports,
      loadingDestinations,
      formData,
      errors,
      recentSearches,
      passengerCabinDisplay,
      isPassengerModalVisible,
      onDepartureChange,
      swapAirports,
      onDepartureDateChange,
      handleRecentRouteSelected,
      submitSearch,
      openPassengerModal,
      closePassengerModal,
      handlePassengerConfirm
    };
  }
};
</script>

<style scoped>
/* Structured Journey Minimalism 設計系統 */
.journey-search-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem 1rem;
  background: linear-gradient(135deg, 
    rgba(255, 255, 255, 0.95) 0%, 
    rgba(248, 250, 252, 0.98) 100%
  );
  backdrop-filter: blur(20px);
  border-radius: 24px;
  box-shadow: 
    0 8px 32px rgba(0, 95, 115, 0.08),
    0 4px 16px rgba(0, 95, 115, 0.04);
  position: relative;
  overflow: hidden;
}

.journey-search-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, 
    transparent 0%, 
    rgba(0, 95, 115, 0.2) 50%, 
    transparent 100%
  );
}

/* 搜尋標題區域 */
.search-header {
  text-align: center;
  margin-bottom: 3rem;
}

.search-title {
  font-size: 2.5rem;
  font-weight: 700;
  color: #005F73;
  margin-bottom: 0.75rem;
  letter-spacing: -0.02em;
  line-height: 1.2;
}

.search-subtitle {
  font-size: 1.125rem;
  color: #6B7280;
  font-weight: 400;
  letter-spacing: 0.01em;
}

/* 搜尋表單 */
.search-form-wrapper {
  position: relative;
}

.journey-form {
  display: flex;
  flex-direction: column;
  gap: 2.5rem;
}

/* 航線選擇區域 */
.route-selection {
  position: relative;
}

.route-inputs {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 1rem;
  align-items: end;
}

/* 交換按鈕 */
.route-swap {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  padding-bottom: 2rem;
}

.swap-button {
  width: 48px;
  height: 48px;
  border: 2px solid #E5E7EB;
  background: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  cursor: pointer;
  position: relative;
}

.swap-button:hover {
  border-color: #005F73;
  transform: rotate(180deg) scale(1.1);
  box-shadow: 0 8px 20px rgba(0, 95, 115, 0.15);
}

.swap-icon {
  position: relative;
  width: 20px;
  height: 20px;
}

.swap-arrow {
  position: absolute;
  width: 12px;
  height: 2px;
  background: #005F73;
  border-radius: 1px;
  transition: all 0.3s ease;
}

.swap-arrow-1 {
  top: 6px;
  left: 4px;
  transform: rotate(45deg);
}

.swap-arrow-2 {
  top: 12px;
  left: 4px;
  transform: rotate(-45deg);
}

/* 輸入組件 */
.input-group {
  position: relative;
}

.input-label {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
  font-weight: 600;
  color: #374151;
  font-size: 0.875rem;
}

.label-text {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.label-icon {
  font-size: 1rem;
  opacity: 0.7;
}

.optional-tag {
  font-size: 0.75rem;
  color: #9CA3AF;
  font-weight: 400;
  background: #F3F4F6;
  padding: 0.125rem 0.5rem;
  border-radius: 12px;
}

/* 旅行選項區域 */
.travel-options {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 2rem;
  align-items: start;
}

.date-selection {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

/* 乘客選擇器 */
.passenger-selector {
  width: 100%;
  padding: 1rem;
  border: 2px solid #E5E7EB;
  border-radius: 12px;
  background: white;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 0.875rem;
}

.passenger-selector:hover {
  border-color: #005F73;
  box-shadow: 0 4px 12px rgba(0, 95, 115, 0.08);
}

.passenger-display {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.passenger-text {
  color: #374151;
  font-weight: 500;
}

.dropdown-arrow {
  color: #9CA3AF;
  font-size: 0.75rem;
  transition: transform 0.2s ease;
}

/* 搜尋按鈕 */
.search-action {
  margin-top: 1rem;
}

.search-button {
  width: 100%;
  padding: 1.25rem 2rem;
  background: linear-gradient(135deg, #005F73 0%, #0A9396 100%);
  color: white;
  border: none;
  border-radius: 16px;
  font-size: 1.125rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  position: relative;
  overflow: hidden;
}

.search-button::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, 
    transparent 0%, 
    rgba(255, 255, 255, 0.2) 50%, 
    transparent 100%
  );
  transition: left 0.5s ease;
}

.search-button:hover::before {
  left: 100%;
}

.search-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 28px rgba(0, 95, 115, 0.25);
}

.search-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
}

.button-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
}

.search-icon {
  font-size: 1.25rem;
}

/* 搜尋中狀態 */
.searching-state {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.search-loader {
  position: relative;
  width: 24px;
  height: 24px;
}

.loader-ring {
  position: absolute;
  width: 100%;
  height: 100%;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid white;
  border-radius: 50%;
  animation: search-spin 1s linear infinite;
}

.loader-dot {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 6px;
  height: 6px;
  background: white;
  border-radius: 50%;
  transform: translate(-50%, -50%);
  animation: search-pulse 1.5s ease-in-out infinite;
}

@keyframes search-spin {
  to { transform: rotate(360deg); }
}

@keyframes search-pulse {
  0%, 100% { opacity: 1; transform: translate(-50%, -50%) scale(1); }
  50% { opacity: 0.5; transform: translate(-50%, -50%) scale(0.8); }
}

/* 最近搜尋 */
.recent-searches {
  margin-top: 2rem;
  padding-top: 2rem;
  border-top: 1px solid #E5E7EB;
}

.recent-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: #6B7280;
  margin-bottom: 1rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.recent-routes {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.recent-route-chip {
  padding: 0.5rem 1rem;
  background: #F8FAFC;
  border: 1px solid #E2E8F0;
  border-radius: 24px;
  font-size: 0.875rem;
  color: #475569;
  cursor: pointer;
  transition: all 0.2s ease;
}

.recent-route-chip:hover {
  background: #005F73;
  color: white;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 95, 115, 0.15);
}

/* 響應式設計 */
@media (max-width: 1024px) {
  .travel-options {
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }
}

@media (max-width: 768px) {
  .route-inputs {
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }
  
  .route-swap {
    order: 2;
    padding-bottom: 0;
    margin: -0.5rem 0;
  }
  
  .destination-group {
    order: 3;
  }
  
  .date-selection {
    grid-template-columns: 1fr;
    gap: 1rem;
  }
  
  .search-title {
    font-size: 2rem;
  }
  
  .journey-search-container {
    margin: 1rem;
    padding: 1.5rem;
    border-radius: 16px;
  }
}

@media (max-width: 480px) {
  .search-title {
    font-size: 1.75rem;
  }
  
  .search-subtitle {
    font-size: 1rem;
  }
  
  .journey-form {
    gap: 2rem;
  }
}
</style> 