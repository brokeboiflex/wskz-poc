"""Offline LangChain schema comparison; creates diagnostic payloads, no inference."""

import json
from pathlib import Path
from typing import Annotated, Literal

import httpx
from langchain.tools import tool
from langchain_core.tools import StructuredTool
from langchain_core.utils.function_calling import convert_to_openai_tool
from router_app.adapters.agent import DECISION_INSTRUCTIONS, DEPARTMENT_CRITERIA, SendArguments
from router_app.config import Settings
from router_app.main import build_model

HERE = Path(__file__).resolve().parent
PREVIOUS = HERE.parent / "observed-debug"
criteria = " ".join(f"{key}: {value}" for key, value in DEPARTMENT_CRITERIA.items())
description = "Send the original message to exactly one department. " + criteria


async def send_department_email(department: str) -> str:
    """Forward the original request to the selected department by email."""
    raise RuntimeError("Schema-only diagnostic; never execute tools")


manual = StructuredTool.from_function(
    coroutine=send_department_email,
    name="send_department_email",
    description=description,
    args_schema=SendArguments.model_json_schema(),
    return_direct=True,
)
decorated = tool(
    "send_department_email",
    description=description,
    args_schema=SendArguments.model_json_schema(),
    return_direct=True,
)(send_department_email)
assert convert_to_openai_tool(manual) == convert_to_openai_tool(decorated)


@tool("send_department_email", return_direct=True)
async def simple_send(
    department: Annotated[
        Literal["human_resources", "payroll", "help_desk", "it", "other"],
        DECISION_INSTRUCTIONS + " " + criteria,
    ],
) -> str:
    """Forward the original request to the selected department by email."""
    raise RuntimeError("Schema-only diagnostic; never execute tools")


schema = convert_to_openai_tool(simple_send)
# Preserve the existing no-extra-arguments contract in the diagnostic variant.
schema["function"]["parameters"]["additionalProperties"] = False
for number in [25, 51]:
    payload = json.loads((PREVIOUS / f"case-{number:03d}-wire-request.json").read_text())
    payload["tools"] = [schema]
    (HERE / f"case-{number:03d}-simple-request.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    )
print(
    json.dumps(
        {"decorator_equals_current_wire_schema": True, "simple_schema": schema},
        ensure_ascii=False,
        indent=2,
    )
)

# Offline binding only: ask LangChain to encode named tool choice in its own format.
payload = json.loads((PREVIOUS / "case-051-wire-request.json").read_text())
model = build_model(Settings(openai_api_key="unused-offline"), httpx.AsyncClient())
named = model.bind_tools([manual], tool_choice="send_department_email")
assert named.kwargs["tools"] == payload["tools"]
payload["tool_choice"] = named.kwargs["tool_choice"]
(HERE / "case-051-named-request.json").write_text(
    json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
)
