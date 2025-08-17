from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "ChatServer"
    debug: bool = True
    api_version: str = "v1"
    port: int = 8000
    
    # Database
    database_url: str
    redis_url: str
    
    # Snowflake
    snowflake_account: str
    snowflake_user: str
    snowflake_password: str
    snowflake_warehouse: str = "COMPUTE_WH"
    snowflake_database: str
    snowflake_schema: str = "PUBLIC"
    snowflake_role: str = "READONLY_ROLE"
    
    # LLM
    openai_api_key: str
    llm_model: str = "gpt-4-turbo-preview"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 2000
    
    # Security
    secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # Rate limiting
    rate_limit_per_minute: int = 60
    websocket_rate_limit: int = 100
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()