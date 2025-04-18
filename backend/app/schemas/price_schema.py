from marshmallow import Schema, fields, validate, ValidationError, validates_schema

class TicketPriceByFlightArgsSchema(Schema):
    class_type = fields.Str(required=False, load_default='經濟', validate=validate.OneOf(['經濟', '商務', '頭等']), metadata={"description": "艙位等級"})

class LowestPricesArgsSchema(Schema):
    departure = fields.Str(required=True, error_messages={'required': '必須提供出發機場代碼'})
    arrival = fields.Str(required=True, error_messages={'required': '必須提供到達機場代碼'})
    start_date = fields.Date(required=True, format='%Y-%m-%d', error_messages={'required': '必須提供開始日期', 'invalid': '日期格式錯誤，請使用 YYYY-MM-DD'})
    end_date = fields.Date(required=False, format='%Y-%m-%d', allow_none=True, error_messages={'invalid': '日期格式錯誤，請使用 YYYY-MM-DD'})

    @validates_schema
    def validate_dates(self, data, **kwargs):
        if data.get('end_date') and data['start_date'] > data['end_date']:
            raise ValidationError('結束日期不能早於開始日期', ['end_date'])

class PriceHistoryArgsSchema(Schema):
    class_type = fields.Str(required=False, load_default='經濟艙', validate=validate.OneOf(['經濟艙', '商務艙', '頭等艙']), metadata={"description": "艙位等級"})
    days = fields.Int(required=False, load_default=30, validate=validate.Range(min=1), error_messages={'invalid': '天數必須是正整數'})

class PriceAnalysisArgsSchema(Schema):
    class_type = fields.Str(required=False, load_default='經濟艙', validate=validate.OneOf(['經濟艙', '商務艙', '頭等艙']), metadata={"description": "艙位等級"})

# 導出 Schema 實例
ticket_price_by_flight_args_schema = TicketPriceByFlightArgsSchema()
lowest_prices_args_schema = LowestPricesArgsSchema()
price_history_args_schema = PriceHistoryArgsSchema()
price_analysis_args_schema = PriceAnalysisArgsSchema() 