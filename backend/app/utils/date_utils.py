"""
日期時間處理工具 - 提供日期時間解析與格式化功能
"""
from datetime import datetime, timedelta
import logging
from typing import Optional, Union, List

logger = logging.getLogger('date_utils')

def parse_datetime(datetime_str: str) -> Optional[datetime]:
    """
    統一的日期時間解析函數，主要支持 ISO 8601 格式
    
    Args:
        datetime_str: 日期時間字符串
        
    Returns:
        解析後的datetime對象，解析失敗時返回None
    """
    if not datetime_str:
        return None
    
    # 標準化支持的格式列表
    formats = [
        '%Y-%m-%dT%H:%M:%S.%f',  # ISO格式帶毫秒
        '%Y-%m-%dT%H:%M:%S',     # ISO格式
        '%Y-%m-%dT%H:%M',        # ISO格式不帶秒
        '%Y-%m-%d %H:%M:%S',     # 標準數據庫格式
        '%Y-%m-%d %H:%M',        # 標準數據庫格式不帶秒
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(datetime_str, fmt)
        except ValueError:
            continue
            
    # 如果標準格式失敗，可以嘗試使用 dateutil (如果安裝了)
    try:
        from dateutil import parser as dateutil_parser
        return dateutil_parser.parse(datetime_str)
    except ImportError:
        logger.debug("dateutil庫不可用，跳過此解析方法")
    except Exception as e:
        logger.error(f"所有解析方法都失敗，無法解析日期時間: {datetime_str}, 錯誤: {str(e)}")
    
    return None

def format_datetime(dt: datetime, format_str: str = '%Y-%m-%dT%H:%M:%S') -> str:
    """
    統一的日期時間格式化函數
    
    Args:
        dt: datetime對象
        format_str: 輸出格式
        
    Returns:
        格式化的日期時間字符串
    """
    if not dt:
        return ""
    return dt.strftime(format_str)

def get_date_range(start_date: Union[str, datetime], days: int = 1) -> List[str]:
    """
    獲取從起始日期開始的一系列日期
    
    Args:
        start_date: 起始日期，可以是字符串或datetime對象
        days: 天數
        
    Returns:
        日期列表，格式為YYYY-MM-DD
    """
    if isinstance(start_date, str):
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        except ValueError:
            parsed_date = parse_datetime(start_date)
            if not parsed_date:
                raise ValueError(f"無法解析日期字符串: {start_date}")
            start_date = parsed_date
    
    return [(start_date + timedelta(days=d)).strftime('%Y-%m-%d') for d in range(days)]

def estimate_arrival_time(departure_time: Union[str, datetime], is_domestic: bool = False) -> datetime:
    """
    估算到達時間
    
    Args:
        departure_time: 出發時間，可以是字符串或datetime對象
        is_domestic: 是否為國內航班
        
    Returns:
        估算的到達時間
    """
    if isinstance(departure_time, str):
        departure_time = parse_datetime(departure_time)
        
    if not departure_time:
        raise ValueError("無效的出發時間")
        
    # 國內航班約1小時，國際航班約3小時
    flight_hours = 1 if is_domestic else 3
    return departure_time + timedelta(hours=flight_hours)
