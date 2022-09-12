from typing import List

from app.domain.hook import Hook, HookType
from app.repository import base_repository, hook_repository
from app.service import schema_service
from app.service.exceptions import ValidationException


async def create_hook_config(hook: Hook) -> Hook:
    if hook.type == HookType.WEBHOOK and not hook.webhook:
        raise ValidationException(f"Attribute 'webhook' is required when type is '{HookType.WEBHOOK}'")

    await schema_service.exists_schema(hook.schema_name)
    return await base_repository.create(hook)


async def find_hooks_by_example(example: Hook) -> List[Hook]:
    return await base_repository.find_by_example(example, return_as=Hook, limit=0)


async def find_eligible_hooks(schema_name: str, event_name: str, tags: List[List[str]]) -> List[Hook]:
    result = []
    for filter_tags in tags if tags else [[]]:
        result.extend(await hook_repository.find_eligible_hooks(schema_name, event_name, filter_tags))
    return result