"""
認證服務模組 - 提供統一的認證邏輯
"""
import jwt
import logging
from datetime import datetime, timedelta
from flask import current_app
from ..utils.token_manager import TokenManager

# 設置日誌
logger = logging.getLogger(__name__)

class AuthService:
    """
    認證服務類 - 處理各種認證邏輯
    """
    
    def __init__(self, test_mode=False):
        """
        初始化認證服務
        
        Args:
            test_mode (bool): 是否為測試模式
        """
        self.test_mode = test_mode
        self.token_manager = TokenManager()
    
    def generate_token(self, user_id):
        """
        生成用戶JWT令牌
        
        Args:
            user_id (str or UUID): 用戶ID
            
        Returns:
            dict: 包含令牌和過期時間的字典
        """
        try:
            # 設定過期時間（24小時）
            expiration = datetime.utcnow() + timedelta(hours=24)
            
            # 建立令牌載荷
            payload = {
                'exp': expiration,
                'iat': datetime.utcnow(),
                'user_id': str(user_id)
            }
            
            # 簽發令牌
            token = jwt.encode(
                payload,
                current_app.config.get('SECRET_KEY'),
                algorithm='HS256'
            )
            
            return {
                'success': True,
                'token': token,
                'expiration': expiration.timestamp()
            }
            
        except Exception as e:
            logger.error(f"生成令牌時發生錯誤: {e}")
            return {
                'success': False,
                'message': f'生成令牌時發生錯誤: {str(e)}'
            }
    
    def verify_token(self, token):
        """
        驗證JWT令牌
        
        Args:
            token (str): JWT令牌
            
        Returns:
            tuple: (是否成功, 用戶ID或錯誤訊息)
        """
        try:
            # 解碼令牌
            payload = jwt.decode(
                token, 
                current_app.config.get('SECRET_KEY'),
                algorithms=['HS256']
            )
            
            # 檢查令牌是否過期
            if datetime.fromtimestamp(payload['exp']) < datetime.utcnow():
                return False, "令牌已過期"
                
            return True, payload['user_id']
            
        except jwt.ExpiredSignatureError:
            return False, "令牌已過期"
        except jwt.InvalidTokenError:
            return False, "無效的令牌"
        except Exception as e:
            logger.error(f"驗證令牌時發生錯誤: {e}")
            return False, f"驗證令牌時發生錯誤: {str(e)}"
    
    def get_tdx_token(self):
        """
        取得TDX API的存取令牌
        
        Returns:
            tuple: (是否成功, 令牌或錯誤訊息)
        """
        try:
            # TDX API的客戶端ID和密鑰
            client_id = current_app.config.get('TDX_CLIENT_ID')
            client_secret = current_app.config.get('TDX_CLIENT_SECRET')
            
            if not client_id or not client_secret:
                raise ValueError("TDX API認證資訊未設置")
            
            # 取得或更新TDX令牌
            return self.token_manager.get_or_refresh_token(
                'tdx',
                client_id=client_id,
                client_secret=client_secret,
                auth_url="https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
            )
            
        except Exception as e:
            logger.error(f"獲取TDX令牌時發生錯誤: {e}")
            return False, f"獲取TDX令牌時發生錯誤: {str(e)}"