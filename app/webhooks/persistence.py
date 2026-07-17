from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.repository import Repository
from app.models.pull_request import PullRequest
from app.models.analysis_run import AnalysisRun


def get_or_create_repository(db: Session, github_id: int, full_name: str) -> Repository:
    stmt = select(Repository).where(Repository.github_id == github_id)
    existing = db.execute(stmt).scalar_one_or_none()

    if existing is not None:
        return existing

    repo = Repository(
        github_id=github_id,
        full_name=full_name,
        webhook_secret=settings.github_webhook_secret,
    )
    db.add(repo)
    db.commit()
    db.refresh(repo)
    return repo

def get_or_create_pull_request(
    db: Session,
    repository_id: int,
    pr_number: int,
    title: str,
    author: str,
    head_sha: str,
    state: str,
) -> PullRequest:
    stmt = select(PullRequest).where(
        PullRequest.repository_id == repository_id,
        PullRequest.pr_number == pr_number,
    )
    existing = db.execute(stmt).scalar_one_or_none()

    if existing is not None:
        # PR already exists — but the head_sha may have changed (new push).
        # Update the moving fields so the row reflects the latest state.
        existing.head_sha = head_sha
        existing.title = title
        existing.state = state
        db.commit()
        db.refresh(existing)
        return existing

    pr = PullRequest(
        repository_id=repository_id,
        pr_number=pr_number,
        title=title,
        author=author,
        head_sha=head_sha,
        state=state,
    )
    db.add(pr)
    db.commit()
    db.refresh(pr)
    return pr


def create_analysis_run(db: Session, pull_request_id: int, commit_sha: str) -> AnalysisRun:
    run = AnalysisRun(
        pull_request_id=pull_request_id,
        commit_sha=commit_sha,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run