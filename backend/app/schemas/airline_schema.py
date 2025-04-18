from marshmallow import Schema, fields

class AirlineSchema(Schema):
    """航空公司 Schema"""
    id = fields.Int(dump_only=True)
    code = fields.Str()
    name_zh = fields.Str()
    name_en = fields.Str()
    logo_path = fields.Str()
    is_domestic = fields.Boolean()
    # 根據需要添加 website, contact_phone
    # dump_only=True

class AirlineBasicSchema(Schema):
    """簡化版航空公司 Schema，用於篩選"""
    code = fields.Str()
    name_zh = fields.Str()
    name_en = fields.Str()
    logo_path = fields.Str()
    is_domestic = fields.Boolean()
    is_target = fields.Bool(dump_only=True) # 由控制器添加的標記

airline_schema = AirlineSchema()
airlines_schema = AirlineSchema(many=True)
airline_basic_schema = AirlineBasicSchema()
airlines_basic_schema = AirlineBasicSchema(many=True) 