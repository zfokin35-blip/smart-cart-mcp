import httpx


class DeepSeekClient:
    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model

    async def extract_action(self, user_text: str, catalog_items: list[dict]) -> dict:
        if not self.api_key:
            return {
                "tool": "add_to_cart",
                "arguments": {
                    "product_id": (
                        catalog_items[0]["id"] if catalog_items else "unknown"
                    ),
                    "title": catalog_items[0]["title"] if catalog_items else user_text,
                    "qty": 1,
                    "unit_price": (
                        catalog_items[0].get("price", 0) if catalog_items else 0
                    ),
                },
            }

        prompt = (
            "Return JSON with tool and arguments for cart operation. "
            f"User input: {user_text}. Catalog: {catalog_items[:3]}"
        )
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0,
                },
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
        return {"tool": "raw", "arguments": {"content": content}}
