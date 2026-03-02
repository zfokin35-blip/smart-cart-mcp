import asyncio
import importlib.util
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
module_path = (
    ROOT / "services" / "agent_api" / "app" / "clients" / "deepseek_client.py"
)
spec = importlib.util.spec_from_file_location("deepseek_client", module_path)
deepseek_client = importlib.util.module_from_spec(spec)
spec.loader.exec_module(deepseek_client)
DeepSeekClient = deepseek_client.DeepSeekClient


class FakeResponse:
    def __init__(self, content: str):
        self._content = content

    def raise_for_status(self):
        return None

    def json(self):
        return {"choices": [{"message": {"content": self._content}}]}


class FakeAsyncClient:
    def __init__(self, content: str, *args, **kwargs):
        self._content = content

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, *args, **kwargs):
        return FakeResponse(self._content)


def test_extract_action_parses_json_and_normalizes_qty_word():
    llm_content = """```json
    {"tool":"add_to_cart","arguments":{"product_id":"p1","title":"Яблоко","qty":"одно","unit_price":120}}
    ```"""
    client = DeepSeekClient(api_key="k", base_url="http://test", model="deepseek-chat")

    with patch.object(
        deepseek_client.httpx,
        "AsyncClient",
        side_effect=lambda *a, **kw: FakeAsyncClient(llm_content, *a, **kw),
    ):
        result = asyncio.run(
            client.extract_action("Яблоко одно", [{"id": "p1", "title": "Яблоко", "price": 120}])
        )

    assert result["tool"] == "add_to_cart"
    assert result["arguments"]["qty"] == 1
    assert result["arguments"]["product_id"] == "p1"


def test_extract_action_falls_back_when_json_is_invalid():
    client = DeepSeekClient(api_key="k", base_url="http://test", model="deepseek-chat")

    with patch.object(
        deepseek_client.httpx,
        "AsyncClient",
        side_effect=lambda *a, **kw: FakeAsyncClient("not a json response", *a, **kw),
    ):
        result = asyncio.run(
            client.extract_action("Яблоко одно", [{"id": "p2", "title": "Яблоко", "price": 99}])
        )

    assert result["tool"] == "add_to_cart"
    assert result["arguments"] == {
        "product_id": "p2",
        "title": "Яблоко",
        "qty": 1,
        "unit_price": 99.0,
    }
