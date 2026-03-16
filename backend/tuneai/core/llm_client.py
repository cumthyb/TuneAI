from __future__ import annotations

from typing import Any


def build_chat_openai(
    cfg: dict[str, Any],
    *,
    default_model: str,
    default_temperature: float,
    default_max_tokens: int,
    default_timeout_seconds: float,
) -> Any:
    """
    统一创建 OpenAI-compatible Chat client（LangChain ChatOpenAI）。
    """
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=cfg.get("model", default_model),
        base_url=cfg.get("base_url") or None,
        api_key=cfg.get("api_key") or "dummy",
        temperature=cfg.get("temperature", default_temperature),
        max_tokens=cfg.get("max_tokens", default_max_tokens),
        timeout=float(cfg.get("timeout_seconds", default_timeout_seconds)),
    )


def get_text_llm_config() -> dict[str, Any]:
    from tuneai.config import get_llm_config

    return get_llm_config()


def get_vision_llm_config() -> dict[str, Any]:
    from tuneai.config import get_vision_llm_config

    return get_vision_llm_config()
