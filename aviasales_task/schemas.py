import enum
import string
from typing import List

from marshmallow import Schema, fields, post_load, validate
from marshmallow.validate import OneOf


class Order(str, enum.Enum):
    price = "price"
    time = "time"
    optimal = "optimal"

    @classmethod
    def all(cls) -> List[str]:
        return [order for order in cls]


class FlightGetSchema(Schema):
    source = fields.Str(required=True, validate=[
        validate.Length(min=3, max=3),
        validate.ContainsOnly(string.ascii_letters)
    ])
    destination = fields.Str(required=True, validate=[
        validate.Length(min=3, max=3),
        validate.ContainsOnly(string.ascii_letters)
    ])
    adult = fields.Integer(missing=1, validate=validate.Range(min=1))
    child = fields.Integer(missing=0, validate=validate.Range(min=0))
    infant = fields.Integer(missing=0, validate=validate.Range(min=0))
    order_by = fields.Str(validate=OneOf(Order.all()), missing="price")
    reverse = fields.Bool(missing=False)
    with_return = fields.Bool(missing=False)

    @post_load
    def order_by_to_enum(self, data, **kwargs):
        data["order_by"] = Order(data["order_by"])
        return data

    @post_load()
    def source_upper(self, data, **kwargs):
        data["source"] = data["source"].upper()
        return data

    @post_load()
    def destination_upper(self, data, **kwargs):
        data["destination"] = data["destination"].upper()
        return data


class DiffGetSchema(Schema):
    use_extended_info = fields.Bool(missing=False)


class PriceSchema(Schema):
    adult = fields.Float()
    child = fields.Float()
    infant = fields.Float()
    currency = fields.Str()


class PathInformationSchema(Schema):
    source = fields.Str()
    destination = fields.Str()
    departure_time = fields.DateTime(format="%Y-%m-%d %H:%M")
    arrival_time = fields.DateTime(format="%Y-%m-%d %H:%M")


class FlightSchema(Schema):
    carrier_id = fields.Str()
    carrier_name = fields.Str()
    number = fields.Str()
    path_info = fields.Nested(nested=PathInformationSchema)
    klass = fields.Str(data_key="class")
    stops = fields.Int()
    fare_basis = fields.Str()
    ticket_type = fields.Str()


class RouteSchema(Schema):
    price = fields.Nested(PriceSchema)

    onward_info = fields.Nested(PathInformationSchema, allow_none=True)
    onward_flights = fields.List(fields.Nested(FlightSchema))
    onward_is_direct = fields.Bool()
    onward_time = fields.TimeDelta(precision=fields.TimeDelta.MINUTES)

    return_info = fields.Nested(PathInformationSchema, allow_none=True)
    return_flights = fields.List(fields.Nested(FlightSchema))
    return_is_direct = fields.Bool()
    return_time = fields.TimeDelta(precision=fields.TimeDelta.MINUTES)


flight_get_schema = FlightGetSchema()
diff_get_schema = DiffGetSchema()
routes_schema = RouteSchema(many=True)
