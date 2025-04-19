# backend/app/controllers/line_webhook_controller.py
import os
import sys
import logging
from flask import Blueprint, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, ReplyMessageRequest, TextMessage
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import MessageEvent, TextMessageContent

# 創建一個新的 Blueprint
line_webhook_bp = Blueprint('line_webhook', __name__, url_prefix='/line')

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 從環境變數獲取 LINE Bot 的憑證
channel_secret = os.environ.get('LINE_CHANNEL_SECRET')
channel_access_token = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')

# 檢查環境變數是否設置
if not channel_secret:
    logger.error("錯誤：LINE_CHANNEL_SECRET 環境變數未設置。")
    # 在生產環境中，您可能希望應用程序在缺少關鍵配置時退出或引發更嚴重的錯誤
    # sys.exit(1) 
if not channel_access_token:
    logger.error("錯誤：LINE_CHANNEL_ACCESS_TOKEN 環境變數未設置。")
    # sys.exit(1)

# 只有在環境變數都存在時才初始化 Handler 和 Configuration
handler = None
configuration = None
if channel_secret and channel_access_token:
    handler = WebhookHandler(channel_secret)
    configuration = Configuration(access_token=channel_access_token)
else:
    logger.warning("LINE Bot SDK 未能初始化，因為缺少必要的環境變數。Webhook 將無法正常工作。")

@line_webhook_bp.route("/callback", methods=['POST'])
def callback():
    """處理來自 LINE Platform 的 Webhook 事件"""
    if not handler:
        logger.error("Webhook handler 未初始化。")
        abort(500) # 內部伺服器錯誤

    # 從請求標頭獲取簽名
    signature = request.headers.get('X-Line-Signature')
    if not signature:
        logger.error("請求缺少 X-Line-Signature 標頭")
        abort(400) # 錯誤請求

    # 獲取請求主體
    body = request.get_data(as_text=True)
    logger.info(f"接收到的請求主體: {body}")

    try:
        # 處理 Webhook 事件（包含簽名驗證）
        handler.handle(body, signature)
    except InvalidSignatureError:
        logger.error("無效的簽名。請檢查 Channel Secret 是否正確。")
        abort(400)
    except Exception as e:
        logger.error(f"處理 Webhook 時發生錯誤: {e}")
        abort(500)

    return 'OK', 200

# 定義一個簡單的訊息處理器，目前僅記錄收到的訊息
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event: MessageEvent):
    """處理文字訊息事件"""
    if not configuration:
        logger.error("MessagingApi configuration 未初始化。")
        return # 無法處理
        
    user_id = event.source.user_id if event.source else '未知使用者'
    text = event.message.text
    reply_token = event.reply_token
    logger.info(f"收到來自 {user_id} 的文字訊息: {text}")

    # 目前階段，我們主要依賴 Rich Menu 進行導航，所以可以暫時不回覆文字訊息
    # 或者可以回覆一個通用訊息提示用戶使用選單
    # with ApiClient(configuration) as api_client:
    #     line_bot_api = MessagingApi(api_client)
    #     try:
    #         line_bot_api.reply_message(
    #             ReplyMessageRequest(
    #                 reply_token=reply_token,
    #                 messages=[TextMessage(text='請點擊下方選單查看航班資訊')]
    #             )
    #         )
    #     except Exception as e:
    #         logger.error(f"回覆訊息時發生錯誤: {e}")

# 可以在此處添加更多事件處理器，例如 FollowEvent
# @handler.add(FollowEvent)
# def handle_follow(event):
#     logger.info(f"使用者 {event.source.user_id} 加入好友")
#     # ... 發送歡迎訊息 ... 