"""HTTP clients for Kerq API — sync and async."""

import httpx

KERQ_API_BASE = "https://kerq.dev"
TELEMETRY_TIMEOUT = 2.0


class KerqClient:
    """Synchronous HTTP client for Kerq API."""

    def __init__(self, api_key: str, base_url: str = KERQ_API_BASE):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=TELEMETRY_TIMEOUT,
        )

    def get_trust_score(self, tool_id: str) -> dict:
        """Fetch trust score for a tool by ID."""
        response = self._client.get(f"/api/tools/{tool_id}/score")
        response.raise_for_status()
        return response.json()

    def report_telemetry(self, payload: dict) -> None:
        """Fire-and-forget telemetry report."""
        try:
            self._client.post("/api/v1/report", json=payload)
        except Exception:
            pass  # telemetry must never throw

    def close(self) -> None:
        self._client.close()


class AsyncKerqClient:
    """Asynchronous HTTP client for Kerq API."""

    def __init__(self, api_key: str, base_url: str = KERQ_API_BASE):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=TELEMETRY_TIMEOUT,
        )

    async def get_trust_score(self, tool_id: str) -> dict:
        """Fetch trust score for a tool by ID."""
        response = await self._client.get(f"/api/tools/{tool_id}/score")
        response.raise_for_status()
        return response.json()

    async def report_telemetry(self, payload: dict) -> None:
        """Fire-and-forget telemetry report."""
        try:
            await self._client.post("/api/v1/report", json=payload)
        except Exception:
            pass  # telemetry must never throw

    async def close(self) -> None:
        await self._client.close()
