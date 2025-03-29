from flask import Blueprint, request, jsonify, current_app
from app.services.auth_service import AuthService
from app.services.user_service import UserService

# 建立認證相關API藍圖
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# 實例化服務
auth_service = None
user_service = None

@auth_bp.before_app_first_request
def setup_services():
    global auth_service, user_service
    test_mode = current_app.config.get('TESTING', False)
    auth_service = AuthService(test_mode=test_mode)
    user_service = UserService(test_mode=test_mode)

@auth_bp.route('/register', methods=['POST'])
def register():
    """用戶註冊API"""
    data = request.json
    
    # 檢查必要欄位
    required_fields = ['email', 'password']
    for field in required_fields:
        if field not in data:
            return jsonify({
                'success': False,
                'message': f'缺少必要欄位: {field}'
            }), 400
    
    # 調用服務層方法
    success, result = user_service.register(
        email=data['email'],
        password=data['password'],
        full_name=data.get('full_name'),
        phone=data.get('phone'),
        passport_number=data.get('passport_number'),
        nationality=data.get('nationality'),
        date_of_birth=data.get('date_of_birth')
    )
    
    if not success:
        return jsonify({
            'success': False,
            'message': result
        }), 400
    
    # 註冊成功後自動登入
    token_result = auth_service.generate_token(result.user_id)
    
    return jsonify({
        'success': True,
        'message': '註冊成功',
        'data': {
            'user': result.to_dict(),
            'token': token_result['token']
        }
    })

@auth_bp.route('/login', methods=['POST'])
def login():
    """用戶登入API"""
    data = request.json
    
    # 檢查必要欄位
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({
            'success': False,
            'message': '請提供電子郵件和密碼'
        }), 400
    
    # 調用服務層方法
    success, result = user_service.login(data['email'], data['password'])
    
    if not success:
        return jsonify({
            'success': False,
            'message': result
        }), 401  # 401 表示未授權
    
    return jsonify({
        'success': True,
        'message': '登入成功',
        'data': {
            'user': result['user'].to_dict(),
            'token': result['token']
        }
    })

@auth_bp.route('/verify-token', methods=['POST'])
def verify_token():
    """驗證令牌API"""
    data = request.json
    
    if not data or 'token' not in data:
        return jsonify({
            'success': False,
            'message': '請提供令牌'
        }), 400
    
    # 調用服務層方法
    success, result = auth_service.verify_token(data['token'])
    
    if not success:
        return jsonify({
            'success': False,
            'message': result
        }), 401
    
    # 獲取用戶資訊
    user = user_service.get_user_by_id(result)
    
    return jsonify({
        'success': True,
        'data': {
            'user_id': result,
            'user': user.to_dict() if user else None
        }
    })

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """用戶登出API"""
    data = request.json
    
    if not data or 'user_id' not in data:
        return jsonify({
            'success': False,
            'message': '請提供用戶ID'
        }), 400
    
    # 登出操作 (主要由前端處理)
    user_service.logout(data['user_id'])
    
    return jsonify({
        'success': True,
        'message': '登出成功'
    })