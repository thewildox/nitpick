import logging

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)

@celery_app.task
def ping(message: str) -> str:
    logger.info("ping received: %s", message)
    return f"pong: {message}"