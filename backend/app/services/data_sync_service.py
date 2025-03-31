"""
數據同步服務模塊
處理與外部API的數據同步操作
"""
import requests
import json
from datetime import datetime, timedelta
from ..models import Airport, Airline, Flight, TicketPrice
from ..models.base import db
from flask import current_app
import logging

logger = logging.getLogger(__name__)

class DataSyncService:
    """
    數據同步服務
    負責從外部API獲取航班數據並同步到本地數據庫
    """
    
    @staticmethod
    def sync_airlines():
        """
        同步航空公司數據
        可以從TDX API或其他來源獲取
        
        Returns:
            dict: 同步結果統計
        """
        # 這裡只是模擬，實際環境中應該調用真實的API
        try:
            # 獲取配置的API密鑰
            client_id = current_app.config.get('TDX_CLIENT_ID')
            client_secret = current_app.config.get('TDX_CLIENT_SECRET')
            
            if not client_id or not client_secret:
                logger.error("缺少TDX API配置")
                return {"error": "缺少TDX API配置"}
            
            # 模擬API調用
            # url = "https://tdx.transportdata.tw/api/basic/v2/Air/Airline"
            # headers = {
            #     "Authorization": f"Bearer {DataSyncService._get_tdx_token(client_id, client_secret)}"
            # }
            # response = requests.get(url, headers=headers)
            # airlines_data = response.json()
            
            # 返回測試結果
            return {
                "status": "success",
                "message": "航空公司數據同步已模擬完成",
                "total": 0,
                "added": 0,
                "updated": 0,
                "skipped": 0
            }
            
        except Exception as e:
            logger.error(f"同步航空公司數據時出錯: {str(e)}")
            return {"error": f"同步過程中出錯: {str(e)}"}
    
    @staticmethod
    def sync_airports():
        """
        同步機場數據
        
        Returns:
            dict: 同步結果統計
        """
        # 這裡只是模擬，實際環境中應該調用真實的API
        try:
            # 獲取配置的API密鑰
            client_id = current_app.config.get('TDX_CLIENT_ID')
            client_secret = current_app.config.get('TDX_CLIENT_SECRET')
            
            if not client_id or not client_secret:
                logger.error("缺少TDX API配置")
                return {"error": "缺少TDX API配置"}
            
            # 模擬API調用
            # url = "https://tdx.transportdata.tw/api/basic/v2/Air/Airport"
            # headers = {
            #     "Authorization": f"Bearer {DataSyncService._get_tdx_token(client_id, client_secret)}"
            # }
            # response = requests.get(url, headers=headers)
            # airports_data = response.json()
            
            # 返回測試結果
            return {
                "status": "success",
                "message": "機場數據同步已模擬完成",
                "total": 0,
                "added": 0,
                "updated": 0,
                "skipped": 0
            }
            
        except Exception as e:
            logger.error(f"同步機場數據時出錯: {str(e)}")
            return {"error": f"同步過程中出錯: {str(e)}"}
    
    @staticmethod
    def sync_flights(departure_iata, arrival_iata, start_date, end_date=None):
        """
        同步特定航線的航班數據
        
        Args:
            departure_iata: 出發機場IATA代碼
            arrival_iata: 到達機場IATA代碼
            start_date: 開始日期
            end_date: 結束日期（可選，默認為開始日期後7天）
            
        Returns:
            dict: 同步結果統計
        """
        # 處理日期格式
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            
        if not end_date:
            end_date = start_date + timedelta(days=7)
        elif isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # 這裡只是模擬，實際環境中應該調用真實的API
        try:
            # 獲取配置的API密鑰
            client_id = current_app.config.get('TDX_CLIENT_ID')
            client_secret = current_app.config.get('TDX_CLIENT_SECRET')
            
            if not client_id or not client_secret:
                logger.error("缺少TDX API配置")
                return {"error": "缺少TDX API配置"}
            
            # 模擬API調用
            # url = f"https://tdx.transportdata.tw/api/basic/v2/Air/FIDS/Flight"
            # params = {
            #     "$filter": f"DepartureAirportID eq '{departure_iata}' and ArrivalAirportID eq '{arrival_iata}'",
            #     "date": start_date.strftime('%Y-%m-%d')
            # }
            # headers = {
            #     "Authorization": f"Bearer {DataSyncService._get_tdx_token(client_id, client_secret)}"
            # }
            # response = requests.get(url, params=params, headers=headers)
            # flights_data = response.json()
            
            # 返回測試結果
            return {
                "status": "success",
                "message": f"航班數據同步已模擬完成: {departure_iata}->{arrival_iata}",
                "total": 0,
                "added": 0,
                "updated": 0,
                "skipped": 0
            }
            
        except Exception as e:
            logger.error(f"同步航班數據時出錯: {str(e)}")
            return {"error": f"同步過程中出錯: {str(e)}"}
    
    @staticmethod
    def _get_tdx_token(client_id, client_secret):
        """
        獲取TDX API的訪問令牌
        
        Args:
            client_id: 客戶端ID
            client_secret: 客戶端密鑰
            
        Returns:
            str: 訪問令牌
        """
        try:
            url = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
            data = {
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret
            }
            
            response = requests.post(url, headers=headers, data=data)
            if response.status_code == 200:
                return response.json().get("access_token")
            else:
                logger.error(f"獲取TDX令牌失敗: {response.status_code} {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"獲取TDX令牌時出錯: {str(e)}")
            return None
            
    @staticmethod
    def generate_test_data(departure_iata, arrival_iata, start_date, num_days=30, num_flights_per_day=5):
        """
        生成測試數據
        
        Args:
            departure_iata: 出發機場IATA代碼
            arrival_iata: 到達機場IATA代碼
            start_date: 開始日期
            num_days: 生成的天數
            num_flights_per_day: 每天的航班數量
            
        Returns:
            dict: 生成結果統計
        """
        from ..models import Airport, Airline
        import random
        from uuid import uuid4
        
        # 處理日期格式
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            
        try:
            # 查詢機場
            departure_airport = Airport.get_by_iata(departure_iata)
            arrival_airport = Airport.get_by_iata(arrival_iata)
            
            if not departure_airport or not arrival_airport:
                return {"error": "找不到指定的機場"}
                
            # 查詢航空公司
            airlines = Airline.get_all()
            if not airlines:
                return {"error": "沒有航空公司數據"}
                
            # 生成航班數據
            flights_added = 0
            prices_added = 0
            
            for day in range(num_days):
                current_date = start_date + timedelta(days=day)
                
                for i in range(num_flights_per_day):
                    # 隨機選擇航空公司
                    airline = random.choice(airlines)
                    
                    # 生成起飛時間和到達時間
                    hours = random.randint(6, 22)
                    minutes = random.choice([0, 15, 30, 45])
                    departure_time = datetime.combine(current_date, datetime.min.time().replace(hour=hours, minute=minutes))
                    
                    # 根據機場間距離計算飛行時間（這裡假設為1-3小時）
                    flight_hours = random.uniform(1, 3)
                    arrival_time = departure_time + timedelta(hours=flight_hours)
                    
                    # 生成航班號
                    flight_number = f"{airline.iata_code}{random.randint(100, 999)}"
                    
                    # 創建航班記錄
                    flight = Flight(
                        flight_id=uuid4(),
                        flight_number=flight_number,
                        airline_id=airline.airline_id,
                        departure_airport_id=departure_airport.airport_id,
                        arrival_airport_id=arrival_airport.airport_id,
                        scheduled_departure=departure_time,
                        scheduled_arrival=arrival_time,
                        status="正常"
                    )
                    db.session.add(flight)
                    flights_added += 1
                    
                    # 創建票價記錄
                    for class_type, base_multiplier in [('經濟艙', 1), ('商務艙', 2.5), ('頭等艙', 4)]:
                        # 基礎票價根據航程距離和隨機因素計算
                        base_price = random.randint(2000, 8000) * base_multiplier
                        
                        # 可用座位數
                        available_seats = random.randint(0, 30) if class_type == '經濟艙' else random.randint(0, 10)
                        
                        ticket_price = TicketPrice(
                            price_id=uuid4(),
                            flight_id=flight.flight_id,
                            class_type=class_type,
                            base_price=base_price,
                            available_seats=available_seats,
                            price_updated_at=datetime.utcnow()
                        )
                        db.session.add(ticket_price)
                        prices_added += 1
            
            # 提交到數據庫
            db.session.commit()
            
            return {
                "status": "success",
                "message": "測試數據生成成功",
                "flights_added": flights_added,
                "prices_added": prices_added
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"生成測試數據時出錯: {str(e)}")
            return {"error": f"生成過程中出錯: {str(e)}"} 