from marshmallow import Schema, fields

class AirlineSchema(Schema):
    id = fields.Str(attribute="airline_id", dump_only=True)
    code = fields.Str(attribute="airline_id") # API 中常用 code
    name_zh = fields.Str()
    name_en = fields.Str()
    is_domestic = fields.Bool()
    # 根據需要添加 website, contact_phone
    # dump_only=True

class AirlineBasicSchema(Schema):
     """用於篩選等簡化場景"""
     id = fields.Str(attribute="airline_id")
     code = fields.Str(attribute="airline_id")
     name_zh = fields.Str()
     name_en = fields.Str()
     is_target = fields.Bool(dump_only=True) # 由控制器添加的標記

airline_schema = AirlineSchema()
airlines_schema = AirlineSchema(many=True)
airline_basic_schema = AirlineBasicSchema()
airlines_basic_schema = AirlineBasicSchema(many=True) 