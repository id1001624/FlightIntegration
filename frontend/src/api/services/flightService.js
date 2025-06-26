import api from '../index';

// 添加緩存系統
const cache = {
  airports: {
    data: {},
    timestamp: {},
    ttl: 60 * 60 * 1000 // 1小時緩存
  },
  destinations: {
    data: {},
    timestamp: {},
    ttl: 30 * 60 * 1000 // 30分鐘緩存
  },
  airlines: {
    data: {},
    timestamp: {},
    ttl: 60 * 60 * 1000 // 1小時緩存
  },
  flights: {
    data: {},
    timestamp: {},
    ttl: 5 * 60 * 1000 // 5分鐘緩存
  }
};

// 緩存檢查函數
function checkCache(cacheType, cacheKey = 'default') {
  const cacheItem = cache[cacheType];
  
  if (!cacheItem) {
    console.warn(`緩存類型 ${cacheType} 不存在`);
    return false;
  }
  
  if (!cacheItem.data) cacheItem.data = {};
  if (!cacheItem.timestamp) cacheItem.timestamp = {};
  
  if (cacheKey === 'default') {
    if (!cacheItem.timestamp.default) return false;
    const now = Date.now();
    return (now - cacheItem.timestamp.default) < cacheItem.ttl;
  } else {
    if (!cacheItem.data[cacheKey]) return false;
    if (!cacheItem.timestamp[cacheKey]) return false;
    
    const now = Date.now();
    return (now - cacheItem.timestamp[cacheKey]) < cacheItem.ttl;
  }
}

/**
 * 航班服務
 * 處理航班查詢和相關數據獲取
 */
