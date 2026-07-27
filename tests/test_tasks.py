import json
from unittest.mock import patch, MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.models.repository import Repository
from app.models.pull_request import PullRequest
from app.models.analysis_run import AnalysisRun, RunStatus
from app.models.finding import Finding, Source
from app.workers.tasks import analyze_pull_request


@pytest.fixture
def session():
    """A fresh in-memory database for each test."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)
    s = TestSession()
    yield s
    s.close()


def test_analyze_persists_findings(session):
    # --- seed the database ---
    repo = Repository(
        github_id=1,
        full_name="thewildox/nitpick-test",
        webhook_secret="testsecret",
    )
    session.add(repo)
    session.commit()

    pr = PullRequest(
        repository_id=repo.id,
        pr_number=1,
        title="test",
        author="tester",
        head_sha="abc123",
        state="open",
    )
    session.add(pr)
    session.commit()

    run = AnalysisRun(
        pull_request_id=pr.id,
        commit_sha="abc123",
        status=RunStatus.QUEUED,
    )
    session.add(run)
    session.commit()

    # --- fake the externals ---
    fake_files = [{
        "filename": "messy.py",
        "raw_url": "http://fake/messy.py",
        "patch": "@@ -0,0 +1,2 @@\n+import os\n+x=1",
    }]

    ruff_json = json.dumps([
        {"code": "F401", "location": {"row": 1}, "message": "unused import"}
    ])
    bandit_json = json.dumps({"results": []})

    def fake_subprocess(cmd, **kwargs):
        result = MagicMock()
        result.stdout = ruff_json if cmd[0] == "ruff" else bandit_json
        return result

    with patch("app.workers.tasks.fetch_pr_files", return_value=fake_files), \
         patch("app.workers.tasks.fetch_file_content", return_value="import os\nx=1"), \
         patch("app.workers.tasks.subprocess.run", side_effect=fake_subprocess), \
         patch("app.workers.tasks.review_snippet", return_value=[]), \
         patch("app.workers.tasks.post_review"):
        result = analyze_pull_request(run.id, session=session)

    # --- assert on the database ---
    findings = session.query(Finding).filter_by(analysis_run_id=run.id).all()
    assert len(findings) == 1
    assert findings[0].source == Source.RUFF
    assert findings[0].rule_id == "F401"
    assert findings[0].line_number == 1

    session.refresh(run)
    assert run.status == RunStatus.COMPLETED