"""
權杖管理工具 - 處理各種API權杖的獲取與刷新
"""
import requests
import logging
from datetime import datetime, timedelta

# 設置日誌
logger = logging.getLogger(__name__)

class TokenManager:
    """
    權杖管理類 - 處理權杖的獲取、緩存與更新
    """
    
    def __init__(self):
        """
        初始化權杖管理器
        """
        self.tokens = {}  # 用於存儲各種API的令牌
    
    def get_or_refresh_token(self, api_name, **kwargs):
        """
        獲取或更新特定API的令牌
        
        Args:
            api_name (str): API名稱，用於識別不同的API
            **kwargs: API特定參數，如client_id, client_secret等
            
        Returns:
            tuple: (是否成功, 令牌或錯誤訊息)
        """
        # 檢查是否已有有效令牌
        if api_name in self.tokens:
            token_info = self.tokens[api_name]
            if datetime.now().timestamp() < token_info['expiry']:
                return True, token_info['token']
        
        # 根據API類型獲取令牌
        if api_name == 'tdx':
            return self._get_tdx_token(**kwargs)
        elif api_name == 'cirium':
            return self._get_cirium_token(**kwargs)
        else:
            return False, f"不支持的API類型: {api_name}"
    
    def _get_tdx_token(self, client_id, client_secret, auth_url):
        """
        獲取TDX API權杖
        
        Args:
            client_id (str): 客戶端ID
            client_secret (str): 客戶端密鑰
            auth_url (str): 認證URL
            
        Returns:
            tuple: (是否成功, 令牌或錯誤訊息)
        """
        try:
            # 設定請求標頭與資料
            headers = {'content-type': 'application/x-www-form-urlencoded'}
            data = {
                'grant_type': 'client_credentials',
                'client_id': client_id,
                'client_secret': client_secret
            }
            
            # 發送POST請求取得權杖
            response = requests.post(auth_url, headers=headers, data=data)
            response.raise_for_status()
            auth_data = response.json()
            
            # 儲存權杖與到期時間
            token = auth_data.get('access_token')
            expires_in = auth_data.get('expires_in', 86400)  # 默認1天
            expiry = datetime.now().timestamp() + expires_in - 300  # 提前5分鐘更新
            
            # 更新權杖緩存
            self.tokens['tdx'] = {
                'token': token,
                'expiry': expiry
            }
            
            logger.info("TDX API 權杖已更新")
            return True, token
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"TDX API 權杖獲取失敗 (HTTP Error): {e}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"TDX API 權杖獲取失敗: {e}"
            logger.error(error_msg)
            return False, error_msg
    
    def _get_cirium_token(self, app_id, app_key):
        """
        獲取Cirium API權杖
        
        Args:
            app_id (str): 應用ID
            app_key (str): 應用密鑰
            
        Returns:
            tuple: (是否成功, 令牌或錯誤訊息)
        """
        try:
            # Cirium API使用應用ID和密鑰作為令牌
            token = f"{app_id}:{app_key}"
            
            # 設定到期時間（30天，但可依需要調整）
            expiry = datetime.now().timestamp() + (30 * 86400)
            
            # 更新權杖緩存
            self.tokens['cirium'] = {
                'token': token,
                'expiry': expiry
            }
            
            logger.info("Cirium API 認證已更新")
            return True, token
            
        except Exception as e:
            error_msg = f"Cirium API 認證設置失敗: {e}"
            logger.error(error_msg)
            return False, error_msg