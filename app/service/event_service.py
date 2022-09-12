import logging
from datetime import datetime

import requests

from app.domain.domain import DomainEvent, DomainEventStatus
from app.domain.hook import HookType
from app.repository import event_respository, base_repository
from app.task import event_tasks

logger = logging.getLogger(__name__)


async def _process_webhook(event: DomainEvent):
    payload = event.json(include={'id', 'event_name', 'schema_name', 'domain_id'})
    logger.info(f'Realizando chamada na api "{event.hook.webhook.callback_url}": {payload}')
    resp = requests.post(event.hook.webhook.callback_url,
                         data=payload,
                         headers={
                             "Content-Type": "application/json",
                             **(event.hook.webhook.http_headers if event.hook.webhook.http_headers else {}),
                         })
    logger.info(f'Realizando chamada na api "{event.hook.webhook.callback_url}" '
                f'para evento {event.id}: HTTP Status={resp.status_code}')
    resp.raise_for_status()


async def dispatch_event(event: DomainEvent):
    if event.hook.type == HookType.WEBHOOK and event.hook.webhook.delay_time <= 0:
        logger.info(f"Agendando evento '{event.event_name}' para {event.schema_name}/{event.domain_id}: {event.id}")
        await event_tasks.dispatch_event(event)


async def process_event(event_id: str):
    logger.info(f"Processando o evento: {event_id}")

    event = await event_respository.get_event_and_mark_processing(event_id)

    if not event:
        logger.info(f"O evento já foi processado ou está inconsistente: {event_id}")
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


async def mark_event_as_failure(sellout_id: str, event_id: str, exc):
    pass


async def trigger_pending_events():
    events = await event_respository.find_pending_events(datetime.utcnow())

    logger.info(f'Starting processing of scheduled events...')

    for event in events:
        await event_tasks.dispatch_event(event)

    logger.info(f'End of processing of scheduled events.')
