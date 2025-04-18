from marshmallow import Schema, fields, validate, ValidationError, validates_schema
from .airline_schema import AirlineBasicSchema # 注意導入路徑
from .airport_schema import AirportBasicSchema # 注意導入路徑

class FlightSearchArgsSchema(Schema):
    """用於驗證 /search 的請求參數"""
    departure = fields.Str(required=True, error_messages={'required': '缺少出發機場參數'})
    arrival = fields.Str(required=True, error_messages={'required': '缺少到達機場參數'})
    date = fields.Date(required=True, format='%Y-%m-%d', error_messages={'required': '缺少出發日期參數', 'invalid': '出發日期格式錯誤，請使用 YYYY-MM-DD'})
    return_date = fields.Date(format='%Y-%m-%d', allow_none=True, error_messages={'invalid': '返回日期格式錯誤，請使用 YYYY-MM-DD'})
    airlines = fields.List(fields.Str(), allow_none=True) # 允許不傳遞
    price_min = fields.Float(validate=validate.Range(min=0), allow_none=True)
    price_max = fields.Float(validate=validate.Range(min=0), allow_none=True)
    class_type = fields.Str(missing='經濟') # 默認值
    only_target_airlines = fields.Bool(missing=True) # 默認值
    passengers = fields.Int(validate=validate.Range(min=1), missing=1) # 默認值
    max_results = fields.Int(validate=validate.Range(min=1), missing=20) # 默認值
    sort_by = fields.Str(validate=validate.OneOf(['price', 'departure_time', 'arrival_time', 'duration']), missing='price') # 限制選項

    # 價格範圍驗證
    @validates_schema
    def validate_prices(self, data, **kwargs):
        if data.get('price_min') is not None and data.get('price_max') is not None:
            if data['price_min'] > data['price_max']:
                raise ValidationError('最低價格不能高於最高價格', ['price_min', 'price_max'])

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

class FlightSearchResultSchema(Schema):
    """用於序列化航班搜索結果列表中的單個航班"""
    flight_id = fields.UUID(dump_only=True)
    flight_number = fields.Str()
    scheduled_departure = fields.DateTime()
    scheduled_arrival = fields.DateTime()
    departure_terminal = fields.Str(allow_none=True)
    arrival_terminal = fields.Str(allow_none=True)
    # 嵌套基本信息即可 - **假設關聯名稱正確**
    airline = fields.Nested(AirlineBasicSchema, attribute="airline_rel", dump_only=True)
    departure_airport = fields.Nested(AirportBasicSchema, attribute="departure_airport_rel", dump_only=True)
    arrival_airport = fields.Nested(AirportBasicSchema, attribute="arrival_airport_rel", dump_only=True)
    # 可能需要最低票價
    lowest_price = fields.Float(allow_none=True) # 假設服務層會計算
    duration_minutes = fields.Int(allow_none=True) # 假設服務層會計算

flight_search_args_schema = FlightSearchArgsSchema()
flight_schema = FlightSchema()
flights_schema = FlightSchema(many=True)
flight_search_result_schema = FlightSearchResultSchema()
flights_search_result_schema = FlightSearchResultSchema(many=True) 