#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修復 ticket_prices 表的緩存欄位
添加實時價格系統架構重構中定義的欄位
"""
import sys
import os
sys.path.append('.')

from app import create_app, db
import logging

logger = logging.getLogger(__name__)

def check_column_exists(table_name, column_name):
    """檢查欄位是否存在"""
    try:
        result = db.session.execute(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = '{table_name}' 
            AND column_name = '{column_name}'
        """)
        return result.fetchone() is not None
    except Exception as e:
        logger.error(f"檢查欄位時發生錯誤: {e}")
        return False

def add_cache_columns():
    """添加緩存相關欄位"""
    
    columns_to_add = [
        # 緩存查詢欄位
        ("origin_airport_code", "VARCHAR(3)"),
        ("destination_airport_code", "VARCHAR(3)"),
        ("departure_date", "DATE"),
        ("is_cached", "BOOLEAN DEFAULT FALSE"),
        ("cache_expires_at", "TIMESTAMP"),
        ("search_key", "VARCHAR(255)"),
        ("cabin_class", "VARCHAR(50) DEFAULT 'ECONOMY'"),
        
        # 新增艙等價格欄位
        ("premium_economy_price", "DECIMAL(10,2)"),
        
        # 座位數量欄位
        ("economy_seats", "INTEGER"),
        ("premium_economy_seats", "INTEGER"),
        ("business_seats", "INTEGER"),
        ("first_seats", "INTEGER"),
        
        # 價格詳細資訊
        ("currency", "VARCHAR(3) DEFAULT 'TWD'"),
        ("base_price", "DECIMAL(10,2)"),
        ("total_price", "DECIMAL(10,2)"),
        ("taxes_and_fees", "DECIMAL(10,2)"),
        
        # Amadeus 特定欄位
        ("amadeus_offer_id", "VARCHAR(255)"),
        ("fare_type", "VARCHAR(50)"),
        ("instant_ticketing_required", "BOOLEAN DEFAULT FALSE"),
        ("last_ticketing_date", "DATE"),
        ("number_of_bookable_seats", "INTEGER"),
        
        # 額外服務費用
        ("checked_bags_fee", "DECIMAL(10,2)"),
        ("seat_selection_fee", "DECIMAL(10,2)"),
        
        # 系統欄位
        ("data_source", "VARCHAR(50) DEFAULT 'amadeus'"),
    ]
    
    print("=== 檢查並添加 ticket_prices 表的緩存欄位 ===\n")
    
    for column_name, column_type in columns_to_add:
        try:
            # 檢查欄位是否已存在
            if check_column_exists('ticket_prices', column_name):
                print(f"✅ 欄位 {column_name} 已存在，跳過")
                continue
            
            # 添加欄位
            sql = f"ALTER TABLE ticket_prices ADD COLUMN {column_name} {column_type};"
            print(f"➕ 添加欄位: {column_name} ({column_type})")
            
            db.session.execute(sql)
            db.session.commit()
            
            print(f"✅ 成功添加欄位: {column_name}")
            
        except Exception as e:
            print(f"❌ 添加欄位 {column_name} 失敗: {e}")
            db.session.rollback()
            
    print("\n=== 創建索引 ===")
    
    indexes_to_create = [
        ("idx_cache_lookup", "origin_airport_code, destination_airport_code, departure_date, is_cached"),
        ("idx_cache_expires", "cache_expires_at"),
        ("idx_search_key", "search_key"),
        ("idx_amadeus_offer", "amadeus_offer_id"),
    ]
    
    for index_name, columns in indexes_to_create:
        try:
            sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON ticket_prices ({columns});"
            print(f"📋 創建索引: {index_name}")
            
            db.session.execute(sql)
            db.session.commit()
            
            print(f"✅ 成功創建索引: {index_name}")
            
        except Exception as e:
            print(f"❌ 創建索引 {index_name} 失敗: {e}")
            db.session.rollback()

def verify_table_structure():
    """驗證表結構"""
    print("\n=== 驗證 ticket_prices 表結構 ===")
    
    try:
        result = db.session.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'ticket_prices'
            ORDER BY ordinal_position
        """)
        
        columns = result.fetchall()
        print(f"表 ticket_prices 包含 {len(columns)} 個欄位:")
        
        for column in columns:
            nullable = "可空" if column[2] == "YES" else "不可空"
            default = f" (預設: {column[3]})" if column[3] else ""
            print(f"  - {column[0]}: {column[1]} ({nullable}){default}")
            
    except Exception as e:
        print(f"❌ 驗證表結構失敗: {e}")

def main():
    """主函數"""
    app = create_app('development')
    
    with app.app_context():
        try:
            print("開始修復 ticket_prices 表的緩存欄位...")
            
            # 添加缺失的欄位
            add_cache_columns()
            
            # 驗證表結構
            verify_table_structure()
            
            print("\n🎉 票價表緩存欄位修復完成！")
            
        except Exception as e:
            print(f"❌ 修復過程中發生錯誤: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main() 