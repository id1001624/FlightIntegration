"""
HTTP 客戶端工具類，用於處理外部 API 請求
集成了原有的 ApiClient 和 HttpClient 功能，提供統一的 API 請求介面
"""
import logging
import requests
import time
import json
from typing import Dict, Any, Optional, Union, List, Tuple
from requests.exceptions import RequestException, Timeout, ConnectionError, HTTPError
from http import HTTPStatus

logger = logging.getLogger(__name__)

class ApiClient:
    """
    API 客戶端類，封裝 HTTP 請求操作並提供進階功能
    包括請求/響應日誌、重試機制、錯誤處理和 JSON 解析
    """
    def __init__(
        self, 
        base_url: str = "", 
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 30, 
        retry_count: int = 3, 
        retry_delay: int = 1,
        verify_ssl: bool = True,
        logger_name: Optional[str] = None
    ):
        """
        初始化 API 客戶端
        
        Args:
            base_url: API 基礎 URL
            headers: 默認請求標頭
            timeout: 請求超時時間（秒）
            retry_count: 請求失敗時的最大重試次數
            retry_delay: 重試間隔基準時間（秒）
            verify_ssl: 是否驗證 SSL 證書
            logger_name: 日誌記錄器名稱，如果為 None，則使用默認日誌記錄器
        """
        self.base_url = base_url
        self.timeout = timeout
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.verify_ssl = verify_ssl
        
        # 設置日誌記錄器
        self.logger = logging.getLogger(logger_name if logger_name else __name__)
        
        # 初始化會話
        self.session = requests.Session()
        self.session.verify = verify_ssl
        
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
        # 避免重複或缺少斜杠
        if self.base_url and self.base_url.endswith('/') and endpoint.startswith('/'):
            endpoint = endpoint[1:]
        elif self.base_url and not self.base_url.endswith('/') and not endpoint.startswith('/'):
            endpoint = f"/{endpoint}"
            
                return f"{self.base_url}{endpoint}"
    
    def _log_request(self, method: str, url: str, params: Optional[Dict[str, Any]] = None,
                     data: Optional[Any] = None, headers: Optional[Dict[str, str]] = None) -> None:
        """
        記錄請求詳情
        
        Args:
            method: HTTP 方法
            url: 請求 URL
            params: URL 查詢參數
            data: 請求體數據
            headers: 請求標頭
        """
        # 移除敏感信息
        safe_headers = {}
        if headers:
            safe_headers = headers.copy()
            for key in ['Authorization', 'X-API-Key', 'api_key', 'apikey']:
                if key in safe_headers:
                    safe_headers[key] = '*** REDACTED ***'
        
        # 記錄請求詳情
        log_message = f"API 請求: {method} {url}"
        if params:
            log_message += f"\n參數: {params}"
        if data:
            # 截斷過長的數據
            data_str = str(data)
            if len(data_str) > 1000:
                data_str = data_str[:1000] + "... [截斷]"
            log_message += f"\n數據: {data_str}"
        if safe_headers:
            log_message += f"\n標頭: {safe_headers}"
            
        self.logger.debug(log_message)
    
    def _log_response(self, response: requests.Response, elapsed_time: float) -> None:
        """
        記錄響應詳情
        
        Args:
            response: 響應對象
            elapsed_time: 請求耗時（秒）
        """
        # 格式化響應內容
        log_message = (
            f"API 響應: {response.status_code} {response.reason} "
            f"({elapsed_time:.2f}s) - {response.url}"
        )
        
        # 添加響應標頭
        log_message += f"\n標頭: {dict(response.headers)}"
        
        # 添加響應內容（如果是 JSON 或文本）
        try:
            if 'application/json' in response.headers.get('Content-Type', ''):
                content = response.json()
                # 截斷過長的響應
                content_str = str(content)
                if len(content_str) > 1000:
                    content_str = content_str[:1000] + "... [截斷]"
                log_message += f"\n內容: {content_str}"
            elif response.headers.get('Content-Type', '').startswith('text/'):
                text = response.text
                if len(text) > 1000:
                    text = text[:1000] + "... [截斷]"
                log_message += f"\n內容: {text}"
        except Exception as e:
            log_message += f"\n無法解析響應內容: {str(e)}"
        
        # 根據狀態碼選擇日誌級別
        if response.status_code >= 500:
            self.logger.error(log_message)
        elif response.status_code >= 400:
            self.logger.warning(log_message)
        else:
            self.logger.debug(log_message)
    
    def _calculate_retry_delay(self, attempt: int, response: Optional[requests.Response] = None) -> float:
        """
        計算重試延遲時間
        
        Args:
            attempt: 當前嘗試次數（從 0 開始）
            response: 上一次響應對象（如果有）
            
        Returns:
            重試延遲時間（秒）
        """
        # 基本延遲時間（指數退避）
        delay = self.retry_delay * (2 ** attempt)
        
        # 如果有 Retry-After 標頭，優先使用
        if response and 'Retry-After' in response.headers:
            retry_after = response.headers['Retry-After']
            try:
                # 嘗試將值轉換為整數（秒數）
                delay = int(retry_after)
            except ValueError:
                # 如果不是整數，可能是 HTTP 日期格式
                self.logger.warning(f"無法解析 Retry-After 標頭值: {retry_after}")
        
        # 添加小量隨機抖動（+/-10%）以避免同步請求
        jitter = delay * 0.1 * (time.time() % 1)
        delay = delay + jitter if attempt % 2 == 0 else delay - jitter
        
        # 確保不低於最小值
        return max(delay, 0.1)
    
    def _should_retry(self, response: Optional[requests.Response] = None, 
                      exception: Optional[Exception] = None) -> bool:
        """
        判斷是否應該重試請求
        
        Args:
            response: HTTP 響應對象（如果有）
            exception: 異常對象（如果有）
            
        Returns:
            是否應該重試
        """
        # 網絡錯誤通常可以重試
        if isinstance(exception, (ConnectionError, Timeout)):
            return True
        
        # 其他類型的異常通常不重試
        if exception and not isinstance(exception, HTTPError):
            return False
        
        # 檢查狀態碼（如果有響應）
        if response:
            # 常見的可重試狀態碼
            retryable_codes = [
                HTTPStatus.TOO_MANY_REQUESTS,  # 429
                HTTPStatus.INTERNAL_SERVER_ERROR,  # 500
                HTTPStatus.BAD_GATEWAY,  # 502
                HTTPStatus.SERVICE_UNAVAILABLE,  # 503
                HTTPStatus.GATEWAY_TIMEOUT  # 504
            ]
            return response.status_code in retryable_codes
        
        return False
    
    def request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None, 
        data: Optional[Any] = None, 
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None, 
        timeout: Optional[int] = None, 
        stream: bool = False
    ) -> Tuple[requests.Response, bool]:
        """
        發送 HTTP 請求並處理重試、錯誤和日誌
        
        Args:
            method: HTTP 方法（GET, POST, PUT, DELETE 等）
            endpoint: API 端點路徑
            params: URL 查詢參數
            data: 請求體數據（字符串或字節）
            json_data: JSON 請求體數據（會自動序列化）
            headers: 附加請求標頭
            timeout: 請求超時時間（覆蓋默認值）
            stream: 是否使用流式傳輸
            
        Returns:
            元組 (響應對象, 是否成功)
            
        Raises:
            RequestException: 請求失敗且無法重試時
        """
        url = self._build_url(endpoint)
        current_timeout = timeout or self.timeout
        
        # 自動序列化普通字典數據
        if isinstance(data, dict) and not json_data:
            json_data = data
            data = None
            
        kwargs = {
            'params': params,
            'data': data,
            'json': json_data,
            'headers': headers,
            'timeout': current_timeout,
            'stream': stream
        }
        
        # 過濾掉 None 值
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        
        # 記錄請求信息
        self._log_request(method, url, params, json_data or data, headers)
        
        # 重試邏輯
        last_exception = None
        last_response = None
        retried = False
        
        for attempt in range(self.retry_count + 1):  # +1 因為第一次不算重試
            start_time = time.time()
            
            try:
                response = self.session.request(method, url, **kwargs)
                elapsed_time = time.time() - start_time
                
                # 記錄響應
                self._log_response(response, elapsed_time)
                    
                # 檢查是否需要重試
                if attempt < self.retry_count and self._should_retry(response=response):
                    retried = True
                    last_response = response
                    wait_time = self._calculate_retry_delay(attempt, response)
                    self.logger.warning(
                        f"收到狀態碼 {response.status_code}，將在 {wait_time:.2f} 秒後重試 "
                        f"(嘗試 {attempt+1}/{self.retry_count}): {url}"
                    )
                    time.sleep(wait_time)
                    continue
                
                # 成功獲取響應
                return response, retried
                
            except (ConnectionError, Timeout, HTTPError) as e:
                elapsed_time = time.time() - start_time
                last_exception = e
                
                # 檢查是否可以重試
                if attempt < self.retry_count and self._should_retry(exception=e):
                    retried = True
                    wait_time = self._calculate_retry_delay(attempt)
                    self.logger.warning(
                        f"請求失敗 ({type(e).__name__}: {str(e)})，將在 {wait_time:.2f} 秒後重試 "
                        f"(嘗試 {attempt+1}/{self.retry_count}): {url}"
                    )
                    time.sleep(wait_time)
                    continue
                else:
                    self.logger.error(
                        f"請求失敗且無法重試 ({type(e).__name__}): {url}, 錯誤: {str(e)}, "
                        f"耗時: {elapsed_time:.2f}s"
                    )
                    raise
            except Exception as e:
                elapsed_time = time.time() - start_time
                self.logger.error(
                    f"請求過程中發生意外錯誤 ({type(e).__name__}): {url}, 錯誤: {str(e)}, "
                    f"耗時: {elapsed_time:.2f}s"
                )
                raise
        
        # 如果所有重試都失敗
        if last_exception:
            raise last_exception
        
        # 如果到這裡還有響應，返回最後一個響應
        return last_response, retried
    
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
        response, _ = self.request('GET', endpoint, params=params, headers=headers, 
                                 timeout=timeout, stream=stream)
        return response
    
    def post(self, endpoint: str, data: Optional[Any] = None, 
             json_data: Optional[Dict[str, Any]] = None,
             params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None, 
             timeout: Optional[int] = None) -> requests.Response:
        """
        發送 POST 請求
        
        Args:
            endpoint: API 端點路徑
            data: 請求體數據
            json_data: JSON 請求體數據（會自動序列化）
            params: URL 查詢參數
            headers: 請求標頭
            timeout: 請求超時時間
            
        Returns:
            API 響應對象
        """
        response, _ = self.request('POST', endpoint, data=data, json_data=json_data, 
                                 params=params, headers=headers, timeout=timeout)
        return response
    
    def put(self, endpoint: str, data: Optional[Any] = None, 
            json_data: Optional[Dict[str, Any]] = None,
            params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None, 
            timeout: Optional[int] = None) -> requests.Response:
        """
        發送 PUT 請求
        
        Args:
            endpoint: API 端點路徑
            data: 請求體數據
            json_data: JSON 請求體數據（會自動序列化）
            params: URL 查詢參數
            headers: 請求標頭
            timeout: 請求超時時間
            
        Returns:
            API 響應對象
        """
        response, _ = self.request('PUT', endpoint, data=data, json_data=json_data,
                                 params=params, headers=headers, timeout=timeout)
        return response
    
    def delete(self, endpoint: str, 
               data: Optional[Any] = None,
               json_data: Optional[Dict[str, Any]] = None,
               params: Optional[Dict[str, Any]] = None, 
               headers: Optional[Dict[str, str]] = None, 
               timeout: Optional[int] = None) -> requests.Response:
        """
        發送 DELETE 請求
        
        Args:
            endpoint: API 端點路徑
            data: 請求體數據
            json_data: JSON 請求體數據（會自動序列化）
            params: URL 查詢參數
            headers: 請求標頭
            timeout: 請求超時時間
            
        Returns:
            API 響應對象
        """
        response, _ = self.request('DELETE', endpoint, data=data, json_data=json_data,
                                 params=params, headers=headers, timeout=timeout)
        return response
    
    def patch(self, endpoint: str, data: Optional[Any] = None, 
              json_data: Optional[Dict[str, Any]] = None,
              params: Optional[Dict[str, Any]] = None, 
              headers: Optional[Dict[str, str]] = None, 
              timeout: Optional[int] = None) -> requests.Response:
        """
        發送 PATCH 請求
        
        Args:
            endpoint: API 端點路徑
            data: 請求體數據
            json_data: JSON 請求體數據（會自動序列化）
            params: URL 查詢參數
            headers: 請求標頭
            timeout: 請求超時時間
            
        Returns:
            API 響應對象
        """
        response, _ = self.request('PATCH', endpoint, data=data, json_data=json_data,
                                 params=params, headers=headers, timeout=timeout)
        return response

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
            
        Raises:
            HTTPError: 當響應狀態碼不是 2xx 時
            ValueError: 當響應不是有效的 JSON 時
        """
        response = self.get(endpoint, params=params, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.json()
    
    def post_json(self, endpoint: str, data: Optional[Any] = None, 
                 json_data: Optional[Dict[str, Any]] = None,
                 params: Optional[Dict[str, Any]] = None,
                 headers: Optional[Dict[str, str]] = None, 
                 timeout: Optional[int] = None) -> Any:
        """
        發送 POST 請求並解析 JSON 響應
        
        Args:
            endpoint: API 端點路徑
            data: 請求體數據
            json_data: JSON 請求體數據（會自動序列化）
            params: URL 查詢參數
            headers: 請求標頭
            timeout: 請求超時時間
            
        Returns:
            解析後的 JSON 數據
            
        Raises:
            HTTPError: 當響應狀態碼不是 2xx 時
            ValueError: 當響應不是有效的 JSON 時
        """
        response = self.post(endpoint, data=data, json_data=json_data, 
                           params=params, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.json()
    
    def put_json(self, endpoint: str, data: Optional[Any] = None, 
                json_data: Optional[Dict[str, Any]] = None,
                params: Optional[Dict[str, Any]] = None,
                headers: Optional[Dict[str, str]] = None, 
                timeout: Optional[int] = None) -> Any:
        """
        發送 PUT 請求並解析 JSON 響應
        
        Args:
            endpoint: API 端點路徑
            data: 請求體數據
            json_data: JSON 請求體數據（會自動序列化）
            params: URL 查詢參數
            headers: 請求標頭
            timeout: 請求超時時間
            
        Returns:
            解析後的 JSON 數據
            
        Raises:
            HTTPError: 當響應狀態碼不是 2xx 時
            ValueError: 當響應不是有效的 JSON 時
        """
        response = self.put(endpoint, data=data, json_data=json_data,
                          params=params, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.json()
    
    def close(self) -> None:
        """
        關閉 HTTP 客戶端會話
        """
        self.session.close()
    
    def __enter__(self):
        """
        支持 with 語句的上下文管理
        """
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        退出上下文時自動關閉會話
        """
        self.close()


# 為了向後兼容性，保留 HttpClient 類作為 ApiClient 的別名
HttpClient = ApiClient
