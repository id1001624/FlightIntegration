"""
票價服務模塊
處理機票價格相關的業務邏輯
"""
from datetime import datetime, timedelta
# 從 ..database.db 導入異步連接池初始化函數
from ..database.db import init_asyncpg_pool 
from ..models import TicketPrice, Flight, Airline, PriceHistory
from ..models.base import db
from sqlalchemy import func, desc, exc as sqlalchemy_exc
from flask import current_app
import logging
import asyncpg # 確保導入 asyncpg

logger = logging.getLogger(__name__)

class PriceService:
    """
    票價服務
    處理票價查詢、分析和統計的邏輯
    """
    
    @staticmethod
    async def get_price_by_flight(flight_id, class_type=None):
        """
        獲取航班的票價信息 (使用 asyncpg)
        
        Args:
            flight_id: 航班ID
            class_type: 艙等類型（可選）
            
        Returns:
            list: 票價列表
        """
        pool = await init_asyncpg_pool() # 獲取連接池
        try:
            async with pool.acquire() as conn: # 從連接池獲取連接
                # 構建基礎查詢字符串
                base_query = """
                    SELECT class_type, economy_price, business_price, first_price, available_seats, price_updated_at
                    FROM ticket_prices
                    WHERE flight_id = $1
                """ # 修正: SQL 內容移到下一行並正確縮排
                
                params = [flight_id] # 參數列表
                query_string = base_query # 初始化查詢字符串
                
                # 如果提供了艙等，添加條件
                if class_type:
                    query_string += " AND class_type = $2" # 修正: 字串使用雙引號包覆
                    params.append(class_type)

                # 使用 conn.fetch 執行查詢
                results = await conn.fetch(query_string, *params) # 傳遞查詢字符串和參數
                prices = results

                return [{
                    'class_type': price['class_type'],
                    'price': float(self._get_price_for_class_type(price, price['class_type'])) if self._get_price_for_class_type(price, price['class_type']) is not None else None,
                    'available_seats': price['available_seats'],
                    'updated_at': price['price_updated_at'].isoformat() if price['price_updated_at'] else None
                } for price in prices]
        except asyncpg.PostgresError as pg_err: # 捕捉 asyncpg 錯誤
            logger.error(f"Error fetching price for flight {flight_id} using asyncpg: {pg_err}", exc_info=True)
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching price for flight {flight_id}: {e}", exc_info=True)
            return []
    
    @staticmethod
    def _get_price_for_class_type(price_record, class_type):
        """根據艙等類型獲取對應價格"""
        if class_type == '經濟':
            return price_record['economy_price']
        elif class_type == '商務':
            return price_record['business_price']
        elif class_type == '頭等':
            return price_record['first_price']
        return None
    
    @staticmethod
    async def get_prices_for_flights_batch(flight_ids: list[str]) -> dict[str, dict[str, dict]]:
        """
        批量獲取多個航班的所有艙位價格信息 (使用 asyncpg)。

        Args:
            flight_ids: 航班 ID 列表。

        Returns:
            一個字典，鍵是航班 ID (str)，值是另一個字典，
            其鍵是艙位類型 (str)，值是包含價格信息的字典。
            例如: {'flight_id1': {'經濟': {'amount': 100.0, ...}, '商務': {...}}, ...}
        """
        if not flight_ids:
            return {}

        prices_map = {}
        pool = await init_asyncpg_pool() # 獲取連接池
        try:
            async with pool.acquire() as conn: # 從連接池獲取連接
                # SQL 查詢字符串
                price_query_str = """
                SELECT flight_id, class_type, economy_price, business_price, first_price, available_seats, price_updated_at
                FROM ticket_prices
                WHERE flight_id = ANY($1::uuid[])
                """ # 修正: SQL 內容移到下一行並正確縮排
                
                # 直接傳遞 flight_ids 列表作為參數
                price_records = await conn.fetch(price_query_str, flight_ids)
                
                for record in price_records:
                    flight_id_str = str(record['flight_id']) # 確保轉換為字符串
                    cabin_class = record['class_type']
                    if flight_id_str not in prices_map:
                        prices_map[flight_id_str] = {}
                    
                    # 獲取對應艙等的價格
                    price_value = None
                    if cabin_class == '經濟':
                        price_value = record['economy_price']
                    elif cabin_class == '商務':
                        price_value = record['business_price']
                    elif cabin_class == '頭等':
                        price_value = record['first_price']
                    
                    prices_map[flight_id_str][cabin_class] = {
                        'amount': float(price_value) if price_value is not None else None,
                        'available_seats': record['available_seats'],
                        'cabin_class': cabin_class,
                        'updated_at': record['price_updated_at'].isoformat() if record['price_updated_at'] else None
                    }
                logger.info(f"批量獲取了 {len(flight_ids)} 個航班的 {len(price_records)} 條票價記錄")

        except asyncpg.PostgresError as pg_err: # 捕捉 asyncpg 特定錯誤
            logger.error(f"批量查詢票價時出錯: {pg_err}", exc_info=True)
        except Exception as e:
            logger.error(f"批量查詢票價時發生未知錯誤: {e}", exc_info=True)
            # 即使出錯，也可能返回部分獲取的數據
        
        return prices_map
    
    @staticmethod
    def get_lowest_prices(departure_iata, arrival_iata, start_date, end_date=None):
        """
        獲取指定日期範圍內的最低票價 (使用同步 SQLAlchemy Session)
        
        Args:
            departure_iata: 出發機場IATA代碼
            arrival_iata: 到達機場IATA代碼
            start_date: 開始日期
            end_date: 結束日期（可選，默認為開始日期後30天）
            
        Returns:
            dict: 日期和最低票價的映射
        """
        from ..models import Airport # Keep local import if only used here
        
        # 處理日期格式
        if isinstance(start_date, str):
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            except ValueError:
                logger.error(f"Invalid start_date format: {start_date}")
                return {"error": "Invalid start date format"}
            
        if end_date is None:
            end_date = start_date + timedelta(days=30)
        elif isinstance(end_date, str):
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                 logger.error(f"Invalid end_date format: {end_date}")
                 return {"error": "Invalid end date format"}
        elif not isinstance(end_date, datetime.date): # Check if it's a date object
             logger.error(f"Invalid end_date type: {type(end_date)}")
             return {"error": "Invalid end date type"}
            
        # 查詢機場ID (使用同步方法)
        # 注意：Airport.get_by_iata 需要是同步方法
        departure_airport = Airport.query.filter_by(airport_id=departure_iata).first()
        arrival_airport = Airport.query.filter_by(airport_id=arrival_iata).first()
        
        if not departure_airport or not arrival_airport:
            logger.warning(f"找不到機場: {departure_iata} 或 {arrival_iata}")
            return {"error": "找不到指定的機場"}
            
        # 構建SQL查詢 (使用同步 SQLAlchemy Session)
        try:
            logger.info(f"開始查詢最低票價: {departure_iata}->{arrival_iata} from {start_date} to {end_date}")
            results = db.session.query(
                func.date(Flight.scheduled_departure).label('flight_date'),
                func.min(TicketPrice.economy_price).label('min_price')
            ).join(
                TicketPrice, Flight.flight_id == TicketPrice.flight_id
            ).filter(
                Flight.departure_airport_id == departure_airport.airport_id,
                Flight.arrival_airport_id == arrival_airport.airport_id,
                func.date(Flight.scheduled_departure) >= start_date,
                func.date(Flight.scheduled_departure) <= end_date,
                TicketPrice.class_type == '經濟'  # 確保使用 '經濟' 而非 '經濟艙'
            ).group_by(
                func.date(Flight.scheduled_departure)
            ).order_by(
                'flight_date'
            ).all()
            logger.info(f"最低票價查詢完成，找到 {len(results)} 個日期的數據")
        except sqlalchemy_exc.SQLAlchemyError as db_err:
            logger.error(f"查詢最低票價時數據庫出錯: {db_err}", exc_info=True)
            db.session.rollback() # 回滾事務
            return {"error": "查詢最低票價時發生數據庫錯誤"}
        except Exception as e:
            logger.error(f"查詢最低票價時發生未知錯誤: {e}", exc_info=True)
            return {"error": "查詢最低票價時發生未知錯誤"}
        finally:
             # 同步方法不需要手動釋放連接池連接，但 session 需要處理
             # Flask-SQLAlchemy 通常會自動管理 session 的生命週期
             pass
        
        # 格式化結果
        price_map = {}
        for date_obj, price in results:
            if price is not None:
                price_map[date_obj.isoformat()] = float(price)
            
        return price_map
    
    @staticmethod
    def get_price_history(flight_id, class_type='經濟', days=30): # 改為 '經濟'
        """
        獲取航班的歷史票價 (使用同步 SQLAlchemy Session)
        
        Args:
            flight_id: 航班ID
            class_type: 艙等類型
            days: 歷史天數
            
        Returns:
            list: 歷史票價列表
        """
        # 計算時間範圍
        end_date = datetime.now() # 移除 UTC 以匹配 created_at (如果不是 UTC)
        start_date = end_date - timedelta(days=days)
        
        # 查詢歷史票價 (使用同步方法)
        try:
            logger.info(f"查詢航班 {flight_id} ({class_type}) 最近 {days} 天的歷史票價")
            history = PriceHistory.query.filter(
                PriceHistory.flight_id == flight_id,
                PriceHistory.class_type == class_type, # 使用傳入的 class_type
                PriceHistory.created_at >= start_date,
                PriceHistory.created_at <= end_date
            ).order_by(
                PriceHistory.created_at
            ).all()
            logger.info(f"找到 {len(history)} 條歷史票價記錄")
        except sqlalchemy_exc.SQLAlchemyError as db_err:
            logger.error(f"查詢歷史票價時數據庫出錯: {db_err}", exc_info=True)
            # 對於歷史數據查詢，可以選擇返回空列表而不是錯誤字典
            return []
        except Exception as e:
            logger.error(f"查詢歷史票價時發生未知錯誤: {e}", exc_info=True)
            return []
        finally:
            # 同步方法 session 會自動管理
             pass
        
        # 格式化結果
        return [{
            'date': record.created_at.isoformat(),
            'price': float(record.price) if record.price is not None else None
        } for record in history]
    
    @staticmethod
    def analyze_price_trend(flight_id, class_type='經濟'): # 改為 '經濟'
        """
        分析票價趨勢並提供購買建議 (使用同步方法)
        
        Args:
            flight_id: 航班ID
            class_type: 艙等類型
            
        Returns:
            dict: 分析結果
        """
        # 獲取歷史票價 (調用修改後的同步方法)
        history = PriceService.get_price_history(flight_id, class_type, days=60)
        
        if not history:
            return {
                "trend": "無法分析",
                "recommendation": "無足夠數據進行分析"
            }
            
        # 計算簡單趨勢
        prices = [item['price'] for item in history if item['price'] is not None] # 過濾 None 值
        
        if len(prices) < 3:
            return {
                "trend": "數據不足",
                "recommendation": "數據點不足，建議等待更多價格數據"
            }
            
        # 計算最近幾次價格變化趨勢
        recent_changes = []
        for i in range(len(prices) - 1):
            change = prices[i+1] - prices[i]
            recent_changes.append(change)
            
        # 計算平均變化
        if not recent_changes: # 如果只有一個有效價格
            avg_change = 0
        else:
            avg_change = sum(recent_changes) / len(recent_changes)
        
        # 當前價格與最低價格的比較
        current_price = prices[-1]
        min_price = min(prices)
        max_price = max(prices)
        
        price_range = max_price - min_price
        if price_range == 0:
            price_position = 0.5  # 如果價格沒有變化，設為中間位置
        else:
            price_position = (current_price - min_price) / price_range
            
        # 根據分析結果提供建議
        if avg_change > 0.01: # 添加一個閾值避免微小波動被判斷為趨勢
            trend = "上漲"
            if price_position < 0.3:
                recommendation = "價格趨勢上漲，但當前價格接近歷史最低點，建議購買"
            else:
                recommendation = "價格呈上漲趨勢，建議等待價格回落"
        elif avg_change < -0.01: # 添加一個閾值
            trend = "下跌"
            if price_position > 0.7:
                recommendation = "價格趨勢下跌，但當前價格仍然較高，建議等待"
            else:
                recommendation = "價格呈下跌趨勢，接近低點，可以考慮購買"
        else:
            trend = "穩定"
            if price_position < 0.4:
                recommendation = "價格穩定且接近歷史低點，適合購買"
            elif price_position > 0.8:
                recommendation = "價格穩定但接近歷史高點，建議等待"
            else:
                recommendation = "價格穩定在中間水平，可以考慮購買"
                
        return {
            "trend": trend,
            "recommendation": recommendation,
            "current_price": current_price,
            "min_price": min_price,
            "max_price": max_price,
            "avg_change": round(avg_change, 2)
        } 