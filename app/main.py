import os
import random
import time
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
from pydantic import BaseModel, Field


app = FastAPI(title="SwiftDeploy API")
START_TIME = time.time()
CHAOS = {"mode": "recover", "duration": 0, "rate": 0.0}

REQUESTS = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status_code"],
)


REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10],
)

APP_UPTIME = Gauge("app_uptime_seconds", "Application uptime in seconds")
APP_MODE = Gauge("app_mode", "Application mode: 0=stable, 1=canary")
CHAOS_ACTIVE = Gauge("chaos_active", "Chaos state: 0=none, 1=slow, 2=error")


def current_mode() -> str:
    return os.getenv("MODE", "stable").lower()


def app_version() -> str:
    return os.getenv("APP_VERSION", "1.0.0")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def chaos_metric_value() -> int:
    if CHAOS["mode"] == "slow":
        return 1
    if CHAOS["mode"] == "error":
        return 2
    return 0


def should_return_chaos_error() -> bool:
    if current_mode() != "canary":
        return False

    if CHAOS["mode"] == "slow":
        time.sleep(float(CHAOS["duration"]))
    elif CHAOS["mode"] == "error":
        if random.random() < float(CHAOS["rate"]):
            return True

    return False


@app.middleware("http")
async def canary_headers_and_chaos(request: Request, call_next):
    start = time.time()

    status_code = "500"
    try:
        if request.url.path != "/chaos" and should_return_chaos_error():
            return JSONResponse(
                status_code=500,
                content={"detail": "simulated canary error"},
            )

        response = await call_next(request)
        status_code = str(response.status_code)
        if current_mode() == "canary":
            response.headers["X-Mode"] = "canary"
        return response
    finally:
        duration = time.time() - start
        path = request.url.path
        method = request.method
        REQUESTS.labels(method=method, path=path, status_code=status_code).inc()
        REQUEST_DURATION.labels(method=method, path=path).observe(duration)


class ChaosRequest(BaseModel):
    mode: str = Field(..., pattern="^(slow|error|recover)$")
    duration: Optional[float] = None
    rate: Optional[float] = None


@app.get("/")
def root():
    return {
        "message": f"Welcome to SwiftDeploy running in {current_mode()} mode.",
        "mode": current_mode(),
        "version": app_version(),
        "timestamp": utc_now(),
    }


@app.get("/healthz")
def healthz():
    return {
        "status": "ok",
        "mode": current_mode(),
        "version": app_version(),
        "uptime_seconds": round(time.time() - START_TIME, 2),
    }


@app.post("/chaos")
def chaos(payload: ChaosRequest, response: Response):
    if current_mode() != "canary":
        raise HTTPException(status_code=403, detail="chaos is only available in canary mode")

    if payload.mode == "slow":
        if payload.duration is None or payload.duration < 0:
            raise HTTPException(status_code=400, detail="slow mode requires duration >= 0")
        CHAOS.update({"mode": "slow", "duration": payload.duration, "rate": 0.0})
    elif payload.mode == "error":
        if payload.rate is None or payload.rate < 0 or payload.rate > 1:
            raise HTTPException(status_code=400, detail="error mode requires rate between 0 and 1")
        CHAOS.update({"mode": "error", "duration": 0, "rate": payload.rate})
    else:
        CHAOS.update({"mode": "recover", "duration": 0, "rate": 0.0})

    response.headers["X-Mode"] = "canary"
    return {"status": "updated", "chaos": CHAOS}


@app.get("/metrics")
def metrics():
    APP_UPTIME.set(time.time() - START_TIME)
    APP_MODE.set(1 if current_mode() == "canary" else 0)
    CHAOS_ACTIVE.set(chaos_metric_value())

    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
