#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
票價模型 - 用於價格歷史記錄和短期緩存
注意：此模型不再用於存儲所有實時 API 價格數據，而是用於：
1. 用戶搜索歷史的價格快照
2. 熱門路線的短期價格緩存（1-4小時）
3. 價格趨勢分析的歷史數據
"""
import logging
from datetime import datetime, timedelta
from uuid import uuid4
from .base import db, Base
from typing import Optional

logger = logging.getLogger(__name__)

class TicketPrice(Base):
    """票價模型 - 支援 Amadeus API 完整數據結構"""
    __tablename__ = 'ticket_prices'
    
    # === 基本欄位 ===
    price_id = db.Column(db.String, primary_key=True, default=lambda: str(uuid4()))
    flight_id = db.Column(db.String, db.ForeignKey('flights.flight_id'), nullable=True)  # 改為可空，因為緩存記錄可能沒有對應航班
    
    # === 緩存相關欄位 ===
    origin_airport_code = db.Column(db.String(3), nullable=True)      # 新增：出發機場代碼
    destination_airport_code = db.Column(db.String(3), nullable=True) # 新增：到達機場代碼
    departure_date = db.Column(db.Date, nullable=True)                # 新增：出發日期
    is_cached = db.Column(db.Boolean, default=False)                  # 新增：是否為緩存記錄
    cache_expires_at = db.Column(db.DateTime, nullable=True)          # 新增：緩存過期時間
    search_key = db.Column(db.String, nullable=True)                  # 新增：搜索鍵值（用於快速查找）
    cabin_class = db.Column(db.String, nullable=True, default='ECONOMY') # 新增：艙等
    
    # === 艙等價格 ===
    economy_price = db.Column(db.Float, nullable=True)
    premium_economy_price = db.Column(db.Float, nullable=True)  # 新增：豪華經濟艙
    business_price = db.Column(db.Float, nullable=True)
    first_price = db.Column(db.Float, nullable=True)
    
    # === 座位數量 ===
    economy_seats = db.Column(db.Integer, nullable=True)        # 新增：經濟艙座位
    premium_economy_seats = db.Column(db.Integer, nullable=True) # 新增：豪華經濟艙座位
    business_seats = db.Column(db.Integer, nullable=True)       # 新增：商務艙座位
    first_seats = db.Column(db.Integer, nullable=True)          # 新增：頭等艙座位
    available_seats = db.Column(db.Integer, nullable=True)      # 保留：總可用座位數
    
    # === 價格詳細資訊 ===
    currency = db.Column(db.String(3), nullable=True, default='TWD')  # 新增：幣別
    base_price = db.Column(db.Float, nullable=True)                   # 新增：基本票價（不含稅費）
    total_price = db.Column(db.Float, nullable=True)                  # 新增：總價（含稅費）
    taxes_and_fees = db.Column(db.Float, nullable=True)               # 新增：稅費
    
    # === Amadeus 特定欄位 ===
    amadeus_offer_id = db.Column(db.String, nullable=True)            # 新增：Amadeus報價ID
    fare_type = db.Column(db.String, nullable=True)                   # 新增：票價類型（PUBLISHED等）
    instant_ticketing_required = db.Column(db.Boolean, default=False)  # 新增：是否需要即時出票
    last_ticketing_date = db.Column(db.Date, nullable=True)           # 新增：最後出票日期
    number_of_bookable_seats = db.Column(db.Integer, nullable=True)   # 新增：可預訂座位數（通常最多顯示9）
    
    # === 額外服務費用 ===
    checked_bags_fee = db.Column(db.Float, nullable=True)             # 新增：托運行李費
    seat_selection_fee = db.Column(db.Float, nullable=True)           # 新增：選位費
    
    # === 系統欄位 ===
    price_updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_test_data = db.Column(db.Boolean, default=False)               # 保留：用於區分測試數據
    data_source = db.Column(db.String, nullable=True, default='amadeus') # 新增：數據來源標識
    
    # === 關聯 ===
    flight = db.relationship('Flight', back_populates='ticket_prices')
    price_history = db.relationship('PriceHistory', back_populates='ticket_price_snapshot', cascade='all, delete-orphan')
    
    __table_args__ = (
        db.Index('idx_cache_lookup', 'origin_airport_code', 'destination_airport_code', 'departure_date', 'is_cached'),
        db.Index('idx_cache_expires', 'cache_expires_at'),
        db.Index('idx_search_key', 'search_key'),
    )
    
    def __repr__(self):
        return f'<TicketPrice {self.price_id}: Flight {self.flight_id}>'
    
    def to_dict(self):
        """轉換為字典格式，便於API返回"""
        return {
            'price_id': self.price_id,
            'flight_id': self.flight_id,
            'currency': self.currency,
            'prices': {
                'economy': self.economy_price,
                'premium_economy': self.premium_economy_price,
                'business': self.business_price,
                'first': self.first_price,
                'base': self.base_price,
                'total': self.total_price,
                'taxes_and_fees': self.taxes_and_fees
            },
            'seats': {
                'economy': self.economy_seats,
                'premium_economy': self.premium_economy_seats,
                'business': self.business_seats,
                'first': self.first_seats,
                'total_available': self.available_seats,
                'bookable': self.number_of_bookable_seats
            },
            'additional_fees': {
                'checked_bags': self.checked_bags_fee,
                'seat_selection': self.seat_selection_fee
            },
            'amadeus_info': {
                'offer_id': self.amadeus_offer_id,
                'fare_type': self.fare_type,
                'instant_ticketing_required': self.instant_ticketing_required,
                'last_ticketing_date': self.last_ticketing_date.isoformat() if self.last_ticketing_date else None
            },
            'cache_info': {
                'is_cached': self.is_cached,
                'cache_expires_at': self.cache_expires_at.isoformat() if self.cache_expires_at else None,
                'cabin_class': self.cabin_class
            },
            'metadata': {
                'updated_at': self.price_updated_at.isoformat() if self.price_updated_at else None,
                'is_test_data': self.is_test_data,
                'data_source': self.data_source
            }
        }

    @classmethod
    def get_by_flight_id(cls, flight_id):
        return cls.query.filter_by(flight_id=flight_id).first()
    
    @classmethod
    def get_lowest_price_for_flight(cls, flight_id: str) -> Optional[float]:
        """獲取指定航班的最低可用票價 (從四個艙等中選取)"""
        price_entry = cls.query.filter_by(flight_id=flight_id).first()
        if not price_entry:
            return None
        
        prices = []
        if price_entry.economy_price is not None:
            prices.append(price_entry.economy_price)
        if price_entry.premium_economy_price is not None:
            prices.append(price_entry.premium_economy_price)
        if price_entry.business_price is not None:
            prices.append(price_entry.business_price)
        if price_entry.first_price is not None:
            prices.append(price_entry.first_price)
            
        return min(prices) if prices else None

    @classmethod
    def get_lowest_price(cls, departure_airport_id, arrival_airport_id, date, cabin_preference: Optional[str] = None):
        """獲取指定航線和日期的最低票價，可選艙等偏好"""
        from .flight import Flight  # 在方法內導入避免循環導入
        query = db.session.query(cls).join(Flight).filter(
            Flight.departure_airport_id == departure_airport_id,
            Flight.arrival_airport_id == arrival_airport_id,
            db.func.date(Flight.scheduled_departure) == date
        )

        flights_prices = query.all()
        if not flights_prices:
            return None

        lowest_overall_price = float('inf')
        
        for price_entry in flights_prices:
            current_flight_prices = []
            if cabin_preference == 'economy' or cabin_preference is None:
                if price_entry.economy_price is not None: current_flight_prices.append(price_entry.economy_price)
            if cabin_preference == 'premium_economy' or cabin_preference is None:
                if price_entry.premium_economy_price is not None: current_flight_prices.append(price_entry.premium_economy_price)
            if cabin_preference == 'business' or cabin_preference is None:
                if price_entry.business_price is not None: current_flight_prices.append(price_entry.business_price)
            if cabin_preference == 'first' or cabin_preference is None:
                if price_entry.first_price is not None: current_flight_prices.append(price_entry.first_price)
            
            if current_flight_prices:
                lowest_overall_price = min(lowest_overall_price, min(current_flight_prices))

        return lowest_overall_price if lowest_overall_price != float('inf') else None

    @classmethod
    def get_latest_price(cls, flight_id, is_test_data=False):
        """獲取最新的票價記錄 (現在一個 flight_id 只有一筆)"""
        query = cls.query.filter_by(flight_id=flight_id)
        if is_test_data is not None:
            query = query.filter_by(is_test_data=is_test_data)
        return query.order_by(cls.price_updated_at.desc()).first()
    
    @classmethod
    def save_search_result(cls, origin_code: str, destination_code: str, 
                         departure_date: datetime, price_data: dict, 
                         amadeus_offer_id: Optional[str] = None, cache_hours: int = 4):
        """
        保存搜索結果作為緩存
        
        Args:
            origin_code: 出發機場代碼
            destination_code: 到達機場代碼
            departure_date: 出發日期
            price_data: 價格數據字典
            amadeus_offer_id: Amadeus 報價 ID
            cache_hours: 緩存小時數
        """
        try:
            # 生成搜索鍵值
            search_key = f"{origin_code}_{destination_code}_{departure_date.strftime('%Y%m%d')}"
            
            # 檢查是否已存在相同的緩存記錄
            existing = cls.query.filter_by(
                origin_airport_code=origin_code,
                destination_airport_code=destination_code,
                departure_date=departure_date.date(),
                amadeus_offer_id=amadeus_offer_id,
                is_cached=True
            ).first()
            
            if existing:
                # 更新現有記錄
                for key, value in price_data.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
                existing.cache_expires_at = datetime.utcnow() + timedelta(hours=cache_hours)
                existing.price_updated_at = datetime.utcnow()
            else:
                # 創建新的緩存記錄
                cache_record = cls(
                    origin_airport_code=origin_code,
                    destination_airport_code=destination_code,
                    departure_date=departure_date.date(),
                    is_cached=True,
                    cache_expires_at=datetime.utcnow() + timedelta(hours=cache_hours),
                    search_key=search_key,
                    amadeus_offer_id=amadeus_offer_id,
                    data_source='amadeus',
                    **price_data
                )
                db.session.add(cache_record)
            
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"保存搜索結果緩存時發生錯誤：{e}")
            raise 