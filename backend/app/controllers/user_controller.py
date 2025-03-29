from flask import Blueprint, request, jsonify, current_app
from app.services import user_service
from app.utils.api_helper import api_response
import logging

# 設置日誌
logger = logging.getLogger(__name__)

# 建立用戶相關API藍圖
user_bp = Blueprint('user', __name__, url_prefix='/api/users')

@user_bp.route('/profile', methods=['GET'])
def get_user_profile():
    """獲取用戶個人資料API"""
    # 從請求頭或請求參數中獲取用戶ID或令牌
    user_id = request.args.get('user_id')
    token = request.headers.get('Authorization')
    
    if not user_id and not token:
        return api_response(False, message='未提供用戶ID或認證令牌', status_code=400)
    
    # 如果提供了令牌，先驗證令牌獲取用戶ID
    if token and not user_id:
        # 去掉Bearer前綴
        if token.startswith('Bearer '):
            token = token[7:]
        
        from app.services import auth_service
        success, result = auth_service.verify_token(token)
        
        if not success:
            return api_response(False, message='無效的認證令牌', status_code=401)
        
        user_id = result
    
    # 獲取用戶資料
    user = user_service.get_user_by_id(user_id)
    
    if not user:
        return api_response(False, message='用戶不存在', status_code=404)
    
    return api_response(True, data=user.to_dict())

@user_bp.route('/search-history', methods=['GET'])
def get_search_history():
    """獲取用戶搜索歷史API"""
    # 從請求頭或請求參數中獲取用戶ID或令牌
    user_id = request.args.get('user_id')
    token = request.headers.get('Authorization')
    
    if not user_id and not token:
        return api_response(False, message='未提供用戶ID或認證令牌', status_code=400)
    
    # 如果提供了令牌，先驗證令牌獲取用戶ID
    if token and not user_id:
        # 去掉Bearer前綴
        if token.startswith('Bearer '):
            token = token[7:]
        
        from app.services import auth_service
        success, result = auth_service.verify_token(token)
        
        if not success:
            return api_response(False, message='無效的認證令牌', status_code=401)
        
        user_id = result
    
    # 獲取分頁參數
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # 獲取搜索歷史
    history_data = user_service.get_search_history(user_id, page, per_page)
    
    return api_response(True, data=history_data)

@user_bp.route('/frequent-searches', methods=['GET'])
def get_frequent_searches():
    """獲取用戶常用搜索API"""
    # 從請求頭或請求參數中獲取用戶ID或令牌
    user_id = request.args.get('user_id')
    token = request.headers.get('Authorization')
    
    if not user_id and not token:
        return api_response(False, message='未提供用戶ID或認證令牌', status_code=400)
    
    # 如果提供了令牌，先驗證令牌獲取用戶ID
    if token and not user_id:
        # 去掉Bearer前綴
        if token.startswith('Bearer '):
            token = token[7:]
        
        from app.services import auth_service
        success, result = auth_service.verify_token(token)
        
        if not success:
            return api_response(False, message='無效的認證令牌', status_code=401)
        
        user_id = result
    
    # 獲取常用搜索
    frequent_searches = user_service.get_frequent_searches(user_id)
    
    return api_response(True, data=frequent_searches)

@user_bp.route('/clear-history', methods=['DELETE'])
def clear_search_history():
    """清除用戶搜索歷史API"""
    # 從請求頭或請求參數中獲取用戶ID或令牌
    user_id = request.args.get('user_id') or request.json.get('user_id')
    token = request.headers.get('Authorization')
    
    if not user_id and not token:
        return api_response(False, message='未提供用戶ID或認證令牌', status_code=400)
    
    # 如果提供了令牌，先驗證令牌獲取用戶ID
    if token and not user_id:
        # 去掉Bearer前綴
        if token.startswith('Bearer '):
            token = token[7:]
        
        from app.services import auth_service
        success, result = auth_service.verify_token(token)
        
        if not success:
            return api_response(False, message='無效的認證令牌', status_code=401)
        
        user_id = result
    
    # 清除搜索歷史
    success = user_service.clear_search_history(user_id)
    
    if not success:
        return api_response(False, message='清除搜索歷史失敗', status_code=500)
    
    return api_response(True, message='搜索歷史已清除')
