import httpx
import json


def _extract_json_object(content: str) -> dict:
    """Parse JSON object from plain text or markdown code block."""
    stripped = content.strip()

    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped.startswith("json"):
            stripped = stripped[4:].strip()

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return {}

    try:
        parsed = json.loads(stripped[start : end + 1])
    except json.JSONDecodeError:
        return {}

    return parsed if isinstance(parsed, dict) else {}


def _normalize_qty(value) -> int:
    if isinstance(value, (int, float)):
        return max(1, int(value))

    if isinstance(value, str):
        lowered = value.strip().lower()
        word_to_num = {
            "one": 1,
            "single": 1,
            "один": 1,
            "одна": 1,
            "одно": 1,
            "два": 2,
            "две": 2,
            "три": 3,
        }
        if lowered in word_to_num:
            return word_to_num[lowered]
        try:
            return max(1, int(float(lowered)))
        except ValueError:
            return 1

    return 1


class DeepSeekClient:
    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model

    async def extract_action(self, user_text: str, catalog_items: list[dict]) -> dict:
        default_item = catalog_items[0] if catalog_items else {}
        default_arguments = {
            "product_id": default_item.get("id", "unknown"),
            "title": default_item.get("title", user_text),
            "qty": 1,
            "unit_price": default_item.get("price", 0),
        }

        if not self.api_key:
            return {"tool": "add_to_cart", "arguments": default_arguments}

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
        parsed = _extract_json_object(content)
        arguments = parsed.get("arguments") if isinstance(parsed.get("arguments"), dict) else {}
        merged_arguments = {
            "product_id": arguments.get("product_id", default_arguments["product_id"]),
            "title": arguments.get("title", default_arguments["title"]),
            "qty": _normalize_qty(arguments.get("qty", default_arguments["qty"])),
            "unit_price": float(arguments.get("unit_price", default_arguments["unit_price"])) if arguments.get("unit_price", default_arguments["unit_price"]) is not None else 0.0,
        }

        return {
            "tool": parsed.get("tool", "add_to_cart"),
            "arguments": merged_arguments,
        }
