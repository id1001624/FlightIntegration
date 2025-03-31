import api from '../index';

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
    // 處理outbound_flights結構
    if (response && response.outbound_flights) {
      return response.outbound_flights;
    }
    
    // 如果回應是數組，直接返回
    if (Array.isArray(response)) {
      return response;
    }
    
    // 如果回應有 data 屬性並且是數組，返回 data
    if (response && response.data && Array.isArray(response.data)) {
      return response.data;
    }
    
    // 其他情況返回空數組
    console.warn('API回應格式不符合預期:', response);
    return [];
  },

  /**
   * 獲取所有有航班的出發機場
   * @returns {Promise} 返回機場列表
   */
  getTaiwanAirports() {
    return api.get('/airports/available-departures')
      .then(response => this._handleResponse(response));
  },

  /**
   * 獲取可選目的地機場
   * @param {string} departureCode 出發機場代碼
   * @returns {Promise} 返回目的地機場列表
   */
  getDestinations(departureCode) {
    return api.get(`/airports/available-destinations/${departureCode}`)
      .then(response => this._handleResponse(response));
  },

  /**
   * 獲取所有航空公司
   * @returns {Promise} 返回航空公司列表
   */
  getAirlines() {
    return api.get('/flights/airlines')
      .then(response => this._handleResponse(response));
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
  searchFlights(params) {
    const apiParams = {};
    
    // 映射參數名稱
    if (params.departureAirportCode) apiParams.departure = params.departureAirportCode;
    if (params.arrivalAirportCode) apiParams.arrival = params.arrivalAirportCode;
    if (params.departureDate) apiParams.date = params.departureDate;
    if (params.returnDate) apiParams.return_date = params.returnDate;
    if (params.airlineCodes) apiParams.airlines = params.airlineCodes;
    if (params.minPrice) apiParams.price_min = params.minPrice;
    if (params.maxPrice) apiParams.price_max = params.maxPrice;
    if (params.classType) apiParams.class_type = this._mapClassTypeToAPI(params.classType);
    
    // 移除所有 undefined 或 null 值
    Object.keys(apiParams).forEach(key => {
      if (apiParams[key] === undefined || apiParams[key] === null) {
        delete apiParams[key];
      }
    });
    
    return api.get('/flights/search', { params: apiParams })
      .then(response => this._handleResponse(response));
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
  }
};

export default flightService; 