from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class PrognosisConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PROG_", env_file=".env", extra="ignore")

    # ollama_base_url: str = "http://192.168.3.106:53317" # qwen
    # ollama_base_url: str = "http://192.168.3.37:53317" # gemma
    ollama_base_url: str = "http://192.168.30.221:11434"
    model: str = "qwen3.5:9b"
    temperature: float = 0.2
    request_timeout_seconds: float = 900.0
    max_output_tokens: int = 4096
    ollama_think: bool = False
    llama_disable_thinking: bool = True


@lru_cache
def get_config() -> PrognosisConfig:
    return PrognosisConfig()
