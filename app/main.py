import os
import random
import time
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import BaseModel, Field


app = FastAPI(title="SwiftDeploy API")
START_TIME = time.monotonic()
CHAOS = {"mode": "recover", "duration": 0, "rate": 0.0}


def current_mode() -> str:
    return os.getenv("MODE", "stable").lower()


def app_version() -> str:
    return os.getenv("APP_VERSION", "1.0.0")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def apply_chaos_if_needed() -> None:
    if current_mode() != "canary":
        return

    if CHAOS["mode"] == "slow":
        time.sleep(float(CHAOS["duration"]))
    elif CHAOS["mode"] == "error":
        if random.random() < float(CHAOS["rate"]):
            raise HTTPException(status_code=500, detail="simulated canary error")


@app.middleware("http")
async def canary_headers_and_chaos(request: Request, call_next):
    if request.url.path != "/chaos":
        apply_chaos_if_needed()

    response = await call_next(request)
    if current_mode() == "canary":
        response.headers["X-Mode"] = "canary"
    return response


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
        "uptime_seconds": round(time.monotonic() - START_TIME, 2),
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
