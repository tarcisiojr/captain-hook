from datetime import timedelta, datetime
from typing import List

from jsonschema.exceptions import ValidationError, SchemaError
from jsonschema.validators import validate

from app.domain.domain import DomainSchema, Domain, DomainEvent, DomainEventStatus
from app.domain.hook import Hook, HookType
from app.repository import base_repository, event_respository
from app.service import schema_service, event_service, hook_service, expression_service
from app.service.exceptions import RecordNotFoundException, ValidationException


def _validate_domain_schema(schema: DomainSchema, domain: Domain):
    try:
        validate(instance=domain.dict().get('data'), schema=schema.domain_schema.dict(exclude_none=True))
    except ValidationError as verr:
        raise ValidationException(f"Domain has a invalid schema: {schema.name}", details=verr.message)
    except SchemaError as err:
        raise ValidationException(f"Invalid schema: {schema.name}", details=err.message)


async def create_domain(domain: Domain) -> Domain:
    schema = await schema_service.get_schema_by_name(domain.schema_name)
    _validate_domain_schema(schema, domain)
    ret = await base_repository.create(domain)
    return ret


async def get_domain_by_id(schema_name: str, domain_id: str):
    key = Domain(schema_name=schema_name, domain_id=domain_id)
    ret = await base_repository.find_by_key(key, Domain)
    if not ret:
        raise RecordNotFoundException(f'Domain not found: {schema_name}/{domain_id}',
                                      details=key.dict(include={'schema_name', 'domain_id'}))
    return ret[0]


async def _validate_domain(schema_name, domain_id):
    await get_domain_by_id(schema_name, domain_id)


def _get_vars(event, domain):
    return {
        "event": event.dict(include={'event_name', 'schema_name', 'domain_id', 'metadata'}),
        "domain": domain.dict()
    }


def _calculate_eta(hook: Hook):
    if hook.type == HookType.WEBHOOK:
        return datetime.utcnow() + timedelta(minutes=hook.webhook.delay_time if hook.webhook.delay_time else 0)
    return datetime.utcnow()


async def insert_event(event: DomainEvent) -> List[DomainEvent]:
    await schema_service.exists_schema(event.schema_name)
    domain = await get_domain_by_id(event.schema_name, event.domain_id)

    hooks = await hook_service.find_eligible_hooks(event.schema_name, event.event_name, domain.tags)
    events: List[DomainEvent] = []

    for hook in hooks:
        if not hook.condition or expression_service.evaluate(hook.condition, _get_vars(event, domain)):
            events.append(DomainEvent(
                **event.dict(exclude={'status', 'hook', 'eta'}),
                status=DomainEventStatus.CREATED,
                hook=hook,
                eta=_calculate_eta(hook)
            ))

    if not events:
        return []

    ret = await event_respository.create_events(events)
    for new_event in ret:
        await event_service.dispatch_event(new_event)
    return ret


async def delete_domain(domain: Domain):
    ret = await base_repository.delete_by_key(domain, return_as=Domain)
    if not ret:
        raise RecordNotFoundException(f'Domain not found: {domain.schema_name}/{domain.domain_id}',
                                      details=domain.dict(include={'schema_name', 'domain_id'}))
    return ret