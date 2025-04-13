"""
緩存工具模組 - 提供簡單的內存緩存功能，用於減少重複API請求
"""
import time
import logging
import functools
from typing import Any, Dict, Optional, Callable, Tuple

logger = logging.getLogger('cache_utils')

class SimpleCache:
    """簡單的內存緩存實現"""
    
    def __init__(self, default_ttl: int = 3600):
        """
        初始化緩存
        
        Args:
            default_ttl: 默認緩存生存時間（秒）
        """
        self.cache: Dict[str, Tuple[Any, float]] = {}
        self.default_ttl = default_ttl
        logger.debug(f"初始化緩存，默認TTL: {default_ttl}秒")
    
    def get(self, key: str) -> Optional[Any]:
        """
        獲取緩存的值
        
        Args:
            key: 緩存鍵
            
        Returns:
            緩存的值，如果不存在或已過期則返回None
        """
        if key not in self.cache:
            return None
            
        value, expiry_time = self.cache[key]
        current_time = time.time()
        
        if current_time > expiry_time:
            # 緩存已過期
            logger.debug(f"緩存項'{key}'已過期")
            del self.cache[key]
            return None
            
        logger.debug(f"緩存命中: {key}")
        return value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        設置緩存
        
        Args:
            key: 緩存鍵
            value: 要緩存的值
            ttl: 生存時間（秒），如果為None則使用默認值
        """
        if ttl is None:
            ttl = self.default_ttl
            
        expiry_time = time.time() + ttl
        self.cache[key] = (value, expiry_time)
        logger.debug(f"設置緩存: {key}, TTL: {ttl}秒")
    
    def delete(self, key: str) -> bool:
        """
        刪除緩存項
        
        Args:
            key: 緩存鍵
            
        Returns:
            是否成功刪除
        """
        if key in self.cache:
            del self.cache[key]
            logger.debug(f"刪除緩存: {key}")
            return True
        return False
    
    def clear(self) -> None:
        """清空緩存"""
        self.cache.clear()
        logger.debug("清空緩存")
    
    def cleanup(self) -> int:
        """
        清理過期緩存項
        
        Returns:
            清理的項目數
        """
        current_time = time.time()
        expired_keys = [
            key for key, (_, expiry_time) in self.cache.items()
            if current_time > expiry_time
        ]
        
        for key in expired_keys:
            del self.cache[key]
            
        if expired_keys:
            logger.debug(f"清理{len(expired_keys)}個過期緩存項")
            
        return len(expired_keys)


# 創建一個全局緩存實例
global_cache = SimpleCache()


def cached(ttl: Optional[int] = None, key_prefix: str = ""):
    """
    緩存裝飾器，用於緩存函數結果
    
    Args:
        ttl: 緩存時間（秒），如果為None則使用默認值
        key_prefix: 緩存鍵前綴
        
    Returns:
        裝飾器函數
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # 創建緩存鍵
            # 使用函數名稱和參數生成唯一鍵
            key_parts = [key_prefix, func.__name__]
            
            # 添加位置參數
            for arg in args:
                if isinstance(arg, (str, int, float, bool)):
                    key_parts.append(str(arg))
                else:
                    # 對於複雜類型，使用類型和id
                    key_parts.append(f"{type(arg).__name__}_{id(arg)}")
            
            # 添加關鍵字參數（按鍵排序）
            for k in sorted(kwargs.keys()):
                v = kwargs[k]
                if isinstance(v, (str, int, float, bool)):
                    key_parts.append(f"{k}={v}")
                else:
                    key_parts.append(f"{k}={type(v).__name__}_{id(v)}")
            
            cache_key = "_".join(key_parts)
            
            # 檢查緩存
            cached_value = global_cache.get(cache_key)
            if cached_value is not None:
                return cached_value
                
            # 未緩存，調用原函數
            result = func(*args, **kwargs)
            
            # 只緩存非None結果
            if result is not None:
                global_cache.set(cache_key, result, ttl)
                
            return result
        return wrapper
    return decorator


def invalidate_cache(key_prefix: str = "") -> int:
    """
    使特定前綴的緩存失效
    
    Args:
        key_prefix: 緩存鍵前綴
        
    Returns:
        失效的緩存項數量
    """
    if not key_prefix:
        global_cache.clear()
        return len(global_cache.cache)
        
    keys_to_delete = [
        key for key in global_cache.cache.keys()
        if key.startswith(key_prefix)
    ]
    
    for key in keys_to_delete:
        global_cache.delete(key)
        
    logger.debug(f"使{len(keys_to_delete)}個緩存項失效，前綴: {key_prefix}")
    return len(keys_to_delete)