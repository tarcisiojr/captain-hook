import logging

logger = logging.getLogger(__name__)

logger.info('Iniciando worker...')
from app.config.celery import celery