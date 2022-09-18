import logging
from datetime import datetime, timedelta
from typing import List

import requests

from app.domain.domain import DomainEvent, DomainEventStatus
from app.domain.hook import HookType, OID, Hook
from app.repository import event_respository, base_repository
from app.service import schema_service, domain_service, hook_service, expression_service
from app.service.exceptions import RecordNotFoundException, ValidationException
from app.task import event_tasks

logger = logging.getLogger(__name__)


async def _process_webhook(event: DomainEvent):
    payload = event.json(include={'id', 'event_name', 'schema_name', 'domain_id'})
    logger.info(f'Calling API "{event.hook.webhook.callback_url}": {payload}')
    resp = requests.post(event.hook.webhook.callback_url,
                         data=payload,
                         timeout=event.hook.webhook.timeout or 3,
                         headers={
                             "Content-Type": "application/json",
                             **(event.hook.webhook.http_headers if event.hook.webhook.http_headers else {}),
                         })
    logger.info(f'API Response "{event.hook.webhook.callback_url}" '
                f'of event {event.id}: HTTP Status={resp.status_code}')
    resp.raise_for_status()


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
    domain = await domain_service.get_domain_by_id(event.schema_name, event.domain_id)

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
        await dispatch_event(new_event)
    return ret


async def dispatch_event(event: DomainEvent):
    if event.hook.type == HookType.WEBHOOK and event.hook.webhook.delay_time <= 0:
        logger.info(f"Dispatching event '{event.event_name}' of {event.schema_name}/{event.domain_id}: {event.id}")
        await event_tasks.dispatch_event(event)


async def process_event(event_id: str):
    logger.info(f"Processing event: {event_id}")

    event = await event_respository.get_event_and_mark_processing(event_id)

    if not event:
        logger.info(f"Event already processed or inconsistent: {event_id}")
        return

    try:
        if event.hook.type == HookType.WEBHOOK:
            await _process_webhook(event)

        event.status = DomainEventStatus.PROCESSED
        await base_repository.update(event, DomainEvent)

    except Exception as err:
        event.status = DomainEventStatus.ERROR
        await base_repository.update(event, DomainEvent)
        raise err


async def mark_event_as_failure(event_id: str, exc):
    event = await base_repository.find_first_by_key(DomainEvent(id=OID(event_id)), return_as=DomainEvent)
    event.status = DomainEventStatus.FAILED
    event.failure_message = str(exc)
    await base_repository.update(event, DomainEvent)


async def trigger_pending_events():
    events = await event_respository.find_pending_events(datetime.utcnow())

    logger.info(f'Starting processing of scheduled events...')

    for event in events:
        await event_tasks.dispatch_event(event)

    logger.info(f'End of processing of scheduled events.')


async def find_events_of_schema(schema_name,
                                event_id=None,
                                event_name=None,
                                queue_name=None,
                                skip: int = 0, limit: int = 100):
    ret = await event_respository.find_events(schema_name, event_id, event_name, queue_name, skip, limit)
    return ret


async def update_event_status(schema_name: str, event_id: str, status: DomainEventStatus) -> DomainEvent:
    events = await base_repository.find_by_example(
        DomainEvent(id=event_id, schema_name=schema_name), return_as=DomainEvent)

    if not events:
        raise RecordNotFoundException(f'Event not found: {schema_name}/{str(event_id)}')

    event = events[0]

    if event.hook == HookType.WEBHOOK:
        raise ValidationException(f'Webhook events does not allow update')

    if event.status not in (DomainEventStatus.CREATED, DomainEventStatus.PROCESSING):
        raise ValidationException(f'Event status does not allow changes: {event.status}')

    event.status = status
    return await base_repository.update(event)
