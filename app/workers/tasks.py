import logging
import random
import json
import subprocess
import tempfile
import os
import anthropic
from sqlalchemy import delete

from app.workers.celery_app import celery_app
from app.db import SessionLocal
from app.models.analysis_run import AnalysisRun, RunStatus
from app.models.pull_request import PullRequest
from app.models.repository import Repository   
from app.models.finding import Finding, Source
from app.github.client import fetch_pr_files, fetch_file_content
from app.analysis.diff import changed_lines
from app.analysis.llm import build_snippet, review_snippet

BANDIT_SEVERITY = {"HIGH": "error", "MEDIUM": "warning", "LOW": "info"}

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

        session.execute(delete(Finding).where(Finding.analysis_run_id == run.id))
        files = fetch_pr_files(owner, repo_name, pr.pr_number)

        for f in files:
            filename = f["filename"]
            if not filename.endswith(".py"):
                continue
            
            patch = f.get("patch")
            if patch is None:
                continue

            changed = changed_lines(patch)
            flagged = set()
            content = fetch_file_content(f["raw_url"])

            result = subprocess.run(
                ["ruff", "check", "--output-format", "json", "-"],
                input=content,
                capture_output=True,
                text=True,
            )
            findings = json.loads(result.stdout)

            for finding in findings:
                if finding["location"]["row"] not in changed:
                    continue
                row = Finding(
                    analysis_run_id=run.id,
                    file_path=filename,
                    line_number=finding["location"]["row"],
                    source=Source.RUFF,
                    rule_id=finding["code"],
                    severity="warning",
                    message=finding["message"],
                )
                session.add(row)
                flagged.add(finding["location"]["row"])
            
            # Bandit Block
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", delete=False
            ) as tmp:
                tmp.write(content)
                tmp_path = tmp.name

            try:
                bandit_result = subprocess.run(
                    ["bandit", "-f", "json", tmp_path],
                    capture_output=True,
                    text=True,
                )
                bandit_data = json.loads(bandit_result.stdout)

                for issue in bandit_data["results"]:
                    if issue["line_number"] not in changed:
                        continue
                    row = Finding(
                        analysis_run_id=run.id,
                        file_path=filename,
                        line_number=issue["line_number"],
                        source=Source.BANDIT,
                        rule_id=issue["test_id"],
                        severity=BANDIT_SEVERITY[issue["issue_severity"]],
                        message=issue["issue_text"],
                    )
                    session.add(row)
                    flagged.add(issue["line_number"])
            finally:
                os.remove(tmp_path)
            try:
                snippet = build_snippet(content, changed)
                for issue in review_snippet(snippet, filename):
                    if issue["line"] not in changed or issue["line"] in flagged:
                        continue
                    row = Finding(
                        analysis_run_id=run.id,
                        file_path=filename,
                        line_number=issue["line"],
                        source=Source.LLM,
                        rule_id="LLM",
                        severity=issue["severity"],
                        message=issue["message"],
                    )
                    session.add(row)

            except anthropic.APIError:
                logger.exception("LLM review failed for %s", filename)

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