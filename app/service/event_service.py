import logging
from datetime import datetime

import requests

from app.domain.domain import DomainEvent, DomainEventStatus
from app.domain.hook import HookType, OID
from app.repository import event_respository, base_repository
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
