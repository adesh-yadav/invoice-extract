"""Server-selected chat model adapters; no client request can choose a provider."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal
from langchain_core.language_models.chat_models import BaseChatModel

Provider = Literal["openai", "anthropic", "ollama"]
DEFAULT_MODELS: dict[str, str] = {
    "openai": "gpt-4.1-mini",
    "anthropic": "claude-haiku-4-5-20251001",
    "ollama": "gemma3:4b",
}


@dataclass(frozen=True)
class ModelConfig:
    provider: Provider
    model: str
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    ollama_base_url: str = "http://ollama:11434"

    @property
    def resolved_model(self) -> str:
        return self.model.strip() or DEFAULT_MODELS[self.provider]

    @property
    def ready(self) -> bool:
        if self.provider == "openai":
            return bool(self.openai_api_key.strip())
        if self.provider == "anthropic":
            return bool(self.anthropic_api_key.strip())
        return True


def create_chat_model(config: ModelConfig) -> BaseChatModel:
    if config.provider == "openai":
        if not config.openai_api_key.strip():
            raise ValueError("OPENAI_API_KEY_MISSING")
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=config.resolved_model, api_key=config.openai_api_key, temperature=0, timeout=90, max_retries=1)
    if config.provider == "anthropic":
        if not config.anthropic_api_key.strip():
            raise ValueError("ANTHROPIC_API_KEY_MISSING")
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=config.resolved_model, anthropic_api_key=config.anthropic_api_key, max_tokens=8192, timeout=90, max_retries=1)
    if config.provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(model=config.resolved_model, base_url=config.ollama_base_url, temperature=0, num_ctx=8192, num_predict=4096, client_kwargs={"timeout": 300.0})
    raise ValueError("UNSUPPORTED_LLM_PROVIDER")
