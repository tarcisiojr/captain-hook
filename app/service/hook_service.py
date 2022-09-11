from typing import List

from app.domain.hook import Hook
from app.repository import base_repository
from app.service import schema_service


async def create_hook_config(hook: Hook) -> Hook:
    await schema_service.exists_schema(hook.schema_name)
    return await base_repository.create(hook)


async def find_hooks_by_example(example: Hook) -> List[Hook]:
    return await base_repository.find_by_example(example, return_as=Hook, limit=0)