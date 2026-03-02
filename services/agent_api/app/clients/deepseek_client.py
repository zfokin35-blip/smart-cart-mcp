import json
import re
from typing import Any

import httpx


def _extract_json_object(content: str) -> dict:
    """
    Пытается вытащить JSON-объект из:
    - чистого JSON
    - markdown code block
    - текста с JSON внутри
    """
    if not content:
        return {}

    stripped = content.strip()

    # убираем ```json ... ```
    if stripped.startswith("```"):
        stripped = stripped.strip("`").strip()
        if stripped.lower().startswith("json"):
            stripped = stripped[4:].strip()

    # ищем первую { и последнюю }
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return {}

    candidate = stripped[start : end + 1]
    try:
        parsed = json.loads(candidate)
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


def _tokenize(text: str) -> set[str]:
    tokens = re.findall(r"[A-Za-zА-Яа-я0-9]+", (text or "").lower())
    return {t for t in tokens if len(t) >= 2}


def _best_match_product(user_text: str, catalog_items: list[dict]) -> dict:
    if not catalog_items:
        return {}
    q = _tokenize(user_text)
    if not q:
        return catalog_items[0]

    best = catalog_items[0]
    best_score = -1
    for p in catalog_items:
        title = str(p.get("title", ""))
        score = len(q & _tokenize(title))
        if score > best_score:
            best_score = score
            best = p
    return best


class DeepSeekClient:
    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def extract_action(self, user_text: str, catalog_items: list[dict]) -> dict:
        # Умный дефолт: не первый элемент, а best match по словам
        default_item = _best_match_product(user_text, catalog_items)
        default_arguments = {
            "product_id": str(default_item.get("id", "unknown")),
            "title": str(default_item.get("title", user_text)),
            "qty": 1,
            "unit_price": float(default_item.get("price", 0) or 0),
        }

        # Если нет ключа — без LLM, только best-match
        if not self.api_key:
            return {"tool": "add_to_cart", "arguments": default_arguments}

        # Просим СТРОГО JSON (без текста), выбирая ТОЛЬКО из каталога
        catalog_view = [
            {"id": str(x.get("id")), "title": str(x.get("title")), "price": x.get("price")}
            for x in (catalog_items[:8] if catalog_items else [])
        ]

        system = (
            "You are a tool planner for a grocery cart service. "
            "Return ONLY a valid JSON object, no markdown, no commentary."
        )
        user = (
            "Choose ONE product from the catalog that best matches user input. "
            "Return JSON in this format:\n"
            '{ "tool": "add_to_cart", "arguments": { "product_id": "<id from catalog>", '
            '"title": "<title from catalog>", "qty": <int>, "unit_price": <number> } }\n'
            f"User input: {user_text}\n"
            f"Catalog: {json.dumps(catalog_view, ensure_ascii=False)}\n"
            "Rules:\n"
            "- product_id MUST be one of catalog ids\n"
            "- qty default 1 if not specified\n"
            "- unit_price MUST match catalog price for выбранного товара\n"
        )

        content = ""
        try:
            async with httpx.AsyncClient(timeout=25) as client:
                resp = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system},
                            {"role": "user", "content": user},
                        ],
                        "temperature": 0,
                    },
                )
                resp.raise_for_status()
                content = resp.json()["choices"][0]["message"]["content"]
        except Exception as exc:
            # LLM упал — возвращаем дефолт по best match
            print(f"[DeepSeekClient] request failed: {exc}")
            return {"tool": "add_to_cart", "arguments": default_arguments}

        parsed = _extract_json_object(content)
        arguments = parsed.get("arguments") if isinstance(parsed.get("arguments"), dict) else {}

        # Валидация: product_id должен быть из каталога
        catalog_by_id = {str(p.get("id")): p for p in catalog_items}
        chosen_id = str(arguments.get("product_id", default_arguments["product_id"]))

        if chosen_id not in catalog_by_id:
            # если модель намудрила — fallback на best match
            chosen = default_item
        else:
            chosen = catalog_by_id[chosen_id]

        merged_arguments = {
            "product_id": str(chosen.get("id", default_arguments["product_id"])),
            "title": str(chosen.get("title", default_arguments["title"])),
            "qty": _normalize_qty(arguments.get("qty", default_arguments["qty"])),
            "unit_price": float(chosen.get("price", default_arguments["unit_price"]) or 0),
        }

        return {
            "tool": parsed.get("tool", "add_to_cart") if isinstance(parsed.get("tool"), str) else "add_to_cart",
            "arguments": merged_arguments,
        }
