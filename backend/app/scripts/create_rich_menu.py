# backend/app/scripts/create_rich_menu.py
import os
import sys
import logging
import requests # <-- 重新導入 requests 庫
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    MessagingApiBlob, # <-- 引入 MessagingApiBlob
    RichMenuRequest,  # <-- 引入 RichMenuRequest
    RichMenuArea,
    RichMenuSize,
    RichMenuBounds,
    URIAction,
    ErrorResponse      # <-- 保持 ErrorResponse
)
# from linebot.v3.messaging.models import ErrorResponse # 已在上面引入
from linebot.v3.messaging.exceptions import ApiException
from dotenv import load_dotenv
from pathlib import Path
from flask import Blueprint, current_app
# from linebot import LineBotApi # <-- 移除 v2 LineBotApi
# from linebot.models import RichMenu # <-- 移除 v2 RichMenu
import json

# 加載環境變數
# load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../../.env')) # 由 Flask app 加載

# 配置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- 配置區 --- 
# 從環境變數讀取配置
CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
# 從環境變數讀取 Vercel 前端 URL，提供預設值以防萬一
FRONTEND_URL = os.environ.get('FRONTEND_URL', "https://flight-integration.vercel.app") 
# Rich Menu 圖片路徑 (相對於專案根目錄)
RICH_MENU_IMAGE_PATH = "backend/app/static/images/flight-search.jpg" # <--- 確認圖片是 jpg 還是 png
# Rich Menu 的名稱和聊天欄文字
RICH_MENU_NAME = "主選單 AlphaVision"
CHAT_BAR_TEXT = "點此開啟網站"
# ----------------

