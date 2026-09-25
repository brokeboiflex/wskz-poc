import httpx

from .domain import AdapterError, Choice


class HttpDecisionEngine:
    def __init__(self, client: httpx.AsyncClient, model: str):
        self.client, self.model = client, model

    async def ready(self) -> bool:
        try:
            response = await self.client.get("health/ready", timeout=5)
            return response.status_code == 200
        except httpx.HTTPError:
            return False

    async def choose(self, choice: Choice) -> str:
        try:
            response = await self.client.post(
                "v1/systemone",
                json={
                    "model": self.model,
                    "state": choice.state,
                    "questions": {
                        "selection": {
                            "type": "choice",
                            "instructions": choice.instructions,
                            "criteria": dict(zip(choice.options, choice.descriptions, strict=True))
                            if choice.descriptions
                            else {item: item for item in choice.options},
                        }
                    },
                },
            )
            response.raise_for_status()
            return response.json()["answers"]["selection"]["choice"]
        except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
            raise AdapterError("decision_engine_unavailable") from exc
