import asyncio
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
module_path = ROOT / "services" / "agent_api" / "app" / "services" / "agent_service.py"
spec = importlib.util.spec_from_file_location("agent_service", module_path)
agent_service = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agent_service)
AgentService = agent_service.AgentService


class FakeLLM:
    async def extract_action(self, user_text, catalog_items):
        return {
            "tool": "add_to_cart",
            "arguments": {
                "product_id": "1",
                "title": "Тест",
                "qty": 1,
                "unit_price": 50.0,
            },
        }


class FakeMCP:
    async def search_products(self, query):
        return [{"id": "1", "title": "Тест", "price": 50.0}]


class FakeCart:
    async def create_cart(self, user_id):
        return 10

    async def add_item(self, cart_id, item):
        return {"total_amount": 50.0}


def test_process_message():
    service = AgentService(llm=FakeLLM(), mcp=FakeMCP(), cart=FakeCart())
    result = asyncio.run(service.process_message("u1", "добавь тест"))
    assert "50.0" in result["reply"]
    assert result["actions"][0]["tool"] == "add_to_cart"
