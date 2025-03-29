"""
API輔助工具模組 - 提供API相關的通用功能
"""
from flask import jsonify

def api_response(success, data=None, message=None, status_code=200):
    """
    生成統一格式的API響應
    
    Args:
        success (bool): 操作是否成功
        data (any, optional): 返回的數據
        message (str, optional): 提示消息
        status_code (int, optional): HTTP狀態碼
        
    Returns:
        tuple: (JSON響應, HTTP狀態碼)
    """
    response = {
        'success': success
    }
    
    if data is not None:
        response['data'] = data
    
    if message is not None:
        response['message'] = message
    
    return jsonify(response), status_code 