"""
機場目的地同步腳本
定期從 Amadeus API 獲取並更新機場目的地數據，存儲到本地緩存表
避免前端選擇機場時的 API 延遲問題
"""
import sys
import os
from datetime import datetime, timedelta, date, timezone
from typing import List, Dict, Optional
import time
import asyncio

# 添加項目根目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app import create_app
from app.models.airport import Airport, AirportDestination
from app.models.flight import Flight
from app.services.amadeus_service import AmadeusService
from app.models.base import db
from sqlalchemy import func

# 只同步有國際航班的台灣機場
TAIWAN_INTERNATIONAL_AIRPORTS = [
    'TPE',  # 台灣桃園國際機場
    'TSA',  # 台北松山機場
    'KHH',  # 高雄國際機場
    'RMQ',  # 台中清泉崗機場
    'HUN',  # 花蓮機場 (主要為包機)
]

class AirportDestinationSyncer:
    """機場目的地同步器"""
    
    def __init__(self):
        self.app = create_app()
        self.amadeus_service = AmadeusService()
        
    def sync_all_destinations(self):
        """同步台灣國際機場的目的地數據"""
        with self.app.app_context():
            print(f"[{datetime.now()}] 開始同步台灣國際機場目的地數據...")
            
            # 獲取需要同步的台灣國際機場
            departure_airports = []
            missing_airports = []
            
            for airport_code in TAIWAN_INTERNATIONAL_AIRPORTS:
                airport = Airport.query.filter_by(airport_id=airport_code).first()
                if airport:
                    departure_airports.append(airport)
                else:
                    missing_airports.append(airport_code)
            
            if missing_airports:
                print(f"⚠️  警告：以下機場在資料庫中不存在: {', '.join(missing_airports)}")
                print(f"   請確認這些機場已正確導入到 airports 表中")
            
            print(f"找到 {len(departure_airports)} 個台灣國際機場需要同步:")
            for airport in departure_airports:
                print(f"  - {airport.airport_id}: {airport.name_zh}")
            
            # 使用單一事件循環處理所有異步操作
            total_synced = 0
            total_errors = 0
            
            try:
                # 運行異步同步任務
                synced_count, error_count = asyncio.run(self._async_sync_all_airports(departure_airports))
                total_synced = synced_count
                total_errors = error_count
            except Exception as e:
                print(f"❌ 異步同步過程中發生錯誤: {str(e)}")
                total_errors = len(departure_airports)
                
            print(f"\n[{datetime.now()}] 同步完成:")
            print(f"  📊 總計同步: {total_synced} 個目的地")
            print(f"  ❌ 錯誤數量: {total_errors}")
            
            # 更新航班統計
            self._update_flight_statistics()
    
    async def _async_sync_all_airports(self, departure_airports):
        """異步同步所有機場"""
        total_synced = 0
        total_errors = 0
        
        for airport in departure_airports:
            try:
                print(f"\n正在同步 {airport.airport_id} - {airport.name_zh}...")
                destinations = await self._async_sync_single_airport_destinations(airport.airport_id)
                
                if destinations:
                    total_synced += len(destinations)
                    print(f"  ✅ 成功同步 {len(destinations)} 個目的地")
                else:
                    print(f"  ⚠️ 未找到目的地或同步失敗")
                    
                # 避免 API 速率限制 - 每個機場間隔 2 秒
                await asyncio.sleep(2)
                
            except Exception as e:
                total_errors += 1
                print(f"  ❌ 同步失敗: {str(e)}")
                continue
        
        return total_synced, total_errors
    
    async def _async_sync_single_airport_destinations(self, departure_airport_id: str) -> List[Dict]:
        """異步同步單個機場的目的地數據"""
        try:
            # 直接調用異步方法，不使用 asyncio.run
            destinations_response = await self.amadeus_service.get_airport_destinations(departure_airport_id)
            
            if not destinations_response or 'data' not in destinations_response:
                print(f"    ⚠️ API 未返回數據")
                return []
            
            destinations = destinations_response['data']
            synced_destinations = []
            
            for dest_data in destinations:
                try:
                    destination_airport_id = dest_data.get('airport_id') or dest_data.get('iataCode')
                    if not destination_airport_id:
                        continue
                    
                    # 🚫 過濾掉台灣國內機場作為目的地
                    if self._is_taiwan_domestic_airport(destination_airport_id):
                        print(f"    ⏭️ 跳過台灣國內機場: {destination_airport_id}")
                        continue
                    
                    # 檢查目的地機場是否存在於我們的數據庫中
                    dest_airport = Airport.query.filter_by(airport_id=destination_airport_id).first()
                    if not dest_airport:
                        # 如果目的地機場不存在，創建基本記錄
                        dest_airport = self._create_basic_airport_record(dest_data)
                        if not dest_airport:
                            continue
                    
                    # 創建或更新 AirportDestination 記錄
                    route = AirportDestination.query.filter_by(
                        departure_airport_id=departure_airport_id,
                        destination_airport_id=destination_airport_id
                    ).first()
                    
                    if route:
                        # 更新現有記錄
                        route.updated_at = datetime.now(timezone.utc)  # 修正棄用警告
                        route.last_synced_at = datetime.now(timezone.utc)
                        route.is_active = True  # 如果 API 返回則認為是活躍的
                    else:
                        # 創建新記錄
                        route = AirportDestination(
                            departure_airport_id=departure_airport_id,
                            destination_airport_id=destination_airport_id,
                            is_active=True,
                            last_synced_at=datetime.now(timezone.utc)
                        )
                        db.session.add(route)
                    
                    synced_destinations.append({
                        'departure': departure_airport_id,
                        'destination': destination_airport_id,
                        'name': dest_data.get('name') or dest_airport.name_en
                    })
                    
                except Exception as e:
                    print(f"    ❌ 處理目的地 {dest_data} 時出錯: {str(e)}")
                    continue
            
            # 提交所有更改
            db.session.commit()
            return synced_destinations
            
        except Exception as e:
            db.session.rollback()
            print(f"    ❌ 同步機場 {departure_airport_id} 失敗: {str(e)}")
            return []
    
    def _is_taiwan_domestic_airport(self, airport_code: str) -> bool:
        """判斷是否為台灣國內機場"""
        # 台灣國內機場列表（離島和國內線機場）
        taiwan_domestic_airports = [
            'CMJ',  # 七美機場
            'CYI',  # 嘉義機場
            'GNI',  # 綠島機場
            'KNH',  # 金門機場
            'KYD',  # 蘭嶼機場
            'LZN',  # 馬祖南竿機場
            'MFK',  # 馬祖北竿機場
            'MZG',  # 澎湖機場
            'TNN',  # 台南機場
            'TTT',  # 台東機場
            'WOT',  # 王安機場
            # 注意：不包含 TPE、TSA、KHH、RMQ、HUN，因為這些是國際機場
        ]
        return airport_code in taiwan_domestic_airports
    
    def _sync_single_airport_destinations(self, departure_airport_id: str) -> List[Dict]:
        """同步單個機場的目的地數據"""
        try:
            # 調用 Amadeus API 獲取目的地 (注意這是異步方法)
            destinations_response = asyncio.run(
                self.amadeus_service.get_airport_destinations(departure_airport_id)
            )
            
            if not destinations_response or 'data' not in destinations_response:
                print(f"    ⚠️ API 未返回數據")
                return []
            
            destinations = destinations_response['data']
            synced_destinations = []
            
            for dest_data in destinations:
                try:
                    destination_airport_id = dest_data.get('airport_id') or dest_data.get('iataCode')
                    if not destination_airport_id:
                        continue
                    
                    # 檢查目的地機場是否存在於我們的數據庫中
                    dest_airport = Airport.query.filter_by(airport_id=destination_airport_id).first()
                    if not dest_airport:
                        # 如果目的地機場不存在，創建基本記錄
                        dest_airport = self._create_basic_airport_record(dest_data)
                        if not dest_airport:
                            continue
                    
                    # 創建或更新 AirportDestination 記錄
                    route = AirportDestination.query.filter_by(
                        departure_airport_id=departure_airport_id,
                        destination_airport_id=destination_airport_id
                    ).first()
                    
                    if route:
                        # 更新現有記錄
                        route.updated_at = datetime.utcnow()
                        route.last_synced_at = datetime.utcnow()
                        route.is_active = True  # 如果 API 返回則認為是活躍的
                    else:
                        # 創建新記錄
                        route = AirportDestination(
                            departure_airport_id=departure_airport_id,
                            destination_airport_id=destination_airport_id,
                            is_active=True,
                            last_synced_at=datetime.utcnow()
                        )
                        db.session.add(route)
                    
                    synced_destinations.append({
                        'departure': departure_airport_id,
                        'destination': destination_airport_id,
                        'name': dest_data.get('name') or dest_airport.name_en
                    })
                    
                except Exception as e:
                    print(f"    ❌ 處理目的地 {dest_data} 時出錯: {str(e)}")
                    continue
            
            # 提交所有更改
            db.session.commit()
            return synced_destinations
            
        except Exception as e:
            db.session.rollback()
            print(f"    ❌ 同步機場 {departure_airport_id} 失敗: {str(e)}")
            return []
    
    def _create_basic_airport_record(self, dest_data: Dict) -> Optional[Airport]:
        """為未知機場創建基本記錄"""
        try:
            airport_id = dest_data.get('airport_id') or dest_data.get('iataCode')
            name = dest_data.get('name', 'Unknown Airport')
            city = dest_data.get('city', 'Unknown City')
            country = dest_data.get('country', 'Unknown Country')
            
            airport = Airport(
                airport_id=airport_id,
                name_zh=name,  # 暫時使用英文名稱
                name_en=name,
                city=city,
                city_en=city,
                country=country,
                timezone='UTC',  # 預設時區
                # needs_manual_update=True  # 暫時註解，可能在模型中不存在
            )
            
            db.session.add(airport)
            db.session.commit()
            
            print(f"    ✅ 創建新機場記錄: {airport_id} - {name}")
            return airport
            
        except Exception as e:
            print(f"    ❌ 創建機場記錄失敗: {str(e)}")
            db.session.rollback()
            return None
    
    def _update_flight_statistics(self):
        """更新航班統計數據"""
        print(f"\n[{datetime.now()}] 開始更新航班統計...")
        
        try:
            # 計算日期範圍
            today = date.today()
            seven_days_ago = today - timedelta(days=7)
            thirty_days_ago = today - timedelta(days=30)
            
            # 查詢所有航線
            routes = AirportDestination.query.all()
            updated_count = 0
            
            for route in routes:
                # 計算過去 7 天的航班數量
                flights_7d = Flight.query.filter(
                    Flight.departure_airport_id == route.departure_airport_id,
                    Flight.arrival_airport_id == route.destination_airport_id,
                    func.date(Flight.scheduled_departure) >= seven_days_ago
                ).count()
                
                # 計算過去 30 天的航班數量
                flights_30d = Flight.query.filter(
                    Flight.departure_airport_id == route.departure_airport_id,
                    Flight.arrival_airport_id == route.destination_airport_id,
                    func.date(Flight.scheduled_departure) >= thirty_days_ago
                ).count()
                
                # 獲取最後一次航班日期
                last_flight = Flight.query.filter(
                    Flight.departure_airport_id == route.departure_airport_id,
                    Flight.arrival_airport_id == route.destination_airport_id
                ).order_by(Flight.scheduled_departure.desc()).first()
                
                # 更新統計數據
                route.flight_count_7days = flights_7d
                route.flight_count_30days = flights_30d
                route.last_flight_date = last_flight.scheduled_departure.date() if last_flight else None
                
                # 如果過去 30 天沒有航班，標記為非活躍
                if flights_30d == 0:
                    route.is_active = False
                
                updated_count += 1
            
            db.session.commit()
            print(f"  ✅ 更新 {updated_count} 條航線的統計數據")
            
        except Exception as e:
            print(f"  ❌ 更新航班統計失敗: {str(e)}")
            db.session.rollback()
    
    def cleanup_inactive_routes(self, days_threshold=90):
        """清理長期無航班的無效航線"""
        print(f"\n[{datetime.now()}] 開始清理無效航線...")
        
        try:
            threshold_date = date.today() - timedelta(days=days_threshold)
            
            # 查找長期無航班的航線
            inactive_routes = AirportDestination.query.filter(
                (AirportDestination.last_flight_date < threshold_date) |
                (AirportDestination.last_flight_date.is_(None) & 
                 AirportDestination.flight_count_30days == 0)
            ).all()
            
            deleted_count = 0
            for route in inactive_routes:
                print(f"  刪除無效航線: {route.departure_airport_id} -> {route.destination_airport_id}")
                db.session.delete(route)
                deleted_count += 1
            
            db.session.commit()
            print(f"  ✅ 清理 {deleted_count} 條無效航線")
            
        except Exception as e:
            print(f"  ❌ 清理無效航線失敗: {str(e)}")
            db.session.rollback()
    
    def cleanup_domestic_destinations(self):
        """清理已存在的台灣國內機場目的地記錄"""
        with self.app.app_context():
            print(f"\n[{datetime.now()}] 開始清理台灣國內機場目的地記錄...")
            
            try:
                # 台灣國內機場列表
                domestic_airports = [
                    'CMJ', 'CYI', 'GNI', 'KNH', 'KYD', 'LZN', 
                    'MFK', 'MZG', 'TNN', 'TTT', 'WOT'
                ]
                
                # 查找以台灣國內機場為目的地的記錄
                domestic_routes = AirportDestination.query.filter(
                    AirportDestination.destination_airport_id.in_(domestic_airports)
                ).all()
                
                deleted_count = 0
                for route in domestic_routes:
                    print(f"  刪除國內目的地: {route.departure_airport_id} -> {route.destination_airport_id}")
                    db.session.delete(route)
                    deleted_count += 1
                
                db.session.commit()
                print(f"  ✅ 清理 {deleted_count} 條國內目的地記錄")
                
            except Exception as e:
                print(f"  ❌ 清理國內目的地記錄失敗: {str(e)}")
                db.session.rollback()

def main():
    """主函數"""
    syncer = AirportDestinationSyncer()
    
    # 清理現有的台灣國內機場目的地記錄
    syncer.cleanup_domestic_destinations()
    
    # 同步台灣國際機場的目的地（現在會自動過濾國內機場）
    syncer.sync_all_destinations()
    
    # 清理無效航線 (可選)
    # syncer.cleanup_inactive_routes()

if __name__ == "__main__":
    main() 