from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="AGENT_")

    app_name: str = "Agent API"
    api_prefix: str = "/api/v1"
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    cart_api_url: str = "http://cart_api:8001"
    mcp_mock_enabled: bool = True
    mcp_search_url: str = ""
    mcp_api_key: str = ""
    mcp_timeout_seconds: float = 8.0


settings = Settings()
