from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    es_url: str = ""
    es_api_key: str = ""
    kibana_url: str = ""
    kibana_api_key: str = ""
    github_token: str = ""
    github_repo: str = ""
    github_client_id: str = ""
    github_client_secret: str = ""
    debug: bool = False
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
