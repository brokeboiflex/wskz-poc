"""Evaluation-only identity endpoint bound to the adapter's actual decision engine."""

from fastapi import Request
from laya_adapter.main import create_app

app = create_app()


@app.get("/health/checkpoint")
async def identity(request: Request):
    client = request.app.state.service.engine.client
    response = await client.get("health/checkpoint", timeout=10)
    response.raise_for_status()
    return response.json()
