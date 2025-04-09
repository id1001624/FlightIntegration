"""
航班模型
"""
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from datetime import datetime, timedelta
from .base import db, Base

class Flight(Base):
    """航班數據模型"""
    __tablename__ = 'flights'
    
    flight_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    flight_number = db.Column(db.String, nullable=False)
    airline_id = db.Column(db.String, db.ForeignKey('airlines.airline_id'), nullable=False)
    departure_airport_id = db.Column(db.String, db.ForeignKey('airports.airport_id'), nullable=False)
    arrival_airport_id = db.Column(db.String, db.ForeignKey('airports.airport_id'), nullable=False)
    scheduled_departure = db.Column(db.DateTime(timezone=True), nullable=False)
    scheduled_arrival = db.Column(db.DateTime(timezone=True), nullable=False)
    status = db.Column(db.String)
    is_delayed = db.Column(db.Boolean, default=False)  # 是否延誤
    
    # 保留的欄位
    terminal = db.Column(db.String, nullable=True)  # 航廈資訊
    gate = db.Column(db.String, nullable=True)      # 登機門資訊
    
    # 使用應用程式所在時區的當前時間，而非UTC時間
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, nullable=True)
    
    # 關聯
    ticket_prices = db.relationship('TicketPrice', backref='flight', lazy='dynamic', cascade='all, delete-orphan')
    price_history = db.relationship('PriceHistory', backref='flight', lazy='dynamic', cascade='all, delete-orphan')
    
    # 狀態常量
    STATUS_ON_TIME = "準時"
    STATUS_DELAYED = "延誤"
    STATUS_CANCELLED = "取消"
    STATUS_DEPARTED = "已起飛"
    STATUS_ARRIVED = "已抵達"
    
    def __repr__(self):
        return f"<Flight {self.flight_number} {self.scheduled_departure.strftime('%Y-%m-%d %H:%M')}>"
    
    @property
    def duration(self):
        """計算航班持續時間"""
        if self.scheduled_departure and self.scheduled_arrival:
            return self.scheduled_arrival - self.scheduled_departure
        return None
    
    @property
    def is_domestic(self):
        """檢查是否為國內航班"""
        # 此處簡單判斷，可能需要根據實際情況調整
        return (self.departure_airport.country == 'Taiwan' or 
                self.arrival_airport.country == 'Taiwan')
                
    def update_status(self):
        """
        根據當前時間和航班計劃時間更新航班狀態
        
        邏輯：
        1. 如果 is_delayed 為真，狀態設為「延誤」
        2. 當前時間超過計劃降落時間，狀態設為「已抵達」
        3. 當前時間超過計劃起飛時間，狀態設為「已起飛」
        4. 其他情況，狀態保持「準時」
        
        注意：如需更精確的狀態判斷，建議通過API獲取實時資料
        """
        now = datetime.now()
        
        # 如果手動標記為延誤
        if self.is_delayed:
            self.status = self.STATUS_DELAYED
            return
            
        # 根據當前時間判斷狀態
        if now > self.scheduled_arrival:
            self.status = self.STATUS_ARRIVED
        elif now > self.scheduled_departure:
            self.status = self.STATUS_DEPARTED
        else:
            self.status = self.STATUS_ON_TIME
    
    @classmethod
    def search_flights(cls, departure_airport_id, arrival_airport_id, 
                      departure_date, return_date=None, airline_id=None):
        """
        搜索符合條件的航班
        
        Args:
            departure_airport_id: 出發機場ID
            arrival_airport_id: 到達機場ID
            departure_date: 出發日期 (datetime.date)
            return_date: 返回日期 (datetime.date, 可選)
            airline_id: 航空公司ID (可選)
            
        Returns:
            outbound_flights: 去程航班
            return_flights: 回程航班 (如果指定了return_date)
        """
        # 設置日期範圍
        departure_start = datetime.combine(departure_date, datetime.min.time())
        departure_end = datetime.combine(departure_date, datetime.max.time())
        
        # 基本查詢
        query = cls.query.filter(
            cls.departure_airport_id == departure_airport_id,
            cls.arrival_airport_id == arrival_airport_id,
            cls.scheduled_departure >= departure_start,
            cls.scheduled_departure <= departure_end
        )
        
        # 如果指定了航空公司，添加過濾條件
        if airline_id:
            query = query.filter(cls.airline_id == airline_id)
        
        outbound_flights = query.order_by(cls.scheduled_departure).all()
        
        # 更新所有航班的狀態
        for flight in outbound_flights:
            flight.update_status()
        
        # 如果指定了返回日期，查詢返回航班
        if return_date:
            return_start = datetime.combine(return_date, datetime.min.time())
            return_end = datetime.combine(return_date, datetime.max.time())
            
            return_query = cls.query.filter(
                cls.departure_airport_id == arrival_airport_id,  # 注意這裡是相反的
                cls.arrival_airport_id == departure_airport_id,
                cls.scheduled_departure >= return_start,
                cls.scheduled_departure <= return_end
            )
            
            if airline_id:
                return_query = return_query.filter(cls.airline_id == airline_id)
                
            return_flights = return_query.order_by(cls.scheduled_departure).all()
            
            # 更新所有返程航班的狀態
            for flight in return_flights:
                flight.update_status()
                
            return outbound_flights, return_flights
        
        return outbound_flights 

    @classmethod
    def search(cls, departure_airport_id=None, arrival_airport_id=None, 
                departure_date=None, airline_id=None, is_test_data=False):
        """搜尋航班"""
        query = cls.query
        
        if hasattr(cls, 'is_test_data'):
            query = query.filter_by(is_test_data=is_test_data)
        
        if departure_airport_id:
            query = query.filter_by(departure_airport_id=departure_airport_id)
        
        if arrival_airport_id:
            query = query.filter_by(arrival_airport_id=arrival_airport_id)
        
        if departure_date:
            # 格式化字符串為日期對象
            if isinstance(departure_date, str):
                departure_date = datetime.strptime(departure_date, '%Y-%m-%d').date()
            
            # 查詢指定日期的航班
            query = query.filter(db.func.date(cls.scheduled_departure) == departure_date)
        
        if airline_id:
            query = query.filter_by(airline_id=airline_id)
        
        flights = query.all()
        
        # 更新所有航班的狀態
        for flight in flights:
            flight.update_status()
            
        return flights 