const flightService = {
  /**
   * 獲取所有有航班的出發機場
   * @returns {Promise} 返回機場列表
   */
  async getTaiwanAirports() {
    const cacheKey = `airports_all_with_activity`;
    
    if (checkCache('airports', cacheKey)) {
      return cache.airports.data[cacheKey];
    }

    try {
      const correctUrl = `/airports/`;
      const response = await api.get(correctUrl);
      
      const data = this._handleResponse(response);
      
      if (!data || !Array.isArray(data)) {
        throw new Error('API未返回有效的機場列表數據');
      }
      
      const enhancedData = data.map(airport => {
        const isTaiwan = airport.country === 'Taiwan';
        return {
          ...airport,
          activity_score: airport.activity_score !== undefined ? airport.activity_score : 0,
          region: isTaiwan ? '台灣' : (airport.region || this._getAirportRegion(airport.code))
        };
      });
      
      cache.airports.data[cacheKey] = enhancedData;
      cache.airports.timestamp[cacheKey] = Date.now();
      
      return enhancedData;
    } catch (error) {
      console.error('獲取所有機場列表失敗 (原getTaiwanAirports):', error);
      throw error;
    }
  },

  /**
   * 獲取指定出發機場的目的地列表 (使用 Amadeus Airport Routes API)
   * 現在使用 Amadeus Airport Routes API 獲取即時目的地資訊，
   * 確保目的地資料與航班搜索使用相同的數據源。
   * 
   * @param {string} departureCode 出發機場代碼
   * @param {string} [date] 日期參數 (暫時忽略，因為 Airport Routes API 不支持日期過濾)
   * @returns {Promise} 返回目的地機場列表
   */
  async getDestinations(departureCode, date) {
    // 使用新的 Airport Routes API，不考慮 date 參數因為 API 不支持
    const cacheKey = `amadeus_routes_${departureCode}`;
    
    if (checkCache('destinations', cacheKey)) {
      console.log(`使用緩存的 Amadeus 目的地機場數據 (${cacheKey})`);
      return cache.destinations.data[cacheKey];
    }
    
    try {
      // 使用新的 Amadeus Airport Routes API
      const url = `/amadeus/flights/airport-destinations/${departureCode}`;
      const response = await api.get(url);
      
      // 處理新的 API 響應格式
      const responseData = response.data;
      
      if (!responseData.success) {
        throw new Error(responseData.message || 'API 返回失敗狀態');
      }
      
      const data = responseData.data;
      
      if (!data || !Array.isArray(data)) {
        throw new Error('API未返回有效的機場列表數據');
      }
      
      // 數據已經在後端格式化，直接使用
      const enhancedData = data.map(airport => ({
        ...airport,
        // 如果沒有 region，使用輔助函數設置
        region: airport.region || this._getAirportRegion(airport.airport_id)
      }));
      
      cache.destinations.data[cacheKey] = enhancedData;
      cache.destinations.timestamp[cacheKey] = Date.now();
      
      console.log(`成功獲取 ${enhancedData.length} 個 Amadeus 目的地機場`);
      return enhancedData;
      
    } catch (error) {
      console.error('獲取 Amadeus 目的地機場列表失敗:', error);
      
      // 如果 Amadeus API 失敗，回退到本地數據庫
      console.log('嘗試回退到本地數據庫API...');
      try {
        const fallbackUrl = date 
          ? `/airports/${departureCode}/destinations?date=${date}` 
          : `/airports/${departureCode}/destinations`;
        const fallbackResponse = await api.get(fallbackUrl);
        
        const fallbackData = fallbackResponse.data;
        
        if (fallbackData && Array.isArray(fallbackData)) {
          const enhancedFallbackData = fallbackData.map(airport => ({
            ...airport,
            region: this._getAirportRegion(airport.code || airport.airport_id)
          }));
          
          console.log(`回退成功：獲取 ${enhancedFallbackData.length} 個本地目的地機場`);
          return enhancedFallbackData;
        }
      } catch (fallbackError) {
        console.error('回退到本地數據庫也失敗:', fallbackError);
      }
      
      throw error;
    }
  },

  /**
   * 獲取所有航空公司
   * @returns {Promise} 返回航空公司列表
   */
  async getAirlines() {
    if (checkCache('airlines')) {
      return cache.airlines.data['default'];
    }
    try {
      const response = await api.get('/airlines/');
      const data = response.data;
      
      if (!data || !Array.isArray(data)) {
        throw new Error('API未返回有效的航空公司列表');
      }
      
      cache.airlines.data['default'] = data;
      cache.airlines.timestamp['default'] = Date.now();
      
      return data;
    } catch (error) {
      console.error('獲取航空公司列表失敗:', error);
      throw error;
    }
  },

  /**
   * 根據指定參數搜索航班
   * @param {object} params - 搜索參數 { departureCode, arrivalCode, departureDate }
   * @returns {Promise<Array>} 返回航班結果數組
   */
  async searchFlights(params) {
    const { departureCode, arrivalCode, departureDate } = params;
    if (!departureCode || !arrivalCode || !departureDate) {
      console.error('搜索航班缺少必要參數:', params);
      return Promise.reject(new Error('出發地、目的地和日期為必填項。'));
    }

    const cacheKey = `${departureCode}-${arrivalCode}-${departureDate}`;
    if (checkCache('flights', cacheKey)) {
      console.log('從快取返回航班數據');
      return cache.flights.data[cacheKey];
    }
    
    try {
      const response = await api.get('/amadeus/flights/offers', {
        params: {
          origin: departureCode,
          destination: arrivalCode,
          date: departureDate,
        }
      });
      
      const flights = response.data.data || [];

      if (!Array.isArray(flights)) {
        console.error("API回傳的數據格式不正確，預期 'data' 是一個陣列:", response.data);
        return [];
      }
      
      console.log('從 API 獲取並處理後的航班數據:', flights);
      
      cache.flights.data[cacheKey] = flights;
      cache.flights.timestamp[cacheKey] = Date.now();

      return flights;
    } catch (error) {
      console.error('搜索航班時發生錯誤:', error);
      if (error.response && error.response.data && error.response.data.message) {
        console.error('API 錯誤訊息:', error.response.data.message);
      }
      return [];
    }
  },

  /**
   * 獲取特定日期範圍內的最低票價
   * @param {Object} params 查詢參數
   * @param {string} params.departure 出發機場代碼
   * @param {string} params.arrival 到達機場代碼
   * @param {string} params.start_date 開始日期
   * @param {string} [params.end_date] 結束日期
   * @returns {Promise} 返回最低票價映射
   */
  getLowestPrices(params) {
    return api.get('/ticket-prices/lowest', { params });
  },

  /**
   * 獲取航班詳情
   * @param {string} flightId 我們系統數據庫中的航班ID
   * @returns {Promise} 返回航班詳情對象 (處理過的)
   */
  async getFlightDetails(flightId) {
    console.log(`獲取航班詳情: ${flightId}`);
    try {
      const response = await api.get(`/flights/${flightId}`);
      console.log(`獲取航班 ${flightId} 詳情 API 回應:`, response);

      if (response && response.success && response.data) {
        return response.data;
      } else {
        throw new Error(response.error || '獲取航班詳情失敗');
      }
    } catch (error) {
      console.error(`獲取航班詳情 ${flightId} 失敗:`, error);
      throw error;
    }
  },

  _mapClassTypeToAPI(classType) {
    const mapping = {
      'Economy': 'ECONOMY',
      'Business': 'BUSINESS',
      'First': 'FIRST',
    };
    return mapping[classType] || 'ECONOMY';
  },

  clearCache() {
    for (const key in cache) {
      cache[key].data = {};
      cache[key].timestamp = {};
    }
    console.log('所有客戶端緩存已清除');
  },

  async getAirportByCode(code) {
    const cacheKey = `airport_${code}`;
    if (checkCache('airports', cacheKey)) {
      return cache.airports.data[cacheKey];
    }
    try {
      const response = await api.get(`/airports/${code}`);
      const airport = this._handleResponse(response);
      cache.airports.data[cacheKey] = airport;
      cache.airports.timestamp[cacheKey] = Date.now();
      return airport;
    } catch (error) {
      console.error(`獲取機場 ${code} 失敗:`, error);
      return null;
    }
  },

  _handleResponse(response) {
    if (response && response.data) {
      if (response.data.hasOwnProperty('success') && response.data.hasOwnProperty('data')) {
        if (response.data.success) {
          return response.data.data;
        } else {
          throw new Error(response.data.message || 'API請求失敗');
        }
      }
      return response.data;
    }
    throw new Error('無效的API響應');
  },
  
  async getAllAirports() {
    const cacheKey = 'all_airports';
    if (checkCache('airports', cacheKey)) {
      return cache.airports.data[cacheKey];
    }
    try {
      const response = await api.get('/airports/all');
      const airports = this._handleResponse(response);
      const enhancedData = airports.map(airport => ({
        ...airport,
        region: airport.region || this._getAirportRegion(airport.airport_id)
      }));
      cache.airports.data[cacheKey] = enhancedData;
      cache.airports.timestamp[cacheKey] = Date.now();
      return enhancedData;
    } catch (error) {
      console.error('獲取所有機場列表失敗:', error);
      throw error;
    }
  },

  _getAirportRegion(code) {
    const regions = {
      'TPE': '台灣', 'TSA': '台灣', 'KHH': '台灣', 'RMQ': '台灣',
      'HKG': '香港', 'MFM': '澳門',
      'NRT': '日本', 'HND': '日本', 'KIX': '日本',
      'ICN': '韓國', 'GMP': '韓國',
      'SIN': '新加坡',
      'BKK': '泰國',
      'KUL': '馬來西亞'
    };
    return regions[code] || '其他';
  },

  async getAirports() {
    try {
      const response = await api.get('/airports');
      return response.data.data;
    } catch (error) {
      console.error('獲取機場時出錯:', error);
      return [];
    }
  }
};

export default flightService;