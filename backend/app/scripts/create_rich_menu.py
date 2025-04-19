# backend/app/scripts/create_rich_menu.py
import os
import sys
import logging
import requests  # <-- 添加 requests 庫
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    RichMenuRequest,
    RichMenuArea,
    RichMenuSize,
    RichMenuBounds,
    URIAction,
    MessagingApiBlob
)
from linebot.v3.messaging.models import ErrorResponse
from linebot.v3.messaging.exceptions import ApiException
from dotenv import load_dotenv
from pathlib import Path
from flask import Blueprint, current_app
from linebot import LineBotApi
from linebot.models import RichMenu

# 加載環境變數
# load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../../.env')) # <-- 註釋掉，由 run.py 統一加載

# 配置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- 配置區 --- 
# 從環境變數讀取配置
CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
# Vercel 前端部署的 URL (請確保這是正確的)
FRONTEND_URL = "https://flight-integration.vercel.app" 
# 您準備好的 Rich Menu 圖片路徑 (相對於項目根目錄)
RICH_MENU_IMAGE_PATH = "backend/app/static/images/flight-search.jpg" # <--- 路徑相對於專案根目錄
# Rich Menu 的名稱和聊天欄文字
RICH_MENU_NAME = "主選單"
CHAT_BAR_TEXT = "點此開啟網站"
# ----------------

def create_rich_menu():
    """創建並設置預設的 Rich Menu"""
    if not CHANNEL_ACCESS_TOKEN:
        logger.error("錯誤：環境變數 LINE_CHANNEL_ACCESS_TOKEN 未設置！")
        return

    # 檢查圖片是否存在於新的路徑
    # 假設 RICH_MENU_IMAGE_PATH 是相對於專案根目錄的路徑
    # 直接使用 abspath 轉換
    image_absolute_path = os.path.abspath(RICH_MENU_IMAGE_PATH)
    # image_absolute_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', RICH_MENU_IMAGE_PATH)) # <-- 舊的錯誤計算方式
    if not os.path.exists(image_absolute_path):
        logger.error(f"錯誤：找不到 Rich Menu 圖片文件於 '{image_absolute_path}' (相對路徑: '{RICH_MENU_IMAGE_PATH}')。請確認路徑相對於專案根目錄且文件存在。")
        return

    configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)

    # 定義 Rich Menu 結構
    rich_menu_to_create = RichMenu(
        size=RichMenuSize(width=2500, height=1686),
        selected=True,
        name="Alpha Vision Rich Menu",
        chat_bar_text="選單",
        areas=[
            RichMenuArea(
                bounds=RichMenuBounds(x=0, y=0, width=833, height=843),
                action=URIAction(label='首頁', uri=f'{FRONTEND_URL}')
            ),
            RichMenuArea(
                bounds=RichMenuBounds(x=833, y=0, width=834, height=843),
                action=URIAction(label='航班搜尋', uri=f'{FRONTEND_URL}/flights/search')
            ),
            RichMenuArea(
                bounds=RichMenuBounds(x=1667, y=0, width=833, height=843),
                action=URIAction(label='熱門航班', uri=f'{FRONTEND_URL}/flights/popular')
            ),
            RichMenuArea(
                bounds=RichMenuBounds(x=0, y=843, width=833, height=843),
                action=URIAction(label='台灣出發', uri=f'{FRONTEND_URL}/flights/from-taiwan')
            ),
            RichMenuArea(
                bounds=RichMenuBounds(x=833, y=843, width=834, height=843),
                action=URIAction(label='常見問題', uri=f'{FRONTEND_URL}/faq')
            ),
            RichMenuArea(
                bounds=RichMenuBounds(x=1667, y=843, width=833, height=843),
                action=URIAction(label='關於我們', uri=f'{FRONTEND_URL}/about')
            )
        ]
    )

    try:
        line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
        # 創建 Rich Menu
        rich_menu_id = line_bot_api.create_rich_menu(rich_menu=rich_menu_to_create)
        logger.info(f"Rich Menu 已創建，ID: {rich_menu_id}")
        
        # 讀取文件內容 (bytes)
        with open(image_absolute_path, 'rb') as f:
            image_data = f.read()
        
        # 使用 requests 直接調用 LINE API 上傳圖片，而不是使用 SDK
        upload_url = f"https://api.line.me/v2/bot/richmenu/{rich_menu_id}/content"
        headers = {
            "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
            "Content-Type": "image/png"  # 根據您的圖片類型調整
        }
        
        try:
            response = requests.post(upload_url, headers=headers, data=image_data)
            response.raise_for_status()  # 如果響應狀態碼不是 2xx，則引發異常
            logger.info(f"Rich Menu 圖片上傳成功，響應碼：{response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.error(f"上傳 Rich Menu 圖片時發生錯誤: {e}")
            return
        
        # 將 Rich Menu 設為默認
        line_bot_api.set_default_rich_menu(rich_menu_id)
        logger.info("Rich Menu 已設為默認")
        
        print(f"\nRich Menu 設置完成！預設選單 ID: {rich_menu_id}")
        print(f"請重新進入與 Bot 的聊天視窗查看效果。")

    except ApiException as e:
        logger.error(f"調用 LINE API 時發生錯誤 (狀態碼: {e.status})：")
        try:
            error_response = ErrorResponse.from_json(e.body)
            logger.error(f"  訊息: {error_response.message}")
            if error_response.details:
                for detail in error_response.details:
                    logger.error(f"  - {detail.property}: {detail.message}")
        except Exception as parse_error:
            logger.error(f"  無法解析錯誤響應體: {e.body}, 解析錯誤: {parse_error}")
    except requests.RequestException as e:
        logger.error(f"使用 requests 發送 HTTP 請求時發生錯誤: {e}")
    except FileNotFoundError:
        logger.error(f"錯誤：找不到指定的圖片文件 '{image_absolute_path}'")
    except Exception as e:
        logger.error(f"創建 Rich Menu 過程中發生預期外的錯誤: {e}")
        logger.exception("詳細錯誤信息:")

if __name__ == "__main__":
    create_rich_menu() 