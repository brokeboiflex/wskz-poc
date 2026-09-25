from contextlib import asynccontextmanager

from fastapi import FastAPI

from .adapters.repository import SqliteDeliveryRepository
from .adapters.smtp import SmtpTransport
from .config import Settings
from .http import install_routes
from .service import DeliveryService


def create_app(service: DeliveryService | None = None, token: str | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        settings = Settings()
        app.state.token = token if token is not None else settings.mailer_token.get_secret_value()
        if not app.state.token:
            raise ValueError("MAILER_TOKEN cannot be empty")
        app.state.service = service or DeliveryService(
            SqliteDeliveryRepository(settings.database_path),
            SmtpTransport(
                settings.smtp_host,
                settings.smtp_port,
                str(settings.mail_from),
                settings.smtp_timeout_seconds,
            ),
            frozenset(address.strip() for address in settings.allowed_recipients.split(",")),
        )
        yield

    app = FastAPI(title="Mail delivery service", version="1.0.0", lifespan=lifespan)
    install_routes(app)
    return app


app = create_app()
