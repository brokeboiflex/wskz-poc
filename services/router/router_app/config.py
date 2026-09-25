from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    openai_base_url: str = "http://ollama:11434/v1"
    openai_api_key: SecretStr = SecretStr("ollama")
    openai_model: str = "qwen3:1.7b"
    model_timeout_seconds: float = Field(default=180, gt=0, le=600)
    model_max_tokens: int = Field(default=1024, ge=64, le=8192)
    mailer_base_url: str = "http://mailer:8000"
    mailer_token: SecretStr = SecretStr("local-poc-mailer-token")
    mailer_timeout_seconds: float = Field(default=40, gt=0, le=120)
