import logging

from celery import Celery

config_obj = {
    "imports": ("app.task.event_tasks",),
    "broker_url": "amqp://",
    "result_backend": "redis://localhost",
    "task_always_eager": False
}

celery = Celery(**config_obj)

logger = logging.getLogger(__name__)


@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    from app.task import event_tasks
    logger.info('Carregando tarefas periódicas...')
    sender.add_periodic_task(10.0, event_tasks.trigger_events.s(), name='Trigger_Events')
