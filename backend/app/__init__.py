from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS  # 處理跨域請求
from flask_migrate import Migrate  # 資料庫遷移工具
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.services.tdx_service import TDXService


# 創建資料庫物件，但還不初始化它
db = SQLAlchemy()

# 建立並配置Flask應用
def create_app():
    app = Flask(__name__)
    
    # 從配置檔案讀取設定
    app.config.from_object('app.config.Config')
    
    # 初始化資料庫連接
    db.init_app(app)
    
    # 允許跨域請求，這樣前端Vue才能訪問API
    CORS(app)
    
    # 註冊藍圖
    from app.controllers.api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')

    # 初始化資料庫遷移
    migrate = Migrate(app, db)

    # 初始化排程器
    scheduler = BackgroundScheduler()
    tdx_service = TDXService()
    
    # 月初 (每月1號凌晨2點)
    scheduler.add_job(
        tdx_service.sync_flight_data,
        CronTrigger(day='1', hour='2', minute='0')
    )
    
    # 月中 (每月15號凌晨2點)
    scheduler.add_job(
        tdx_service.sync_flight_data,
        CronTrigger(day='15', hour='2', minute='0')
    )
    
    # 月底 (每月最後一天凌晨2點)
    scheduler.add_job(
        tdx_service.sync_flight_data,
        CronTrigger(day='28-31', hour='2', minute='0', day_of_week='*'),
        # 這會在28-31日都執行，但我們需要加入檢查確保只在月底執行
        kwargs={'check_last_day': True}
    )
    
    # 啟動排程器
    scheduler.start()
    
    # 建立所有資料表（開發時可用，生產環境應使用遷移）
    with app.app_context():
        db.create_all()

    #錯誤處理
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'success': False, 'message': '找不到請求的資源'}), 404

    @app.errorhandler(500)
    def server_error(error):
        return jsonify({'success': False, 'message': '伺服器內部錯誤'}), 500
    
    
    return app