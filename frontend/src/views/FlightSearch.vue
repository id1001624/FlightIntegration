<template>
  <div class="flight-search-page">
    <div class="container">
      <h1 class="page-title">航班搜尋</h1>
      
      <div class="search-panel">
        <div class="search-form">
          <div class="form-row">
            <div class="form-group">
              <AirportSelector 
                id="departure"
                label="出發地"
                placeholder="選擇出發機場"
                :airports="taiwanAirports"
                v-model="searchParams.departureAirport"
                :loading="loadingTaiwanAirports"
                :error="errors.departureAirport"
                :disabled="isSearching"
                @change="onDepartureChange"
              />
            </div>
            
            <div class="form-group">
              <AirportSelector 
                id="arrival"
                label="目的地"
                placeholder="選擇目的地機場"
                :airports="destinationAirports"
                v-model="searchParams.arrivalAirport"
                :loading="loadingDestinations"
                :error="errors.arrivalAirport"
                :disabled="!searchParams.departureAirport || isSearching"
              />
            </div>
          </div>
          
          <div class="form-row">
            <div class="form-group">
              <DateSelector 
                id="departure-date"
                label="出發日期"
                v-model="searchParams.departureDate"
                :error="errors.departureDate"
              />
            </div>
            
            <div class="form-group">
              <DateSelector 
                id="return-date"
                label="回程日期 (選填)"
                v-model="searchParams.returnDate"
                :min-date="searchParams.departureDate"
                :error="errors.returnDate"
              />
            </div>
          </div>
          
          <div class="form-row">
            <div class="form-group">
              <ClassTypeSelector 
                v-model="searchParams.classType"
                :error="errors.classType"
              />
            </div>
            
            <div class="form-group search-btn-container">
              <button 
                class="search-btn" 
                @click="searchFlights"
                :disabled="isSearching"
              >
                <span v-if="isSearching">搜尋中...</span>
                <span v-else>搜尋航班</span>
              </button>
            </div>
          </div>
        </div>
      </div>
      
      <div class="flight-results" v-if="hasSearched && !loading">
        <div class="results-header">
          <h2 class="results-title">
            {{ formatAirportCode(searchParams.departureAirport) }} → 
            {{ formatAirportCode(searchParams.arrivalAirport) }}
          </h2>
          <div class="results-count">找到 {{ displayedFlightsCount }} 個航班</div>
        </div>
        
        <div class="results-container">
          <div class="filters-panel">
            <div class="filters-header">
              <h3>篩選條件</h3>
              <button class="clear-filters" @click="clearFilters">清除</button>
            </div>
            
            <AirlineFilter 
              :airlines="availableAirlines"
              v-model="filters.selectedAirlines"
              :loading="loadingAirlines"
            />
            
            <PriceRangeSlider 
              :min="filters.priceRange.min"
              :max="filters.priceRange.max"
              v-model="filters.selectedPriceRange"
            />
          </div>
          
          <div class="results-content" v-if="filteredFlights.length > 0">
            <FlightCard 
              v-for="flight in filteredFlights" 
              :key="flight.id || index" 
              :flight="flight"
              @select="selectFlight"
              class="flight-card-item"
            />
          </div>
          
          <div class="no-results" v-else-if="flights.length > 0">
            <p>沒有符合當前篩選條件的航班，請調整篩選條件。</p>
            <button class="clear-filters-btn" @click="clearFilters">清除所有篩選</button>
          </div>
          
          <div class="no-results" v-else>
            <p>{{ flightsNotFoundMessage }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import AirportSelector from '@/components/AirportSelector.vue';
import DateSelector from '@/components/DateSelector.vue';
import ClassTypeSelector from '@/components/ClassTypeSelector.vue';
import AirlineFilter from '@/components/AirlineFilter.vue';
import PriceRangeSlider from '@/components/PriceRangeSlider.vue';
import FlightCard from '@/components/FlightCard.vue';
import flightService from '@/api/services/flightService';

export default {
  name: 'FlightSearch',
  components: {
    AirportSelector,
    DateSelector,
    ClassTypeSelector,
    AirlineFilter,
    PriceRangeSlider,
    FlightCard
  },
  data() {
    return {
      taiwanAirports: [],
      destinationAirports: [],
      airlines: [],
      flights: [],
      loadingTaiwanAirports: false,
      loadingDestinations: false,
      loadingAirlines: false,
      isSearching: false,
      hasSearched: false,
      searchParams: {
        departureAirport: null,
        arrivalAirport: null,
        departureDate: new Date().toISOString().split('T')[0],
        returnDate: '',
        classType: 'economy'
      },
      filters: {
        selectedAirlines: [],
        priceRange: {
          min: 0,
          max: 50000
        },
        selectedPriceRange: {
          min: 0,
          max: 50000
        }
      },
      errors: {
        departureAirport: '',
        arrivalAirport: '',
        departureDate: '',
        returnDate: '',
        classType: ''
      },
      loading: false,
      flightsNotFoundMessage: '',
      minAvailablePrice: 0,
      maxAvailablePrice: 0,
      priceRange: [0, 50000],
      filteredFlights: []
    };
  },
  computed: {
    filteredFlights() {
      return this.flights.filter(flight => {
        // 航空公司篩選
        if (this.filters.selectedAirlines.length > 0 && 
            !this.filters.selectedAirlines.includes(flight.airline_code)) {
          return false;
        }
        
        // 價格篩選
        if (flight.price < this.filters.selectedPriceRange.min || 
            flight.price > this.filters.selectedPriceRange.max) {
          return false;
        }
        
        return true;
      });
    },
    departureAirportCode() {
      return this.searchParams.departureAirport ? this.searchParams.departureAirport.code : '';
    },
    arrivalAirportCode() {
      return this.searchParams.arrivalAirport ? this.searchParams.arrivalAirport.code : '';
    },
    departureDate() {
      return this.searchParams.departureDate;
    },
    returnDate() {
      return this.searchParams.returnDate;
    },
    selectedAirline() {
      return this.searchParams.classType;
    },
    selectedClass() {
      return this.searchParams.classType;
    },
    availableAirlines() {
      if (!this.flights || this.flights.length === 0) {
        return [];
      }
      
      // 從所有航班中提取不重複的航空公司
      const uniqueAirlines = new Set();
      const airlines = [];
      
      this.flights.forEach(flight => {
        let airlineCode = '';
        let airlineName = '';
        
        // 處理不同的數據結構
        if (flight.airline && typeof flight.airline === 'object') {
          airlineCode = flight.airline.code || flight.airline.iata_code || '';
          airlineName = flight.airline.name || flight.airline.name_zh || '';
        } else {
          airlineCode = flight.airline_code || '';
          airlineName = flight.airline_name || '';
        }
        
        // 只添加有效的航空公司，並避免重複
        if (airlineCode && !uniqueAirlines.has(airlineCode)) {
          uniqueAirlines.add(airlineCode);
          airlines.push({
            code: airlineCode,
            name: airlineName || airlineCode
          });
        }
      });
      
      return airlines;
    },
    displayedFlightsCount() {
      return this.filteredFlights.length;
    }
  },
  methods: {
    async fetchTaiwanAirports() {
      this.loadingTaiwanAirports = true;
      try {
        const airports = await flightService.getTaiwanAirports();
        console.log('API 回傳的機場資料:', airports);
        
        if (airports && airports.length > 0) {
          this.taiwanAirports = airports;
          console.log('載入了 Taiwan 機場:', this.taiwanAirports);
        } else {
          console.error('API 未返回有效機場資料');
          this.taiwanAirports = [];
          alert('無法載入機場資料。請檢查後端連接和資料庫。');
        }
      } catch (error) {
        console.error('獲取機場資料時出錯:', error);
        console.error('錯誤詳情:', error.response ? `狀態碼: ${error.response.status}, 資料: ${JSON.stringify(error.response.data)}` : '無回應資料');
        this.taiwanAirports = [];
        alert('獲取機場資料時出錯。請檢查後端連接。');
      } finally {
        this.loadingTaiwanAirports = false;
      }
    },
    async fetchAirlines() {
      this.loadingAirlines = true;
      try {
        const response = await flightService.getAirlines();
        this.airlines = response.data;
      } catch (error) {
        console.error('Error fetching airlines:', error);
      } finally {
        this.loadingAirlines = false;
      }
    },
    async onDepartureChange(departureCode) {
      if (!departureCode) {
        this.destinationAirports = [];
        this.searchParams.arrivalAirport = null;
        return;
      }
      
      console.log('正在獲取目的地機場，出發地代碼:', departureCode);
      this.loadingDestinations = true;
      
      try {
        const destinations = await flightService.getDestinations(departureCode);
        console.log('API 回傳的目的地機場資料:', destinations);
        
        if (destinations && destinations.length > 0) {
          // 確保數據格式正確
          this.destinationAirports = destinations.map(airport => ({
            id: airport.id,
            code: airport.code || airport.iata_code,
            name: airport.name || airport.name_zh || airport.name_en,
            city: airport.city,
          }));
          
          console.log(`成功載入 ${this.destinationAirports.length} 個目的地機場`);
        } else {
          this.destinationAirports = [];
          console.warn('未找到可用的目的地機場');
        }
      } catch (error) {
        console.error('獲取目的地機場時出錯:', error);
        this.destinationAirports = [];
      } finally {
        this.loadingDestinations = false;
      }
    },
    validateForm() {
      let isValid = true;
      this.errors = {
        departureAirport: '',
        arrivalAirport: '',
        departureDate: '',
        returnDate: '',
        classType: ''
      };
      
      if (!this.searchParams.departureAirport) {
        this.errors.departureAirport = '請選擇出發機場';
        isValid = false;
      }
      
      if (!this.searchParams.arrivalAirport) {
        this.errors.arrivalAirport = '請選擇目的地機場';
        isValid = false;
      }
      
      if (!this.searchParams.departureDate) {
        this.errors.departureDate = '請選擇出發日期';
        isValid = false;
      }
      
      // 如果有填寫回程日期，檢查是否在出發日期之後
      if (this.searchParams.returnDate) {
        const depDate = new Date(this.searchParams.departureDate);
        const retDate = new Date(this.searchParams.returnDate);
        
        if (retDate < depDate) {
          this.errors.returnDate = '回程日期必須在出發日期之後';
          isValid = false;
        }
      }
      
      return isValid;
    },
    async searchFlights() {
      if (!this.validateForm()) {
        return;
      }

      this.resetFlightResults();
      this.loading = true;
      this.isSearching = true;
      this.hasSearched = true;

      try {
        // 獲取格式化的參數
        const departureCode = this.searchParams.departureAirport?.code;
        const arrivalCode = this.searchParams.arrivalAirport?.code;
        
        console.log('正在搜索航班，參數:', {
          departure: departureCode,
          arrival: arrivalCode,
          date: this.searchParams.departureDate
        });
        
        // 確保departureCode和arrivalCode非空
        if (!departureCode || !arrivalCode) {
          console.error('缺少必要的參數: 出發地或目的地');
          this.flightsNotFoundMessage = '請選擇有效的出發地和目的地機場';
          this.isSearching = false;
          this.loading = false;
          return;
        }
        
        const searchParams = {
          departureAirportCode: departureCode,
          arrivalAirportCode: arrivalCode,
          departureDate: this.searchParams.departureDate,
          returnDate: this.searchParams.returnDate || undefined,
          classType: this.searchParams.classType || 'economy'
        };
        
        console.log('發送搜索參數:', searchParams);
        const response = await flightService.searchFlights(searchParams);

        console.log('API 回傳原始結果:', response);

        // 使用統一處理 API 回應的方法
        let flights = [];
        
        // 檢查API回傳的格式
        if (response && response.outbound_flights) {
          console.log('API 返回 outbound_flights 格式數據');
          flights = response.outbound_flights;
        } else {
          // 使用統一處理方法
          flights = flightService._handleResponse(response);
        }
        
        console.log('處理後的航班數據:', flights);

        // 如果沒有航班數據
        if (!flights || flights.length === 0) {
          console.log('API 回傳了空的航班列表');
          this.flights = [];
          this.flightsNotFoundMessage = `沒有找到從 ${this.searchParams.departureAirport.name} 到 ${this.searchParams.arrivalAirport.name} 的航班，請選擇其他日期或目的地。`;
          alert(this.flightsNotFoundMessage);
          return;
        }

        // 直接使用處理後的航班數據
        this.flights = flights;
        
        // 初始化篩選後的航班數據
        this.filteredFlights = [...this.flights];
        
        console.log(`獲取到 ${this.flights.length} 個有效航班`);
        console.log('第一個航班:', this.flights[0]);

        // 更新價格範圍
        if (this.flights.length > 0) {
          const prices = this.flights.map(flight => Number(flight.price) || 0).filter(price => price > 0);
          if (prices.length > 0) {
            this.minAvailablePrice = Math.min(...prices);
            this.maxAvailablePrice = Math.max(...prices);
            this.priceRange = [this.minAvailablePrice, this.maxAvailablePrice];
            
            // 更新篩選面板的價格範圍
            this.filters.priceRange.min = this.minAvailablePrice;
            this.filters.priceRange.max = this.maxAvailablePrice;
            this.filters.selectedPriceRange.min = this.minAvailablePrice;
            this.filters.selectedPriceRange.max = this.maxAvailablePrice;
          }
        }
      } catch (error) {
        console.error('搜索航班時出錯:', error);
        console.error('錯誤詳情:', error.response ? 
          `狀態碼: ${error.response.status}, 資料: ${JSON.stringify(error.response.data)}` : 
          '無回應資料');
        
        alert('搜索航班時發生錯誤。請檢查後端連接和伺服器日誌。');
        this.flightsNotFoundMessage = '搜索航班時發生錯誤，請檢查後端連接';
      } finally {
        this.loading = false;
        this.isSearching = false;
      }
    },
    resetFlightResults() {
      this.flights = [];
      this.flightsNotFoundMessage = '';
    },
    formatAirportName(code) {
      if (!code) return '';
      
      const airport = [...this.taiwanAirports, ...this.destinationAirports]
        .find(airport => airport.code === code);
      
      return airport ? airport.name : code;
    },
    formatAirportCode(code) {
      if (!code) return '';
      
      const airport = [...this.taiwanAirports, ...this.destinationAirports]
        .find(airport => airport.code === code);
      
      return airport ? `${airport.code} - ${airport.name}` : code;
    },
    clearFilters() {
      this.filters.selectedAirlines = [];
      this.filters.selectedPriceRange.min = this.filters.priceRange.min;
      this.filters.selectedPriceRange.max = this.filters.priceRange.max;
      this.filteredFlights = [...this.flights];
    },
    selectFlight(flight) {
      console.log('Selected flight:', flight);
      // 這裡可以實現導航到詳細資訊頁，或者打開對話框等功能
      // this.$router.push({ name: 'FlightDetails', params: { id: flight.id } });
      alert(`您已選擇航班: ${flight.airline_code} ${flight.flight_number}`);
    },
    applyFilters() {
      if (!this.flights || this.flights.length === 0) {
        this.filteredFlights = [];
        return;
      }
      
      // 篩選航班
      this.filteredFlights = this.flights.filter(flight => {
        // 價格篩選
        const flightPrice = Number(flight.price) || 0;
        if (flightPrice < this.filters.selectedPriceRange.min || 
            flightPrice > this.filters.selectedPriceRange.max) {
          return false;
        }
        
        // 航空公司篩選
        if (this.filters.selectedAirlines.length > 0) {
          let airlineCode = '';
          
          // 處理不同的數據結構
          if (flight.airline && typeof flight.airline === 'object') {
            airlineCode = flight.airline.code || flight.airline.iata_code || '';
          } else {
            airlineCode = flight.airline_code || '';
          }
          
          if (!this.filters.selectedAirlines.includes(airlineCode)) {
            return false;
          }
        }
        
        return true;
      });
    },
    onPriceRangeChange() {
      this.applyFilters();
    },
    onAirlinesChange() {
      this.applyFilters();
    }
  },
  created() {
    this.fetchTaiwanAirports();
    this.fetchAirlines();
  },
  watch: {
    'filters.selectedPriceRange': {
      handler() {
        this.applyFilters();
      },
      deep: true
    },
    'filters.selectedAirlines': {
      handler() {
        this.applyFilters();
      },
      deep: true
    }
  }
}
</script>

<style scoped>
.flight-search-page {
  padding: 2rem 0;
  background-color: #f8f8f8;
  min-height: calc(100vh - 60px);
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1rem;
}

.page-title {
  margin-bottom: 2rem;
  color: #1a1a1a;
  font-weight: 600;
  text-align: center;
  letter-spacing: 0.05em;
  font-size: 2rem;
}

.search-panel {
  background-color: #ffffff;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  padding: 2.5rem;
  margin-bottom: 2.5rem;
  transition: box-shadow 0.3s ease;
}

.search-form {
  display: flex;
  flex-direction: column;
  gap: 1.8rem;
}

.form-row {
  display: flex;
  gap: 1.8rem;
}

.form-group {
  flex: 1;
}

.search-btn-container {
  display: flex;
  align-items: flex-end;
}

.search-btn {
  width: 100%;
  padding: 0.85rem 1.5rem;
  background-color: #1a1a1a;
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  letter-spacing: 0.03em;
}

.search-btn:hover {
  background-color: #333333;
  transform: translateY(-2px);
}

.search-btn:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
  transform: none;
}

