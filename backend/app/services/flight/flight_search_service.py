"""
航班搜索服務 - 負責處理航班搜索功能
"""
import logging
from datetime import datetime
from app.models.base import db
from app.models.user_search_history import UserSearchHistory
from flask import current_app

logger = logging.getLogger(__name__)

class FlightSearchService:
    """航班搜索服務類，提供航班搜索功能"""
    
    def __init__(self, test_mode=False, tdx_service=None, 
                 flight_cache_service=None, price_service=None):
        """初始化航班搜索服務
        
        Args:
            test_mode (bool): 是否為測試模式，測試模式下返回模擬數據
            tdx_service: TDX服務實例
            flight_cache_service: 航班緩存服務實例
            price_service: 價格服務實例
        """
        self.test_mode = test_mode
        self.tdx_service = tdx_service
        self.flight_cache_service = flight_cache_service
        self.price_service = price_service
    
    def search_flights(self, departure_airport=None, arrival_airport=None, 
                       departure_date=None, return_date=None, 
                       airline=None, sort_by='departure_time', user_id=None):
        """搜索航班
        
        Args:
            departure_airport (str): 出發機場代碼
            arrival_airport (str): 到達機場代碼
            departure_date (str): 出發日期，格式為 YYYY-MM-DD
            return_date (str, optional): 返回日期，格式為 YYYY-MM-DD
            airline (str, optional): 航空公司代碼
            sort_by (str): 排序方式，可選 departure_time, arrival_time, price
            user_id (int, optional): 用戶ID，用於記錄查詢歷史
            
        Returns:
            dict: 搜索結果，包含去程航班和返程航班
        """
        if not departure_airport or not arrival_airport or not departure_date:
            logger.error("搜索航班時缺少必要參數")
            return {
                'success': False,
                'message': "缺少必要參數：出發機場、到達機場和出發日期"
            }
        
        try:
            # 驗證日期格式
            try:
                dep_date = datetime.strptime(departure_date, '%Y-%m-%d')
                ret_date = datetime.strptime(return_date, '%Y-%m-%d') if return_date else None
            except ValueError:
                logger.error("日期格式錯誤")
                return {
                    'success': False,
                    'message': "日期格式錯誤，應為 YYYY-MM-DD"
                }
            
            # 1. 檢查緩存中是否有有效結果
            cached_outbound = self.flight_cache_service.check_cached_flights(
                departure_airport, arrival_airport, dep_date.strftime('%Y-%m-%d'), airline
            )
            
            # 2. 如果有緩存，使用緩存數據，否則從API獲取
            if cached_outbound and not current_app.config.get('BYPASS_CACHE', False):
                logger.info(f"使用緩存的航班數據: {departure_airport} -> {arrival_airport}, 日期: {departure_date}")
                outbound_flights = cached_outbound
            else:
                # 從API獲取航班數據
                if self.test_mode:
                    outbound_flights = self._get_mock_flights(
                        departure_airport, arrival_airport, dep_date.strftime('%Y-%m-%d'), airline
                    )
                else:
                    outbound_flights = self._get_real_flights(
                        departure_airport, arrival_airport, dep_date.strftime('%Y-%m-%d'), airline
                    )
                
                # 保存到緩存
                self.flight_cache_service.save_flights_to_cache(
                    outbound_flights, departure_airport, arrival_airport, 
                    dep_date.strftime('%Y-%m-%d'), airline
                )
            
            # 排序航班
            outbound_flights = self._sort_flights(outbound_flights, sort_by)
            
            # 同樣處理返程航班
            inbound_flights = []
            if return_date:
                cached_inbound = self.flight_cache_service.check_cached_flights(
                    arrival_airport, departure_airport, ret_date.strftime('%Y-%m-%d'), airline
                )
                
                if cached_inbound and not current_app.config.get('BYPASS_CACHE', False):
                    logger.info(f"使用緩存的返程航班數據: {arrival_airport} -> {departure_airport}, 日期: {return_date}")
                    inbound_flights = cached_inbound
                else:
                    if self.test_mode:
                        inbound_flights = self._get_mock_flights(
                            arrival_airport, departure_airport, ret_date.strftime('%Y-%m-%d'), airline
                        )
                    else:
                        inbound_flights = self._get_real_flights(
                            arrival_airport, departure_airport, ret_date.strftime('%Y-%m-%d'), airline
                        )
                    
                    # 保存到緩存
                    self.flight_cache_service.save_flights_to_cache(
                        inbound_flights, arrival_airport, departure_airport, 
                        ret_date.strftime('%Y-%m-%d'), airline
                    )
                
                # 排序航班
                inbound_flights = self._sort_flights(inbound_flights, sort_by)
            
            # 記錄用戶搜索歷史
            if user_id:
                self._record_search_history(
                    user_id, 
                    {
                        'departure_airport': departure_airport,
                        'arrival_airport': arrival_airport,
                        'departure_date': departure_date,
                        'return_date': return_date,
                        'airline': airline,
                        'sort_by': sort_by
                    },
                    len(outbound_flights) + len(inbound_flights)
                )
            
            return {
                'success': True,
                'data': {
                    'outbound_flights': outbound_flights,
                    'inbound_flights': inbound_flights,
                    'search_params': {
                        'departure_airport': departure_airport,
                        'arrival_airport': arrival_airport,
                        'departure_date': departure_date,
                        'return_date': return_date,
                        'airline': airline,
                        'sort_by': sort_by
                    },
                    'from_cache': bool(cached_outbound and (not return_date or cached_inbound))
                }
            }
        
        except Exception as e:
            logger.error(f"搜索航班時發生錯誤: {str(e)}")
            return {
                'success': False,
                'message': f"搜索航班時發生錯誤: {str(e)}"
            }
    
    def _get_mock_flights(self, departure_airport, arrival_airport, date, airline=None):
        """獲取模擬航班數據
        
        Args:
            departure_airport (str): 出發機場代碼
            arrival_airport (str): 到達機場代碼
            date (str): 日期，格式為 YYYY-MM-DD
            airline (str, optional): 航空公司代碼
            
        Returns:
            list: 航班列表
        """
        from app.utils.mock_data_generator import MockDataGenerator
        mock_generator = MockDataGenerator()
        return mock_generator.generate_flight_list(
            departure_airport, arrival_airport, date, airline
        )
    
    def _get_real_flights(self, departure_airport, arrival_airport, date, airline=None):
        """從TDX API獲取真實航班數據
        
        Args:
            departure_airport (str): 出發機場代碼
            arrival_airport (str): 到達機場代碼
            date (str): 日期，格式為 YYYY-MM-DD
            airline (str, optional): 航空公司代碼
            
        Returns:
            list: 航班列表
        """
        flights = self.tdx_service.get_flights(
            departure_airport, arrival_airport, date, airline
        )
        
        # 補充航班資訊
        for flight in flights:
            # 獲取票價信息
            prices = self.price_service.fetch_ticket_prices(
                flight.get('AirlineID', ''),
                flight.get('FlightNumber', '').replace(flight.get('AirlineID', ''), ''),
                date
            )
            
            if prices.get('success'):
                flight['prices'] = prices.get('data', [])
            
            # 計算飛行時間（分鐘）
            if 'ScheduleDepartureTime' in flight and 'ScheduleArrivalTime' in flight:
                try:
                    dep_time = datetime.strptime(flight['ScheduleDepartureTime'], '%Y-%m-%dT%H:%M:%S')
                    arr_time = datetime.strptime(flight['ScheduleArrivalTime'], '%Y-%m-%dT%H:%M:%S')
                    duration = int((arr_time - dep_time).total_seconds() / 60)
                    flight['Duration'] = duration
                except (ValueError, TypeError):
                    flight['Duration'] = None
        
        return flights
    
    def _sort_flights(self, flights, sort_by):
        """排序航班
        
        Args:
            flights (list): 航班列表
            sort_by (str): 排序方式，可選 departure_time, arrival_time, price, duration
            
        Returns:
            list: 排序後的航班列表
        """
        if not flights:
            return []
        
        # 根據不同條件排序
        if sort_by == 'departure_time':
            return sorted(flights, key=lambda x: x.get('ScheduleDepartureTime', ''))
        elif sort_by == 'arrival_time':
            return sorted(flights, key=lambda x: x.get('ScheduleArrivalTime', ''))
        elif sort_by == 'price':
            # 使用經濟艙最低價格排序
            return sorted(
                flights, 
                key=lambda x: min([p.get('amount', float('inf')) for p in x.get('prices', [])]) 
                if x.get('prices') else float('inf')
            )
        elif sort_by == 'duration':
            return sorted(flights, key=lambda x: x.get('Duration', float('inf')))
        else:
            return flights
    
    def _record_search_history(self, user_id, search_params, results_count):
        """記錄用戶搜索歷史
        
        Args:
            user_id (int): 用戶ID
            search_params (dict): 搜索參數
            results_count (int): 結果數量
        """
        try:
            search_history = UserSearchHistory(
                user_id=user_id,
                departure_airport_id=search_params.get('departure_airport'),
                arrival_airport_id=search_params.get('arrival_airport'),
                departure_date=datetime.strptime(search_params.get('departure_date'), '%Y-%m-%d').date(),
                return_date=datetime.strptime(search_params.get('return_date'), '%Y-%m-%d').date() if search_params.get('return_date') else None
            )
            
            db.session.add(search_history)
            db.session.commit()
            logger.info(f"用戶 {user_id} 的搜索歷史已記錄")
        except Exception as e:
            db.session.rollback()
            logger.error(f"記錄搜索歷史時發生錯誤: {str(e)}")
