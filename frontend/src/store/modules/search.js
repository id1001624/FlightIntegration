import { defineStore } from 'pinia';

/**
 * 航班搜索狀態存儲
 * 用於保持搜尋結果和條件，避免彈窗關閉或頁面切換時丟失狀態
 */
export const useSearchStore = defineStore('search', {
  state: () => ({
    // 搜索參數
    searchParams: {
      departureAirport: null,
      arrivalAirport: null,
      departureDate: null,
      returnDate: null,
      classType: 'economy'
    },
    
    // 搜索結果
    flights: [],
    filteredFlights: [],
    
    // 搜索狀態
    hasSearched: false,
    isSearching: false,
    
    // 篩選條件
    filters: {
      airlines: [],
      priceRange: {
        min: 0,
        max: 50000
      }
    }
  }),
  
  getters: {
    // 獲取搜索路線
    searchRoute: (state) => {
      if (!state.searchParams.departureAirport || !state.searchParams.arrivalAirport) {
        return '';
      }
      return `${state.searchParams.departureAirport.code || ''} → ${state.searchParams.arrivalAirport.code || ''}`;
    },
    
    // 獲取格式化的出發日期
    formattedDepartureDate: (state) => {
      if (!state.searchParams.departureDate) return '';
      const date = new Date(state.searchParams.departureDate);
      return date.toLocaleDateString('zh-TW', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        weekday: 'long'
      });
    },
    
    // 搜索結果是否為空
    hasResults: (state) => {
      return state.filteredFlights && state.filteredFlights.length > 0;
    }
  },
  
  actions: {
    // 更新搜索參數
    setSearchParams(params) {
      this.searchParams = { ...params };
    },
    
    // 更新搜索結果
    setFlights(flights) {
      this.flights = [...flights];
      this.filteredFlights = [...flights];
      
      // 動態設定價格範圍
      if (flights && flights.length > 0) {
        const maxPrice = Math.max(...flights.map(f => f.price?.amount || 0), 0);
        this.filters.priceRange.max = Math.ceil(maxPrice / 1000) * 1000 || 50000;
        this.filters.priceRange.min = 0;
      }
    },
    
    // 更新搜索狀態
    setSearchState(isSearching, hasSearched) {
      this.isSearching = isSearching;
      if (hasSearched !== undefined) {
        this.hasSearched = hasSearched;
      }
    },
    
    // 應用篩選條件
    applyFilters(newFilters) {
      // 更新篩選條件
      if (newFilters) {
        if (newFilters.airlines) {
          this.filters.airlines = [...newFilters.airlines];
        }
        if (newFilters.priceRange) {
          this.filters.priceRange.min = newFilters.priceRange.min;
          this.filters.priceRange.max = newFilters.priceRange.max;
        }
      }
      
      // 應用篩選條件到航班列表
      this.filteredFlights = this.flights.filter(flight => {
        // 航空公司篩選
        if (this.filters.airlines.length > 0) {
          const airlineCode = flight.airline?.code || '';
          if (!airlineCode || !this.filters.airlines.includes(airlineCode)) {
            return false;
          }
        }

        // 價格篩選
        const flightPrice = flight.price?.amount;
        if (flightPrice === null || typeof flightPrice === 'undefined') {
          if (this.filters.priceRange.min > 0) {
            return false;
          }
        } else if (flightPrice < this.filters.priceRange.min || flightPrice > this.filters.priceRange.max) {
          return false;
        }

        return true;
      });
    },
    
    // 重置所有狀態
    resetAll() {
      this.searchParams = {
        departureAirport: null,
        arrivalAirport: null,
        departureDate: null,
        returnDate: null,
        classType: 'economy'
      };
      this.flights = [];
      this.filteredFlights = [];
      this.hasSearched = false;
      this.filters = {
        airlines: [],
        priceRange: {
          min: 0,
          max: 50000
        }
      };
    }
  }
}); 