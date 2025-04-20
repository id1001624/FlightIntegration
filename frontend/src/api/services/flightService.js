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
    console.log('[flightService] _handleResponse input:', JSON.parse(JSON.stringify(response)));
    let result = []; // 確保只在這裡宣告一次

    if (response === null || response === undefined) {
      console.warn('API回應為null或undefined');
      // result 已初始化為 []
    } else if (typeof response === 'string') {
      try {
          response = JSON.parse(response);
          // 再次檢查解析後的對象
          if (response && response.data && response.data.outbound_flights && Array.isArray(response.data.outbound_flights)) {
              console.log('找到 response.data.outbound_flights 數組 (from string)');
              result = response.data.outbound_flights; // 賦值，不重新宣告
          } else if (response && response.data && Array.isArray(response.data)) {
             console.log('找到 response.data 作為數組 (from string)');
             result = response.data; // 賦值，不重新宣告
          } else {
             console.warn('Parsed string response format not recognized:', response);
             // result 已初始化為 []
          }
      } catch (e) {
          console.error('無法解析JSON響應:', e);
          // result 已初始化為 []
      }
    } else if (response && response.data && response.data.outbound_flights && Array.isArray(response.data.outbound_flights)) {
        console.log('找到 response.data.outbound_flights 數組');
        result = response.data.outbound_flights; // 賦值，不重新宣告
    } else if (response && response.outbound && Array.isArray(response.outbound)) {
      console.log('找到 outbound 屬性，返回航班列表');
      result = response.outbound; // 賦值，不重新宣告
    } else if (response && response.outbound_flights && Array.isArray(response.outbound_flights)) {
      result = response.outbound_flights; // 賦值，不重新宣告
    } else if (Array.isArray(response)) {
      result = response; // 賦值，不重新宣告
    } else if (response && response.data && Array.isArray(response.data)) {
       console.log('找到 response.data 作為數組');
       result = response.data; // 賦值，不重新宣告
    } else if (response && typeof response === 'object') {
      console.warn('API回應是對象，嘗試轉換為數組:', response);
      try {
        result = Object.values(response); // 賦值，不重新宣告
      } catch (e) {
        console.error('無法將對象轉換為數組:', e);
        // result 已初始化為 []
      }
    } else {
      console.warn('API回應格式不符合預期:', response);
      // result 已初始化為 []
    }

    console.log('[flightService] _handleResponse output:', JSON.parse(JSON.stringify(result)));
    return result;
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
      // 發送API請求 - 修正端點 URL
      const correctUrl = `/airports/taiwan${date ? `?date=${date}` : ''}`;
      console.log(`[flightService] Requesting Taiwan airports: ${correctUrl}`); // <-- 更新日誌標識
      const response = await api.get(correctUrl);
      console.log('[flightService] Raw API response for Taiwan airports:', JSON.parse(JSON.stringify(response))); // <-- 添加日誌
      
      // 處理API回應
      const data = this._handleResponse(response);
      console.log('[flightService] Processed airport data:', JSON.parse(JSON.stringify(data))); // <-- 更新日誌標識
      
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
      console.log(`[flightService] Requesting destinations for ${departureCode} with params:`, params); // <-- 添加日誌
      const response = await api.get(`/flights/${departureCode}/destinations`, { params });
      console.log('[flightService] Raw API response for destinations:', JSON.parse(JSON.stringify(response))); // <-- 添加日誌
      const data = this._handleResponse(response);
      console.log('[flightService] Processed destination data:', JSON.parse(JSON.stringify(data))); // <-- 添加日誌
      
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
        departure: params.departure,
        arrival: params.arrival,
        date: params.date,
        return_date: params.return_date,
        airlines: params.airlines,
        price_min: params.price_min,
        price_max: params.price_max,
        class_type: this._mapClassTypeToAPI(params.class_type)
      };
      
      console.log('[flightService] Requesting flight search with params:', apiParams); // <-- 添加日誌
      const response = await api.get('/flights/search', { params });
      console.log('[flightService] Raw API response for flights:', JSON.parse(JSON.stringify(response)));

      // *** 修正：直接處理新的響應結構 ***
      let flightsData = [];
      if (response && response.data && response.data.departure && Array.isArray(response.data.departure)) {
        flightsData = response.data.departure;
        console.log('[flightService] Extracted flights directly from response.data.departure');
        // 如果需要合併回程
        // if (response.data.return && Array.isArray(response.data.return)) {
        //   flightsData = flightsData.concat(response.data.return);
        //   console.log('[flightService] Appended return flights');
        // }
      } else {
        // 如果結構不匹配或沒有航班，記錄警告
        console.warn('[flightService] Unexpected response structure or no departure flights in response.data:', response?.data);
        // flightsData 保持為 []
      }

      // *** 修正：緩存並返回直接提取的數據 ***
      cache.flights.data[cacheKey] = flightsData;
      cache.flights.timestamp[cacheKey] = Date.now();
      return flightsData;

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
   * @param {string} flightId 我們系統數據庫中的航班ID
   * @returns {Promise} 返回航班詳情對象 (處理過的)
   */
  async getFlightDetails(flightId) {
    console.log(`獲取航班詳情: ${flightId}`);
    try {
      // 注意: 後端端點是 /flights/<flight_id>
      const response = await api.get(`/flights/${flightId}`);
      console.log(`獲取航班 ${flightId} 詳情 API 回應:`, response);

      // 後端應該返回標準化的 {success: true/false, data: ..., error: ...} 格式
      if (response && response.success && response.data) {
        // 可以直接返回後端處理好的 data
        return response.data;
      } else {
        // 如果後端返回 success: false 或格式不對
        const errorMsg = (response && response.message) || '無法獲取航班詳情';
        console.error(`獲取航班 ${flightId} 詳情失敗:`, errorMsg);
        throw new Error(errorMsg);
      }
    } catch (error) {
      console.error(`調用獲取航班 ${flightId} 詳情 API 時出錯:`, error);
      // 重新拋出錯誤，讓調用者處理
      throw error;
    }
  },

  /**
   * 刷新特定航班的狀態
   * @param {string} flightId 我們系統數據庫中的航班ID
   * @returns {Promise} 返回最新的狀態信息 (處理過的)
   */
  async refreshFlightStatus(flightId) {
    console.log(`請求刷新航班狀態: ${flightId}`);
    try {
      // 調用後端新添加的端點 /flights/<flight_id>/status
      const response = await api.get(`/flights/${flightId}/status`);
      console.log(`刷新航班 ${flightId} 狀態 API 回應:`, response);

      // 檢查後端返回的標準格式
      if (response && response.success && response.data) {
        // 返回包含最新狀態信息的 data 對象
        return response.data;
      } else {
        const errorMsg = (response && response.message) || '無法刷新航班狀態';
        console.error(`刷新航班 ${flightId} 狀態失敗:`, errorMsg);
        throw new Error(errorMsg);
      }
    } catch (error) {
      console.error(`調用刷新航班 ${flightId} 狀態 API 時出錯:`, error);
      throw error;
    }
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