def create_rich_menu():
    """使用 v3 SDK 創建並設置預設的 Rich Menu"""
    if not CHANNEL_ACCESS_TOKEN:
        logger.error("錯誤：環境變數 LINE_CHANNEL_ACCESS_TOKEN 未設置！")
        return

    # 檢查圖片是否存在
    image_absolute_path = os.path.abspath(RICH_MENU_IMAGE_PATH)
    if not os.path.exists(image_absolute_path):
        logger.error(f"錯誤：找不到 Rich Menu 圖片文件於 '{image_absolute_path}' (相對路徑: '{RICH_MENU_IMAGE_PATH}')。")
        return

    configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)

    # 定義 Rich Menu 結構 (使用 v3 的 RichMenuRequest)
    rich_menu_to_create = RichMenuRequest( # <-- 使用 RichMenuRequest
        size=RichMenuSize(width=2500, height=1686), # 確保尺寸正確
        selected=True,
        name=RICH_MENU_NAME, # 使用變數
        chat_bar_text=CHAT_BAR_TEXT, # 使用變數
        areas=[
            RichMenuArea(
                bounds=RichMenuBounds(x=0, y=0, width=2500, height=1686), # <--- 讓首頁按鈕涵蓋整個區域
                action=URIAction(label='首頁', uri=f'{FRONTEND_URL}/') # 確保結尾有斜線
            ),
            # RichMenuArea(
            #     bounds=RichMenuBounds(x=833, y=0, width=834, height=843),
            #     action=URIAction(label='航班搜尋', uri=f'{FRONTEND_URL}/flight-search') # <-- 修正 URI
            # ),
            # RichMenuArea(
            #     bounds=RichMenuBounds(x=1667, y=0, width=833, height=843),
            #     action=URIAction(label='熱門航班', uri=f'{FRONTEND_URL}/flights/popular')
            # ),
            # RichMenuArea(
            #     bounds=RichMenuBounds(x=0, y=843, width=833, height=843),
            #     action=URIAction(label='台灣出發', uri=f'{FRONTEND_URL}/flights/from-taiwan')
            # ),
            # RichMenuArea(
            #     bounds=RichMenuBounds(x=833, y=843, width=834, height=843),
            #     action=URIAction(label='常見問題', uri=f'{FRONTEND_URL}/faq')
            # ),
            # RichMenuArea(
            #     bounds=RichMenuBounds(x=1667, y=843, width=833, height=843),
            #     action=URIAction(label='關於我們', uri=f'{FRONTEND_URL}/about')
            # )
        ]
    )

    try:
        # 使用 v3 SDK 進行 API 調用
        with ApiClient(configuration) as api_client:
            messaging_api = MessagingApi(api_client)
            messaging_api_blob = MessagingApiBlob(api_client)
            
            # 1. 創建 Rich Menu
            rich_menu_response = messaging_api.create_rich_menu(rich_menu_request=rich_menu_to_create)
            rich_menu_id = rich_menu_response.rich_menu_id
            logger.info(f"Rich Menu 已創建，ID: {rich_menu_id}")
            
            # 2. 上傳圖片 (恢復使用 requests)
            content_type = 'image/jpeg' if RICH_MENU_IMAGE_PATH.lower().endswith('.jpg') else 'image/png'

            with open(image_absolute_path, 'rb') as f:
                image_data = f.read() # 讀取圖片 bytes

            # --- 開始 requests 上傳 ---
            upload_url = f"https://api-data.line.me/v2/bot/richmenu/{rich_menu_id}/content"
            headers = {
                "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
                "Content-Type": content_type # 使用偵測到的 content_type
            }
            try:
                response = requests.post(upload_url, headers=headers, data=image_data)
                response.raise_for_status() # 如果響應狀態碼不是 2xx，則引發異常
                logger.info(f"Rich Menu 圖片上傳成功 (使用 requests)，響應碼：{response.status_code}")
            except requests.exceptions.RequestException as e:
                logger.error(f"使用 requests 上傳 Rich Menu 圖片時發生錯誤: {e}")
                # 如果上傳失敗，刪除已創建的 Rich Menu
                try:
                    messaging_api.delete_rich_menu(rich_menu_id)
                    logger.warning(f"已刪除因圖片上傳失敗而創建的 Rich Menu: {rich_menu_id}")
                except Exception as delete_error:
                    logger.error(f"嘗試刪除失敗的 Rich Menu {rich_menu_id} 時出錯: {delete_error}")
                return # 終止腳本執行
            # --- 結束 requests 上傳 ---

            # 3. 將 Rich Menu 設為默認
            messaging_api.set_default_rich_menu(rich_menu_id=rich_menu_id)
            logger.info(f"Rich Menu (ID: {rich_menu_id}) 已設為默認")
            
            print(f"\nRich Menu 設置完成！預設選單 ID: {rich_menu_id}")
            print(f"請重新進入與 Bot 的聊天視窗查看效果。")

    except ApiException as e:
        logger.error(f"調用 LINE API 時發生錯誤 (狀態碼: {e.status})：")
        try:
            # 嘗試解析標準的 ErrorResponse
            error_body_dict = json.loads(e.body) # 先嘗試解析 JSON
            error_response = ErrorResponse.from_dict(error_body_dict)
            logger.error(f"  訊息: {error_response.message}")
            if error_response.details:
                for detail in error_response.details:
                    logger.error(f"  - Property: {detail.property}, Message: {detail.message}")
        except json.JSONDecodeError:
             logger.error(f"  無法解析錯誤響應體 (非 JSON): {e.body}")
        except Exception as parse_error:
            # 如果解析失敗，直接打印原始 body
            logger.error(f"  無法解析錯誤響應體，原始 Body: {e.body}, 解析錯誤: {parse_error}")
            # 打印更多 ApiException 的信息
            logger.error(f"  Reason: {e.reason}")
            logger.error(f"  Headers: {e.headers}")

    # 恢復 requests 的錯誤處理
    except requests.RequestException as e:
        # 這個錯誤現在會在恢復的 requests 代碼塊中被捕獲和處理
        # 這裡只是為了完整性，但上面的 try/except 應該已經處理了
        logger.error(f"處理 HTTP 請求時發生錯誤 (可能是 requests): {e}")
    except FileNotFoundError:
        # 這個錯誤應該在函數開頭就被捕獲了，但保留以防萬一
        logger.error(f"錯誤：找不到指定的圖片文件 '{image_absolute_path}'")
    except Exception as e:
        logger.error(f"創建 Rich Menu 過程中發生預期外的錯誤: {e}")
        logger.exception("詳細錯誤信息:") # 打印完整的 traceback

if __name__ == "__main__":
    # 如果直接運行此腳本，需要確保環境變數已設置
    # 通常建議通過 Flask CLI 運行
    # load_dotenv() # 可以取消註釋以從 .env 加載（如果存在）
    if not CHANNEL_ACCESS_TOKEN or not os.environ.get('LINE_CHANNEL_SECRET'): # 假設 CLI 也需要 secret
        print("錯誤：運行此腳本需要設置 LINE_CHANNEL_ACCESS_TOKEN 和 LINE_CHANNEL_SECRET 環境變數。")
        print("建議使用 'flask scripts setup-rich-menu' 命令運行。")
    else:
        create_rich_menu() 