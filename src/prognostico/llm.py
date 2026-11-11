from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Type

import httpx
from pydantic import BaseModel


class LLMClient(ABC):
    @abstractmethod
    def chat_json(self, system: str, user: str, *, schema: Type[BaseModel]) -> dict: ...


def build_message(task: str, context: dict) -> str:
    return f"[TASK {task}]\n\n{json.dumps(context, ensure_ascii=False, separators=(',', ':'))}"


def parse_structured_response(content: str, schema: Type[BaseModel]) -> dict:
    """Accept JSON returned with incidental Markdown fencing by local models."""
    normalized = content.strip()
    if normalized.startswith("```"):
        normalized = normalized.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    return schema.model_validate(json.loads(normalized)).model_dump()


class OllamaClient(LLMClient):
    def __init__(self, base_url: str, model: str, temperature: float = 0.2, request_timeout_seconds: float = 900.0, max_output_tokens: int = 768, *, think: bool = False) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self.think = think
        self._client = httpx.Client(timeout=httpx.Timeout(request_timeout_seconds, connect=15.0))

    def chat_json(self, system: str, user: str, *, schema: Type[BaseModel]) -> dict:
        last_error: Exception | None = None
        for attempt in range(3):
            correction = "" if not attempt else f"\nA resposta anterior falhou na validação: {last_error}. Corrija o JSON e responda somente no schema solicitado."
            content = ""
            try:
                chunks: list[str] = []
                payload = {
                    "model": self.model,
                    "stream": True,
                    "format": schema.model_json_schema(),
                    "think": self.think,
                    "options": {"temperature": self.temperature, "num_predict": self.max_output_tokens},
                    "messages": [{"role": "system", "content": system}, {"role": "user", "content": user + correction}],
                }
                with self._client.stream(
                    "POST",
                    f"{self.base_url}/api/chat",
                    json=payload,
                ) as response:
                    response.raise_for_status()
                    for line in response.iter_lines():
                        if line:
                            chunks.append(json.loads(line)["message"]["content"])
                content = "".join(chunks)
                return parse_structured_response(content, schema)
            except (httpx.HTTPError, KeyError, json.JSONDecodeError, ValueError) as error:
                last_error = ValueError(f"{error}; resposta recebida: {content[:800]!r}")
        raise ValueError(f"resposta estruturada inválida do LLM: {last_error}")


class LlamaCppClient(LLMClient):
    """Cliente para o endpoint OpenAI-compatível do llama-server."""

    def __init__(self, base_url: str, model: str, temperature: float = 0.2, request_timeout_seconds: float = 900.0, max_output_tokens: int = 768, *, disable_thinking: bool = False) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self.disable_thinking = disable_thinking
        self._client = httpx.Client(timeout=httpx.Timeout(request_timeout_seconds, connect=15.0))

    def chat_json(self, system: str, user: str, *, schema: Type[BaseModel]) -> dict:
        last_error: Exception | None = None
        for attempt in range(3):
            correction = "" if not attempt else f"\nA resposta anterior falhou na validação: {last_error}. Corrija o JSON e responda somente no schema solicitado."
            content = ""
            try:
                payload = {
                    "model": self.model,
                    "temperature": self.temperature,
                    "max_tokens": self.max_output_tokens,
                    "response_format": {
                        "type": "json_schema",
                        "json_schema": {"name": schema.__name__, "schema": schema.model_json_schema()},
                    },
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user + correction},
                    ],
                }
                if self.disable_thinking:
                    payload["chat_template_kwargs"] = {"enable_thinking": False}
                response = self._client.post(
                    f"{self.base_url}/v1/chat/completions",
                    json=payload,
                )
                response.raise_for_status()
                content = response.json()["choices"][0]["message"]["content"]
                return parse_structured_response(content, schema)
            except (httpx.HTTPError, KeyError, json.JSONDecodeError, ValueError) as error:
                last_error = ValueError(f"{error}; resposta recebida: {content[:800]!r}")
        raise ValueError(f"resposta estruturada inválida do llama.cpp: {last_error}")
