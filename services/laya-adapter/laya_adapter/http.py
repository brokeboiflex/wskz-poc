"""Explicit, deliberately narrow OpenAI Chat Completions compatibility surface.

One enum-valued function argument is translated into a Laya typed choice. The
adapter has no mail addresses, SMTP access or routing policy of its own.
"""

import json
import time
from typing import Any, Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from .domain import AdapterError, Choice


class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: Literal["system", "user"]
    content: str = Field(min_length=1, max_length=4000)


class FunctionDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(pattern=r"^[A-Za-z_][A-Za-z0-9_]{0,63}$")
    description: str = Field(default="", max_length=4000)
    parameters: dict[str, Any]


class FunctionTool(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["function"]
    function: FunctionDefinition


class CompletionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    model: str
    messages: list[ChatMessage] = Field(min_length=1, max_length=2)
    tools: list[FunctionTool] = Field(min_length=1, max_length=1)
    stream: Literal[False] = False
    n: Literal[1] = 1
    tool_choice: Literal["auto", "required"] = "auto"
    max_tokens: int | None = Field(default=None, gt=0)
    max_completion_tokens: int | None = Field(default=None, gt=0)


def parse_choice(body: CompletionRequest) -> tuple[str, Choice]:
    users = [m for m in body.messages if m.role == "user"]
    if len(users) != 1 or body.messages[-1].role != "user":
        raise HTTPException(400, "one user message, optionally preceded by system, is required")
    definition = body.tools[0].function
    schema = definition.parameters
    properties = schema.get("properties", {})
    if schema.get("type") != "object" or not isinstance(properties, dict) or len(properties) != 1:
        raise HTTPException(400, "only a single enum-valued tool argument is supported")
    name, prop = next(iter(properties.items()))
    if not isinstance(prop, dict):
        raise HTTPException(400, "tool argument must have a JSON schema object")
    options = prop.get("enum", [])
    if (
        schema.get("required") != [name]
        or prop.get("type") != "string"
        or not isinstance(options, list)
        or not 2 <= len(options) <= 32
        or any(not isinstance(item, str) or not 1 <= len(item) <= 200 for item in options)
        or len(set(options)) != len(options)
    ):
        raise HTTPException(400, "a required string enum with 2-32 distinct choices is required")
    instructions = "\n".join(
        [
            *(m.content for m in body.messages if m.role == "system"),
            definition.description,
            str(prop.get("description", "")),
        ]
    )
    # Keep the model's context bounded. No silent input truncation by the adapter.
    if len((users[0].content + instructions + json.dumps(options)).encode()) > 7000:
        raise HTTPException(413, "Laya input exceeds the 7000-byte decision budget")
    return name, Choice(users[0].content, instructions, tuple(options))


def install_routes(app: FastAPI) -> None:
    @app.exception_handler(AdapterError)
    async def adapter_error(_request: Request, exc: AdapterError):
        return JSONResponse(
            {"error": {"message": str(exc), "type": "upstream_error"}}, status_code=502
        )

    @app.get("/health/ready", include_in_schema=False)
    async def ready(request: Request):
        healthy = await request.app.state.service.ready()
        return JSONResponse(
            {"status": "ready" if healthy else "unavailable"}, status_code=200 if healthy else 503
        )

    @app.get("/v1/models")
    async def models(request: Request):
        if not await request.app.state.service.ready():
            raise HTTPException(503, "decision engine unavailable")
        return {
            "object": "list",
            "data": [
                {
                    "id": request.app.state.model,
                    "object": "model",
                    "created": 0,
                    "owned_by": "local-laya-adapter",
                }
            ],
        }

    @app.post("/v1/chat/completions")
    async def complete(body: CompletionRequest, request: Request):
        if body.model != request.app.state.model:
            raise HTTPException(404, "unknown model")
        argument, choice = parse_choice(body)
        selected = await request.app.state.service.choose(choice)
        return {
            "id": "chatcmpl-" + uuid4().hex,
            "object": "chat.completion",
            "created": int(time.time()),
            "model": body.model,
            "choices": [
                {
                    "index": 0,
                    "finish_reason": "tool_calls",
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": "call_" + uuid4().hex,
                                "type": "function",
                                "function": {
                                    "name": body.tools[0].function.name,
                                    "arguments": json.dumps({argument: selected}),
                                },
                            }
                        ],
                    },
                }
            ],
        }
