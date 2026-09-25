"""Composition root: only this module constructs concrete dependencies."""

from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from .adapters.agent import LangChainRoutingAgent
from .adapters.mailer import HttpDeliveryGateway
from .config import Settings
from .http import install_routes
from .service import RoutingService


def create_app(service: RoutingService | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if service is not None:
            app.state.service = service
            yield
            return
        from langchain_openai import ChatOpenAI

        settings = Settings()
        async with (
            httpx.AsyncClient(
                base_url=settings.openai_base_url.rstrip("/") + "/",
                headers={"Authorization": f"Bearer {settings.openai_api_key.get_secret_value()}"},
                follow_redirects=False,
            ) as model_health,
            httpx.AsyncClient(
                base_url=settings.mailer_base_url.rstrip("/") + "/",
                headers={"Authorization": f"Bearer {settings.mailer_token.get_secret_value()}"},
                timeout=settings.mailer_timeout_seconds,
                follow_redirects=False,
            ) as mailer,
            httpx.AsyncClient(
                timeout=settings.model_timeout_seconds, follow_redirects=False
            ) as inference,
        ):
            model = ChatOpenAI(
                model=settings.openai_model,
                base_url=settings.openai_base_url,
                api_key=settings.openai_api_key.get_secret_value(),
                timeout=settings.model_timeout_seconds,
                max_retries=0,
                max_tokens=settings.model_max_tokens,
                use_responses_api=False,
                http_async_client=inference,
            )
            app.state.service = RoutingService(
                LangChainRoutingAgent(model, model_health, settings.openai_model),
                HttpDeliveryGateway(mailer),
            )
            yield

    app = FastAPI(
        title="AI Message Router",
        version="1.0.0",
        docs_url="/api/v1/docs",
        openapi_url="/api/v1/openapi.json",
        redoc_url=None,
        lifespan=lifespan,
    )
    install_routes(app)
    return app


app = create_app()
