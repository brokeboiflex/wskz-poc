from pydantic import EmailStr, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")
    smtp_host: str = "mailpit"
    smtp_port: int = Field(default=1025, ge=1, le=65535)
    smtp_timeout_seconds: float = Field(default=15, gt=0, le=30)
    mail_from: EmailStr = "router@example.com"
    mailer_token: SecretStr = SecretStr("local-poc-mailer-token")
    database_path: str = "/data/deliveries.sqlite3"
    allowed_recipients: str = "human-resources@example.com,help-desk@example.com,it@example.com,kadry@example.com,other@example.com"
