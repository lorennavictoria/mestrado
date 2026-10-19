from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class PrognosisConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PROG_", env_file=".env", extra="ignore")

    ollama_base_url: str = "http://localhost:11434"
    model: str = "qwen2.5:7b"
    temperature: float = 0.2
    request_timeout_seconds: float = 900.0
    max_output_tokens: int = 768


@lru_cache
def get_config() -> PrognosisConfig:
    return PrognosisConfig()
