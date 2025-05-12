#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
航班舊資料清理腳本

用途:
    定期清理資料庫中的舊航班和票價資料，可配置保留期限、資料類型和備份選項。
    主要用於維護資料庫健康和控制資料庫大小。

用法:
    python cleanup_old_data.py --retention-days 90 --data-type test --backup

參數:
    --retention-days: 要保留的天數，默認為30天
    --data-type: 要清理的資料類型，可選 'test'(測試資料)、'real'(實際資料)、'all'(所有資料)，默認為'test'
    --backup: 是否在刪除前備份資料，默認不備份
    --dry-run: 僅顯示將被刪除的記錄數量，不實際刪除
"""

import sys
import os
import argparse
import logging
import json
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Any, Optional
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
import traceback

# --- 添加正確的導入路徑 (確保在導入 app 之前) ---
current_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.dirname(current_dir)
backend_dir = os.path.dirname(app_dir)
sys.path.insert(0, backend_dir)

# --- 配置日誌 (必須在導入 app 之前) ---
logs_dir = os.path.join(os.path.dirname(os.path.dirname(current_dir)), 'logs')
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(logs_dir, 'cleanup_old_data.log'))
    ]
)
logger = logging.getLogger('cleanup_old_data')

# --- 導入並創建 Flask app 以獲取上下文 ---
try:
    if app_dir not in sys.path:
        sys.path.insert(0, app_dir)
    from app import create_app
    flask_app = create_app()
    flask_app.app_context().push()
    logger.info("Flask app context 已創建並推入。")
except ImportError as e:
    logger.error(f"無法導入或創建 Flask app ({e})。請確保腳本可以訪問 Flask app 實例。")
    sys.exit(1)

# --- 現在導入 db 對象 ---
try:
    from app.models.base import db
    logger.info("成功導入 db 對象。")
except ImportError:
    logger.error("即使創建了 app context，仍然無法從 app.models.base 導入 db 對象。請檢查 Flask app 初始化過程。")
    sys.exit(1)

# --- 導入其他必要的模塊 ---
from app.models.flight import Flight
from app.models.ticket_price import TicketPrice


def parse_arguments():
    """解析命令行參數"""
    parser = argparse.ArgumentParser(description='清除舊航班資料')
    parser.add_argument('--retention-days', type=int, default=30,
                      help='要保留的天數，默認30天')
    parser.add_argument('--data-type', choices=['test', 'real', 'all'],
                      default='test', help='要清除的資料類型 (test/real/all)，默認為test')
    parser.add_argument('--backup', action='store_true',
                      help='是否在刪除前備份資料')
    parser.add_argument('--dry-run', action='store_true',
                      help='僅顯示將被刪除的記錄數量，不實際刪除')
    
    return parser.parse_args()


def get_old_flight_ids(reference_date: datetime.date, data_type: str) -> List[str]:
    """獲取指定日期之前的航班ID列表"""
    session = db.session
    try:
        reference_date_str = reference_date.strftime('%Y-%m-%d')
        
        # 構建過濾條件
        if data_type == "test":
            filter_condition = "AND is_test_data = TRUE"
        elif data_type == "real":
            filter_condition = "AND is_test_data = FALSE"
        else:  # "all"
            filter_condition = ""
        
        # 獲取需要刪除的航班ID
        flight_ids_query = text(f"""
            SELECT flight_id FROM flights 
            WHERE DATE(scheduled_departure) < :ref_date
            {filter_condition}
        """)
        
        result = session.execute(flight_ids_query, {"ref_date": reference_date_str})
        flight_ids = [str(row[0]) for row in result]
        
        return flight_ids
    except SQLAlchemyError as e:
        logger.error(f"獲取舊航班ID時發生資料庫錯誤: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"獲取舊航班ID時發生未預期錯誤: {str(e)}")
        raise


def backup_data(flight_ids: List[str], backup_dir: str = "./backups") -> str:
    """在刪除前備份資料"""
    session = db.session
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    backup_file = f"{backup_dir}/flights_backup_{timestamp}.json"
    
    try:
        # 查詢要備份的航班資料
        flights_query = text("""
            SELECT flight_id, flight_number, airline_id, departure_airport_id, arrival_airport_id,
                   scheduled_departure, scheduled_arrival, aircraft, is_test_data
            FROM flights
            WHERE flight_id IN :flight_ids
        """)
        flights_result = session.execute(flights_query, {"flight_ids": tuple(flight_ids)})
        
        flights_data = []
        for row in flights_result:
            flights_data.append({
                'flight_id': str(row[0]),
                'flight_number': row[1],
                'airline_id': row[2],
                'departure_airport_id': row[3],
                'arrival_airport_id': row[4],
                'scheduled_departure': row[5].isoformat() if row[5] else None,
                'scheduled_arrival': row[6].isoformat() if row[6] else None,
                'aircraft': row[7],
                'is_test_data': row[8]
            })
        
        # 查詢要備份的票價資料
        prices_query = text("""
            SELECT price_id, flight_id, economy_price, business_price, 
                   first_price, available_seats, is_test_data
            FROM ticket_prices
            WHERE flight_id IN :flight_ids
        """)
        prices_result = session.execute(prices_query, {"flight_ids": tuple(flight_ids)})
        
        prices_data = []
        for row in prices_result:
            prices_data.append({
                'price_id': str(row[0]),
                'flight_id': str(row[1]),
                'economy_price': float(row[2]) if row[2] is not None else None,
                'business_price': float(row[3]) if row[3] is not None else None,
                'first_price': float(row[4]) if row[4] is not None else None,
                'available_seats': row[5],
                'is_test_data': row[6]
            })
        
        # 寫入備份文件
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump({
                'flights': flights_data,
                'ticket_prices': prices_data
            }, f, ensure_ascii=False, indent=2)
        
        logger.info(f"成功備份 {len(flights_data)} 個航班和 {len(prices_data)} 個票價記錄到 {backup_file}")
        return backup_file
    
    except Exception as e:
        logger.error(f"備份資料時發生錯誤: {str(e)}")
        if os.path.exists(backup_file):
            try:
                os.remove(backup_file)
            except:
                pass
        raise


def batch_delete_data(flight_ids: List[str], batch_size: int = 1000, dry_run: bool = False) -> Tuple[int, int]:
    """分批刪除航班和票價資料"""
    if not flight_ids:
        logger.info("沒有符合條件的航班資料需要刪除")
        return 0, 0
    
    if dry_run:
        logger.info(f"【模擬刪除】將刪除 {len(flight_ids)} 個航班及其相關票價")
        return len(flight_ids), 0  # 無法確切知道票價數量，除非實際查詢
    
    session = db.session
    total = len(flight_ids)
    deleted_flights = 0
    deleted_prices = 0
    
    try:
        # 分批處理以避免一次性處理過多資料
        for i in range(0, total, batch_size):
            batch_ids = flight_ids[i:i+batch_size]
            if not batch_ids:
                continue
            
            # 先刪除相關的票價資料
            delete_prices_query = text("""
                DELETE FROM ticket_prices 
                WHERE flight_id IN :flight_ids
                RETURNING flight_id
            """)
            price_result = session.execute(delete_prices_query, {"flight_ids": tuple(batch_ids)})
            batch_deleted_prices = price_result.rowcount
            deleted_prices += batch_deleted_prices
            
            # 再刪除航班資料
            delete_flights_query = text("""
                DELETE FROM flights 
                WHERE flight_id IN :flight_ids
                RETURNING flight_id
            """)
            flight_result = session.execute(delete_flights_query, {"flight_ids": tuple(batch_ids)})
            batch_deleted_flights = flight_result.rowcount
            deleted_flights += batch_deleted_flights
            
            logger.info(f"已刪除第 {i+1} 至 {min(i+batch_size, total)} 批資料: {batch_deleted_flights} 個航班, {batch_deleted_prices} 個票價")
            
            # 每批次提交一次事務
            session.commit()
        
        return deleted_flights, deleted_prices
    
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"批次刪除資料時發生資料庫錯誤: {str(e)}")
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"批次刪除資料時發生未預期錯誤: {str(e)}")
        raise


def generate_report(
    start_time: datetime,
    reference_date: datetime.date,
    retention_days: int,
    data_type: str,
    flight_count: int,
    price_count: int,
    backup_file: Optional[str] = None,
    dry_run: bool = False
) -> Dict[str, Any]:
    """產生執行報告"""
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    report = {
        "執行開始時間": start_time.strftime('%Y-%m-%d %H:%M:%S'),
        "執行結束時間": end_time.strftime('%Y-%m-%d %H:%M:%S'),
        "執行時間": f"{duration:.2f}秒",
        "參考日期": reference_date.strftime('%Y-%m-%d'),
        "保留天數": retention_days,
        "資料類型": data_type,
        "模擬執行": dry_run,
        "刪除航班數": flight_count,
        "刪除票價數": price_count
    }
    
    if backup_file:
        report["備份文件"] = backup_file
    
    return report


def clear_old_data(retention_days: int = 30, data_type: str = "test", 
                  backup: bool = False, dry_run: bool = False) -> Dict[str, Any]:
    """
    清除指定日期之前的資料
    
    Args:
        retention_days: 保留天數，默認30天
        data_type: 資料類型 "test"(測試資料)、"all"(所有資料)、"real"(實際資料)
        backup: 是否在刪除前備份資料
        dry_run: 僅顯示將被刪除的記錄數量，不實際刪除
    
    Returns:
        執行報告字典
    """
    start_time = datetime.now()
    reference_date = datetime.now().date()
    
    # 計算刪除日期界限
    delete_before_date = reference_date - timedelta(days=retention_days)
    
    logger.info(f"開始清理 {delete_before_date} 之前的{'測試' if data_type == 'test' else '所有' if data_type == 'all' else '實際'}航班資料")
    
    try:
        # 獲取舊航班ID
        flight_ids = get_old_flight_ids(delete_before_date, data_type)
        
        if not flight_ids:
            logger.info(f"沒有找到 {delete_before_date} 之前的{'測試' if data_type == 'test' else '所有' if data_type == 'all' else '實際'}航班資料")
            return generate_report(
                start_time, reference_date, retention_days, 
                data_type, 0, 0, None, dry_run
            )
        
        logger.info(f"找到 {len(flight_ids)} 個符合刪除條件的航班")
        
        # 備份資料（如果需要）
        backup_file = None
        if backup and not dry_run:
            backup_file = backup_data(flight_ids)
            logger.info(f"已將資料備份至 {backup_file}")
        
        # 執行刪除
        deleted_flights, deleted_prices = batch_delete_data(flight_ids, dry_run=dry_run)
        
        if dry_run:
            logger.info(f"【模擬執行】將刪除 {deleted_flights} 個航班及其相關票價")
        else:
            logger.info(f"已成功刪除 {deleted_flights} 個航班和 {deleted_prices} 個票價記錄")
        
        # 生成報告
        report = generate_report(
            start_time, reference_date, retention_days, 
            data_type, deleted_flights, deleted_prices, 
            backup_file, dry_run
        )
        
        return report
    
    except Exception as e:
        logger.error(f"清理舊資料時發生錯誤: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "執行開始時間": start_time.strftime('%Y-%m-%d %H:%M:%S'),
            "執行狀態": "失敗",
            "錯誤訊息": str(e)
        }


def main():
    """主函數，處理命令行參數並執行資料清理"""
    # 解析命令行參數
    args = parse_arguments()
    
    # 執行資料清理
    try:
        report = clear_old_data(
            retention_days=args.retention_days,
            data_type=args.data_type,
            backup=args.backup,
            dry_run=args.dry_run
        )
        
        # 輸出報告
        logger.info("=== 執行報告 ===")
        for key, value in report.items():
            logger.info(f"{key}: {value}")
        
        # 將報告保存為JSON文件
        report_dir = "./reports"
        if not os.path.exists(report_dir):
            os.makedirs(report_dir)
        
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        report_file = f"{report_dir}/cleanup_report_{timestamp}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"報告已保存至 {report_file}")
        
    except Exception as e:
        logger.error(f"執行資料清理時發生錯誤: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main() 