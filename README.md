# Nitpick

Nitpick is an automated code-review tool that reviews every pull request you open and leaves inline comments on the exact lines that need a second look.

## What it does

You open (or update) a pull request on a connected repository, just as you always would. Nitpick picks it up automatically and looks only at the lines your PR actually changed, reviewing each changed Python file for real problems: likely bugs, unhandled edge cases, and security issues rather than the style nits your linter already flags. Moments later the findings appear as inline review comments on the PR, each pinned to a specific line and tagged with a severity (error, warning, or info). Push another commit and Nitpick re-reviews the updated code, so its feedback always reflects the latest state of the branch.

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
