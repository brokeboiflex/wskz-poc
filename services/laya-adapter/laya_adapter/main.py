from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .engine import HttpDecisionEngine
from .http import install_routes
from .service import ChoiceService


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")
    laya_base_url: str = "http://laya-runtime:8000"
    laya_model: str = "multilingual"
    laya_timeout_seconds: float = Field(default=150, gt=0, le=300)
    adapter_model: str = "laya-multilingual"


def create_app(service: ChoiceService | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        settings = Settings()
        app.state.model = settings.adapter_model
        if service is not None:
            app.state.service = service
            yield
            return
        async with httpx.AsyncClient(
            base_url=settings.laya_base_url.rstrip("/") + "/",
            timeout=settings.laya_timeout_seconds,
            follow_redirects=False,
        ) as client:
            app.state.service = ChoiceService(HttpDecisionEngine(client, settings.laya_model))
            yield

    app = FastAPI(title="Laya choice-to-tool adapter", version="1.0.0", lifespan=lifespan)
    install_routes(app)
    return app


app = create_app()
