"""
緩存管理模塊

提供一個 CacheManager 類來封裝與 Flask-Caching 的互動。
"""
import logging
from typing import Any, Optional

# 從應用初始化文件中導入 cache 對象
# 使用相對導入從 app 目錄下的 __init__.py 導入
try:
    from .. import cache
except ImportError:
    # 如果在不同環境下運行（例如，獨立腳本測試），可能無法相對導入
    # 提供一個備選方案或明確的錯誤
    logging.warning("無法從 .. 導入 cache，CacheManager 可能無法正常工作。")
    cache = None

logger = logging.getLogger(__name__)

class CacheManager:
    """緩存管理器類"""

    @staticmethod
    def get(key: str) -> Optional[Any]:
        """從緩存中獲取數據"""
        if cache is None:
            logger.error("Cache 對象未初始化。")
            return None
        try:
            value = cache.get(key)
            if value is not None:
                logger.debug(f"緩存命中: key='{key}'")
            else:
                logger.debug(f"緩存未命中: key='{key}'")
            return value
        except Exception as e:
            logger.error(f"從緩存獲取 key='{key}' 時出錯: {e}", exc_info=True)
            return None

    @staticmethod
    def set(key: str, value: Any, timeout: Optional[int] = None) -> bool:
        """將數據設置到緩存中"""
        if cache is None:
            logger.error("Cache 對象未初始化。")
            return False
        try:
            # 使用 cache.set，可以指定 timeout
            # 如果 timeout 為 None，則使用默認超時
            success = cache.set(key, value, timeout=timeout)
            if success:
                logger.debug(f"數據已設置到緩存: key='{key}', timeout={timeout or 'default'}")
            else:
                # Flask-Caching 的 set 通常返回 True，除非有底層錯誤
                # 但某些緩存後端可能返回 False
                logger.warning(f"設置緩存 key='{key}' 可能失敗。")
            return success if success is not None else True # 假設 None 也表示成功
        except Exception as e:
            logger.error(f"設置緩存 key='{key}' 時出錯: {e}", exc_info=True)
            return False

    @staticmethod
    def delete(key: str) -> bool:
        """從緩存中刪除數據"""
        if cache is None:
            logger.error("Cache 對象未初始化。")
            return False
        try:
            success = cache.delete(key)
            if success:
                logger.debug(f"已從緩存刪除: key='{key}'")
            else:
                logger.debug(f"嘗試刪除緩存 key='{key}'，但鍵可能不存在。")
            # delete 通常在鍵存在時返回 True，不存在時返回 False
            return success if success is not None else False
        except Exception as e:
            logger.error(f"刪除緩存 key='{key}' 時出錯: {e}", exc_info=True)
            return False

    @staticmethod
    def clear() -> bool:
        """清除整個緩存（請謹慎使用）"""
        if cache is None:
            logger.error("Cache 對象未初始化。")
            return False
        try:
            success = cache.clear()
            if success:
                logger.warning("整個緩存已被清除。")
            else:
                logger.error("清除緩存失敗。")
            return success if success is not None else False
        except Exception as e:
            logger.error(f"清除緩存時出錯: {e}", exc_info=True)
            return False

# 可以在這裡添加更多緩存相關的輔助函數，例如裝飾器等 