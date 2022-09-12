import asyncio
import typing
from datetime import date, datetime, timezone
from decimal import Decimal
from functools import partial
from typing import Tuple

from bson import Decimal128
from bson.codec_options import CodecOptions, TypeCodec, TypeRegistry
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient, ReturnDocument
from pymongo.database import Database

from app.config.app import settings
from app.domain.hook import HookBaseDomain, OID
from app.repository.utils import split_key_and_values, fill_audit

E = typing.TypeVar("E", bound=HookBaseDomain)


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


def from_mongo(entity_cls: typing.Type[E], document: dict) -> E:
    data_copy = dict(document)
    document_id = data_copy.pop("id", None)
    document_id = data_copy.pop("_id", document_id)
    return entity_cls(**data_copy, id=OID(document_id))


async def exists(key_filter, get_collection_name: typing.Callable):
    return await default_database[get_collection_name()].count_documents(key_filter) > 0


async def upsert(entity: E, get_collection_name: typing.Callable) -> E:
    key_filter, dict_entity = split_key_and_values(entity, {"exclude_unset": True})
    exists_rec = partial(exists, key_filter=key_filter, get_collection_name=get_collection_name)
    dict_entity = await fill_audit(dict_entity, exists_rec)

    updated = await default_database[get_collection_name()].find_one_and_update(
        key_filter, {"$set": dict_entity}, upsert=True, return_document=ReturnDocument.AFTER
    )

    return from_mongo(type(entity), updated) if updated else None