from fastapi import FastAPI
from fastapi.responses import JSONResponse
import redis
from app.db import engine
from app.config import settings
from sqlalchemy import text

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