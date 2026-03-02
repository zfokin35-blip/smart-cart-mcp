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
