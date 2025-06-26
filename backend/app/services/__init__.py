"""
服務層初始化模塊
包含業務邏輯處理的服務類
"""

# 服務模組初始化

# 新的服務結構導入
from .flight_search_service import FlightSearchService
from .airport_service import AirportService
from .airline_service import AirlineService
from .flight_details_service import FlightDetailsService
from .price_analysis_service import PriceAnalysisService
from .db_utils import execute_db_operation, execute_query, normalize_cabin_class, get_price_field_by_cabin_class

# 設置服務別名 (向後兼容)
SearchService = FlightSearchService
# 為了向後兼容，將 PriceService 設為 PriceAnalysisService 的別名
PriceService = PriceAnalysisService
