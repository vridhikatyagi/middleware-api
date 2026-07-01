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
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)

# Store timestamps per client
rate_limit_store = {}


@app.middleware("http")
async def middleware(request: Request, call_next):
    # Allow CORS preflight requests
    if request.method == "OPTIONS":
        return await call_next(request)

    # Request ID
    request_id = request.headers.get("X-Request-ID")
    if not request_id:
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id

    # Rate limiting
    client_id = request.headers.get("X-Client-Id", "anonymous")
    now = time.time()

    timestamps = rate_limit_store.get(client_id, [])
    timestamps = [t for t in timestamps if now - t < WINDOW]

    if len(timestamps) >= RATE_LIMIT:
        response = JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"},
        )
        response.headers["X-Request-ID"] = request_id
        return response

    timestamps.append(now)
    rate_limit_store[client_id] = timestamps

    response = await call_next(request)

    # Always echo request ID
    response.headers["X-Request-ID"] = request_id

    return response


@app.get("/ping")
async def ping(request: Request):
    request_id = request.state.request_id

    response = JSONResponse(
        content={
            "email": EMAIL,
            "request_id": request_id,
        }
    )

    # Echo request ID here as well
    response.headers["X-Request-ID"] = request_id

    return response
