"""
限制 API 請求頻率的工具
"""
import time
from datetime import datetime
import threading
from typing import Dict, Tuple, Optional
from functools import wraps
from flask import request, jsonify

class RateLimiter:
    """
    API 請求頻率限制器
    """
    def __init__(self, limit: int = 60, window: int = 60):
        """
        初始化速率限制器
        
        Args:
            limit: 在時間窗口內允許的最大請求數
            window: 時間窗口大小（秒）
        """
        self.limit = limit  # 單位時間內允許的最大請求數
        self.window = window  # 時間窗口（秒）
        self.requests: Dict[str, list] = {}  # 記錄每個IP的請求時間
        self.lock = threading.Lock()
    
    def is_rate_limited(self, client_ip: str) -> Tuple[bool, Optional[int]]:
        """
        檢查客戶端IP是否超過請求限制
        
        Args:
            client_ip: 客戶端 IP 地址
            
        Returns:
            (是否被限制, 剩餘秒數)
        """
        with self.lock:
            now = time.time()
            
            # 如果這是首次看到這個IP, 創建一個新的記錄
            if client_ip not in self.requests:
                self.requests[client_ip] = [now]
                return False, None
            
            # 清理舊的請求記錄（超過窗口期的）
            request_times = self.requests[client_ip]
            request_times = [t for t in request_times if now - t <= self.window]
            
            # 更新請求記錄
            self.requests[client_ip] = request_times
            
            # 檢查是否超過限制
            if len(request_times) >= self.limit:
                # 計算最早的請求何時可以過期
                oldest_request = min(request_times)
                time_to_wait = int(oldest_request + self.window - now) + 1
                return True, time_to_wait
            
            # 添加當前請求
            self.requests[client_ip].append(now)
            return False, None
    
    def get_remaining(self, client_ip: str) -> Tuple[int, int]:
        """
        獲取剩餘的請求配額和重置時間
        
        Args:
            client_ip: 客戶端 IP 地址
            
        Returns:
            (剩餘請求數, 重置時間)
        """
        with self.lock:
            now = time.time()
            
            if client_ip not in self.requests:
                return self.limit, 0
            
            # 清理舊的請求記錄
            request_times = self.requests[client_ip]
            request_times = [t for t in request_times if now - t <= self.window]
            self.requests[client_ip] = request_times
            
            # 計算剩餘配額
            remaining = max(0, self.limit - len(request_times))
            
            # 計算重置時間
            if request_times:
                reset_time = int(min(request_times) + self.window - now) + 1
            else:
                reset_time = 0
                
            return remaining, reset_time
    
    def limiter(self, f):
        """
        限制 API 請求頻率的裝飾器
        
        Args:
            f: 要裝飾的函數
            
        Returns:
            裝飾後的函數
        """
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 獲取客戶端IP
            client_ip = request.remote_addr
            
            # 檢查是否超過請求限制
            limited, wait_time = self.is_rate_limited(client_ip)
            
            # 獲取剩餘配額和重置時間
            remaining, reset_time = self.get_remaining(client_ip)
            
            # 在響應頭中添加限流信息
            resp = f(*args, **kwargs)
            
            if hasattr(resp, 'headers'):
                resp.headers['X-RateLimit-Limit'] = str(self.limit)
                resp.headers['X-RateLimit-Remaining'] = str(remaining)
                resp.headers['X-RateLimit-Reset'] = str(reset_time)
            
            # 如果超過限制，返回 429 Too Many Requests
            if limited:
                return jsonify({
                    'error': '請求過於頻繁',
                    'message': f'請在 {wait_time} 秒後再試',
                    'retry_after': wait_time
                }), 429, {
                    'Retry-After': str(wait_time),
                    'X-RateLimit-Limit': str(self.limit),
                    'X-RateLimit-Remaining': '0',
                    'X-RateLimit-Reset': str(reset_time)
                }
            
            return resp
        
        return decorated_function
