from __future__ import annotations

import json
import re
from typing import Iterable

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
        q = (query or "").strip()
        if self.mock_enabled:
            return self._mock_products(q)

        if not self.search_url:
            # вместо hard fail — пусть Agent скажет "не нашёл/сервис недоступен"
            return []

        try:
            if self.search_url.rstrip("/").endswith("/mcp"):
                products = await self._search_products_via_mcp_tool(q)
            else:
                products = await self._search_products_via_http_proxy(q)
        except Exception as exc:
            # не валим весь интент, просто возвращаем пусто
            print(f"[MCPRetailClient] search failed: {exc}")
            return []

        return self._normalize_products(products)

    async def _search_products_via_http_proxy(self, query: str) -> list[dict]:
        payload = {"query": query}
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(self.search_url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        if isinstance(data, dict):
            return data.get("items") or data.get("products") or []
        if isinstance(data, list):
            return data
        return []

    async def _search_products_via_mcp_tool(self, query: str) -> list[dict]:
        from mcp import ClientSession
        from mcp.client.streamable_http import streamablehttp_client

        headers: dict[str, str] = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        async with streamablehttp_client(
            self.search_url,
            timeout=self.timeout_seconds,
            headers=headers or None,
        ) as transport:
            read_stream, write_stream, _ = transport
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool(
                    "vkusvill_products_search",
                    {"q": query, "page": 1, "sort": "popularity"},
                )

        text_chunks: list[str] = []
        for content in result.content:
            text = getattr(content, "text", None)
            if text:
                text_chunks.append(text)

        raw_text = "\n".join(text_chunks).strip()
        if not raw_text:
            return []

        try:
            parsed = json.loads(raw_text)
        except Exception:
            return []

        if isinstance(parsed, dict):
            return parsed.get("products") or parsed.get("items") or []
        if isinstance(parsed, list):
            return parsed
        return []

    @staticmethod
    def _normalize_products(products: list[dict]) -> list[dict]:
        normalized: list[dict] = []
        for item in products:
            product_id = item.get("id") or item.get("product_id") or item.get("xml_id")
            title = item.get("title") or item.get("name")
            price_data = item.get("price")
            if isinstance(price_data, dict):
                price = price_data.get("current")
            else:
                price = price_data or item.get("unit_price")
            if product_id and title and price is not None:
                try:
                    normalized.append(
                        {
                            "id": str(product_id),
                            "title": str(title),
                            "price": float(price),
                        }
                    )
                except Exception:
                    continue
        return normalized

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        tokens = re.findall(r"[A-Za-zА-Яа-я0-9]+", (text or "").lower())
        return {t for t in tokens if len(t) >= 2}

    def _mock_products(self, query: str) -> list[dict]:
        """
        Mock-каталог НЕ должен всегда отдавать "молоко первым".
        Делает простой подбор по ключевым словам.
        """
        base = [
            {"id": "vv-001", "title": "Молоко 3.2%", "price": 129.9},
            {"id": "vv-002", "title": "Хлеб цельнозерновой", "price": 79.0},
            {"id": "vv-003", "title": "Бананы", "price": 119.0},
            {"id": "vv-004", "title": "Яйцо куриное C1 10 шт", "price": 139.0},
            {"id": "vv-005", "title": "Сыр Российский", "price": 219.0},
        ]

        q_tokens = self._tokenize(query)
        if not q_tokens:
            return base

        scored: list[tuple[int, dict]] = []
        for p in base:
            t_tokens = self._tokenize(p["title"])
            score = len(q_tokens & t_tokens)
            scored.append((score, p))

        scored.sort(key=lambda x: x[0], reverse=True)
        # если вообще ничего не совпало — вернем весь список как есть
        if scored[0][0] == 0:
            return base
        return [p for _, p in scored]
