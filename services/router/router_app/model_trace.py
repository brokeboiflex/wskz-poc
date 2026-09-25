"""Opt-in synthetic diagnostics on the existing OpenAI-compatible HTTP transport."""

import json
import logging
import time
from contextlib import contextmanager
from contextvars import ContextVar

import httpx

_request_id: ContextVar[str | None] = ContextVar("model_trace_request_id", default=None)
logger = logging.getLogger("uvicorn.error.model_trace")


@contextmanager
def trace_scope(request_id: str | None):
    token = _request_id.set(request_id)
    try:
        yield
    finally:
        _request_id.reset(token)


def emit(event: str, **details):
    if request_id := _request_id.get():
        logger.info(
            "model_trace %s",
            json.dumps({"event": event, "request_id": request_id, **details}, ensure_ascii=False),
        )


async def log_request(request: httpx.Request):
    if _request_id.get() is None:
        return
    request.extensions["model_trace_started"] = time.perf_counter()
    body = await request.aread()
    emit("request", method=request.method, path=request.url.path, body=body.decode("utf-8"))


async def log_response(response: httpx.Response):
    if _request_id.get() is None:
        return
    body = await response.aread()
    started = response.request.extensions["model_trace_started"]
    emit(
        "response",
        status=response.status_code,
        seconds=round(time.perf_counter() - started, 3),
        body=body.decode("utf-8", errors="replace"),
    )


def event_hooks(enabled: bool):
    return {"request": [log_request], "response": [log_response]} if enabled else {}
