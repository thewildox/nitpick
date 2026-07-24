import httpx

from app.config import settings
from app.models.finding import Finding

GITHUB_API_BASE = "https://api.github.com"


def fetch_pr_files(owner: str, repo: str, pr_number: int) -> list[dict]:
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{pr_number}/files"
    headers = {
        "Authorization": f"Bearer {settings.github_token}",
        "Accept": "application/vnd.github+json",
    }
    response = httpx.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def fetch_file_content(raw_url: str) -> str:
    headers = {
        "Authorization": f"Bearer {settings.github_token}",
    }
    response = httpx.get(raw_url, headers=headers, follow_redirects=True)
    response.raise_for_status()
    return response.text

def post_review(
    owner: str,
    repo: str,
    pr_number: int,
    commit_sha: str,
    findings: list,
) -> None:
    """Post all findings as one inline review on the PR."""
    if not findings:
        return                                    # 1: why does this guard matter?

    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
    headers = {
        "Authorization": f"Bearer {settings.github_token}",
        "Accept": "application/vnd.github+json",
    }

    comments = [
        {
            "path": f.file_path,
            "line": f.line_number,
            "side": "RIGHT",
            "body": f"**{f.source.value}** `{f.rule_id}` ({f.severity})\n\n{f.message}",
        }
        for f in findings
    ]

    payload = {
        "commit_id": commit_sha,
        "event": "COMMENT",
        "body": f"Nitpick found {len(comments)} issue(s).",
        "comments": comments,
    }

    response = httpx.post(url, headers=headers, json=payload)
    response.raise_for_status()