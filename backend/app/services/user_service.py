"""
用戶服務模組 - 處理用戶相關的服務邏輯
"""
import logging
import jwt
import uuid
from datetime import datetime, timedelta
from flask import current_app
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash
from ..models.base import db
from ..models.user import User
from ..models.user_search_history import UserSearchHistory
from ..models.user_query import UserQuery

# 設置日誌
logger = logging.getLogger(__name__)

class UserService:
    """
    用戶服務類 - 提供用戶相關功能的業務邏輯
    """
    
    def __init__(self, test_mode=False):
        """
        初始化用戶服務
        
        Args:
            test_mode (bool): 是否為測試模式
        """
        self.test_mode = test_mode
        
    def register(self, email, password, full_name=None, phone=None, 
                 passport_number=None, nationality=None, date_of_birth=None):
        """
        註冊新用戶
        
        Args:
            email (str): 用戶電子郵件
            password (str): 用戶密碼
            full_name (str, optional): 用戶全名
            phone (str, optional): 聯絡電話
            passport_number (str, optional): 護照號碼
            nationality (str, optional): 國籍
            date_of_birth (date, optional): 生日
            
        Returns:
            tuple: (是否成功, 用戶對象或錯誤訊息)
        """
        try:
            # 檢查email是否已存在
            if User.get_by_email(email):
                return False, "電子郵件已被註冊"
            
            # 創建新用戶
            user = User(
                email=email,
                full_name=full_name,
                phone=phone,
                passport_number=passport_number,
                nationality=nationality,
                date_of_birth=date_of_birth
            )
            user.password = password  # 這會調用密碼的setter方法進行加密
            
            # 保存到資料庫
            db.session.add(user)
            db.session.commit()
            
            logger.info(f"成功註冊用戶: {email}")
            return True, user
            
        except SQLAlchemyError as e:
            db.session.rollback()
            error_msg = f"註冊用戶時發生資料庫錯誤: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"註冊用戶時發生錯誤: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
            
    def register_with_line(self, line_user_id, user_info=None):
        """
        使用LINE ID註冊新用戶
        
        Args:
            line_user_id (str): LINE用戶ID
            user_info (dict, optional): 用戶附加信息
            
        Returns:
            tuple: (是否成功, 用戶對象或錯誤訊息)
        """
        try:
            # 檢查LINE ID是否已存在
            if User.get_by_line_id(line_user_id):
                return False, "LINE帳號已被註冊"
                
            # 創建新用戶
            user = User(line_user_id=line_user_id)
            
            # 如果有提供其他信息，則更新用戶信息
            if user_info:
                if 'email' in user_info:
                    user.email = user_info['email']
                if 'full_name' in user_info:
                    user.full_name = user_info['full_name']
                if 'picture_url' in user_info:
                    user.preferences = {'profile_picture': user_info['picture_url']}
            
            # 保存到資料庫
            db.session.add(user)
            db.session.commit()
            
            logger.info(f"成功註冊LINE用戶: {line_user_id}")
            return True, user
            
        except SQLAlchemyError as e:
            db.session.rollback()
            error_msg = f"註冊LINE用戶時發生資料庫錯誤: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"註冊LINE用戶時發生錯誤: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def login(self, email, password):
        """
        用戶登入
        
        Args:
            email (str): 電子郵件
            password (str): 密碼
            
        Returns:
            tuple: (是否成功, 令牌/用戶或錯誤訊息)
        """
        try:
            # 獲取用戶
            user = User.get_by_email(email)
            if not user:
                return False, "用戶不存在"
                
            # 驗證密碼
            if not user.verify_password(password):
                return False, "密碼錯誤"
                
            # 更新登入時間
            user.update_login_time()
            
            # 生成令牌
            token = self._generate_token(user.user_id)
            
            logger.info(f"用戶成功登入: {email}")
            return True, {"token": token, "user": user}
            
        except Exception as e:
            error_msg = f"用戶登入時發生錯誤: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def login_with_line(self, line_user_id, user_info=None):
        """
        使用LINE ID登入
        
        Args:
            line_user_id (str): LINE用戶ID
            user_info (dict, optional): 用戶附加信息
            
        Returns:
            tuple: (是否成功, 令牌/用戶或錯誤訊息, 是否為新用戶)
        """
        try:
            # 獲取用戶
            user = User.get_by_line_id(line_user_id)
            is_new_user = False
            
            # 如果用戶不存在，則自動註冊
            if not user:
                success, result = self.register_with_line(line_user_id, user_info)
                if not success:
                    return success, result, False
                user = result
                is_new_user = True
            
            # 更新登入時間
            user.update_login_time()
            
            # 生成令牌
            token = self._generate_token(user.user_id)
            
            logger.info(f"LINE用戶成功登入: {line_user_id}")
            return True, {"token": token, "user": user}, is_new_user
            
        except Exception as e:
            error_msg = f"LINE用戶登入時發生錯誤: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, False
    
    def verify_token(self, token):
        """
        驗證令牌
        
        Args:
            token (str): 用戶令牌
            
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
            
        except jwt.InvalidTokenError:
            return False, "無效的令牌"
        except Exception as e:
            error_msg = f"驗證令牌時發生錯誤: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def get_user_by_id(self, user_id):
        """
        根據ID獲取用戶
        
        Args:
            user_id (int): 用戶ID
            
        Returns:
            User: 用戶對象，若不存在則返回None
        """
        try:
            return User.query.get(user_id)
        except Exception as e:
            logger.error(f"獲取用戶時發生錯誤: {str(e)}")
            return None
    
    def logout(self, user_id):
        """
        用戶登出
        
        Args:
            user_id (str or UUID): 用戶ID
            
        Returns:
            bool: 是否成功登出
        """
        # 實際邏輯由前端處理令牌的刪除
        # 這裡只記錄日誌
        logger.info(f"用戶登出: {user_id}")
        return True
    
    def update_profile(self, user_id, **kwargs):
        """
        更新用戶資料
        
        Args:
            user_id (str or UUID): 用戶ID
            **kwargs: 要更新的欄位，可以包括email, full_name, phone, 
                     passport_number, nationality, date_of_birth, password
            
        Returns:
            tuple: (是否成功, 用戶對象或錯誤訊息)
        """
        try:
            # 獲取用戶
            user = self.get_user_by_id(user_id)
            if not user:
                return False, "用戶不存在"
            
            # 如果更新郵箱，檢查是否已存在
            if 'email' in kwargs and kwargs['email'] != user.email:
                existing_user = User.get_by_email(kwargs['email'])
                if existing_user:
                    return False, "電子郵件已被使用"
                user.email = kwargs['email']
            
            # 更新其他字段
            if 'full_name' in kwargs:
                user.full_name = kwargs['full_name']
            if 'phone' in kwargs:
                user.phone = kwargs['phone']
            if 'passport_number' in kwargs:
                user.passport_number = kwargs['passport_number']
            if 'nationality' in kwargs:
                user.nationality = kwargs['nationality']
            if 'date_of_birth' in kwargs and kwargs['date_of_birth']:
                user.date_of_birth = kwargs['date_of_birth']
            
            # 特殊處理密碼
            if 'password' in kwargs and kwargs['password']:
                user.password = kwargs['password']
            
            # 更新偏好設置
            if 'preferences' in kwargs and isinstance(kwargs['preferences'], dict):
                user.preferences.update(kwargs['preferences'])
            
            db.session.commit()
            logger.info(f"更新用戶資料: {user_id}")
            return True, user
            
        except SQLAlchemyError as e:
            db.session.rollback()
            error_msg = f"更新用戶資料時發生資料庫錯誤: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"更新用戶資料時發生錯誤: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def change_password(self, user_id, old_password, new_password):
        """
        更改用戶密碼
        
        Args:
            user_id (str or UUID): 用戶ID
            old_password (str): 舊密碼
            new_password (str): 新密碼
            
        Returns:
            tuple: (是否成功, 成功訊息或錯誤訊息)
        """
        try:
            # 獲取用戶
            user = self.get_user_by_id(user_id)
            if not user:
                return False, "用戶不存在"
            
            # 驗證舊密碼
            if not user.verify_password(old_password):
                return False, "舊密碼不正確"
            
            # 更新密碼
            user.password = new_password
            db.session.commit()
            
            logger.info(f"用戶成功更改密碼: {user_id}")
            return True, "密碼已成功更改"
            
        except Exception as e:
            db.session.rollback()
            error_msg = f"更改密碼時發生錯誤: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def save_search_history(self, user_id, departure_airport_id, arrival_airport_id, 
                          departure_date, return_date=None, adults=1, children=0, 
                          infants=0, class_type='經濟'):
        """
        保存用戶搜索歷史
        
        Args:
            user_id (str or UUID): 用戶ID
            departure_airport_id (str or UUID): 出發機場ID
            arrival_airport_id (str or UUID): 到達機場ID
            departure_date (date): 出發日期
            return_date (date, optional): 返回日期
            adults (int, optional): 成人數量
            children (int, optional): 兒童數量
            infants (int, optional): 嬰兒數量
            class_type (str, optional): 艙等類型
            
        Returns:
            tuple: (是否成功, 搜索歷史對象或錯誤訊息)
        """
        try:
            # 創建搜索歷史記錄
            search_history = UserSearchHistory(
                user_id=user_id,
                departure_airport_id=departure_airport_id,
                arrival_airport_id=arrival_airport_id,
                departure_date=departure_date,
                return_date=return_date,
                adults=adults,
                children=children,
                infants=infants,
                class_type=class_type
            )
            
            db.session.add(search_history)
            db.session.commit()
            
            logger.info(f"保存用戶搜索歷史: {user_id}, {departure_airport_id} -> {arrival_airport_id}")
            return True, search_history
            
        except SQLAlchemyError as e:
            db.session.rollback()
            error_msg = f"保存搜索歷史時發生資料庫錯誤: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"保存搜索歷史時發生錯誤: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def get_search_history(self, user_id, page=1, per_page=10):
        """
        獲取用戶搜索歷史
        
        Args:
            user_id (int): 用戶ID
            page (int, optional): 頁碼，默認為1
            per_page (int, optional): 每頁數量，默認為10
            
        Returns:
            dict: 包含分頁信息和搜索歷史記錄的字典
        """
        try:
            # 查詢該用戶的搜索歷史
            query = UserSearchHistory.query.filter_by(
                user_id=user_id,
                is_test_data=self.test_mode
            ).order_by(UserSearchHistory.search_time.desc())
            
            # 獲取分頁結果
            pagination = query.paginate(page=page, per_page=per_page)
            
            # 將結果轉換為字典
            history_list = []
            for history in pagination.items:
                history_dict = history.to_dict()
                # 解析搜索參數
                import json
                search_params = json.loads(history.search_params) if history.search_params else {}
                history_dict['search_params'] = search_params
                history_list.append(history_dict)
            
            # 構建分頁信息
            return {
                'history': history_list,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': pagination.total,
                    'pages': pagination.pages,
                    'has_next': pagination.has_next,
                    'has_prev': pagination.has_prev
                }
            }
            
        except Exception as e:
            logger.error(f"獲取搜索歷史時發生錯誤: {str(e)}")
            return {
                'history': [],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': 0,
                    'pages': 0,
                    'has_next': False,
                    'has_prev': False
                }
            }
    
    def get_frequent_searches(self, user_id, limit=5):
        """
        獲取用戶常用搜索
        
        Args:
            user_id (int): 用戶ID
            limit (int, optional): 返回的數量限制，默認為5
            
        Returns:
            list: 常用搜索列表
        """
        try:
            import json
            from sqlalchemy import func
            
            # 查詢該用戶的搜索歷史
            query = db.session.query(
                UserSearchHistory.search_params,
                func.count(UserSearchHistory.id).label('count')
            ).filter(
                UserSearchHistory.user_id == user_id,
                UserSearchHistory.is_test_data == self.test_mode
            ).group_by(
                UserSearchHistory.search_params
            ).order_by(
                db.desc('count')
            ).limit(limit)
            
            # 解析結果
            frequent_searches = []
            for search_params_str, count in query.all():
                search_params = json.loads(search_params_str) if search_params_str else {}
                frequent_searches.append({
                    'search_params': search_params,
                    'count': count
                })
            
            return frequent_searches
            
        except Exception as e:
            logger.error(f"獲取常用搜索時發生錯誤: {str(e)}")
            return []
    
    def clear_search_history(self, user_id):
        """
        清除用戶搜索歷史
        
        Args:
            user_id (int): 用戶ID
            
        Returns:
            bool: 操作是否成功
        """
        try:
            # 刪除該用戶的所有搜索歷史
            UserSearchHistory.query.filter_by(
                user_id=user_id,
                is_test_data=self.test_mode
            ).delete()
            
            db.session.commit()
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"清除搜索歷史時發生錯誤: {str(e)}")
            return False
    
    def save_user_query(self, user_id, platform, query_type, query_content, response_content=None):
        """
        保存用戶查詢
        
        Args:
            user_id (str or UUID): 用戶ID
            platform (str): 平台，例如'web', 'line', 'mobile'
            query_type (str): 查詢類型，例如'flight', 'airport', 'airline', 'weather'
            query_content (str): 查詢內容
            response_content (str, optional): 回應內容
            
        Returns:
            tuple: (是否成功, 查詢對象或錯誤訊息)
        """
        try:
            # 創建用戶查詢
            user_query = UserQuery(
                user_id=user_id,
                platform=platform,
                query_type=query_type,
                query_content=query_content,
                response_content=response_content
            )
            
            db.session.add(user_query)
            db.session.commit()
            
            logger.info(f"保存用戶查詢: {user_id}, {query_type}, {query_content[:20]}...")
            return True, user_query
            
        except SQLAlchemyError as e:
            db.session.rollback()
            error_msg = f"保存用戶查詢時發生資料庫錯誤: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"保存用戶查詢時發生錯誤: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def get_user_queries(self, user_id, limit=10):
        """
        獲取用戶查詢歷史
        
        Args:
            user_id (str or UUID): 用戶ID
            limit (int, optional): 限制返回的記錄數
            
        Returns:
            list: 用戶查詢列表
        """
        try:
            return UserQuery.get_by_user(user_id, limit)
        except Exception as e:
            logger.error(f"獲取用戶查詢時發生錯誤: {str(e)}")
            return []
    
    def mark_query_helpful(self, query_id, helpful=True):
        """
        標記查詢是否有幫助
        
        Args:
            query_id (str or UUID): 查詢ID
            helpful (bool, optional): 是否有幫助
            
        Returns:
            tuple: (是否成功, 查詢對象或錯誤訊息)
        """
        try:
            # 獲取查詢
            if isinstance(query_id, str):
                query_id = uuid.UUID(query_id)
                
            query = UserQuery.query.get(query_id)
            if not query:
                return False, "查詢不存在"
            
            # 標記是否有幫助
            query.mark_helpful(helpful)
            
            logger.info(f"標記查詢 {query_id} 為{'有' if helpful else '無'}幫助")
            return True, query
            
        except Exception as e:
            error_msg = f"標記查詢時發生錯誤: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def get_popular_routes(self, days=30, limit=5):
        """
        獲取熱門路線
        
        Args:
            days (int, optional): 天數限制
            limit (int, optional): 結果數量限制
            
        Returns:
            list: 熱門路線列表
        """
        try:
            return UserSearchHistory.get_popular_routes(days, limit)
        except Exception as e:
            logger.error(f"獲取熱門路線時發生錯誤: {str(e)}")
            return []
    
    def get_popular_queries(self, days=30, limit=10):
        """
        獲取熱門查詢
        
        Args:
            days (int, optional): 天數限制
            limit (int, optional): 結果數量限制
            
        Returns:
            list: 熱門查詢列表
        """
        try:
            return UserQuery.get_popular_queries(days, limit)
        except Exception as e:
            logger.error(f"獲取熱門查詢時發生錯誤: {str(e)}")
            return []
    
    def delete_account(self, user_id, password=None):
        """
        刪除用戶帳號
        
        Args:
            user_id (str or UUID): 用戶ID
            password (str, optional): 密碼，用於驗證
            
        Returns:
            tuple: (是否成功, 成功訊息或錯誤訊息)
        """
        try:
            # 獲取用戶
            user = self.get_user_by_id(user_id)
            if not user:
                return False, "用戶不存在"
            
            # 如果提供了密碼，則驗證密碼
            if password and not user.verify_password(password):
                return False, "密碼不正確"
            
            # 刪除用戶
            db.session.delete(user)
            db.session.commit()
            
            logger.info(f"刪除用戶帳號: {user_id}")
            return True, "用戶帳號已刪除"
            
        except SQLAlchemyError as e:
            db.session.rollback()
            error_msg = f"刪除用戶帳號時發生資料庫錯誤: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"刪除用戶帳號時發生錯誤: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def _generate_token(self, user_id):
        """
        生成JWT令牌
        
        Args:
            user_id (UUID): 用戶ID
            
        Returns:
            str: JWT令牌
        """
        expiration = datetime.utcnow() + timedelta(hours=24)
        payload = {
            'exp': expiration,
            'iat': datetime.utcnow(),
            'user_id': str(user_id)
        }
        return jwt.encode(
            payload,
            current_app.config.get('SECRET_KEY'),
            algorithm='HS256'
        )