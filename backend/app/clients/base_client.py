"""
API客戶端基類 - 提供所有API客戶端共用的基礎功能
"""
import logging
import time
import requests
from typing import Dict, Optional, Any, Union

class BaseAPIClient:
    """所有API客戶端的基類，處理通用的請求邏輯、錯誤處理和重試機制"""
    
    def __init__(self):
        """初始化API客戶端基類"""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.max_retries = 3
        self.retry_delay = 5
        self.request_interval = 0.5  # 請求間隔（秒）
        self.last_request_time = 0
        self.session = requests.Session()  # 使用會話提高效率
    
    def make_request(self, url: str, method: str = 'GET', 
                    params: Optional[Dict] = None, 
                    headers: Optional[Dict] = None, 
                    data: Any = None,
                    timeout: int = 10) -> Optional[Dict]:
        """
        發送API請求並處理重試、錯誤等通用邏輯
        
        Args:
            url: 請求URL
            method: HTTP方法，默認GET
            params: URL參數
            headers: HTTP頭
            data: 請求體數據
            timeout: 請求超時時間（秒）
            
        Returns:
            API響應，解析為字典，失敗時返回None
        """
        # 控制請求頻率
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.request_interval:
            sleep_time = self.request_interval - time_since_last_request
            time.sleep(sleep_time)
        
        # 參數準備
        if params is None:
            params = {}
        if headers is None:
            headers = {}
            
        # 重試邏輯
        retry_count = 0
        current_retry_delay = self.retry_delay
        
        while retry_count < self.max_retries:
            try:
                self.logger.debug(f"請求: {params} {url}")
                
                # 檢查參數類型
                if not isinstance(url, str):
                    self.logger.error(f"URL必須是字串類型，而不是 {type(url)}: {url}")
                    return None
                
                if not isinstance(method, str):
                    self.logger.error(f"HTTP方法必須是字串類型，而不是 {type(method)}: {method}")
                    method = 'GET'  # 預設為GET
                
                # 發送請求
                try:
                    method_upper = method.upper()
                    self.logger.debug(f"HTTP方法轉換成功: {method} -> {method_upper}")
                except Exception as e:
                    self.logger.error(f"HTTP方法轉換失敗: {str(e)}")
                    method_upper = 'GET'  # 預設為GET
                
                if method_upper == 'GET':
                    response = self.session.get(
                        url, params=params, headers=headers, timeout=timeout
                    )
                elif method_upper == 'POST':
                    response = self.session.post(
                        url, params=params, headers=headers, data=data, timeout=timeout
                    )
                else:
                    self.logger.error(f"不支持的HTTP方法: {method}")
                    return None
                
                self.last_request_time = time.time()
                
                # 處理常見狀態碼
                if response.status_code == 200:
                    try:
                        return response.json()
                    except ValueError:
                        self.logger.error("無法解析JSON響應")
                        return None
                elif response.status_code == 429:  # 速率限制
                    current_retry_delay = min(current_retry_delay * 2, 60)
                    self.logger.warning(f"API速率限制，等待{current_retry_delay}秒後重試...")
                    time.sleep(current_retry_delay)
                    retry_count += 1
                    continue
                elif response.status_code == 401:  # 認證問題
                    self.logger.warning("認證錯誤，嘗試重新獲取認證...")
                    if self._handle_auth_error():
                        retry_count += 1
                        continue
                    else:
                        return None
                else:
                    self.logger.error(f"API請求失敗: HTTP {response.status_code}")
                    self.logger.error(f"響應內容: {response.text[:200]}...")
                    if retry_count < self.max_retries - 1:
                        retry_count += 1
                        time.sleep(current_retry_delay)
                        continue
                    return None
                    
            except requests.RequestException as e:
                self.logger.error(f"API請求失敗: RequestException - {e}", exc_info=True)
                if retry_count < self.max_retries - 1:
                    self.logger.warning(f"請求異常，{current_retry_delay}秒後進行第 {retry_count + 1} 次重試...")
                    retry_count += 1
                    time.sleep(current_retry_delay)
                    continue
                self.logger.error(f"請求異常且達到最大重試次數 ({self.max_retries})，最終失敗")
                return None
        
        self.logger.error(f"達到最大重試次數({self.max_retries})，請求失敗")
        return None
    
    def _handle_auth_error(self) -> bool:
        """
        處理認證錯誤的方法，由子類實現
        
        Returns:
            bool: 認證問題是否已解決
        """
        self.logger.warning("認證錯誤處理方法未實現")
        return False
    
    def close(self):
        """關閉會話"""
        self.session.close()