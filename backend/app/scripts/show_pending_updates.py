import os
import sys

# 將專案根目錄添加到 sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app import create_app
from app.models import Airport, Airline
from app.database.db import db

def show_pending_updates():
    """
    查詢並顯示所有需要手動更新中文名稱的機場和航空公司。
    """
    app = create_app()
    with app.app_context():
        print("\n" + "="*50)
        print("          需要手動更新的資料報告")
        print("="*50 + "\n")

        # 查詢需要更新的機場
        airports_to_update = Airport.query.filter_by(needs_manual_update=True).order_by(Airport.created_at).all()
        
        if airports_to_update:
            print("--- ✈️  需要更新的機場 ---")
            for airport in airports_to_update:
                print(f"  - 機場代碼: {airport.airport_id}")
                print(f"    英文名稱: {airport.name_en}")
                print(f"    目前中文名: {airport.name_zh}")
                print(f"    城市: {airport.city}, 國家: {airport.country}")
                print("-" * 20)
        else:
            print("--- ✈️  所有機場資料都已更新 ---\n")

        print("\n")

        # 查詢需要更新的航空公司
        airlines_to_update = Airline.query.filter_by(needs_manual_update=True).order_by(Airline.created_at).all()

        if airlines_to_update:
            print("--- 🛩️  需要更新的航空公司 ---")
            for airline in airlines_to_update:
                print(f"  - 航空代碼: {airline.airline_id}")
                print(f"    英文名稱: {airline.name_en}")
                print(f"    目前中文名: {airline.name_zh}")
                print("-" * 20)
        else:
            print("--- 🛩️  所有航空公司資料都已更新 ---\n")
        
        print("="*50)
        print("報告結束")
        print("="*50 + "\n")

if __name__ == '__main__':
    show_pending_updates() 