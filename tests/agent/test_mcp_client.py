import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
module_path = ROOT / "services" / "agent_api" / "app" / "clients" / "mcp_client.py"
spec = importlib.util.spec_from_file_location("mcp_client", module_path)
mcp_client = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mcp_client)
MCPRetailClient = mcp_client.MCPRetailClient


@pytest.mark.asyncio
async def test_mcp_mock_mode_returns_products():
    client = MCPRetailClient(mock_enabled=True)
    products = await client.search_products("молоко")
    assert len(products) == 2
    assert products[0]["id"].startswith("vv-")


@pytest.mark.asyncio
async def test_mcp_real_mode_requires_url():
    client = MCPRetailClient(mock_enabled=False, search_url="")
    with pytest.raises(RuntimeError):
        await client.search_products("молоко")


@pytest.mark.asyncio
async def test_mcp_uses_streamable_mode_for_mcp_url(monkeypatch):
    client = MCPRetailClient(mock_enabled=False, search_url="https://mcp001.vkusvill.ru/mcp")

    async def fake_mcp(query):
        assert query == "йогурт"
        return [{"id": "1", "name": "Йогурт", "price": {"current": 99}}]

    async def fail_proxy(_query):
        raise AssertionError("proxy mode should not be used")

    monkeypatch.setattr(client, "_search_products_via_mcp_tool", fake_mcp)
    monkeypatch.setattr(client, "_search_products_via_http_proxy", fail_proxy)

    products = await client.search_products("йогурт")
    assert products == [{"id": "1", "title": "Йогурт", "price": 99.0}]


@pytest.mark.asyncio
async def test_mcp_uses_http_proxy_mode_for_non_mcp_url(monkeypatch):
    client = MCPRetailClient(mock_enabled=False, search_url="https://proxy.local/search")

    async def fake_proxy(query):
        assert query == "сыр"
        return [{"product_id": "2", "title": "Сыр", "unit_price": 159}]

    async def fail_mcp(_query):
        raise AssertionError("mcp mode should not be used")

    monkeypatch.setattr(client, "_search_products_via_http_proxy", fake_proxy)
    monkeypatch.setattr(client, "_search_products_via_mcp_tool", fail_mcp)

    products = await client.search_products("сыр")
    assert products == [{"id": "2", "title": "Сыр", "price": 159.0}]
