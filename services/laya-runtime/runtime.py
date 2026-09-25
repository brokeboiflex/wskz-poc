"""Thin host for the real Laya SDK; no routing policy or OpenAI protocol here.

Matches Laya's /v1/systemone choice wire format, with an explicit 8192-token
budget rather than the upstream HTTP server's implicit 1024-token default.
"""

import json
import os
from contextlib import asynccontextmanager
from threading import Lock
from typing import Literal, Protocol

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field


class Question(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["choice"]
    instructions: str = Field(max_length=6000)
    criteria: dict[str, str] = Field(min_length=2, max_length=32)


class DecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    model: Literal["multilingual"] = "multilingual"
    state: str = Field(min_length=1, max_length=4000)
    questions: dict[str, Question] = Field(min_length=1, max_length=1)


class Predictor(Protocol):
    def predict(self, state: str, questions: dict) -> dict: ...


class LayaPredictor:
    def __init__(self):
        import torch
        from laya import Router

        torch.set_num_threads(int(os.environ.get("LAYA_THREADS", "4")))
        self.router = Router(device="cpu", default="multilingual", max_loaded=1)
        self.router.preload(["multilingual"])
        self.lock = Lock()

    def predict(self, state: str, questions: dict) -> dict:
        with self.lock:
            return self.router.predict(state, questions, model="multilingual", max_len=8192)


class InferenceService:
    def __init__(self, predictor: Predictor):
        self.predictor = predictor

    def decide(self, state: str, questions: dict) -> dict:
        return self.predictor.predict(state, questions)


def create_app(service: InferenceService | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Download/preload happens before the server advertises readiness.
        app.state.service = service or InferenceService(LayaPredictor())
        yield

    app = FastAPI(title="Laya decision engine", version="1.0.0", lifespan=lifespan)

    @app.get("/health/ready")
    def ready():
        return {"status": "ready", "model": "multilingual"}

    @app.post("/v1/systemone")
    def decide(body: DecisionRequest, request: Request):
        questions = {key: value.model_dump() for key, value in body.questions.items()}
        if len((body.state + json.dumps(questions, ensure_ascii=False)).encode()) > 7600:
            raise HTTPException(413, "decision context too large")
        try:
            return request.app.state.service.decide(body.state, questions)
        except Exception as exc:
            raise HTTPException(502, "model inference failed") from exc

    return app


app = create_app()
