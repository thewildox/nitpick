import httpx

from app.config import settings

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
