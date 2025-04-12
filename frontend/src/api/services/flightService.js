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
  
  // 檢查cacheItem是否存在
  if (!cacheItem) {
    console.warn(`緩存類型 ${cacheType} 不存在`);
    return false;
  }
  
  // 確保緩存數據和時間戳對象已初始化
  if (!cacheItem.data) cacheItem.data = {};
  if (!cacheItem.timestamp) cacheItem.timestamp = {};
  
  if (cacheKey === 'default') {
    if (!cacheItem.timestamp.default) return false;
    const now = Date.now();
    return (now - cacheItem.timestamp.default) < cacheItem.ttl;
  } else {
    // 檢查特定鍵的緩存
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
   * 處理API回應，統一處理不同格式的回應
   * @param {Object|Array} response - API回應
   * @returns {Array} - 處理後的數據數組
   */
  _handleResponse(response) {
    // 如果響應為null或undefined，返回空數組
    if (response === null || response === undefined) {
      console.warn('API回應為null或undefined');
      return [];
    }
    
    // 如果響應是字符串，嘗試解析JSON
    if (typeof response === 'string') {
      try {
        response = JSON.parse(response);
      } catch (e) {
        console.error('無法解析JSON響應:', e);
        return [];
      }
    }
    
    // 處理outbound結構 (後端API返回格式)
    if (response && response.outbound) {
      console.log('找到outbound屬性，返回航班列表');
      // 確保返回數組
      return Array.isArray(response.outbound) ? response.outbound : [];
    }
    
    // 處理outbound_flights結構 (舊版API返回格式)
    if (response && response.outbound_flights) {
      // 確保返回數組
      return Array.isArray(response.outbound_flights) ? response.outbound_flights : [];
    }
    
    // 如果回應是數組，直接返回
    if (Array.isArray(response)) {
      return response;
    }
    
    // 如果回應有 data 屬性並且是數組，返回 data
    if (response && response.data && Array.isArray(response.data)) {
      return response.data;
    }
    
    // 如果響應是對象，嘗試以數組形式返回
    if (response && typeof response === 'object') {
      console.warn('API回應是對象，嘗試轉換為數組:', response);
      try {
        return Object.values(response);
      } catch (e) {
        console.error('無法將對象轉換為數組:', e);
      }
    }
    
    // 其他情況返回空數組
    console.warn('API回應格式不符合預期:', response);
    return [];
  },

  /**
   * 獲取所有有航班的出發機場
   * @param {string} [date] 出發日期 YYYY-MM-DD格式，如提供將只返回該日期有航班的機場
   * @returns {Promise} 返回機場列表
   */
  async getTaiwanAirports(date) {
    console.log(`獲取台灣機場列表，日期: ${date}`);
    
    // 生成緩存鍵
    const cacheKey = `airports_${date}`;
    
    // 檢查緩存
    if (checkCache('airports', cacheKey)) {
      console.log(`從緩存返回台灣機場列表: ${cacheKey}`);
      return cache.airports.data[cacheKey];
    }

    try {
      // 發送API請求
      const response = await api.get(`/flights/taiwan-airports?date=${date}`);
      console.log('獲取台灣機場API回應:', response);
      
      // 處理API回應
      const data = this._handleResponse(response);
      console.log('處理後的機場數據:', data);
      
      // 如果數據為空，丟出錯誤
      if (!data || !Array.isArray(data)) {
        throw new Error('API未返回有效的機場列表數據');
      }
      
      // 添加國家和地區信息
      const enhancedData = data.map(airport => {
        return {
          ...airport,
          country: airport.country || 'Taiwan',
          region: '台灣'
        };
      });
      
      // 設置緩存
      cache.airports.data[cacheKey] = enhancedData;
      cache.airports.timestamp[cacheKey] = Date.now();
      
      return enhancedData;
    } catch (error) {
      console.error('獲取台灣機場列表失敗:', error);
      throw error;
    }
  },

  /**
   * 獲取可選目的地機場
   * @param {string} departureCode 出發機場代碼
   * @param {string} [date] 日期 YYYY-MM-DD格式，如提供將只返回該日期有航班的目的地
   * @returns {Promise} 返回目的地機場列表
   */
  async getDestinations(departureCode, date) {
    // 緩存鍵包含出發地和日期
    const cacheKey = date ? `${departureCode}_${date}` : departureCode;
    
    // 檢查緩存
    if (checkCache('destinations', cacheKey)) {
      console.log(`使用緩存的目的地機場數據 (${cacheKey})`);
      return cache.destinations.data[cacheKey];
    }
    
    try {
      // 構建請求參數
      const params = {};
      if (date) {
        params.date = date;
      }
      
      const response = await api.get(`/flights/${departureCode}/destinations`, { params });
      const data = this._handleResponse(response);
      
      // 機場按國家和地區進行分類
      const regionMap = {
        'TPE': { country: 'Taiwan', region: '台灣' },
        'TSA': { country: 'Taiwan', region: '台灣' },
        'KHH': { country: 'Taiwan', region: '台灣' },
        'RMQ': { country: 'Taiwan', region: '台灣' },
        'TNN': { country: 'Taiwan', region: '台灣' },
        'PEK': { country: 'China', region: '中國' },
        'PVG': { country: 'China', region: '中國' },
        'CAN': { country: 'China', region: '中國' },
        'SHA': { country: 'China', region: '中國' },
        'SZX': { country: 'China', region: '中國' },
        'CTU': { country: 'China', region: '中國' },
        'CSX': { country: 'China', region: '中國' },
        'HKG': { country: 'Hong Kong', region: '香港/澳門' },
        'MFM': { country: 'Macau', region: '香港/澳門' },
        'NRT': { country: 'Japan', region: '東北亞' },
        'HND': { country: 'Japan', region: '東北亞' },
        'KIX': { country: 'Japan', region: '東北亞' },
        'ITM': { country: 'Japan', region: '東北亞' },
        'NGO': { country: 'Japan', region: '東北亞' },
        'ICN': { country: 'South Korea', region: '東北亞' },
        'GMP': { country: 'South Korea', region: '東北亞' },
        'BKK': { country: 'Thailand', region: '東南亞' },
        'DMK': { country: 'Thailand', region: '東南亞' },
        'HKT': { country: 'Thailand', region: '東南亞' },
        'CNX': { country: 'Thailand', region: '東南亞' },
        'SIN': { country: 'Singapore', region: '東南亞' },
        'KUL': { country: 'Malaysia', region: '東南亞' },
        'MNL': { country: 'Philippines', region: '東南亞' },
        'CGK': { country: 'Indonesia', region: '東南亞' },
        'DPS': { country: 'Indonesia', region: '東南亞' },
        'LAX': { country: 'United States', region: '美洲' },
        'JFK': { country: 'United States', region: '美洲' },
        'SFO': { country: 'United States', region: '美洲' },
        'YVR': { country: 'Canada', region: '美洲' },
        'LHR': { country: 'United Kingdom', region: '歐洲' },
        'CDG': { country: 'France', region: '歐洲' },
        'FRA': { country: 'Germany', region: '歐洲' },
        'SYD': { country: 'Australia', region: '大洋洲' },
        'MEL': { country: 'Australia', region: '大洋洲' },
        'AKL': { country: 'New Zealand', region: '大洋洲' }
      };
      
      // 為每個機場添加區域信息
      const enhancedData = data.map(airport => {
        const code = airport.iata_code || airport.code || '';
        const mapping = regionMap[code] || {};
        
        return {
          ...airport,
          country: airport.country || mapping.country || '其他',
          region: mapping.region || '其他'
        };
      });
      
      // 更新緩存
      if (!cache.destinations.data) cache.destinations.data = {};
      if (!cache.destinations.timestamp) cache.destinations.timestamp = {};
      
      cache.destinations.data[cacheKey] = enhancedData;
      cache.destinations.timestamp[cacheKey] = Date.now();
      
      return enhancedData;
    } catch (error) {
      console.error('獲取目的地機場時出錯:', error);
      throw error;
    }
  },

  /**
   * 獲取所有航空公司
   * @returns {Promise} 返回航空公司列表
   */
  async getAirlines() {
    // 檢查緩存
    if (checkCache('airlines')) {
      console.log('使用緩存的航空公司數據');
      return cache.airlines.data;
    }
    
    try {
      const response = await api.get('/flights/airlines');
      const data = this._handleResponse(response);
      
      // 更新緩存
      cache.airlines.data = data;
      cache.airlines.timestamp = Date.now();
      
      return data;
    } catch (error) {
      console.error('獲取航空公司時出錯:', error);
      throw error;
    }
  },

  /**
   * 搜索航班
   * @param {Object} params 查詢參數
   * @param {string} params.departureAirportCode 出發機場代碼
   * @param {string} params.arrivalAirportCode 到達機場代碼
   * @param {string} params.departureDate 出發日期 (YYYY-MM-DD)
   * @param {string} [params.returnDate] 返回日期
   * @param {string} [params.airlineCodes] 航空公司代碼(逗號分隔)
   * @param {number} [params.minPrice] 最低價格
   * @param {number} [params.maxPrice] 最高價格
   * @param {string} [params.classType] 艙位類型
   * @returns {Promise} 返回航班列表
   */
  async searchFlights(params) {
    // 構建緩存鍵
    const cacheKey = JSON.stringify(params);
    
    // 檢查緩存
    if (checkCache('flights', cacheKey)) {
      console.log('使用緩存的航班數據');
      return cache.flights.data[cacheKey];
    }
    
    try {
      // 轉換參數格式以符合後端API
      const apiParams = {
        departure: params.departureAirportCode,
        arrival: params.arrivalAirportCode,
        date: params.departureDate,
        return_date: params.returnDate,
        airlines: params.airlineCodes,
        price_min: params.minPrice,
        price_max: params.maxPrice,
        class_type: this._mapClassTypeToAPI(params.classType)
      };
      
      console.log('正在搜索航班，參數:', apiParams);
      const response = await api.get('/flights/search', { params: apiParams });
      const data = this._handleResponse(response);
      
      // 更新緩存
      if (!cache.flights.data) cache.flights.data = {};
      if (!cache.flights.timestamp) cache.flights.timestamp = {};
      
      cache.flights.data[cacheKey] = data;
      cache.flights.timestamp[cacheKey] = Date.now();
      
      return data;
    } catch (error) {
      console.error('搜索航班時出錯:', error);
      throw error;
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
   * @param {string} flightId 航班ID
   * @returns {Promise} 返回航班詳情
   */
  getFlightDetails(flightId) {
    return api.get(`/flights/${flightId}`);
  },

  /**
   * 將前端艙位類型映射到後端API期望的格式
   * @param {string} classType - 前端使用的艙位類型值
   * @returns {string} - 後端期望的艙位類型值
   */
  _mapClassTypeToAPI(classType) {
    // 艙位類型映射（前端值 -> 後端值）
    const classTypeMap = {
      'economy': '經濟',
      'business': '商務',
      'first': '頭等'
    };
    
    return classType ? (classTypeMap[classType.toLowerCase()] || '經濟') : '經濟';
  },
  
  /**
   * 清除所有緩存
   */
  clearCache() {
    Object.keys(cache).forEach(key => {
      cache[key].data = null;
      cache[key].timestamp = null;
      if (typeof cache[key].data === 'object' && cache[key].data !== null) {
        cache[key].data = {};
        cache[key].timestamp = {};
      }
    });
    console.log('已清除所有緩存');
  }
};

export default flightService; 