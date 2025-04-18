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
    """用於下拉選單等簡化場景"""
    id = fields.Str(attribute="airport_id")
    code = fields.Str() # 移除屬性映射，讓它直接使用同名字段
    name = fields.Str() # 可能由 name_zh 或 name_en 組合
    city = fields.Str()

airport_schema = AirportSchema()
airports_schema = AirportSchema(many=True)
airport_basic_schema = AirportBasicSchema()
airports_basic_schema = AirportBasicSchema(many=True) 