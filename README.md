# Nitpick

Nitpick is an automated code-review tool that reviews every pull request you open and leaves inline comments on the exact lines that need a second look.

## What it does

You open (or update) a pull request on a connected repository, just as you always would. Nitpick picks it up automatically and looks only at the lines your PR actually changed, reviewing each changed Python file for real problems: likely bugs, unhandled edge cases, and security issues rather than the style nits your linter already flags. Moments later the findings appear as inline review comments on the PR, each pinned to a specific line and tagged with a severity (error, warning, or info). Push another commit and Nitpick re-reviews the updated code against the new commit.

## Architecture

The path a single PR takes, from webhook to posted comment:

1. **Webhook** — GitHub POSTs to `/webhooks/github` when a PR is opened or synchronized.
2. **Verify** — recompute the HMAC-SHA256 of the raw body and constant-time compare it against `X-Hub-Signature-256`; reject with `403` on mismatch.
3. **Persist intake** — upsert the Repository and PullRequest, then create an AnalysisRun pinned to the head commit SHA.
4. **Enqueue + ack** — hand the run id to Celery over Redis and return `202` immediately, well under GitHub's 10s timeout; all real work is async.
5. **Task starts** — a Celery worker marks the run `RUNNING` and deletes any prior findings for that run, so re-runs are idempotent.
6. **Fetch** — pull the PR's changed files from the GitHub API; for each `.py` file with a patch, fetch its full content.
7. **Diff filter** — parse the patch into the set of added line numbers; only those lines can produce findings.
8. **Ruff** — lint the file; keep hits that land on changed lines → RUFF findings.
9. **Bandit** — security-scan the file; keep hits that land on changed lines → BANDIT findings.
10. **LLM** — send a context-windowed snippet to Claude; keep findings on changed lines not already flagged by Ruff or Bandit → LLM findings.
11. **Persist findings** — write all findings to Postgres and mark the run `COMPLETED`.
12. **Post back** — bundle every finding into one inline PR review, one comment per finding pinned to its file and line.

## Tech stack

- **FastAPI + Uvicorn** — async HTTP, fast webhook acks.
- **Celery + Redis** — async task queue so webhook responses stay fast (Redis is broker *and* result backend).
- **PostgreSQL + SQLAlchemy 2.0** — durable single source of truth for runs and findings.
- **Ruff + Bandit** — deterministic lint and security scan (run as CLIs).
- **Anthropic Claude** — contextual review linters can't do.
- **httpx** — GitHub REST calls (fetch files, post review).
- **Docker Compose** — one-command Postgres + Redis for local dev.
- **pydantic-settings** — typed config loaded from `.env`.

## Running locally

**Prerequisites**

- Python 3.13
- Docker (runs Postgres + Redis)
- A GitHub personal access token with PR **write** scope
- An Anthropic API key

**Setup**

```bash
# 1. Create a virtualenv and install (Python 3.13)
python -m venv .venv && source .venv/bin/activate
pip install -e . bandit          # bandit isn't in pyproject yet — install it explicitly

# 2. Fill in .env (keys below), then start infrastructure
docker compose up -d             # Postgres + Redis

# 3. Create the database schema — REQUIRED before the first run.
#    This project uses SQLAlchemy create_all (no Alembic migrations),
#    so a fresh clone has empty tables until you run this.
python scripts/create_tables.py
```

**Run the four processes** (each in its own terminal):

```bash
# Celery worker — does all the analysis
celery -A app.workers.celery_app worker --loglevel=info

# API server
uvicorn app.main:app --reload

# Forward GitHub webhooks to your local API.
# First get a channel URL from https://smee.io ("Start a new channel").
npx smee-client --url https://smee.io/<your-channel> --target http://localhost:8000/webhooks/github
```

(Docker Compose is the fourth: it keeps Postgres + Redis running in the background.)

**Environment variables** — set these keys in `.env`:

- `DATABASE_URL`
- `REDIS_URL`
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`
- `GITHUB_WEBHOOK_SECRET`
- `GITHUB_TOKEN`
- `ANTHROPIC_API_KEY`

## Testing

Run the suite with `pytest`. It covers the pure functions (diff parsing, snippet building), LLM response parsing (findings and the refusal branch), and the orchestrator's happy path and idempotency. One caveat: the tests run against in-memory SQLite, so they don't catch Postgres-specific behavior.
