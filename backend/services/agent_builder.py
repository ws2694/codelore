"""Client for the Elastic Agent Builder API (via Kibana)."""

import logging

import httpx
from backend.config import get_settings

logger = logging.getLogger(__name__)


class AgentBuilderClient:
    def __init__(self):
        settings = get_settings()
        self.kibana_url = settings.kibana_url.rstrip("/")
        self.headers = {
            "Authorization": f"ApiKey {settings.kibana_api_key}",
            "kbn-xsrf": "true",
            "Content-Type": "application/json",
        }

    async def converse(
        self,
        message: str,
        agent_id: str = "codelore-agent",
        conversation_id: str | None = None,
    ) -> dict:
        """Send a message to the Agent Builder and get a response."""
        payload = {
            "input": message,
            "agent_id": agent_id,
        }
        if conversation_id:
            payload["conversation_id"] = conversation_id

        async with httpx.AsyncClient(headers=self.headers, timeout=90.0) as client:
            resp = await client.post(
                f"{self.kibana_url}/api/agent_builder/converse",
                json=payload,
            )
            if resp.status_code >= 400:
                logger.error("Agent Builder HTTP %d: %s", resp.status_code, resp.text[:500])
            resp.raise_for_status()
            data = resp.json()
            logger.info("Agent Builder response keys: %s", list(data.keys()) if isinstance(data, dict) else type(data).__name__)
            logger.debug("Agent Builder full response: %s", data)
            return data

    async def list_tools(self) -> list[dict]:
        async with httpx.AsyncClient(headers=self.headers, timeout=15.0) as client:
            resp = await client.get(f"{self.kibana_url}/api/agent_builder/tools")
            resp.raise_for_status()
            return resp.json()

    async def list_agents(self) -> list[dict]:
        async with httpx.AsyncClient(headers=self.headers, timeout=15.0) as client:
            resp = await client.get(f"{self.kibana_url}/api/agent_builder/agents")
            resp.raise_for_status()
            return resp.json()


_client: AgentBuilderClient | None = None


def get_agent_builder() -> AgentBuilderClient:
    global _client
    if _client is None:
        _client = AgentBuilderClient()
    return _client
