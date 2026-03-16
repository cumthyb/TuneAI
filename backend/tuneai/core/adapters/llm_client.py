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


def _load_client_class(path: str):
    module_name, sep, class_name = path.rpartition(".")
    if not sep or not module_name or not class_name:
        raise ValueError(f"invalid client_class path: {path!r}")
    module = importlib.import_module(module_name)
    return getattr(module, class_name)


def _resolve_client_class(cfg: dict[str, Any]):
    class_path = cfg.get("client_class")
    if not isinstance(class_path, str) or not class_path.strip():
        raise ValueError("llm.client_class must be a non-empty string")
    return _load_client_class(class_path)


def _required_string(cfg: dict[str, Any], key: str) -> str:
    value = cfg.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"llm.{key} must be a non-empty string")
    return value


def _required_number(cfg: dict[str, Any], key: str) -> float:
    value = cfg.get(key)
    if not isinstance(value, (int, float)):
        raise ValueError(f"llm.{key} must be a number")
    return float(value)


def _required_object(cfg: dict[str, Any], key: str) -> dict[str, Any]:
    value = cfg.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"llm.{key} must be an object")
    return value


def list_supported_providers() -> list[str]:
    return list_registered_providers()


def _apply_provider_override(cfg: dict[str, Any], provider: str | None) -> dict[str, Any]:
    if not provider:
        return cfg
    next_cfg = dict(cfg)
    target = str(provider).strip().lower()
    next_cfg["provider"] = target
    return next_cfg


def build_chat_openai(cfg: dict[str, Any]) -> Any:
    client_cls = _resolve_client_class(cfg)
    client_kwargs = _required_object(cfg, "client_kwargs")
    kwargs = {
        "model": _required_string(cfg, "model"),
        "base_url": _required_string(cfg, "base_url"),
        "api_key": _required_string(cfg, "api_key"),
        "temperature": _required_number(cfg, "temperature"),
        "max_tokens": int(_required_number(cfg, "max_tokens")),
        "timeout": _required_number(cfg, "timeout_seconds"),
    }
    model_kwargs = _required_object(cfg, "model_kwargs")
    extra_body = _required_object(cfg, "extra_body")
    if model_kwargs:
        kwargs["model_kwargs"] = model_kwargs
    if extra_body:
        kwargs["extra_body"] = extra_body
    if cfg.get("disable_parallel_tool_calls") is True:
        kwargs["disabled_params"] = {"parallel_tool_calls": None}
    kwargs.update(client_kwargs)
    return client_cls(**kwargs)


def get_text_llm_config() -> dict[str, Any]:
    text_override, _, _ = get_provider_overrides()
    provider = text_override.strip().lower() if isinstance(text_override, str) else ""
    if not provider:
        provider = get_default_provider()
    cfg = dict(get_llm_config_from_registry(provider))
    cfg["provider"] = provider
    return _apply_provider_override(cfg, provider)


def get_vision_llm_config() -> dict[str, Any]:
    _, vision_override, _ = get_provider_overrides()
    provider = vision_override.strip().lower() if isinstance(vision_override, str) else ""
    if not provider:
        provider = get_default_provider()
    cfg = dict(get_vision_llm_config_from_registry(provider))
    cfg["provider"] = provider
    return _apply_provider_override(cfg, provider)
