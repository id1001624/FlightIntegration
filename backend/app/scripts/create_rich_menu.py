# backend/app/scripts/create_rich_menu.py
import os
import sys
import logging
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

# 加載環境變數
# load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../../.env')) # <-- 註釋掉，由 run.py 統一加載

# 配置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- 配置區 --- 
# 從環境變數讀取配置
CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
# Vercel 前端部署的 URL (請確保這是正確的)
FRONTEND_URL = "https://flight-integration.vercel.app" 
# 您準備好的 Rich Menu 圖片路徑 (相對於項目根目錄)
RICH_MENU_IMAGE_PATH = "backend/app/static/images/flight-search.png" # <--- 路徑相對於專案根目錄
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
    rich_menu_to_create = RichMenuRequest(
        size=RichMenuSize(width=2500, height=843), # <--- 這裡的尺寸需要匹配您的圖片！
        selected=False, # 預設是否展開
        name=RICH_MENU_NAME,
        chat_bar_text=CHAT_BAR_TEXT,
        areas=[
            RichMenuArea(
                # 整個區域都是一個按鈕
                bounds=RichMenuBounds(x=0, y=0, width=2500, height=843), # <--- 這裡的尺寸需要匹配您的圖片！
                # 點擊後打開前端網站
                action=URIAction(uri=FRONTEND_URL, label="開啟航班查詢網站") 
            )
        ]
    )

    try:
        with ApiClient(configuration) as api_client:
            # 1. 創建 Rich Menu 物件
            line_bot_api = MessagingApi(api_client)
            rich_menu_response = line_bot_api.create_rich_menu(rich_menu_request=rich_menu_to_create)
            rich_menu_id = rich_menu_response.rich_menu_id
            logger.info(f"成功創建 Rich Menu 物件，ID: {rich_menu_id}")

            # 2. 上傳 Rich Menu 圖片 (使用 MessagingApiBlob)
            line_bot_blob_api = MessagingApiBlob(api_client)
            with open(image_absolute_path, 'rb') as image_file:
                # 讀取文件內容 (bytes)
                image_content = image_file.read()
                # 調用 set_rich_menu_image，並明確指定 Content-Type
                set_rich_menu_image_response = line_bot_blob_api.set_rich_menu_image(
                    rich_menu_id=rich_menu_id,
                    body=image_content,    # <-- 傳遞讀取到的 bytes
                    _content_type='image/png' # <-- 明確指定 Content-Type
                )
            logger.info(f"成功上傳 Rich Menu 圖片 ({image_absolute_path}) 到 ID: {rich_menu_id} (響應: {set_rich_menu_image_response})")

            # 3. 設置為預設 Rich Menu
            set_default_rich_menu_response = line_bot_api.set_default_rich_menu(rich_menu_id=rich_menu_id)
            logger.info(f"成功將 Rich Menu (ID: {rich_menu_id}) 設置為預設選單。")

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
    except FileNotFoundError:
        logger.error(f"錯誤：找不到指定的圖片文件 '{image_absolute_path}'")
    except Exception as e:
        logger.error(f"創建 Rich Menu 過程中發生預期外的錯誤: {e}")
        logger.exception("詳細錯誤信息:")

if __name__ == "__main__":
    create_rich_menu() 