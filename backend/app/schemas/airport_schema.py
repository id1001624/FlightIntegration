from marshmallow import Schema, fields

class AirportSchema(Schema):
    id = fields.Str(attribute="airport_id", dump_only=True) # dump_only 因為通常不由客戶端提供
    code = fields.Str() # 移除屬性映射，讓它直接使用同名字段
    name_zh = fields.Str()
    name_en = fields.Str()
    city = fields.Str()
    city_en = fields.Str()
    country = fields.Str()
    timezone = fields.Str()
    # 根據需要添加 contact_info, website_url
    # dump_only=True 表示這些欄位只在序列化（輸出）時使用

class AirportBasicSchema(Schema):
    """用於下拉選單等簡化場景，以及嵌套在 FlightSearchResult 中"""
    # --- 修改：移除 attribute 映射，直接使用鍵名 ---
    code = fields.Str() # 直接使用 'code'
    name = fields.Str() # 直接使用 'name' (我們在 _format_flights 中會提供 'name_zh')
    # --- 結束修改 ---
    city = fields.Str()
    country = fields.Str(allow_none=True)
    terminal = fields.Str(allow_none=True)
    time = fields.Str(allow_none=True) # 時間以 ISO 格式字符串表示

airport_schema = AirportSchema()
airports_schema = AirportSchema(many=True)
airport_basic_schema = AirportBasicSchema()
airports_basic_schema = AirportBasicSchema(many=True) 