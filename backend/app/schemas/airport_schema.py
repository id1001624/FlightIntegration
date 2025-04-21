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
    # 恢復 attribute 映射
    code = fields.Str(attribute="airport_id") # 映射回 airport_id
    name = fields.Str(attribute="name_zh")    # 映射回 name_zh
    city = fields.Str() # 保留 city
    country = fields.Str(allow_none=True) # 保留 country，允許為空
    terminal = fields.Str(allow_none=True)
    time = fields.Str(allow_none=True) # 時間以 ISO 格式字符串表示

airport_schema = AirportSchema()
airports_schema = AirportSchema(many=True)
airport_basic_schema = AirportBasicSchema()
airports_basic_schema = AirportBasicSchema(many=True) 