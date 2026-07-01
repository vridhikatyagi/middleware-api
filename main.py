from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
import uuid
import time

EMAIL = "24f2006788@ds.study.iitm.ac.in"
RATE_LIMIT = 14
WINDOW = 10

ALLOWED_ORIGIN = "https://app-03f3fx.example.com"
EXAM_ORIGIN = "https://exam.sanand.workers.dev"

app = FastAPI()

rate_limit_store = {}


@app.middleware("http")
async def middleware(request: Request, call_next):
    # ---------- Request ID ----------
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id

    # ---------- Handle CORS Preflight ----------
    if request.method == "OPTIONS":
        response = Response(status_code=204)
    else:
        # ---------- Rate Limiting ----------
        client_id = request.headers.get("X-Client-Id", "anonymous")
        now = time.time()

        timestamps = rate_limit_store.get(client_id, [])
        timestamps = [t for t in timestamps if now - t < WINDOW]

        if len(timestamps) >= RATE_LIMIT:
            response = JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
                headers={"Retry-After": "10"},
            )
        else:
            timestamps.append(now)
            rate_limit_store[client_id] = timestamps
            response = await call_next(request)

    # ---------- Echo Request ID ----------
    response.headers["X-Request-ID"] = request_id

    # ---------- CORS ----------
    origin = request.headers.get("Origin")

    if origin in (ALLOWED_ORIGIN, EXAM_ORIGIN):
        response.headers["Access-Control-Allow-Origin"] = origin

    response.headers["Access-Control-Allow-Methods"] = "GET,OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Expose-Headers"] = "X-Request-ID"

    return response


@app.get("/ping")
async def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.request_id,
    }
