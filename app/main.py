from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
import redis
from sqlalchemy import text
from sqlalchemy.orm import Session
from pydantic import BaseModel
import json

from app.db import engine
from app.config import settings
from app.workers.tasks import ping, analyze_pull_request
from app.webhooks.security import verify_signature
from app.db import get_db
from app.webhooks.persistence import (
    get_or_create_repository,
    get_or_create_pull_request,
    create_analysis_run,
)

app = FastAPI()

@app.get("/health")
def health():
    postgres_ok = True
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        postgres_ok = False
    
    redis_ok = True
    try:
        redis.Redis.from_url(settings.redis_url).ping()
    except Exception:
        redis_ok = False
    
    body = {
        "status" : "ok" if postgres_ok and redis_ok else "degraded",
            "postgres": postgres_ok,
            "redis": redis_ok
            }

    if redis_ok and postgres_ok:
        return body
    return JSONResponse(status_code=503, content=body)

class PingRequest(BaseModel):
    message: str

@app.post("/tasks/ping", status_code=202)
def enqueue_ping(payload: PingRequest):
    result = ping.delay(payload.message)
    return {"task_id": result.id}

@app.post("/webhooks/github", status_code=202)
async def github_webhook(request: Request, db: Session = Depends(get_db)):
    raw_body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")

    if not verify_signature(raw_body, signature):
        raise HTTPException(status_code=403, detail="Invalid signature")

    payload = json.loads(raw_body)

    if payload.get("action") not in ("opened", "synchronize"):
        return {"status": "ignored"}

    pr_data = payload["pull_request"]
    repo_data = payload["repository"]

    repo = get_or_create_repository(
        db,
        github_id=repo_data["id"],
        full_name=repo_data["full_name"],
    )
    pr = get_or_create_pull_request(
        db,
        repository_id=repo.id,
        pr_number=pr_data["number"],
        title=pr_data["title"],
        author=pr_data["user"]["login"],
        head_sha=pr_data["head"]["sha"],
        state=pr_data["state"],
    )
    run = create_analysis_run(
        db,
        pull_request_id=pr.id,
        commit_sha=pr_data["head"]["sha"],
    )

    analyze_pull_request.delay(run.id)

    return {"analysis_run_id": run.id}