import json
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

from bson import ObjectId

INFINITY = datetime.max.replace(tzinfo=timezone.utc)


def utcnow():
    return datetime.utcnow().replace(tzinfo=timezone.utc)


def encode_datetime(dt: datetime):
    return dt.replace(tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def encode_object_id(oid: ObjectId):
    return str(oid)


def get_meta(entity: Any, attribute: str, raise_exc: bool = True):
    if hasattr(entity, "Meta") and hasattr(entity.Meta, attribute):
        return getattr(entity.Meta, attribute)

    if raise_exc:
        raise TypeError(f"A entidade {type(entity)} não possui o meta: {attribute}")

    return None


class JsonEncoders(json.JSONEncoder):
    def default(self, o):
        types = (Decimal, date)
        if isinstance(o, datetime):
            return encode_datetime(o)
        return str(o) if isinstance(o, types) else super(JsonEncoders, self).default(o)


def encode_str(s: str) -> bytes:
    return s.encode("utf-8")

