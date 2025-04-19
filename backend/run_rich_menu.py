"""
一個簡單的腳本，用於加載環境變數並執行create_rich_menu.py
"""

import os
import sys
from dotenv import load_dotenv
from pathlib import Path

# 載入環境變數
dotenv_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=dotenv_path)

# 檢查關鍵環境變數
token = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
if not token:
    print("錯誤: 環境變數 LINE_CHANNEL_ACCESS_TOKEN 未設置!")
    sys.exit(1)

# 執行Rich Menu設置腳本
print("開始設置Rich Menu...")
try:
    from app.scripts.create_rich_menu import create_rich_menu
    create_rich_menu()
    print("Rich Menu設置腳本執行完成。")
except Exception as e:
    print(f"執行Rich Menu設置腳本時發生錯誤: {e}")
    import traceback
    traceback.print_exc() 