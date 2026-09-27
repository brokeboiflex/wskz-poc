from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    openai_base_url: str = "http://ollama:11434/v1"
    openai_api_key: SecretStr = SecretStr("ollama")
    openai_model: str = "gemma4:e2b"
    model_timeout_seconds: float = Field(default=180, gt=0, le=600)
    model_trace: bool = False
    model_tool_choice: Literal["auto", "required", "named"] | None = "required"
    model_max_tokens: int = Field(default=1024, ge=64, le=8192)
    model_token_limit_field: Literal["max_tokens", "max_completion_tokens"] = "max_tokens"
    model_reasoning_effort: str | None = "none"
    model_temperature: float | None = Field(default=0, ge=0, le=2)
    model_top_p: float | None = Field(default=0.8, gt=0, le=1)

    @field_validator(
        "model_reasoning_effort",
        "model_temperature",
        "model_top_p",
        "model_tool_choice",
        mode="before",
    )
    @classmethod
    def omit_empty_options(cls, value):
        # An empty env value explicitly omits a field for providers without support.
        return None if value == "" else value

    mailer_base_url: str = "http://mailer:8000"
    mailer_token: SecretStr = SecretStr("local-poc-mailer-token")
    mailer_timeout_seconds: float = Field(default=40, gt=0, le=120)
