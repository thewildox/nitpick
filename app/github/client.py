import httpx

from app.config import settings

GITHUB_API_BASE = "https://api.github.com"
NITPICK_MARKER = "<!-- nitpick -->"
DEFAULT_TIMEOUT = httpx.Timeout(connect=5.0, read=10.0, write=5.0, pool=5.0)


def fetch_pr_files(owner: str, repo: str, pr_number: int) -> list[dict]:
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{pr_number}/files"
    headers = {
        "Authorization": f"Bearer {settings.github_token}",
        "Accept": "application/vnd.github+json",
    }
    response = httpx.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)
    response.raise_for_status()
    return response.json()

def fetch_file_content(raw_url: str) -> str:
    headers = {
        "Authorization": f"Bearer {settings.github_token}",
    }
    response = httpx.get(raw_url, headers=headers, timeout=DEFAULT_TIMEOUT)
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
    
    # remove Nitpick's previous comments so re-runs don't stack duplicates
    for old in fetch_review_comments(owner, repo, pr_number):
        delete_review_comment(owner, repo, old["id"])

    if not findings:
        return

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
            "body": f"{NITPICK_MARKER}\n**{f.source.value}** `{f.rule_id}` ({f.severity})\n\n{f.message}",
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


def fetch_review_comments(owner: str, repo: str, pr_number: int) -> list[dict]:
    """Return the inline review comments Nitpick previously left on this PR."""
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{pr_number}/comments"
    headers = {
        "Authorization": f"Bearer {settings.github_token}",
        "Accept": "application/vnd.github+json",
    }
    response = httpx.get(url, headers=headers)
    response.raise_for_status()
    all_comments = response.json()

    return [c for c in all_comments if NITPICK_MARKER in c["body"]]   # filter to Nitpick's


def delete_review_comment(owner: str, repo: str, comment_id: int) -> None:
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/comments/{comment_id}"
    headers = {
        "Authorization": f"Bearer {settings.github_token}",
        "Accept": "application/vnd.github+json",
    }
    response = httpx.delete(url, headers=headers)
    response.raise_for_status()