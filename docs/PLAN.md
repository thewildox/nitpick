# Nitpick — Project Plan

AI code review assistant for GitHub PRs: deterministic static analysis
(Ruff, Bandit, AST) + contextual LLM review (Claude), built async for
speed and cost-efficiency.

## Scope (MVP)
Python-only analysis, repos I own, webhook-triggered, findings stored
per commit SHA, React dashboard with inline findings.
Out of scope for v1: multi-language, posting comments to GitHub,
auth/multi-user, CI integration.

## Architecture decisions
- Fast-ack webhooks: verify → persist → enqueue → 202 in <200ms; all
  work happens in Celery workers (GitHub's 10s timeout demands it)
- Celery + Redis for the job queue; Postgres as single source of truth
- Two-tier analysis: linters always (free, deterministic), LLM only
  for what linters can't judge (design, logic, context)
- Cache key: commit SHA + hunk hash + analyzer version → never
  re-analyze unchanged code

## Data model
Repository → PullRequest → AnalysisRun (pinned to a commit_sha,
status enum) → Finding (file, line, severity, source, message).
The SHA lives on AnalysisRun because a PR is a moving target;
an analysis is a fact about one immutable commit.

## Milestones
- [x] Week 1 — Foundation: Docker Compose, models, /health endpoint
- [ ] Week 2 — Celery pipeline: task round-trips through Redis
- [ ] Week 3 — Webhook ingestion: signed GitHub webhooks → tasks
- [ ] Week 4 — Static analysis: Ruff/Bandit/AST mapped to diff lines
- [ ] Week 5 — LLM review: Claude findings, rate limiting, backoff
- [ ] Week 6 — SHA cache + React diff viewer
- [ ] Week 7 (stretch) — Deploy, README, demo GIF