# controllers 包的初始化文件
# 此文件標記 controllers 目錄為 Python 包

# 如果需要在其他地方直接訪問 api 藍圖，可以導出它
from .api import api

# 未來可能需要導出的其他控制器，可以添加在這裡
# 例如：from .auth import auth
# 或：from .user import user_controller