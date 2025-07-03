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
            # 修改查詢邏輯：檢查city或country為Unknown的機場
            airports_query = """
                SELECT airport_id, name_en, name_zh, city, country
                FROM airports 
                WHERE city = 'Unknown City' 
                   OR country = 'Unknown Country'
                   OR name_zh IS NULL 
                   OR name_zh = '' 
                   OR name_zh = name_en
                ORDER BY 
                    CASE 
                        WHEN city = 'Unknown City' OR country = 'Unknown Country' THEN 1
                        ELSE 2
                    END,
                    airport_id
                LIMIT 30
            """
            airports_to_update = await conn.fetch(airports_query)
            
            if airports_to_update:
                print("--- ✈️  需要更新的機場 (前30個，優先顯示Unknown資料) ---")
                for airport in airports_to_update:
                    # 標記問題類型
                    issues = []
                    if airport['city'] == 'Unknown City':
                        issues.append("城市未知")
                    if airport['country'] == 'Unknown Country':
                        issues.append("國家未知")
                    if not airport['name_zh'] or airport['name_zh'] == airport['name_en']:
                        issues.append("缺少中文名")
                    
                    print(f"  - 機場代碼: {airport['airport_id']}")
                    print(f"    英文名稱: {airport['name_en']}")
                    print(f"    目前中文名: {airport['name_zh']}")
                    print(f"    城市: {airport['city']}, 國家: {airport['country']}")
                    print(f"    問題: {', '.join(issues)}")
                    print("-" * 20)
            else:
                print("--- ✈️  所有機場資料都已更新 ---\n")

            # 查詢各種類型的機場統計
            total_airports = await conn.fetchval("SELECT COUNT(*) FROM airports")
            
            unknown_city_count = await conn.fetchval("SELECT COUNT(*) FROM airports WHERE city = 'Unknown City'")
            unknown_country_count = await conn.fetchval("SELECT COUNT(*) FROM airports WHERE country = 'Unknown Country'")
            missing_zh_name_count = await conn.fetchval("SELECT COUNT(*) FROM airports WHERE name_zh IS NULL OR name_zh = '' OR name_zh = name_en")
            
            # 統計有完整資訊的機場（所有欄位都正確）
            complete_airports = await conn.fetchval("""
                SELECT COUNT(*) FROM airports 
                WHERE city != 'Unknown City' 
                AND country != 'Unknown Country'
                AND name_zh IS NOT NULL 
                AND name_zh != '' 
                AND name_zh != name_en
            """)
            
            print(f"\n📊 機場資料統計：")
            print(f"  - 總機場數: {total_airports}")
            print(f"  - 完整資料機場: {complete_airports}")
            print(f"  - 城市未知: {unknown_city_count}")
            print(f"  - 國家未知: {unknown_country_count}")
            print(f"  - 缺少中文名: {missing_zh_name_count}")
            print(f"  - 完整度: {complete_airports/total_airports*100:.1f}%")

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