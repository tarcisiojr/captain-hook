import logging

logger = logging.getLogger(__name__)

from app.config.celery import celery


if __file__ == '__main__':
    logger.info('Starting worker...')