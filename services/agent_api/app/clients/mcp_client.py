from __future__ import annotations

import httpx


class MCPRetailClient:
    """VkusVill MCP product search client with mock fallback."""

    def __init__(
        self,
        *,
        mock_enabled: bool = True,
        search_url: str = "",
        api_key: str = "",
        timeout_seconds: float = 8.0,
    ) -> None:
        self.mock_enabled = mock_enabled
        self.search_url = search_url
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    async def search_products(self, query: str) -> list[dict]:
        if self.mock_enabled:
            return self._mock_products()

        if not self.search_url:
            raise RuntimeError(
                "AGENT_MCP_MOCK_ENABLED=false, но AGENT_MCP_SEARCH_URL не задан"
            )

        payload = {"query": query}
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(self.search_url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        if isinstance(data, dict):
            products = data.get("items") or data.get("products") or []
        elif isinstance(data, list):
            products = data
        else:
            products = []

        normalized: list[dict] = []
        for item in products:
            product_id = item.get("id") or item.get("product_id")
            title = item.get("title") or item.get("name")
            price = item.get("price") or item.get("unit_price")
            if product_id and title and price is not None:
                normalized.append(
                    {
                        "id": str(product_id),
                        "title": str(title),
                        "price": float(price),
                    }
                )
        return normalized

    @staticmethod
    def _mock_products() -> list[dict]:
        return [
            {"id": "vv-001", "title": "Молоко 3.2%", "price": 129.9},
            {"id": "vv-002", "title": "Хлеб цельнозерновой", "price": 79.0},
        ]
