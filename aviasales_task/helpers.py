import json
from typing import Dict, List

from aiohttp.web_exceptions import HTTPBadRequest
from marshmallow import Schema, ValidationError


def load_data(data, load_schema: Schema) -> Dict or List:
    try:
        return load_schema.load(data)
    except ValidationError as err:
        raise HTTPBadRequest(
            body=json.dumps(err.normalized_messages()),
            content_type="application/json",
        )
