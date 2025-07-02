from marshmallow import Schema, fields, validate, ValidationError, validates_schema

class TicketPriceByFlightArgsSchema(Schema):
    cabin_preference = fields.Str(required=False, load_default='economy', 
                               validate=validate.OneOf(['economy', 'premium_economy', 'business', 'first', None]),
                               metadata={"description": "艙等偏好 (空值表示不指定)"})

class LowestPricesArgsSchema(Schema):
    departure = fields.Str(required=True, error_messages={'required': '必須提供出發機場代碼'})
    arrival = fields.Str(required=True, error_messages={'required': '必須提供到達機場代碼'})
    start_date = fields.Date(required=True, format='%Y-%m-%d', error_messages={'required': '必須提供開始日期', 'invalid': '日期格式錯誤，請使用 YYYY-MM-DD'})
    end_date = fields.Date(required=False, format='%Y-%m-%d', allow_none=True, error_messages={'invalid': '日期格式錯誤，請使用 YYYY-MM-DD'})
    cabin_preference = fields.Str(required=False, load_default=None, 
                               validate=validate.OneOf(['economy', 'premium_economy', 'business', 'first', None]),
                               metadata={"description": "艙等偏好 (空值表示比較所有艙等)"})

    @validates_schema
    def validate_dates(self, data, **kwargs):
        if data.get('end_date') and data['start_date'] > data['end_date']:
            raise ValidationError('結束日期不能早於開始日期', ['end_date'])

class PriceHistoryArgsSchema(Schema):
    cabin_info = fields.Str(required=False, load_default='economy_price', 
                          validate=validate.OneOf(['economy_price', 'premium_economy_price', 'business_price', 'first_price']),
                          metadata={"description": "價格欄位標識符"})
    days = fields.Int(required=False, load_default=30, validate=validate.Range(min=1), error_messages={'invalid': '天數必須是正整數'})

class PriceAnalysisArgsSchema(Schema):
    cabin_info = fields.Str(required=False, load_default='economy_price', 
                          validate=validate.OneOf(['economy_price', 'premium_economy_price', 'business_price', 'first_price']),
                          metadata={"description": "價格欄位標識符"})

# 導出 Schema 實例
ticket_price_by_flight_args_schema = TicketPriceByFlightArgsSchema()
lowest_prices_args_schema = LowestPricesArgsSchema()
price_history_args_schema = PriceHistoryArgsSchema()
price_analysis_args_schema = PriceAnalysisArgsSchema() 