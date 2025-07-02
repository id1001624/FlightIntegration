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
   * 獲取台灣國際機場（僅有國際航班的機場）
   * @returns {Promise} 返回台灣國際機場列表
   */
  async getTaiwanInternationalAirports() {
    const cacheKey = `taiwan_international_airports`;
    
    if (checkCache('airports', cacheKey)) {
      return cache.airports.data[cacheKey];
    }
    
    try {
      const response = await api.get('/airports/taiwan-international');
      
      const data = this._handleResponse(response);
      
      if (!data || !Array.isArray(data)) {
        throw new Error('API未返回有效的台灣國際機場列表數據');
      }
      
      // 為台灣機場添加活躍度分數和地區信息
      const enhancedData = data.map(airport => ({
        ...airport,
        activity_score: airport.activity_score !== undefined ? airport.activity_score : 0,
        region: '台灣'
      }));
      
      // 按活躍度分數排序（如果有的話）
      enhancedData.sort((a, b) => (b.activity_score || 0) - (a.activity_score || 0));
      
      cache.airports.data[cacheKey] = enhancedData;
      cache.airports.timestamp[cacheKey] = Date.now();
      
      return enhancedData;
    } catch (error) {
      console.error('獲取台灣國際機場列表失敗:', error);
      throw error;
    }
  },

  /**
   * 獲取指定出發機場的目的地列表（優先使用快速緩存）
   * @param {string} departureCode 出發機場代碼
   * @param {string} date 日期（可選）
   * @param {boolean} useCache 是否優先使用緩存（默認 true）
   * @returns {Promise<Array>} 目的地機場列表
   */
  async getDestinations(departureCode, date, useCache = true) {
    try {
      console.log(`正在獲取從 ${departureCode} 出發的目的地...`);
      
      // 優先使用快速緩存端點
      if (useCache) {
        try {
          const cacheResponse = await api.get(`/airports/${departureCode}/destinations-cached`);
          
          if (cacheResponse.success && cacheResponse.data && cacheResponse.data.length > 0) {
            console.log(`從緩存成功獲取 ${cacheResponse.data.length} 個目的地機場`);
            
            // 轉換數據格式以保持兼容性
            const formattedDestinations = cacheResponse.data.map(dest => ({
              code: dest.airport_id,
              airport_id: dest.airport_id,
              name: dest.name_zh || dest.name || dest.airport_id,
              name_zh: dest.name_zh || '',
              name_en: dest.name || '',
              city: dest.city || '',
              country: dest.country || '',
              region: this._getAirportRegion(dest.airport_id)
            }));
            
            return formattedDestinations;
          }
        } catch (cacheError) {
          console.warn('緩存端點失敗，回退到 Amadeus API:', cacheError.message);
        }
      }
      
      // 回退到 Amadeus API
      const response = await api.get(`/amadeus/flights/airport-destinations/${departureCode}`);
      
      if (!response.success) {
        throw new Error(response.message || '獲取目的地失敗');
      }
      
      const destinations = response.data || [];
      console.log(`從 Amadeus API 成功獲取 ${destinations.length} 個目的地機場`);
      
      // 後端已經處理了中文名稱，直接返回數據
      return destinations;
      
    } catch (error) {
      console.error('獲取目的地時發生錯誤:', error);
      throw error;
    }
  },

  /**
   * 獲取指定出發機場的熱門目的地列表（僅使用緩存，極快響應）
   * @param {string} departureCode 出發機場代碼
   * @param {number} limit 限制返回數量
   * @returns {Promise<Array>} 熱門目的地機場列表
   */
  async getPopularDestinations(departureCode, limit = 10) {
    try {
      console.log(`正在獲取從 ${departureCode} 出發的熱門目的地...`);
      
      const response = await api.get(`/airports/${departureCode}/destinations-popular?limit=${limit}`);
      
      if (!response.success) {
        throw new Error(response.message || '獲取熱門目的地失敗');
      }
      
      const destinations = response.data || [];
      console.log(`成功獲取 ${destinations.length} 個熱門目的地機場`);
      
      // 轉換數據格式以保持兼容性
      const formattedDestinations = destinations.map(dest => ({
        code: dest.airport_id,
        airport_id: dest.airport_id,
        name: dest.name_zh || dest.name || dest.airport_id,
        name_zh: dest.name_zh || '',
        name_en: dest.name || '',
        city: dest.city || '',
        country: dest.country || '',
        region: this._getAirportRegion(dest.airport_id),
        flight_count_30days: dest.flight_count_30days || 0,
        popularity_rank: dest.popularity_rank || 0
      }));
      
      return formattedDestinations;
      
    } catch (error) {
      console.error('獲取熱門目的地時發生錯誤:', error);
      throw error;
    }
  },

  /**
   * 為 Amadeus 目的地資料添加中文名稱
   * @param {Array} destinations Amadeus 目的地資料
   * @returns {Promise<Array>} 包含中文名稱的目的地資料
   */
  async _enrichDestinationsWithChineseNames(destinations) {
    try {
      // 提取所有機場代碼 - 修正屬性名稱
      const airportCodes = destinations
        .map(dest => dest.airport_id || dest.iataCode || dest.code)
        .filter(code => code && code.trim()) // 過濾空值
        .join(',');
      
      // 如果沒有有效的機場代碼，直接返回原數據
      if (!airportCodes) {
        console.warn('沒有找到有效的機場代碼');
        return destinations.map(dest => ({
          code: dest.airport_id || dest.iataCode || dest.code,
          airport_id: dest.airport_id || dest.iataCode || dest.code,
          name: dest.name_zh || dest.name || dest.airport_id || dest.iataCode || dest.code,
          name_zh: dest.name_zh || '',
          name_en: dest.name_en || dest.name || '',
          city: dest.city || '',
          country: dest.country || '',
          region: dest.region || this._getAirportRegion(dest.airport_id || dest.iataCode || dest.code)
        }));
      }
      
      // 批量獲取機場資訊
      const airportsResponse = await api.get(`/airports/batch?codes=${airportCodes}`);
      const airportsData = airportsResponse.data || [];
      
      // 創建機場代碼到資料的映射
      const airportMap = {};
      airportsData.forEach(airport => {
        airportMap[airport.code] = airport;
      });
      
      // 合併 Amadeus 資料和本地中文名稱
      const enrichedDestinations = destinations.map(dest => {
        const airportCode = dest.airport_id || dest.iataCode || dest.code;
        const localAirport = airportMap[airportCode];
        
        return {
          code: airportCode,
          airport_id: airportCode,
          name: localAirport?.name_zh || dest.name_zh || localAirport?.name_en || dest.name || airportCode,
          name_zh: localAirport?.name_zh || dest.name_zh || '',
          name_en: localAirport?.name_en || dest.name_en || dest.name || '',
          city: localAirport?.city || dest.city || '',
          country: localAirport?.country || dest.country || '',
          region: localAirport?.region || dest.region || this._getAirportRegion(airportCode)
        };
      });
      
      return enrichedDestinations;
      
    } catch (error) {
      console.warn('批量獲取機場中文名稱失敗，使用原始資料:', error);
      
      // 如果批量請求失敗，返回基本格式的資料
      return destinations.map(dest => {
        const airportCode = dest.airport_id || dest.iataCode || dest.code;
        return {
          code: airportCode,
          airport_id: airportCode,
          name: dest.name_zh || dest.name || airportCode,
          name_zh: dest.name_zh || '',
          name_en: dest.name_en || dest.name || '',
          city: dest.city || '',
          country: dest.country || '',
          region: dest.region || this._getAirportRegion(airportCode)
        };
      });
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
      
      // 檢查是否為統一的API回應格式
      if (response.success !== undefined) {
        // 新的統一格式：{success: true, message: '...', data: [...]}
        if (!response.success) {
          throw new Error(response.message || 'API 返回失敗狀態');
        }
      }
      
      // 統一處理航班數據
      const flights = response.data || [];

      if (!Array.isArray(flights)) {
        console.error("API回傳的數據格式不正確，預期 'data' 是一個陣列:", response);
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