"""
服務層 - 實現業務邏輯

此包包含所有業務邏輯服務，負責：
1. 實現核心業務邏輯
2. 與數據庫交互
3. 調用外部API和第三方服務
4. 處理數據轉換和業務規則

服務層不直接處理HTTP請求/響應，而是由控制器層調用。
"""

import os
from app.services.auth_service import AuthService
from app.services.flight.flight_search_service import FlightSearchService
from app.services.flight.flight_detail_service import FlightDetailService
from app.services.flight.flight_status_service import FlightStatusService
from app.services.flight.flight_cache_service import FlightCacheService
from app.services.user_service import UserService
from app.services.tdx_service import TDXService
from app.services.price_service import PriceService
from app.services.prediction_service import PredictionService
from app.services.data_sync_service import DataSyncService
from app.services.weather_service import WeatherService
from app.services.flightstats_service import FlightStatsService
from app.utils.api_client import ApiClient

# 獲取測試模式設置
TEST_MODE = os.environ.get('TEST_MODE', 'False').lower() == 'true'

# 創建共享服務實例
auth_service = AuthService()
api_client = ApiClient()
tdx_service = TDXService(test_mode=TEST_MODE, auth_service=auth_service)
flightstats_service = FlightStatsService(test_mode=TEST_MODE)
weather_service = WeatherService(test_mode=TEST_MODE, tdx_service=tdx_service)
price_service = PriceService(test_mode=TEST_MODE)

# 航班相關服務
flight_cache_service = FlightCacheService(test_mode=TEST_MODE)
flight_search_service = FlightSearchService(
    test_mode=TEST_MODE, 
    tdx_service=tdx_service, 
    flight_cache_service=flight_cache_service,
    price_service=price_service
)
flight_detail_service = FlightDetailService(
    test_mode=TEST_MODE,
    flightstats_service=flightstats_service,
    price_service=price_service,
    weather_service=weather_service
)
flight_status_service = FlightStatusService(
    test_mode=TEST_MODE,
    flightstats_service=flightstats_service
)

# 其他服務
prediction_service = PredictionService(test_mode=TEST_MODE, weather_service=weather_service)
user_service = UserService(auth_service=auth_service)
data_sync_service = DataSyncService(test_mode=TEST_MODE, tdx_service=tdx_service)

# 導出所有服務實例，便於在控制器中使用
__all__ = [
    'auth_service',
    'flight_search_service',
    'flight_detail_service',
    'flight_status_service',
    'flight_cache_service',
    'user_service',
    'tdx_service',
    'price_service',
    'prediction_service',
    'data_sync_service',
    'weather_service',
    'flightstats_service'
]