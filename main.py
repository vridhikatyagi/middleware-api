from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uuid
import time

EMAIL = "24f2006788@ds.study.iitm.ac.in"
RATE_LIMIT = 14
WINDOW = 10  # seconds

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app-03f3fx.example.com",
        "https://exam.sanand.workers.dev",
    ],
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=[
        "X-Request-ID",
        "X-Client-Id",
        "Content-Type",
    ],
    expose_headers=[
        "X-Request-ID",
    ],
)

# client_id -> timestamps
rate_limit_store = {}


# ---------- Middleware 1: Request Context ----------
@app.middleware("http")
async def request_context(request: Request, call_next):
    if request.method == "OPTIONS":
        return await call_next(request)

    request_id = request.headers.get("X-Request-ID")
    if not request_id:
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id

    response = await call_next(request)

    # Echo request id in response header
    response.headers["X-Request-ID"] = request_id

    return response


# ---------- Middleware 2: Rate Limiter ----------
@app.middleware("http")
async def rate_limiter(request: Request, call_next):
    if request.method == "OPTIONS":
        return await call_next(request)

    client_id = request.headers.get("X-Client-Id", "anonymous")

    now = time.time()

    timestamps = rate_limit_store.get(client_id, [])
    timestamps = [t for t in timestamps if now - t < WINDOW]

    if len(timestamps) >= RATE_LIMIT:
        response = JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"},
        )

        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())

        response.headers["X-Request-ID"] = request_id
        return response

    timestamps.append(now)
    rate_limit_store[client_id] = timestamps

    return await call_next(request)


@app.get("/ping")
async def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.request_id,
    }
