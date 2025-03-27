# run.py - 後端啟動腳本

from app import create_app  # 從 app/__init__.py 導入 create_app 函數

# 創建 Flask 應用
app = create_app()

# 如果直接執行這個腳本，則啟動應用
if __name__ == '__main__':
    # 啟動開發伺服器
    # debug=True 啟用調試模式，代碼變更時自動重啟
    # host='0.0.0.0' 允許外部連接
    app.run(debug=True, host='0.0.0.0', port=5000)