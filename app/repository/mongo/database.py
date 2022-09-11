import asyncio
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Tuple

from bson import Decimal128
from bson.codec_options import CodecOptions, TypeCodec, TypeRegistry
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from pymongo.database import Database

from app.config.app import settings


class DateCodec(TypeCodec):
    python_type = date
    bson_type = datetime

    def transform_python(self, value: date) -> datetime:
        return datetime(
            year=value.year,
            month=value.month,
            day=value.day,
        ).replace(tzinfo=timezone.utc)

    def transform_bson(self, value: datetime) -> datetime:
        return value


class DecimalCodec(TypeCodec):
    python_type = Decimal
    bson_type = Decimal128

    def transform_python(self, value: Decimal) -> Decimal128:
        return Decimal128(str(value))

    def transform_bson(self, value: Decimal128) -> Decimal:
        return value.to_decimal()


def create_mongo_client_db() -> Tuple[MongoClient, Database]:
    client: MongoClient = AsyncIOMotorClient(settings.mongo.connection_uri)
    client.get_io_loop = asyncio.get_event_loop
    type_registry = TypeRegistry([DecimalCodec(), DateCodec()])
    codec_options = CodecOptions(type_registry=type_registry, tz_aware=True, tzinfo=timezone.utc)
    default_db = client.get_default_database(codec_options=codec_options)

    return client, default_db


mongo_client, default_database = create_mongo_client_db()
