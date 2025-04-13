"""
日期時間處理工具 - 提供日期時間解析與格式化功能
"""
from datetime import datetime, timedelta
import logging
from typing import Optional, Union, List

logger = logging.getLogger('date_utils')

def parse_datetime(datetime_str: str) -> Optional[datetime]:
    """
    統一的日期時間解析函數，支持多種格式
    
    Args:
        datetime_str: 日期時間字符串
        
    Returns:
        解析後的datetime對象，解析失敗時返回None
    """
    if not datetime_str:
        logger.warning("提供的日期時間字符串為空")
        return None
    
    # 嘗試標準格式
    formats = [
        '%Y-%m-%dT%H:%M:%S.%f',  # ISO格式帶毫秒
        '%Y-%m-%dT%H:%M:%S',     # ISO格式
        '%Y-%m-%dT%H:%M',        # ISO格式不帶秒
        '%Y-%m-%d %H:%M:%S',     # 標準格式
        '%Y-%m-%d %H:%M',        # 標準格式不帶秒
        '%m/%d/%Y %H:%M',        # FlightStats格式
        '%m/%d/%Y %H:%M:%S'      # FlightStats格式帶秒
    ]
    
    # 嘗試已知格式
    for fmt in formats:
        try:
            return datetime.strptime(datetime_str, fmt)
        except ValueError:
            continue
    
    # 嘗試手動清理和解析
    try:
        # 處理ISO格式的'T'分隔符
        clean_str = datetime_str.replace('T', ' ')
        
        # 處理毫秒
        if '.' in clean_str:
            clean_str = clean_str.split('.')[0]
            
        # 分割日期和時間部分
        parts = clean_str.strip().split(' ')
        if len(parts) >= 2:
            date_part = parts[0]
            time_part = parts[1]
            
            # 處理MM/DD/YYYY格式的日期
            if '/' in date_part:
                month, day, year = date_part.split('/')
                date_part = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            
            # 根據時間部分長度選擇格式
            if len(time_part) <= 5:  # HH:MM
                return datetime.strptime(f"{date_part} {time_part}", "%Y-%m-%d %H:%M")
            else:  # HH:MM:SS
                return datetime.strptime(f"{date_part} {time_part}", "%Y-%m-%d %H:%M:%S")
    except Exception as e:
        logger.warning(f"手動解析日期時間失敗: {str(e)}")
    
    # 如果有dateutil庫，可以嘗試使用它
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
            # 嘗試解析其他格式
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