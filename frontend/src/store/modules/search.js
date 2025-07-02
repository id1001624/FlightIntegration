import { defineStore } from 'pinia';
import flightService from '@/api/services/flightService';

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
      classType: 'Economy'
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
    },
    recentSearches: [] // 新增：最近搜尋記錄
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
    // 新增：載入最近搜尋記錄
    loadRecentSearches() {
      try {
        const storedSearches = localStorage.getItem('recentFlightSearches');
        if (storedSearches) {
          const parsedSearches = JSON.parse(storedSearches);
          if (Array.isArray(parsedSearches)) {
            this.recentSearches = parsedSearches;
            console.log('[SearchStore] Loaded recent searches from localStorage:', this.recentSearches);
          }
        }
      } catch (error) {
        console.error('[SearchStore] Error loading recent searches from localStorage:', error);
        this.recentSearches = []; // 發生錯誤時重置為空
      }
    },

    // 新增：添加最近搜尋記錄
    addRecentSearch(routeDetails) {
      if (!routeDetails || !routeDetails.departureAirport || !routeDetails.departureAirport.code ||
          !routeDetails.arrivalAirport || !routeDetails.arrivalAirport.code) {
        console.warn('[SearchStore] Invalid routeDetails for addRecentSearch:', routeDetails);
        return;
      }

      const newSearch = {
        departureAirport: { ...routeDetails.departureAirport },
        arrivalAirport: { ...routeDetails.arrivalAirport }
        // 可以在這裡添加其他需要儲存的資訊，例如：
        // departureDate: routeDetails.departureDate,
        // classType: routeDetails.classType,
      };

      // 去重：檢查是否已存在相同的路線
      this.recentSearches = this.recentSearches.filter(search => 
        !(search.departureAirport.code === newSearch.departureAirport.code && 
          search.arrivalAirport.code === newSearch.arrivalAirport.code)
      );

      // 添加到列表頂部
      this.recentSearches.unshift(newSearch);

      // 限制數量，最多5條
      if (this.recentSearches.length > 5) {
        this.recentSearches.pop(); // 移除最舊的（最後一個）
      }

      // 更新 localStorage
      try {
        localStorage.setItem('recentFlightSearches', JSON.stringify(this.recentSearches));
        console.log('[SearchStore] Saved recent searches to localStorage:', this.recentSearches);
      } catch (error) {
        console.error('[SearchStore] Error saving recent searches to localStorage:', error);
      }
    },
    
    // 更新搜索參數
    setSearchParams(params) {
      // 創建深拷貝以避免對原始對象的修改影響 store
      const paramsCopy = JSON.parse(JSON.stringify(params));
      
      // 確保機場對象包含所有必要字段
      if (paramsCopy.departureAirport) {
        // 確保 departureAirport 有完整資訊
        this.searchParams.departureAirport = { 
          ...paramsCopy.departureAirport 
        };
      }
      
      if (paramsCopy.arrivalAirport) {
        // 確保 arrivalAirport 有完整資訊
        this.searchParams.arrivalAirport = { 
          ...paramsCopy.arrivalAirport 
        };
      }
      
      // 更新其他參數
      this.searchParams.departureDate = paramsCopy.departureDate || this.searchParams.departureDate;
      this.searchParams.returnDate = paramsCopy.returnDate || this.searchParams.returnDate;
      this.searchParams.classType = paramsCopy.classType || this.searchParams.classType;
    },
    
    // 異步搜索航班的 Action
    async searchFlights(params) {
      console.log('[SearchStore] searchFlights action 觸發，參數:', params);

      this.setSearchParams(params); // 首先更新並存儲搜索參數
      this.setSearchState(true, true); // isSearching = true, hasSearched = true

      try {
        // 適配 SearchForm.vue 發出的參數格式
        // SearchForm 發出: { departure: 'TPE', arrival: 'ICN', date: '2025-06-26', ... }
        // 但 flightService.searchFlights 期望: { departureCode, arrivalCode, departureDate }
        const searchParams = {
          departureCode: params.departure || params.departureAirport?.code,
          arrivalCode: params.arrival || params.arrivalAirport?.code,
          departureDate: params.date || params.departureDate,
        };
        
        console.log('[SearchStore] 轉換後的 flightService 參數:', searchParams);
        
        const flightResults = await flightService.searchFlights(searchParams);
        
        console.log('[SearchStore] 從 flightService 收到航班結果:', flightResults);
        
        this.setFlights(flightResults); // 將結果更新到 state
        
        // 搜索成功後，添加到最近搜索記錄
        // 如果參數中沒有完整的機場物件，就不添加到最近搜索
        if (params.departureAirport && params.arrivalAirport) {
        this.addRecentSearch(params);
        }

      } catch (error) {
        console.error('[SearchStore] searchFlights action 過程中發生錯誤:', error);
        this.setFlights([]); // 出錯時清空結果
      } finally {
        this.setSearchState(false, true); // isSearching = false, hasSearched 保持 true
      }
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
        classType: 'Economy'
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
    },
    
    // 清除機場選擇
    clearAirportSelections() {
      console.log('[SearchStore] Clearing airport selections.');
      this.searchParams.departureAirport = null;
      this.searchParams.arrivalAirport = null;
      // 注意：這裡不清空日期或其他參數，僅機場

      // 當清除機場選擇時，也考慮是否要清除最近一次的 flights 和 filteredFlights，
      // 以及 hasSearched 狀態，讓介面回到初始狀態。
      // 或者，這部分邏輯應由調用方（例如 FlightSearch.vue 的路由監聽器）決定。
      // 目前保持原樣，只清除機場選擇。
    }
  }
}); 