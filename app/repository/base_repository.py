import typing
from functools import partial
from typing import Type

from bson import ObjectId
from pymongo import ReturnDocument
from pymongo.results import InsertOneResult

from app.domain.hook import HookBaseDomain
from app.repository.mongo import database
from app.repository.mongo.database import default_database, from_mongo
from app.repository.utils import split_key_and_values, get_collection_name, fill_audit


E = typing.TypeVar("E", bound=HookBaseDomain)


def _set_document_id(document: dict):
    document_id = document.pop("id", None)

    if document_id and not document.get("_id", None):
        document["_id"] = document_id

    return document


async def create(entity: E) -> E:
    mongo_dict = await fill_audit(_set_document_id(entity.dict()))
    insert_result: InsertOneResult = await default_database[get_collection_name(entity)].insert_one(mongo_dict)
    document_id = insert_result.inserted_id
    inserted_document = {"_id": document_id, **mongo_dict}
    entity = from_mongo(type(entity), inserted_document)
    return entity


async def update(entity: E, return_as: Type[E] = None) -> E:
    key_filter, dict_entity = split_key_and_values(entity, {"exclude_unset": True})
    dict_entity = await fill_audit(dict_entity)

    updated = await default_database[get_collection_name(entity)].find_one_and_update(
        key_filter, {"$set": dict_entity}, return_document=ReturnDocument.AFTER
    )
    return from_mongo(type(entity) if not return_as else return_as, updated) if updated else None


async def find_by_key(entity: E, return_as: Type[E], skip: int = 0, limit: int = 100):
    key_filter, _ = split_key_and_values(entity)
    cursor = default_database[get_collection_name(entity)].find(key_filter, skip=skip, limit=limit)
    return [from_mongo(return_as, document) async for document in cursor]


async def find_first_by_key(entity: E, return_as: Type[E]):
    ret = await find_by_key(entity, return_as, 0, 0)
    return ret[0] if ret else None


async def find_by_example(entity: E, return_as: Type[E], skip: int = 0, limit: int = 100):
    key_filter = entity.dict(exclude_defaults=True, exclude_none=True, exclude_unset=True)

    limits = {"skip": skip, "limit": limit}

    if limit <= 0:
        limits = {}

    entity_id = key_filter.pop("id", None)

    if entity_id:
        key_filter["_id"] = ObjectId(entity_id) if type(entity_id) == str else entity_id

    cursor = default_database[get_collection_name(entity)].find(key_filter, **limits)
    return [from_mongo(return_as, document) async for document in cursor]


async def _get_collection(entity):
    return default_database[get_collection_name(entity)]


async def upsert(entity: E) -> E:
    return await database.upsert(entity, partial(get_collection_name, entity=entity))


async def replace(entity: E) -> E:
    key_filter, dict_entity = split_key_and_values(entity)
    dict_entity = await fill_audit(dict_entity, False)

    replaced = await default_database[get_collection_name(entity)].find_one_and_replace(
        key_filter, {**key_filter, **dict_entity}, upsert=True, return_document=ReturnDocument.AFTER
    )

    return from_mongo(type(entity), replaced) if replaced else None


async def delete_by_key(entity: E, return_as: Type[E]):
    key_filter, _ = split_key_and_values(entity)
    ret = await default_database[get_collection_name(entity)].find_one_and_delete(key_filter)

    return from_mongo(return_as, ret) if ret else None
