from typing import TypeVar, List

from app.domain.hook import HookBaseDomain
from app.repository import base_repository
from app.service.exceptions import RecordNotFoundException

E = TypeVar("E", bound=HookBaseDomain)


async def create_entity(entity: E) -> E:
    return await base_repository.upsert(entity)


async def find_entity(example: E, skip: int = 0, limit: int = 100) -> List[E]:
    return await base_repository.find_by_example(example, return_as=type(example), skip=skip, limit=limit)


async def delete_entity_by_key(entity: E) -> E:
    ret = await base_repository.delete_by_key(entity, return_as=type(entity))
    if not ret:
        raise RecordNotFoundException()
    return ret
