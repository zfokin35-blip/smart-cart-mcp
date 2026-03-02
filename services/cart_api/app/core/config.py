from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="CART_")

    app_name: str = "Cart API"
    api_prefix: str = "/api/v1"
    database_url: str = "postgresql+psycopg2://cart:cart@postgres:5432/cartdb"
    redis_url: str = "redis://redis:6379/0"


settings = Settings()