.flight-results {
  background-color: #ffffff;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  padding: 2.5rem;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.8rem;
  padding-bottom: 1.2rem;
  border-bottom: 1px solid #f0f0f0;
}

.results-title {
  font-size: 1.6rem;
  color: #1a1a1a;
  font-weight: 600;
  letter-spacing: 0.03em;
}

.results-count {
  font-size: 1rem;
  color: #555555;
  font-weight: 500;
}

.results-container {
  display: flex;
  gap: 2.5rem;
}

.filters-panel {
  width: 320px;
  flex-shrink: 0;
  background-color: #fafafa;
  padding: 1.5rem;
  border-radius: 8px;
}

.filters-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.8rem;
}

.filters-header h3 {
  margin: 0;
  color: #1a1a1a;
  font-weight: 600;
  letter-spacing: 0.03em;
}

.clear-filters {
  background: none;
  border: none;
  color: #333333;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  transition: color 0.2s ease;
}

.clear-filters:hover {
  color: #000000;
  text-decoration: underline;
}

.results-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 1.2rem;
}

.flight-card-item {
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.flight-card-item:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}

.no-results {
  padding: 4rem 0;
  text-align: center;
  color: #555555;
}

.clear-filters-btn {
  background-color: #1a1a1a;
  color: white;
  border: none;
  border-radius: 6px;
  padding: 0.85rem 1.8rem;
  cursor: pointer;
  margin-top: 1.5rem;
  font-weight: 500;
  letter-spacing: 0.03em;
  transition: background-color 0.2s ease;
}

.clear-filters-btn:hover {
  background-color: #333333;
}

@media (max-width: 992px) {
  .results-container {
    flex-direction: column;
  }
  
  .filters-panel {
    width: 100%;
    margin-bottom: 1.8rem;
  }
}

@media (max-width: 768px) {
  .form-row {
    flex-direction: column;
    gap: 1.2rem;
  }
  
  .search-panel, .flight-results {
    padding: 1.8rem;
  }
  
  .results-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.8rem;
  }
  
  .page-title {
    font-size: 1.8rem;
  }
}
</style> 