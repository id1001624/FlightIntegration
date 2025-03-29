from flask import Blueprint, request, jsonify, current_app
from app.services import data_sync_service

# 創建管理員藍圖
admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

@admin_bp.route('/sync-data', methods=['POST'])
def sync_all_data():
    """同步所有數據（機場、航空公司、航班）"""
    result = data_sync_service.sync_all_data()
    
    if not result['success']:
        return jsonify(result), 500
    
    return jsonify(result)

@admin_bp.route('/sync-airports', methods=['POST'])
def sync_airports():
    """同步機場數據"""
    result = data_sync_service.sync_airports()
    
    if not result['success']:
        return jsonify(result), 500
    
    return jsonify(result)

@admin_bp.route('/sync-airlines', methods=['POST'])
def sync_airlines():
    """同步航空公司數據"""
    result = data_sync_service.sync_airlines()
    
    if not result['success']:
        return jsonify(result), 500
    
    return jsonify(result)

@admin_bp.route('/sync-flights', methods=['POST'])
def sync_flights():
    """同步航班數據"""
    result = data_sync_service.sync_flights()
    
    if not result['success']:
        return jsonify(result), 500
    
    return jsonify(result)

@admin_bp.route('/sync-delays', methods=['POST'])
def sync_flight_delays():
    """同步航班延誤統計數據"""
    result = data_sync_service.sync_flight_delays()
    
    if not result['success']:
        return jsonify(result), 500
    
    return jsonify(result)

@admin_bp.route('/test-tdx', methods=['GET'])
def test_tdx_connection():
    """測試TDX API連線"""
    result = data_sync_service.test_tdx_connection()
    
    if not result['success']:
        return jsonify(result), 500
    
    return jsonify(result)

@admin_bp.route('/test-flightstats', methods=['GET'])
def test_flightstats_connection():
    """測試FlightStats API連線"""
    result = data_sync_service.test_flightstats_connection()
    
    if not result['success']:
        return jsonify(result), 500
    
    return jsonify(result)

@admin_bp.route('/test-mode', methods=['GET'])
def get_test_mode():
    """獲取當前測試模式狀態"""
    test_mode = current_app.config.get('TEST_MODE', False)
    return jsonify({
        'success': True,
        'test_mode': test_mode
    })

@admin_bp.route('/test-mode', methods=['POST'])
def set_test_mode():
    """設置測試模式"""
    try:
        data = request.get_json()
        if 'test_mode' not in data:
            return jsonify({
                'success': False,
                'message': '請提供test_mode參數'
            }), 400
            
        test_mode = data['test_mode']
        current_app.config['TEST_MODE'] = test_mode
        
        return jsonify({
            'success': True,
            'message': f'測試模式已{'啟用' if test_mode else '停用'}',
            'test_mode': test_mode
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'設置測試模式時發生錯誤: {str(e)}'
        }), 500