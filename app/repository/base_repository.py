import typing
from functools import partial
from typing import Tuple, Type

from bson import ObjectId
from pymongo import ReturnDocument
from pymongo.results import InsertOneResult

from app.domain.hook import HookBaseDomain, OID
from app.repository.mongo.database import default_database
from app.utils.misc import get_meta, utcnow


class RepositoryException(Exception):
    pass


E = typing.TypeVar("E", bound=HookBaseDomain)


def _set_document_id(document: dict):
    document_id = document.pop("id", None)

    if document_id and not document.get("_id", None):
        document["_id"] = document_id

    return document


def get_collection_name(entity: E) -> str:
    return get_meta(entity, "collection_name")


def _is_oid(value, key, type_hints):
    return isinstance(value, ObjectId) or type_hints.get(key, None) == OID


def split_key_and_values(entity: E, to_dict_opts: dict = None) -> Tuple[dict, dict]:
    key_filter = {}
    dict_entity = entity.dict(**to_dict_opts or {})
    key = get_meta(entity, "key", raise_exc=False)

    if not key:
        key = list(dict_entity.keys())

    type_hints = typing.get_type_hints(entity)

    for key_attr in key:
        key_filter[key_attr] = dict_entity.pop(key_attr)

        if not key_filter[key_attr]:
            raise RepositoryException(f"A chave não pode ter atributos nulos: {key_attr}")

        if _is_oid(key_filter[key_attr], key_attr, type_hints):
            value = key_filter.pop(key_attr)
            key_filter["_id"] = ObjectId(value) if type(value) == str else value

    return key_filter, dict_entity


def from_mongo(entity_cls: Type[E], document: dict) -> E:
    data_copy = dict(document)
    document_id = data_copy.pop("id", None)
    document_id = data_copy.pop("_id", document_id)
    return entity_cls(**data_copy, id=OID(document_id))


async def create(entity: E) -> E:
    mongo_dict = await _fill_audit(_set_document_id(entity.dict()))
    insert_result: InsertOneResult = await default_database[get_collection_name(entity)].insert_one(mongo_dict)
    document_id = insert_result.inserted_id
    inserted_document = {"_id": document_id, **mongo_dict}
    entity = from_mongo(type(entity), inserted_document)
    return entity


async def update(entity: E, return_as: Type[E] = None) -> E:
    key_filter, dict_entity = split_key_and_values(entity, {"exclude_unset": True})
    dict_entity = await _fill_audit(dict_entity)

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


async def _exists(entity: E, key_filter):
    return await default_database[get_collection_name(entity)].count_documents(key_filter) > 0


def _create_audit_info():
    now = utcnow()
    sub, iss = 'unknown', 'unknown'
    audit_info = {"updated_by": {"subject": sub, "issuer": iss}, "updated_at": now}
    return audit_info


async def _fill_audit(dict_entity, exists_fnc=None):
    audit_info = _create_audit_info()

    if not exists_fnc or (exists_fnc and not await exists_fnc()):
        audit_info["created_by"] = audit_info["updated_by"]
        audit_info["created_at"] = audit_info["updated_at"]

    return {**dict_entity, **audit_info}


async def upsert(entity: E) -> E:
    key_filter, dict_entity = split_key_and_values(entity, {"exclude_unset": True})
    dict_entity = await _fill_audit(dict_entity, partial(_exists, entity, key_filter))

    updated = await default_database[get_collection_name(entity)].find_one_and_update(
        key_filter, {"$set": dict_entity}, upsert=True, return_document=ReturnDocument.AFTER
    )

    return from_mongo(type(entity), updated) if updated else None


async def replace(entity: E) -> E:
    key_filter, dict_entity = split_key_and_values(entity)
    dict_entity = await _fill_audit(dict_entity, False)

    replaced = await default_database[get_collection_name(entity)].find_one_and_replace(
        key_filter, {**key_filter, **dict_entity}, upsert=True, return_document=ReturnDocument.AFTER
    )

    return from_mongo(type(entity), replaced) if replaced else None


async def delete_by_key(entity: E, return_as: Type[E]):
    key_filter, _ = split_key_and_values(entity)
    ret = await default_database[get_collection_name(entity)].find_one_and_delete(key_filter)

    return from_mongo(return_as, ret) if ret else None
