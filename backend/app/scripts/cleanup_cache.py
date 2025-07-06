#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
緩存清理腳本
清理過期的航班價格緩存和舊日期的數據
"""
import sys
import os
from datetime import datetime, timedelta

# 添加項目根目錄到 Python 路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(backend_dir)
sys.path.insert(0, backend_dir)  # 添加backend目錄到路徑
sys.path.insert(0, project_root)

from app import create_app
from app.models.ticket_price import TicketPrice
from app.models.base import db

def cleanup_expired_cache():
    """清理過期的緩存數據"""
    print("=== 清理過期緩存數據 ===")
    
    try:
        # 清理過期的緩存記錄（根據cache_expires_at）
        expired_count = TicketPrice.query.filter(
            TicketPrice.is_cached == True,
            TicketPrice.cache_expires_at < datetime.utcnow()
        ).delete()
        
        print(f"✅ 清理了 {expired_count} 條過期緩存記錄")
        return expired_count
        
    except Exception as e:
        print(f"❌ 清理過期緩存時發生錯誤: {e}")
        return 0

def cleanup_old_date_data():
    """清理舊日期的航班數據"""
    print("=== 清理舊日期航班數據 ===")
    
    try:
        # 清理昨天之前的航班數據
        yesterday = datetime.now().date() - timedelta(days=1)
        
        old_flight_count = TicketPrice.query.filter(
            TicketPrice.departure_date < yesterday
        ).delete()
        
        print(f"✅ 清理了 {old_flight_count} 條舊日期航班記錄（{yesterday}之前）")
        return old_flight_count
        
    except Exception as e:
        print(f"❌ 清理舊日期數據時發生錯誤: {e}")
        return 0

def cleanup_duplicate_cache():
    """清理重複的緩存記錄"""
    print("=== 清理重複緩存記錄 ===")
    
    try:
        # 找出重複的緩存記錄（相同的航班但有多個緩存版本）
        duplicate_query = """
        DELETE FROM ticket_prices 
        WHERE price_id NOT IN (
            SELECT MIN(price_id) 
            FROM ticket_prices 
            WHERE is_cached = true 
            GROUP BY amadeus_offer_id, origin_airport_code, destination_airport_code, departure_date, cabin_class
        ) AND is_cached = true
        """
        
        result = db.session.execute(duplicate_query)
        duplicate_count = result.rowcount
        
        print(f"✅ 清理了 {duplicate_count} 條重複緩存記錄")
        return duplicate_count
        
    except Exception as e:
        print(f"❌ 清理重複緩存時發生錯誤: {e}")
        return 0

def get_cache_statistics():
    """獲取緩存統計信息"""
    print("=== 緩存統計信息 ===")
    
    try:
        # 總緩存記錄數
        total_cache = TicketPrice.query.filter(TicketPrice.is_cached == True).count()
        
        # 有效緩存記錄數
        valid_cache = TicketPrice.query.filter(
            TicketPrice.is_cached == True,
            TicketPrice.cache_expires_at > datetime.utcnow()
        ).count()
        
        # 今天的緩存記錄數
        today = datetime.now().date()
        today_cache = TicketPrice.query.filter(
            TicketPrice.is_cached == True,
            TicketPrice.departure_date >= today
        ).count()
        
        # 按艙等分組統計
        cabin_stats = db.session.query(
            TicketPrice.cabin_class,
            db.func.count(TicketPrice.price_id)
        ).filter(
            TicketPrice.is_cached == True,
            TicketPrice.cache_expires_at > datetime.utcnow()
        ).group_by(TicketPrice.cabin_class).all()
        
        print(f"📊 總緩存記錄: {total_cache}")
        print(f"📊 有效緩存記錄: {valid_cache}")
        print(f"📊 今日緩存記錄: {today_cache}")
        print("📊 按艙等分佈:")
        for cabin_class, count in cabin_stats:
            print(f"   - {cabin_class or '未知'}: {count}")
        
        return {
            "total": total_cache,
            "valid": valid_cache,
            "today": today_cache,
            "by_cabin": dict(cabin_stats)
        }
        
    except Exception as e:
        print(f"❌ 獲取統計信息時發生錯誤: {e}")
        return {}

def main():
    """主函數"""
    print("🧹 開始緩存清理作業...")
    print(f"⏰ 執行時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 創建應用上下文
    app = create_app()
    with app.app_context():
        try:
            # 獲取清理前統計
            print("\n📊 清理前統計:")
            get_cache_statistics()
            
            # 執行清理
            print("\n🧹 執行清理作業:")
            expired_count = cleanup_expired_cache()
            old_count = cleanup_old_date_data()
            duplicate_count = cleanup_duplicate_cache()
            
            # 提交事務
            db.session.commit()
            
            # 獲取清理後統計
            print("\n📊 清理後統計:")
            get_cache_statistics()
            
            # 總結
            total_cleaned = expired_count + old_count + duplicate_count
            print(f"\n✅ 清理完成！總共清理了 {total_cleaned} 條記錄")
            print(f"   - 過期緩存: {expired_count}")
            print(f"   - 舊日期數據: {old_count}")
            print(f"   - 重複記錄: {duplicate_count}")
            
        except Exception as e:
            print(f"❌ 清理過程中發生錯誤: {e}")
            db.session.rollback()
            return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 