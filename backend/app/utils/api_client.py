"""
API客戶端模組 - 提供與外部API通信的工具

注意：此模塊的名稱應使用ApiClient命名風格，與之前的APIClient命名風格可能有差異，
但為了保持一致性，在代碼使用中應統一使用ApiClient
"""
import requests
import logging
import json
from time import sleep
from datetime import datetime
import time
import random
from flask import current_app

logger = logging.getLogger(__name__)

class ApiClient:
    """API客戶端，封裝HTTP請求方法"""
    
    def __init__(self, base_url=None, headers=None, timeout=30, retry_count=5, retry_delay=2):
        """初始化API客戶端
        
        Args:
            base_url (str, optional): 基礎URL，會被附加到每個請求前
            headers (dict, optional): 預設請求頭
            timeout (int, optional): 請求超時時間（秒）
            retry_count (int, optional): 重試次數
            retry_delay (int, optional): 重試延遲（秒）
        """
        self.base_url = base_url
        self.headers = headers or {}
        self.timeout = timeout
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.session = requests.Session()
        # 重試相關配置
        self.max_retries = 5          # 增加最大重試次數
        self.base_delay = 3           # 增加基礎延遲秒數
        self.max_delay = 30           # 增加最大延遲秒數
        self.rate_limit_delay = 20    # 429錯誤後的默認等待時間
    
    def _make_url(self, endpoint):
        """構建完整URL
        
        Args:
            endpoint (str): API端點
            
        Returns:
            str: 完整URL
        """
        if self.base_url:
            # 確保base_url和endpoint之間只有一個斜杠
            if self.base_url.endswith('/') and endpoint.startswith('/'):
                return f"{self.base_url}{endpoint[1:]}"
            elif not self.base_url.endswith('/') and not endpoint.startswith('/'):
                return f"{self.base_url}/{endpoint}"
            else:
                return f"{self.base_url}{endpoint}"
        return endpoint
    
    def _log_request(self, method, url, params=None, data=None, json_data=None):
        """記錄請求信息
        
        Args:
            method (str): HTTP方法
            url (str): 請求URL
            params (dict, optional): 查詢參數
            data (dict, optional): 表單數據
            json_data (dict, optional): JSON數據
        """
        logger.debug(f"API請求: {method} {url}")
        if params:
            logger.debug(f"查詢參數: {params}")
        if data:
            logger.debug(f"表單數據: {data}")
        if json_data:
            logger.debug(f"JSON數據: {json_data}")
    
    def _log_response(self, response):
        """記錄響應信息
        
        Args:
            response (Response): 響應對象
        """
        try:
            logger.debug(f"API響應: {response.status_code} {response.reason}")
            if response.status_code >= 400:
                logger.error(f"API錯誤: {response.status_code} {response.text}")
        except Exception as e:
            logger.error(f"記錄響應信息時發生錯誤: {str(e)}")
    
    def _handle_response(self, response):
        """處理API響應
        
        Args:
            response (Response): 響應對象
            
        Returns:
            tuple: (success, data) 元組
        """
        self._log_response(response)
        
        try:
            # 檢查是否為JSON響應
            content_type = response.headers.get('Content-Type', '')
            if 'application/json' in content_type or response.text.strip().startswith('{') or response.text.strip().startswith('['):
                data = response.json()
            else:
                data = response.text
                
            if response.ok:
                return True, data
            else:
                error_msg = data if isinstance(data, dict) else {'error': response.text, 'status_code': response.status_code}
                return False, error_msg
        except json.JSONDecodeError:
            logger.error(f"JSON解析錯誤: {response.text}")
            return False, {'error': 'JSON解析錯誤', 'raw': response.text, 'status_code': response.status_code}
        except Exception as e:
            logger.error(f"處理響應時發生錯誤: {str(e)}")
            return False, {'error': str(e), 'status_code': response.status_code}
    
    def _send_request(self, method, endpoint, params=None, data=None, json_data=None, headers=None, timeout=None):
        """發送HTTP請求
        
        Args:
            method (str): HTTP方法 ('GET', 'POST', 等)
            endpoint (str): API端點
            params (dict, optional): 查詢參數
            data (dict, optional): 表單數據
            json_data (dict, optional): JSON數據
            headers (dict, optional): 請求頭
            timeout (int, optional): 超時時間（秒）
            
        Returns:
            tuple: (success, data) 元組
        """
        url = self._make_url(endpoint)
        _headers = {**self.headers, **(headers or {})}
        _timeout = timeout or self.timeout
        
        self._log_request(method, url, params, data, json_data)
        
        tries = 0
        while tries <= self.retry_count:
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    params=params,
                    data=data,
                    json=json_data,
                    headers=_headers,
                    timeout=_timeout
                )
                
                # 處理429錯誤（API速率限制）
                if response.status_code == 429:
                    # 優先使用服務器返回的 Retry-After 標頭
                    retry_after = None
                    if 'Retry-After' in response.headers:
                        try:
                            retry_after = int(response.headers.get('Retry-After'))
                            logger.warning(f"API速率限制 (429)，服務器指定等待 {retry_after} 秒")
                        except (ValueError, TypeError):
                            logger.warning(f"無法解析 Retry-After 標頭: {response.headers.get('Retry-After')}")
                    
                    # 如果沒有 Retry-After 或解析失敗，使用指數退避策略
                    if retry_after is None:
                        retry_after = min(self.rate_limit_delay * (1.5 ** tries), 60)
                        logger.warning(f"API速率限制 (429)，使用退避策略等待 {retry_after:.2f} 秒")
                    
                    # 加入一些隨機抖動，避免多個客戶端同時重試
                    jitter = random.uniform(0.5, 2.5)
                    wait_time = retry_after + jitter
                    
                    logger.warning(f"API速率限制 (429)，等待 {wait_time:.2f} 秒後重試... (嘗試 {tries+1}/{self.retry_count+1})")
                    time.sleep(wait_time)
                    tries += 1
                    continue
                
                # 處理其他服務器錯誤 (500, 502, 503, 504)
                if response.status_code >= 500:
                    if tries < self.retry_count:
                        retry_delay = self.retry_delay * (2 ** tries) + random.uniform(0, 1)
                        logger.warning(f"服務器錯誤 ({response.status_code})，等待 {retry_delay:.2f} 秒後重試... (嘗試 {tries+1}/{self.retry_count+1})")
                        time.sleep(retry_delay)
                        tries += 1
                        continue
                
                return self._handle_response(response)
            
            except requests.exceptions.RequestException as e:
                logger.error(f"請求失敗 ({tries+1}/{self.retry_count+1}): {str(e)}")
                
                if tries == self.retry_count:
                    # 最後一次嘗試失敗，返回錯誤
                    return False, {'error': str(e), 'status_code': 'connection_error'}
                
                # 重試前等待，使用指數退避策略
                retry_delay = self.retry_delay * (2 ** tries) + random.uniform(0, 1)
                logger.info(f"API請求重試，等待 {retry_delay:.2f} 秒...")
                time.sleep(retry_delay)
                tries += 1
    
    def get(self, endpoint, params=None, headers=None, timeout=None):
        """發送GET請求
        
        Args:
            endpoint (str): API端點
            params (dict, optional): 查詢參數
            headers (dict, optional): 請求頭
            timeout (int, optional): 超時時間（秒）
            
        Returns:
            tuple: (success, data) 元組
        """
        return self._request_with_retry('GET', endpoint, params=params, headers=headers, timeout=timeout)
    
    def post(self, endpoint, params=None, data=None, json_data=None, headers=None, timeout=None):
        """發送POST請求
        
        Args:
            endpoint (str): API端點
            params (dict, optional): 查詢參數
            data (dict, optional): 表單數據
            json_data (dict, optional): JSON數據
            headers (dict, optional): 請求頭
            timeout (int, optional): 超時時間（秒）
            
        Returns:
            tuple: (success, data) 元組
        """
        return self._request_with_retry('POST', endpoint, params=params, data=data, json_data=json_data, headers=headers, timeout=timeout)
    
    def put(self, endpoint, params=None, data=None, json_data=None, headers=None, timeout=None):
        """發送PUT請求
        
        Args:
            endpoint (str): API端點
            params (dict, optional): 查詢參數
            data (dict, optional): 表單數據
            json_data (dict, optional): JSON數據
            headers (dict, optional): 請求頭
            timeout (int, optional): 超時時間（秒）
            
        Returns:
            tuple: (success, data) 元組
        """
        return self._send_request('PUT', endpoint, params=params, data=data, json_data=json_data, headers=headers, timeout=timeout)
    
    def delete(self, endpoint, params=None, headers=None, timeout=None):
        """發送DELETE請求
        
        Args:
            endpoint (str): API端點
            params (dict, optional): 查詢參數
            headers (dict, optional): 請求頭
            timeout (int, optional): 超時時間（秒）
            
        Returns:
            tuple: (success, data) 元組
        """
        return self._send_request('DELETE', endpoint, params=params, headers=headers, timeout=timeout)
    
    def patch(self, endpoint, params=None, data=None, json_data=None, headers=None, timeout=None):
        """發送PATCH請求
        
        Args:
            endpoint (str): API端點
            params (dict, optional): 查詢參數
            data (dict, optional): 表單數據
            json_data (dict, optional): JSON數據
            headers (dict, optional): 請求頭
            timeout (int, optional): 超時時間（秒）
            
        Returns:
            tuple: (success, data) 元組
        """
        return self._send_request('PATCH', endpoint, params=params, data=data, json_data=json_data, headers=headers, timeout=timeout)

    def _request_with_retry(self, method, url, **kwargs):
        """帶重試機制的請求方法
        
        Args:
            method (str): HTTP方法
            url (str): 請求URL或端點
            **kwargs: 其他請求參數
            
        Returns:
            tuple: (success, data) 元組
        """
        start_time = time.time()
        retries = 0
        last_error = None
        
        # 在第一次請求前添加小延遲，避免瞬間發送大量請求
        time.sleep(random.uniform(0.1, 0.5))
        
        while retries <= self.max_retries:
            try:
                # 添加隨機延遲，避免頻繁請求
                if retries > 0:
                    # 使用指數退避策略計算延遲時間
                    delay = min(self.base_delay * (2 ** (retries - 1)) + random.uniform(0, 2), self.max_delay)
                    logger.info(f"API請求重試 ({retries}/{self.max_retries})，等待 {delay:.2f} 秒...")
                    time.sleep(delay)
                
                logger.debug(f"發送 {method} 請求到 {url} (嘗試 {retries+1}/{self.max_retries+1})")
                
                # 使用原始的 _send_request 方法
                success, result = self._send_request(method, url, **kwargs)
                
                if success:
                    elapsed = time.time() - start_time
                    if retries > 0:
                        logger.info(f"請求成功 (重試 {retries} 次後), 耗時 {elapsed:.2f} 秒")
                    return success, result
                elif isinstance(result, dict) and result.get('status_code') == 429:
                    # 如果是速率限制錯誤，使用特殊處理
                    retries += 1
                    if retries <= self.max_retries:
                        wait_time = self.rate_limit_delay + random.uniform(1, 5)
                        logger.warning(f"API速率限制，等待 {wait_time:.2f} 秒後重試... (嘗試 {retries}/{self.max_retries})")
                        time.sleep(wait_time)
                        continue
                
                # 其他錯誤，記錄並重試
                logger.error(f"API請求失敗: {result}")
                last_error = result
                retries += 1
                if retries <= self.max_retries:
                    continue
                
                # 達到最大重試次數
                elapsed = time.time() - start_time
                logger.error(f"API請求最終失敗，共重試 {retries-1} 次，總耗時 {elapsed:.2f} 秒")
                return False, last_error or {'error': '請求失敗', 'status_code': 'unknown_error'}
            
            except requests.exceptions.RequestException as e:
                logger.error(f"API請求發生網絡異常: {str(e)}")
                last_error = {'error': str(e), 'status_code': 'connection_error'}
                retries += 1
                if retries <= self.max_retries:
                    continue
                
                # 達到最大重試次數
                elapsed = time.time() - start_time
                logger.error(f"API請求網絡錯誤，共重試 {retries-1} 次，總耗時 {elapsed:.2f} 秒")
                return False, last_error
