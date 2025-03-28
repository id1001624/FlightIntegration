"""
通用API客戶端模組 - 提供統一的API調用介面
"""
import requests
import logging
from datetime import datetime
from flask import current_app

# 設置日誌
logger = logging.getLogger(__name__)

class APIClient:
    """
    通用API客戶端類 - 處理API請求的發送和錯誤處理
    """
    
    def __init__(self, base_url=None, default_headers=None, default_timeout=30):
        """
        初始化API客戶端
        
        Args:
            base_url (str, optional): API基礎URL
            default_headers (dict, optional): 默認請求頭
            default_timeout (int, optional): 默認請求超時時間（秒）
        """
        self.base_url = base_url
        self.default_headers = default_headers or {}
        self.default_timeout = default_timeout
    
    def get(self, endpoint, params=None, headers=None, timeout=None):
        """
        發送GET請求
        
        Args:
            endpoint (str): API終端點
            params (dict, optional): 查詢參數
            headers (dict, optional): 請求頭
            timeout (int, optional): 請求超時時間（秒）
            
        Returns:
            tuple: (是否成功, 回應數據或錯誤訊息)
        """
        return self._request('GET', endpoint, params=params, headers=headers, timeout=timeout)
    
    def post(self, endpoint, data=None, json=None, params=None, headers=None, timeout=None):
        """
        發送POST請求
        
        Args:
            endpoint (str): API終端點
            data (dict/str, optional): 表單數據
            json (dict, optional): JSON數據
            params (dict, optional): 查詢參數
            headers (dict, optional): 請求頭
            timeout (int, optional): 請求超時時間（秒）
            
        Returns:
            tuple: (是否成功, 回應數據或錯誤訊息)
        """
        return self._request('POST', endpoint, data=data, json=json, 
                            params=params, headers=headers, timeout=timeout)
    
    def put(self, endpoint, data=None, json=None, params=None, headers=None, timeout=None):
        """
        發送PUT請求
        
        Args:
            endpoint (str): API終端點
            data (dict/str, optional): 表單數據
            json (dict, optional): JSON數據
            params (dict, optional): 查詢參數
            headers (dict, optional): 請求頭
            timeout (int, optional): 請求超時時間（秒）
            
        Returns:
            tuple: (是否成功, 回應數據或錯誤訊息)
        """
        return self._request('PUT', endpoint, data=data, json=json, 
                            params=params, headers=headers, timeout=timeout)
    
    def delete(self, endpoint, params=None, headers=None, timeout=None):
        """
        發送DELETE請求
        
        Args:
            endpoint (str): API終端點
            params (dict, optional): 查詢參數
            headers (dict, optional): 請求頭
            timeout (int, optional): 請求超時時間（秒）
            
        Returns:
            tuple: (是否成功, 回應數據或錯誤訊息)
        """
        return self._request('DELETE', endpoint, params=params, headers=headers, timeout=timeout)
    
    def _request(self, method, endpoint, **kwargs):
        """
        發送HTTP請求的內部方法
        
        Args:
            method (str): HTTP方法 (GET, POST, PUT, DELETE等)
            endpoint (str): API終端點
            **kwargs: 其他請求參數
            
        Returns:
            tuple: (是否成功, 回應數據或錯誤訊息)
        """
        url = self._build_url(endpoint)
        headers = {**self.default_headers, **(kwargs.pop('headers', {}) or {})}
        timeout = kwargs.pop('timeout', None) or self.default_timeout
        
        try:
            logger.debug(f"發送 {method} 請求至 {url}")
            response = requests.request(method, url, headers=headers, timeout=timeout, **kwargs)
            
            # 記錄回應狀態
            logger.debug(f"收到回應: 狀態碼 {response.status_code}")
            
            # 嘗試強制回應為 JSON 格式
            try:
                data = response.json()
            except ValueError:
                data = {'text': response.text}
            
            # 檢查回應狀態碼
            if response.ok:  # 狀態碼 2xx
                return True, data
            else:
                error_msg = f"API錯誤: {response.status_code} - {response.reason}"
                logger.error(error_msg)
                return False, {'error': error_msg, 'details': data}
                
        except requests.exceptions.Timeout:
            error_msg = f"請求超時: {url}"
            logger.error(error_msg)
            return False, {'error': error_msg}
            
        except requests.exceptions.ConnectionError:
            error_msg = f"連接錯誤: {url}"
            logger.error(error_msg)
            return False, {'error': error_msg}
            
        except Exception as e:
            error_msg = f"請求發生未知錯誤: {str(e)}"
            logger.error(error_msg)
            return False, {'error': error_msg}
    
    def _build_url(self, endpoint):
        """
        構建完整的URL
        
        Args:
            endpoint (str): API終端點
            
        Returns:
            str: 完整URL
        """
        if self.base_url and not endpoint.startswith(('http://', 'https://')):
            # 確保base_url和endpoint之間有一個且只有一個斜槓
            if self.base_url.endswith('/') and endpoint.startswith('/'):
                endpoint = endpoint[1:]
            elif not self.base_url.endswith('/') and not endpoint.startswith('/'):
                endpoint = f"/{endpoint}"
            return f"{self.base_url}{endpoint}"
        return endpoint
