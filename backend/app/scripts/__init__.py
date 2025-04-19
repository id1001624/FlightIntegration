#!/usr/bin/env python
# -*- coding: utf-8 -*-
"Scripts模組初始化文件"
__version__ = '1.0.0'

import click
from flask.cli import AppGroup
import logging

logger = logging.getLogger(__name__)

# --- 嘗試在頂層導入腳本函數 ---
_crm_func = None
try:
    from .create_rich_menu import create_rich_menu
    _crm_func = create_rich_menu
    logger.info("[scripts/__init__] 成功導入 create_rich_menu 函數.")
except ImportError as e:
    logger.error(f"[scripts/__init__] 無法導入 create_rich_menu: {e}")
except Exception as e:
    logger.error(f"[scripts/__init__] 導入 create_rich_menu 時發生其他錯誤: {e}")
# ---

# 創建一個新的 CLI 命令組
scripts_cli = AppGroup('scripts', help='運行維護和設置腳本。')

@scripts_cli.command('setup-rich-menu')
def setup_rich_menu_command():
    """創建並設置預設的 LINE Rich Menu。"""
    if _crm_func is None:
        print("錯誤：無法執行命令，因為 create_rich_menu 函數導入失敗。")
        logger.error("無法執行 setup-rich-menu 命令，因為 _crm_func 為 None")
        return
        
    try:
        print("開始執行 Rich Menu 設置腳本...")
        _crm_func()
        print("Rich Menu 設置腳本執行完畢。")
    except Exception as e:
        print(f"執行 Rich Menu 設置腳本時出錯：{e}")
        logger.exception("執行 setup_rich_menu_command 時發生詳細錯誤:")

# 將這個命令組註冊到 Flask App 的函數
def register_script_commands(app):
    app.cli.add_command(scripts_cli)
