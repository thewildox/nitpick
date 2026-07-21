import logging
import random
import json
import subprocess

from app.workers.celery_app import celery_app
from app.db import SessionLocal
from app.models.analysis_run import AnalysisRun, RunStatus
from app.models.pull_request import PullRequest
from app.models.repository import Repository   
from app.github.client import fetch_pr_files, fetch_file_content

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
    session = SessionLocal()
    run = None
    try:
        run = session.get(AnalysisRun, analysis_run_id)   # fetch the row by primary key
        if run is None:
            logger.warning("analysis run %s not found", analysis_run_id)
            return "not found"

        run.status = RunStatus.RUNNING
        session.commit()
        logger.info("analysis run %s now RUNNING", analysis_run_id)

        pr = session.get(PullRequest, run.pull_request_id)
        repo = session.get(Repository, pr.repository_id)

        owner, repo_name = repo.full_name.split("/")

        files = fetch_pr_files(owner, repo_name, pr.pr_number)

        for f in files:
            filename = f["filename"]
            if not filename.endswith(".py"):
                continue

            content = fetch_file_content(f["raw_url"])

            result = subprocess.run(
                ["ruff", "check", "--output-format", "json", "-"],
                input=content,
                capture_output=True,
                text=True,
            )
            findings = json.loads(result.stdout)
            print(filename, "->", len(findings), "findings")

        run.status = RunStatus.COMPLETED
        session.commit()
        return f"completed run {analysis_run_id}"
    except Exception:
        session.rollback()
        if run is not None: run.status = RunStatus.FAILED
        session.commit()
        raise
    finally:
        session.close()