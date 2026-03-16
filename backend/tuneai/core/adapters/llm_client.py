from __future__ import annotations

import importlib
from typing import Any


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
    from tuneai.config import get_llm_config

    return get_llm_config()


def get_vision_llm_config() -> dict[str, Any]:
    from tuneai.config import get_vision_llm_config

    return get_vision_llm_config()
