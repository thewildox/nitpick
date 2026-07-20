import logging
import random

from app.workers.celery_app import celery_app
from app.db import SessionLocal
from app.models.analysis_run import AnalysisRun, RunStatus
from app.models.pull_request import PullRequest
from app.models.repository import Repository      

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

@celery_app.task
def analyze_pull_request(analysis_run_id: int) -> str:
    db = SessionLocal()
    try:
        run = db.get(AnalysisRun, analysis_run_id)   # fetch the row by primary key
        if run is None:
            logger.warning("analysis run %s not found", analysis_run_id)
            return "not found"

        run.status = RunStatus.RUNNING
        db.commit()
        logger.info("analysis run %s now RUNNING", analysis_run_id)

        # (real analysis will go here in a later week)

        return f"started run {analysis_run_id}"
    finally:
        db.close()