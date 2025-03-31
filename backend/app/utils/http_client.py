"""
HTTP 客戶端工具類，用於處理外部 API 請求
"""
import logging
import requests
from typing import Dict, Any, Optional, Union, List
from requests.exceptions import RequestException, Timeout, ConnectionError
import time
import json

logger = logging.getLogger(__name__)

class HttpClient:
    """
    HTTP 客戶端類，封裝常用的 HTTP 請求操作
    """
    def __init__(self, base_url: str = "", timeout: int = 30, max_retries: int = 3, 
                 retry_delay: int = 1, headers: Optional[Dict[str, str]] = None):
        """
        初始化 HTTP 客戶端
        
        Args:
            base_url: API 基礎 URL
            timeout: 請求超時時間（秒）
            max_retries: 最大重試次數
            retry_delay: 重試間隔（秒）
            headers: 默認請求標頭
        """
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.session = requests.Session()
        
        # 設置默認請求標頭
        default_headers = {
            'User-Agent': 'FlightIntegration/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        if headers:
            default_headers.update(headers)
            
        self.session.headers.update(default_headers)
    
    def _build_url(self, endpoint: str) -> str:
        """
        構建完整的 URL
        
        Args:
            endpoint: API 端點路徑
            
        Returns:
            完整的 URL
        """
        # 處理 base_url 和 endpoint 都有或都沒有 '/' 的情況
        if self.base_url and self.base_url.endswith('/') and endpoint.startswith('/'):
            endpoint = endpoint[1:]
        elif self.base_url and not self.base_url.endswith('/') and not endpoint.startswith('/'):
            endpoint = f"/{endpoint}"
            
        return f"{self.base_url}{endpoint}"
    
    def request(self, method: str, endpoint: str, params: Optional[Dict[str, Any]] = None, 
                data: Optional[Any] = None, headers: Optional[Dict[str, str]] = None, 
                timeout: Optional[int] = None, stream: bool = False) -> requests.Response:
        """
        發送 HTTP 請求
        
        Args:
            method: HTTP 方法（GET, POST, PUT, DELETE 等）
            endpoint: API 端點路徑
            params: URL 查詢參數
            data: 請求體數據
            headers: 請求標頭
            timeout: 請求超時時間（覆蓋默認值）
            stream: 是否使用流式傳輸
            
        Returns:
            API 響應對象
            
        Raises:
            RequestException: 當請求發生錯誤時
        """
        url = self._build_url(endpoint)
        timeout = timeout or self.timeout
        
        # 序列化 JSON 數據
        if isinstance(data, (dict, list)):
            data = json.dumps(data)
            
        kwargs = {
            'params': params,
            'data': data,
            'headers': headers,
            'timeout': timeout,
            'stream': stream
        }
        
        # 過濾掉 None 值
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        
        # 重試邏輯
        for attempt in range(self.max_retries):
            try:
                response = self.session.request(method, url, **kwargs)
                return response
            except (ConnectionError, Timeout) as e:
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)  # 指數退避策略
                    logger.warning(f"請求失敗，將在 {wait_time} 秒後重試: {url}, 錯誤: {str(e)}")
                    time.sleep(wait_time)
                else:
                    logger.error(f"請求失敗，已達到最大重試次數: {url}, 錯誤: {str(e)}")
                    raise
            except RequestException as e:
                logger.error(f"請求發生錯誤: {url}, 錯誤: {str(e)}")
                raise
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, 
            headers: Optional[Dict[str, str]] = None, timeout: Optional[int] = None, 
            stream: bool = False) -> requests.Response:
        """
        發送 GET 請求
        
        Args:
            endpoint: API 端點路徑
            params: URL 查詢參數
            headers: 請求標頭
            timeout: 請求超時時間
            stream: 是否使用流式傳輸
            
        Returns:
            API 響應對象
        """
        return self.request('GET', endpoint, params=params, headers=headers, 
                           timeout=timeout, stream=stream)
    
    def post(self, endpoint: str, data: Optional[Any] = None, 
             params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None, 
             timeout: Optional[int] = None) -> requests.Response:
        """
        發送 POST 請求
        
        Args:
            endpoint: API 端點路徑
            data: 請求體數據
            params: URL 查詢參數
            headers: 請求標頭
            timeout: 請求超時時間
            
        Returns:
            API 響應對象
        """
        return self.request('POST', endpoint, data=data, params=params, 
                           headers=headers, timeout=timeout)
    
    def put(self, endpoint: str, data: Optional[Any] = None, 
            params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None, 
            timeout: Optional[int] = None) -> requests.Response:
        """
        發送 PUT 請求
        
        Args:
            endpoint: API 端點路徑
            data: 請求體數據
            params: URL 查詢參數
            headers: 請求標頭
            timeout: 請求超時時間
            
        Returns:
            API 響應對象
        """
        return self.request('PUT', endpoint, data=data, params=params, 
                           headers=headers, timeout=timeout)
    
    def delete(self, endpoint: str, params: Optional[Dict[str, Any]] = None, 
               headers: Optional[Dict[str, str]] = None, 
               timeout: Optional[int] = None) -> requests.Response:
        """
        發送 DELETE 請求
        
        Args:
            endpoint: API 端點路徑
            params: URL 查詢參數
            headers: 請求標頭
            timeout: 請求超時時間
            
        Returns:
            API 響應對象
        """
        return self.request('DELETE', endpoint, params=params, headers=headers, 
                           timeout=timeout)
    
    def get_json(self, endpoint: str, params: Optional[Dict[str, Any]] = None, 
                headers: Optional[Dict[str, str]] = None, 
                timeout: Optional[int] = None) -> Any:
        """
        發送 GET 請求並解析 JSON 響應
        
        Args:
            endpoint: API 端點路徑
            params: URL 查詢參數
            headers: 請求標頭
            timeout: 請求超時時間
            
        Returns:
            解析後的 JSON 數據
        """
        response = self.get(endpoint, params=params, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.json()
    
    def post_json(self, endpoint: str, data: Optional[Any] = None, 
                 params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None, 
                 timeout: Optional[int] = None) -> Any:
        """
        發送 POST 請求並解析 JSON 響應
        
        Args:
            endpoint: API 端點路徑
            data: 請求體數據
            params: URL 查詢參數
            headers: 請求標頭
            timeout: 請求超時時間
            
        Returns:
            解析後的 JSON 數據
        """
        response = self.post(endpoint, data=data, params=params, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.json()
    
    def close(self) -> None:
        """
        關閉 HTTP 客戶端會話
        """
        self.session.close()
