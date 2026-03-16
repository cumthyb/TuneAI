from __future__ import annotations

import importlib
from typing import Any

from tuneai.core.adapters.provider_context import get_provider_overrides
from tuneai.config import (
    get_default_provider,
    get_llm_config as get_llm_config_from_registry,
    get_vision_llm_config as get_vision_llm_config_from_registry,
    list_registered_providers,
)


_PROVIDER_PRESETS: dict[str, dict[str, str]] = {
    # DashScope OpenAI-compatible endpoint for Qwen series.
    "qwen": {"base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"},
    # GLM OpenAI-compatible endpoint.
    "glm": {"base_url": "https://open.bigmodel.cn/api/paas/v4"},
}


def _load_client_class(path: str):
    module_name, sep, class_name = path.rpartition(".")
    if not sep or not module_name or not class_name:
        raise ValueError(f"invalid client_class path: {path!r}")
    module = importlib.import_module(module_name)
    return getattr(module, class_name)


def _resolve_client_class(cfg: dict[str, Any]):
    class_path = str(cfg.get("client_class") or "langchain_openai.ChatOpenAI")
    return _load_client_class(class_path)


def _resolved_base_url(cfg: dict[str, Any]) -> str | None:
    explicit = cfg.get("base_url")
    if explicit:
        return str(explicit)
    provider = str(cfg.get("provider") or "").strip().lower()
    if not provider:
        return None
    return _PROVIDER_PRESETS.get(provider, {}).get("base_url")


def list_supported_providers() -> list[str]:
    return list_registered_providers()


def _apply_provider_override(cfg: dict[str, Any], provider: str | None) -> dict[str, Any]:
    if not provider:
        return cfg
    next_cfg = dict(cfg)
    target = str(provider).strip().lower()
    current = str(cfg.get("provider") or "").strip().lower()
    next_cfg["provider"] = target
    # 切换供应商时，优先使用目标供应商预设 base_url，避免沿用旧供应商地址。
    if current and current != target and cfg.get("base_url"):
        next_cfg["base_url"] = ""
    return next_cfg


def build_chat_openai(
    cfg: dict[str, Any],
    *,
    default_model: str,
    default_temperature: float,
    default_max_tokens: int,
    default_timeout_seconds: float,
) -> Any:
    client_cls = _resolve_client_class(cfg)
    client_kwargs = dict(cfg.get("client_kwargs") or {})
    kwargs = {
        "model": cfg.get("model", default_model),
        "base_url": _resolved_base_url(cfg),
        "api_key": cfg.get("api_key") or "dummy",
        "temperature": cfg.get("temperature", default_temperature),
        "max_tokens": cfg.get("max_tokens", default_max_tokens),
        "timeout": float(cfg.get("timeout_seconds", default_timeout_seconds)),
    }
    if model_kwargs := cfg.get("model_kwargs"):
        kwargs["model_kwargs"] = model_kwargs
    if extra_body := cfg.get("extra_body"):
        kwargs["extra_body"] = extra_body
    if cfg.get("disable_parallel_tool_calls"):
        kwargs["disabled_params"] = {"parallel_tool_calls": None}
    kwargs.update(client_kwargs)
    return client_cls(**kwargs)


def get_text_llm_config() -> dict[str, Any]:
    text_override, _, _ = get_provider_overrides()
    provider = text_override or get_default_provider()
    cfg = dict(get_llm_config_from_registry(provider))
    cfg["provider"] = provider
    return _apply_provider_override(cfg, provider)


def get_vision_llm_config() -> dict[str, Any]:
    _, vision_override, _ = get_provider_overrides()
    provider = vision_override or get_default_provider()
    cfg = dict(get_vision_llm_config_from_registry(provider))
    cfg["provider"] = provider
    return _apply_provider_override(cfg, provider)
