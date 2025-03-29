"""
控制器層 - 處理HTTP請求和響應

此包包含所有API端點控制器，負責：
1. 接收並驗證HTTP請求
2. 調用適當的服務層方法
3. 格式化API響應
4. 錯誤處理和狀態碼管理
"""

# 允許從controllers包直接導入所有控制器
from app.controllers.flight_controller import flight_bp
from app.controllers.airport_controller import airport_bp
from app.controllers.admin_controller import admin_bp
from app.controllers.auth_controller import auth_bp


# 導出所有藍圖，便於在應用初始化時註冊
__all__ = ['flight_bp', 'airport_bp', 'admin_bp', 'auth_bp']