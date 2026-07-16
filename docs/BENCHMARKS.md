# Benchmarks

## Webhook enqueue latency

**Date:** July 13, 2026
**Endpoint:** POST /tasks/ping
**Command:** ab -n 200 -c 10 -p payload.json -T application/json http://localhost:8000/tasks/ping

**Conditions:**
- Local machine, localhost
- uvicorn without --reload
- Redis + Postgres up via Docker Compose, Celery worker running
- 200 requests, concurrency 10
- tiny payload

**Results:**
| Metric | Value |
| --- | --- |
| Requests | 200|
| Failed | 0 |
| Mean | 6.25ms |
| p99 | 45ms |
| Throughput | ~1600 req/s |

**What this does and doesn't prove:** This means under 10 concurrent connections, 99% of enqueues complete in 45ms. It does not include the time the it takes for the llm to process the pr and make recommendations. 