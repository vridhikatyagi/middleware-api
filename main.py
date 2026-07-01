from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import uuid

EMAIL = "24f2006788@ds.study.iitm.ac.in"
RATE_LIMIT = 14
WINDOW = 10

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app-03f3fx.example.com",
        "https://exam.sanand.workers.dev",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

rate_limit_store = {}


@app.middleware("http")
async def request_context(request: Request, call_next):
    if request.method == "OPTIONS":
        return await call_next(request)

    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id

    response = await call_next(request)

    # Set BOTH spellings just in case an intermediary normalizes one.
    response.headers["X-Request-ID"] = request_id
    response.headers["x-request-id"] = request_id

    return response


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    if request.method == "OPTIONS":
        return await call_next(request)

    client = request.headers.get("X-Client-Id", "anonymous")
    now = time.time()

    hits = [t for t in rate_limit_store.get(client, []) if now - t < WINDOW]

    if len(hits) >= RATE_LIMIT:
        response = JSONResponse(
            {"detail": "Rate limit exceeded"},
            status_code=429,
        )
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        response.headers["X-Request-ID"] = request_id
        response.headers["x-request-id"] = request_id
        return response

    hits.append(now)
    rate_limit_store[client] = hits

    return await call_next(request)


@app.get("/ping")
async def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.request_id,
    }
