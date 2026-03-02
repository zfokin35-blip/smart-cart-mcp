from app.clients.cart_client import CartApiClient
from app.clients.deepseek_client import DeepSeekClient
from app.clients.mcp_client import MCPRetailClient
from app.core.config import settings
from app.services.agent_service import AgentService


def get_agent_service() -> AgentService:
    return AgentService(
        llm=DeepSeekClient(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
            model=settings.deepseek_model,
        ),
        mcp=MCPRetailClient(
            mock_enabled=settings.mcp_mock_enabled,
            search_url=settings.mcp_search_url,
            api_key=settings.mcp_api_key,
            timeout_seconds=settings.mcp_timeout_seconds,
        ),
        cart=CartApiClient(settings.cart_api_url),
    )
