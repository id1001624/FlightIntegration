#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Flight Schema
"""
from marshmallow import Schema, fields, validate, ValidationError, validates_schema
from decimal import Decimal # 導入 Decimal
from .airline_schema import AirlineBasicSchema # 注意導入路徑
from .airport_schema import AirportBasicSchema # 注意導入路徑

# *** 新增: 定義用於嵌套的 PriceSchema ***
class PriceSchema(Schema):
    amount = fields.Float(allow_none=True)
    currency = fields.Str(load_default='TWD')
    cabin_class = fields.Str()
    isAvailable = fields.Boolean(dump_default=False)  # 將 default 參數更新為 dump_default

class FlightSearchArgsSchema(Schema):
    """航班搜索請求的參數驗證模型"""
    departure_code = fields.Str(required=True, validate=validate.Length(equal=3), metadata={"description": "出發機場IATA代碼"})
    arrival_code = fields.Str(required=True, validate=validate.Length(equal=3), metadata={"description": "抵達機場IATA代碼"})
    
    # 支持兩種日期參數格式 - 都設為非必需，在validates_schema中處理
    date = fields.Date(required=False, allow_none=True, metadata={"description": "出發日期 (YYYY-MM-DD)"})
    date_str = fields.Str(required=False, allow_none=True, metadata={"description": "出發日期字符串 (YYYY-MM-DD) - 前端格式"})
    
    # 支持兩種乘客數量參數格式 - 都設為非必需，在validates_schema中處理
    adults = fields.Int(required=False, load_default=1, validate=validate.Range(min=1), metadata={"description": "成人數量"})
    passengers = fields.Int(required=False, allow_none=True, validate=validate.Range(min=1), metadata={"description": "乘客數量 - 前端格式"})
    
    children = fields.Int(required=False, load_default=0, validate=validate.Range(min=0), metadata={"description": "兒童數量"})
    infants = fields.Int(required=False, load_default=0, validate=validate.Range(min=0), metadata={"description": "嬰兒數量"})
    travel_class = fields.Str(required=False, load_default=None, allow_none=True, metadata={"description": "艙等等級"})
    cabin_class = fields.Str(required=False, load_default='Economy', validate=validate.OneOf(['Economy', 'Premium_Economy', 'Business', 'First']), metadata={"description": "艙位等級 (Economy, Premium_Economy, Business, First)"})
    non_stop = fields.Bool(required=False, load_default=False, metadata={"description": "是否僅限直飛"})
    currency_code = fields.Str(required=False, load_default="TWD", metadata={"description": "貨幣代碼"})
    max_price = fields.Int(required=False, load_default=None, allow_none=True, metadata={"description": "最高價格"})
    
    # 支持兩種最大結果數量參數格式 - 都設為非必需，在validates_schema中處理
    max = fields.Int(required=False, load_default=250, metadata={"description": "返回結果的最大數量"})
    max_results = fields.Int(required=False, allow_none=True, validate=validate.Range(min=1), metadata={"description": "最大結果數量 - 前端格式"})

    @validates_schema
    def resolve_parameter_aliases(self, data, **kwargs):
        """解析參數別名，優先使用前端格式"""
        from datetime import datetime
        
        # 處理日期參數 - 優先使用 date_str，並轉換為 date 對象
        if 'date_str' in data and data['date_str']:
            try:
                # 將字符串轉換為 date 對象
                if isinstance(data['date_str'], str):
                    data['date'] = datetime.strptime(data['date_str'], '%Y-%m-%d').date()
                else:
                    data['date'] = data['date_str']
            except ValueError:
                raise ValidationError('日期格式錯誤，請使用 YYYY-MM-DD 格式', ['date_str'])
        elif 'date' not in data or not data['date']:
            raise ValidationError('必須提供出發日期 (date 或 date_str)', ['date', 'date_str'])
        
        # 處理乘客數量參數 - 優先使用 passengers
        if 'passengers' in data and data['passengers']:
            data['adults'] = data['passengers']
        elif 'adults' not in data or not data['adults']:
            data['adults'] = 1  # 預設值
        
        # 處理最大結果數量參數 - 優先使用 max_results  
        if 'max_results' in data and data['max_results']:
            data['max'] = data['max_results']
        elif 'max' not in data or not data['max']:
            data['max'] = 250  # 預設值
        
        return data

class FlightSchema(Schema):
    """用於序列化單個航班詳細信息"""
    flight_id = fields.UUID(dump_only=True)
    flight_number = fields.Str()
    scheduled_departure = fields.DateTime()
    scheduled_arrival = fields.DateTime()
    actual_departure = fields.DateTime(allow_none=True)
    actual_arrival = fields.DateTime(allow_none=True)
    departure_terminal = fields.Str(allow_none=True)
    arrival_terminal = fields.Str(allow_none=True)
    aircraft = fields.Str(allow_none=True)
    # 嵌套關聯對象的 Schema - **假設關聯名稱為 airline_rel, departure_airport_rel, arrival_airport_rel**
    # **您需要根據實際的 SQLAlchemy 模型關聯名稱調整 attribute 值**
    airline = fields.Nested(AirlineBasicSchema, attribute="airline_rel", dump_only=True)
    departure_airport = fields.Nested(AirportBasicSchema, attribute="departure_airport_rel", dump_only=True)
    arrival_airport = fields.Nested(AirportBasicSchema, attribute="arrival_airport_rel", dump_only=True)
    # 票價信息可能需要單獨的 Schema 或在此嵌套
    # prices = fields.Nested(PriceSchema, many=True, attribute="prices_rel")
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

# *** 修改: 更新 FlightSearchResultSchema 以匹配新的嵌套結構 ***
class FlightSearchResultSchema(Schema):
    """用於序列化航班搜索結果列表中的單個航班"""
    flight_id = fields.UUID(dump_only=True)
    flight_number = fields.Str()
    aircraft = fields.Str(allow_none=True)
    duration_minutes = fields.Int(allow_none=True)
    available_seats = fields.Int(allow_none=True)
    price_updated_at = fields.String(allow_none=True)
    
    # 嵌套字段
    airline = fields.Nested(AirlineBasicSchema, dump_only=True) # 保持不變
    price = fields.Nested(PriceSchema, dump_only=True)         # 使用新的 PriceSchema
    departure = fields.Nested(AirportBasicSchema, dump_only=True) # 使用更新後的 AirportBasicSchema
    arrival = fields.Nested(AirportBasicSchema, dump_only=True)   # 使用更新後的 AirportBasicSchema
    
    # 移除舊的、現在已嵌套的字段
    # scheduled_departure = fields.String(attribute="departure_time", allow_none=True)
    # scheduled_arrival = fields.String(attribute="arrival_time", allow_none=True)
    # departure_terminal = fields.Str(allow_none=True)
    # arrival_terminal = fields.Str(allow_none=True)
    # departure_airport = fields.Nested(AirportBasicSchema, dump_only=True)
    # arrival_airport = fields.Nested(AirportBasicSchema, dump_only=True)
    # price = fields.Float(allow_none=True)
    # cabin_class = fields.Str(allow_none=True)

# --- 新增用於 /from_taiwan 端點的請求參數 Schema ---
class FlightsFromTaiwanArgsSchema(Schema):
    date = fields.Date(required=True, format='%Y-%m-%d', error_messages={'required': '必須提供出發日期', 'invalid': '日期格式錯誤，請使用 YYYY-MM-DD'})
    airlines = fields.List(fields.String(), required=False, load_default=None, metadata={"description": "航空公司代碼列表 (e.g., 'CI,BR')"})
    price_min = fields.Float(required=False, load_default=None, validate=validate.Range(min=0), metadata={"description": "最低價格"})
    price_max = fields.Float(required=False, load_default=None, validate=validate.Range(min=0), metadata={"description": "最高價格"})
    cabin_class = fields.String(required=False, load_default='Economy', validate=validate.OneOf(['Economy', 'Business', 'First']), metadata={"description": "艙位等級 (Economy, Business, First)"})
    adults = fields.Int(required=False, load_default=1, validate=validate.Range(min=1), metadata={"description": "成人乘客數量"})
    max_results = fields.Int(required=False, load_default=20, validate=validate.Range(min=1), metadata={"description": "最大結果數量"})
    sort_by = fields.String(required=False, load_default='price', validate=validate.OneOf(['price', 'duration', 'departure_time', 'arrival_time']), metadata={"description": "排序依據"})
    only_target_airlines = fields.Boolean(required=False, load_default=True, metadata={"description": "是否僅顯示目標航空公司"})

    @validates_schema
    def validate_prices(self, data, **kwargs):
        if data.get('price_min') is not None and data.get('price_max') is not None and data['price_min'] > data['price_max']:
            raise ValidationError('最低價格不能高於最高價格', ['price_min', 'price_max'])

# --- 新增用於 /status 端點的響應 Schema ---
class FlightStatusSchema(Schema):
    status = fields.String(allow_none=True, metadata={"description": "航班狀態 (中文)"})
    status_en = fields.String(allow_none=True, metadata={"description": "航班狀態 (英文)"})
    actual_departure_time = fields.DateTime(allow_none=True, metadata={"description": "實際起飛時間"})
    actual_arrival_time = fields.DateTime(allow_none=True, metadata={"description": "實際到達時間"})
    gate = fields.String(allow_none=True, metadata={"description": "登機門"})
    terminal = fields.String(allow_none=True, metadata={"description": "航廈"})
    source = fields.String(required=True, metadata={"description": "狀態來源 (e.g., FlightStats)"})
    retrieved_at = fields.DateTime(required=True, metadata={"description": "狀態獲取時間"})

# --- 新增用於 /sync-taiwan-flights 端點的請求體 Schema ---
class SyncTaiwanFlightsArgsSchema(Schema):
    date = fields.Date(required=True, format='%Y-%m-%d', error_messages={'required': '必須提供日期', 'invalid': '日期格式錯誤，請使用 YYYY-MM-DD'})
    days = fields.Int(required=False, load_default=1, validate=validate.Range(min=1), error_messages={'invalid': '天數必須是有效的正整數'})

# --- 新增用於 /generate-test-data 端點的請求體 Schema ---
class GenerateTestDataArgsSchema(Schema):
    departure = fields.Str(required=True, error_messages={'required': '必須提供出發機場代碼'})
    arrival = fields.Str(required=True, error_messages={'required': '必須提供到達機場代碼'})
    start_date = fields.Date(required=True, format='%Y-%m-%d', error_messages={'required': '必須提供開始日期', 'invalid': '日期格式錯誤，請使用 YYYY-MM-DD'})
    num_days = fields.Int(required=False, load_default=30, validate=validate.Range(min=1), error_messages={'invalid': '天數必須是有效的正整數'})
    flights_per_day = fields.Int(required=False, load_default=5, validate=validate.Range(min=1), error_messages={'invalid': '每日航班數必須是有效的正整數'})

# --- 導出 Schema 實例 ---
flight_search_args_schema = FlightSearchArgsSchema()
flights_search_result_schema = FlightSearchResultSchema(many=True)
flight_schema = FlightSchema()
flights_from_taiwan_args_schema = FlightsFromTaiwanArgsSchema()
flight_status_schema = FlightStatusSchema()
sync_taiwan_flights_args_schema = SyncTaiwanFlightsArgsSchema()
generate_test_data_args_schema = GenerateTestDataArgsSchema()

airport_basic_schema = AirportBasicSchema()
airports_basic_schema = AirportBasicSchema(many=True) 