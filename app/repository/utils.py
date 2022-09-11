import typing

from bson import ObjectId

from app.domain.hook import OID, HookBaseDomain
from app.repository.exceptions import RepositoryException
from app.utils.misc import get_meta, utcnow

E = typing.TypeVar("E", bound=HookBaseDomain)


def is_oid(value, key, type_hints):
    return isinstance(value, ObjectId) or type_hints.get(key, None) == OID


def split_key_and_values(entity: E, to_dict_opts: dict = None) -> typing.Tuple[dict, dict]:
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

        if is_oid(key_filter[key_attr], key_attr, type_hints):
            value = key_filter.pop(key_attr)
            key_filter["_id"] = ObjectId(value) if type(value) == str else value

    return key_filter, dict_entity


def get_collection_name(entity: E) -> str:
    return get_meta(entity, "collection_name")


def create_audit_info():
    now = utcnow()
    sub, iss = 'unknown', 'unknown'
    audit_info = {"updated_by": {"subject": sub, "issuer": iss}, "updated_at": now}
    return audit_info


async def fill_audit(dict_entity, exists_fnc=None):
    audit_info = create_audit_info()

    if not exists_fnc or (exists_fnc and not await exists_fnc()):
        audit_info["created_by"] = audit_info["updated_by"]
        audit_info["created_at"] = audit_info["updated_at"]

    return {**dict_entity, **audit_info}
