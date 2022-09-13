import logging

from app.config.celery import celery
from app.domain.domain import DomainEvent
from app.service import event_service
from app.task.utils import run_in_new_loop, run_in_executor

logger = logging.getLogger(__name__)


@run_in_new_loop
async def _call_service(fun, *args, **kwargs):
    return await fun(*args, **kwargs)


def _on_failure(task, exc, task_id, args, kwargs, einfo):
    _call_service(event_service.mark_event_as_failure,
                  args[0] or kwargs["event_id"],
                  str(exc))


@celery.task(
    autoretry_for=[Exception],
    retry_kwargs={"max_retries": 3},
    on_failure=_on_failure,
    retry_backoff=30,
    retry_jitter=True,
    acks_late=True
)
def _process_event(event_id):
    logger.debug(f'Starting to process event: {event_id}')
    _call_service(event_service.process_event, event_id=event_id)


@celery.task()
def trigger_events():
    logger.info('Triggering pending events...')
    _call_service(event_service.trigger_pending_events)


async def dispatch_event(event: DomainEvent):
    await run_in_executor(
        _process_event.s(str(event.id)).apply_async,
        retry=True,
        queue=event.hook.queue_name or 'default',
        retry_policy={'max_retries': event.hook.webhook.max_retries})
