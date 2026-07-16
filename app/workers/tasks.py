import logging
import random

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)

@celery_app.task
def ping(message: str) -> str:
    logger.info("ping received: %s", message)
    return f"pong: {message}"

@celery_app.task(bind=True, autoretry_for=(RuntimeError,), max_retries=3, retry_backoff=True)
def flaky(self) -> str:
    attempt = self.request.retries + 1
    logger.info("flaky attempt %d", attempt)
    if random.random() < 0.7:
        raise RuntimeError(f"simulated transient failure on attempt {attempt}")
    return f"succeeded on attempt {attempt}"
