import os
import sys
import asyncio

# 將專案根目錄添加到 sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app import create_app
from app.database.db import get_pool

async def show_pending_updates():
    """
    查詢並顯示所有需要手動更新中文名稱的機場和航空公司。
    """
    print("\n" + "="*50)
    print("          需要手動更新的資料報告")
    print("="*50 + "\n")

    try:
        # 初始化連接池
        pool = await get_pool()
        
        # 查詢需要更新的機場
        async with pool.acquire() as conn:
            # 先查詢一些機場看看結構
            airports_query = """
                SELECT airport_id, name_en, name_zh, city, country
                FROM airports 
                WHERE name_zh IS NULL OR name_zh = '' OR name_zh = name_en
                ORDER BY airport_id
                LIMIT 20
            """
            airports_to_update = await conn.fetch(airports_query)
            
            if airports_to_update:
                print("--- ✈️  可能需要更新的機場 (前20個) ---")
                for airport in airports_to_update:
                    print(f"  - 機場代碼: {airport['airport_id']}")
                    print(f"    英文名稱: {airport['name_en']}")
                    print(f"    目前中文名: {airport['name_zh']}")
                    print(f"    城市: {airport['city']}, 國家: {airport['country']}")
                    print("-" * 20)
            else:
                print("--- ✈️  所有機場資料都已更新 ---\n")

            # 查詢總機場數和有中文名稱的機場數
            total_airports = await conn.fetchval("SELECT COUNT(*) FROM airports")
            airports_with_zh = await conn.fetchval("SELECT COUNT(*) FROM airports WHERE name_zh IS NOT NULL AND name_zh != '' AND name_zh != name_en")
            
            print(f"\n統計資訊：")
            print(f"  - 總機場數: {total_airports}")
            print(f"  - 有中文名稱的機場數: {airports_with_zh}")
            print(f"  - 完成度: {airports_with_zh/total_airports*100:.1f}%")

            print("\n")

            # 查詢需要更新的航空公司
            airlines_query = """
                SELECT airline_id, name_en, name_zh, created_at
                FROM airlines 
                WHERE needs_manual_update = true 
                ORDER BY created_at
            """
            airlines_to_update = await conn.fetch(airlines_query)

            if airlines_to_update:
                print("--- 🛩️  需要更新的航空公司 ---")
                for airline in airlines_to_update:
                    print(f"  - 航空代碼: {airline['airline_id']}")
                    print(f"    英文名稱: {airline['name_en']}")
                    print(f"    目前中文名: {airline['name_zh']}")
                    print("-" * 20)
            else:
                print("--- 🛩️  所有航空公司資料都已更新 ---\n")
        
    except Exception as e:
        print(f"查詢過程中發生錯誤: {e}")
    
    print("="*50)
    print("報告結束")
    print("="*50 + "\n")

def run_show_pending_updates():
    """同步執行入口"""
    app = create_app()
    with app.app_context():
        asyncio.run(show_pending_updates())

if __name__ == '__main__':
    run_show_pending_updates() 