"""
配置中心：仅支持新的 providers 注册表格式（不兼容旧格式）。
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

_CONFIG_DIR = Path(__file__).resolve().parent.parent.parent


def _load_json(path: Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _find_config() -> Path:
    p = _CONFIG_DIR / "config.json"
    if p.is_file():
        return p
    raise FileNotFoundError(f"未找到 config.json，目录: {_CONFIG_DIR}")


def _require_object(parent: dict[str, Any], key: str) -> dict[str, Any]:
    value = parent.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"{key} must be an object")
    return value


def _require_string(parent: dict[str, Any], key: str) -> str:
    value = parent.get(key)
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    s = value.strip()
    if not s:
        raise ValueError(f"{key} must be a non-empty string")
    return s


def _normalize_provider_name(name: str) -> str:
    normalized = name.strip().lower()
    if not normalized:
        raise ValueError("provider name must be non-empty")
    return normalized


def _resolve_provider_env(var_name: str, configured_default: str) -> str:
    env_value = os.getenv(var_name)
    if env_value is None:
        return configured_default
    return _normalize_provider_name(env_value)


def _provider_entry(cfg: dict[str, Any], provider: str) -> dict[str, Any]:
    providers = _require_object(cfg, "providers")
    normalized = _normalize_provider_name(provider)
    if normalized not in providers:
        raise ValueError(f"provider is not registered: {provider}")
    entry = providers.get(normalized)
    if not isinstance(entry, dict):
        raise ValueError(f"provider entry must be an object: {normalized}")
    return entry


def _overlay_provider_section(
    cfg: dict[str, Any],
    *,
    provider: str,
    section: str,
    updates: dict[str, Any],
) -> None:
    entry = _provider_entry(cfg, provider)
    section_cfg = entry.get(section)
    if not isinstance(section_cfg, dict):
        raise ValueError(f"provider section must be an object: {provider}.{section}")
    section_cfg.update({k: v for k, v in updates.items() if v is not None})


def load_config() -> dict[str, Any]:
    cfg = _load_json(_find_config())
    if not isinstance(cfg, dict):
        raise ValueError("config root must be an object")

    if port := os.getenv("TUNEAI_PORT"):
        try:
            _require_object(cfg, "server")["port"] = int(port)
        except ValueError:
            raise ValueError("TUNEAI_PORT must be an integer") from None
    if level := os.getenv("TUNEAI_LOG_LEVEL"):
        _require_object(cfg, "logging")["level"] = level

    policy = _require_object(cfg, "provider_policy")
    default_provider = _normalize_provider_name(_require_string(policy, "default_provider"))
    policy["default_provider"] = default_provider

    env_provider = os.getenv("TUNEAI_PROVIDER")
    if env_provider:
        default_provider = _normalize_provider_name(env_provider)
        policy["default_provider"] = default_provider

    providers = _require_object(cfg, "providers")
    if default_provider not in providers:
        raise ValueError(f"default_provider is not registered: {default_provider}")

    text_provider = _resolve_provider_env("TUNEAI_LLM_PROVIDER", default_provider)
    vision_provider = _resolve_provider_env("TUNEAI_VISION_LLM_PROVIDER", default_provider)
    ocr_provider = _resolve_provider_env("TUNEAI_OCR_PROVIDER", default_provider)

    llm_updates = {
        "api_key": os.getenv("TUNEAI_LLM_API_KEY"),
        "base_url": os.getenv("TUNEAI_LLM_BASE_URL"),
        "model": os.getenv("TUNEAI_LLM_MODEL"),
    }
    if any(v is not None for v in llm_updates.values()):
        _overlay_provider_section(cfg, provider=text_provider, section="llm", updates=llm_updates)

    vision_updates = {
        "api_key": os.getenv("TUNEAI_VISION_LLM_API_KEY"),
        "base_url": os.getenv("TUNEAI_VISION_LLM_BASE_URL"),
        "model": os.getenv("TUNEAI_VISION_LLM_MODEL"),
    }
    if any(v is not None for v in vision_updates.values()):
        _overlay_provider_section(cfg, provider=vision_provider, section="vision_llm", updates=vision_updates)

    ocr_updates = {
        "api_key": os.getenv("TUNEAI_OCR_API_KEY"),
        "base_url": os.getenv("TUNEAI_OCR_BASE_URL"),
        "model": os.getenv("TUNEAI_OCR_MODEL"),
    }
    if any(v is not None for v in ocr_updates.values()):
        _overlay_provider_section(cfg, provider=ocr_provider, section="ocr", updates=ocr_updates)

    for provider_name, entry in providers.items():
        if not isinstance(entry, dict):
            raise ValueError(f"provider entry must be an object: {provider_name}")

    return cfg


_config: dict[str, Any] | None = None


def get_config() -> dict[str, Any]:
    global _config
    if _config is None:
        _config = load_config()
    return _config


def get_default_provider() -> str:
    return get_config()["provider_policy"]["default_provider"]


def list_registered_providers() -> list[str]:
    providers = get_config()["providers"]
    return sorted(str(k).strip().lower() for k in providers.keys() if str(k).strip())


def get_llm_config(provider: str | None = None) -> dict[str, Any]:
    p = _normalize_provider_name(provider if provider is not None else get_default_provider())
    entry = get_config()["providers"].get(p)
    if not isinstance(entry, dict):
        raise ValueError(f"provider entry must be an object: {p}")
    llm = entry.get("llm")
    if not isinstance(llm, dict):
        raise ValueError(f"no llm config for provider: {p}")
    return llm


def get_vision_llm_config(provider: str | None = None) -> dict[str, Any]:
    p = _normalize_provider_name(provider if provider is not None else get_default_provider())
    entry = get_config()["providers"].get(p)
    if not isinstance(entry, dict):
        raise ValueError(f"provider entry must be an object: {p}")
    vision_llm = entry.get("vision_llm")
    if not isinstance(vision_llm, dict):
        raise ValueError(f"no vision_llm config for provider: {p}")
    return vision_llm


def get_ocr_config(provider: str | None = None) -> dict[str, Any]:
    p = _normalize_provider_name(provider if provider is not None else get_default_provider())
    entry = get_config()["providers"].get(p)
    if not isinstance(entry, dict):
        raise ValueError(f"provider entry must be an object: {p}")
    ocr = entry.get("ocr")
    if not isinstance(ocr, dict):
        raise ValueError(f"no ocr config for provider: {p}")
    return ocr


def get_pipeline_config() -> dict[str, Any]:
    return _require_object(get_config(), "pipeline")


def get_logging_config() -> dict[str, Any]:
    return _require_object(get_config(), "logging")


def get_frontend_config() -> dict[str, Any]:
    return _require_object(get_config(), "frontend")


def get_server_host() -> str:
    return _require_string(get_config()["server"], "host")


def get_server_port() -> int:
    port = get_config()["server"].get("port")
    if not isinstance(port, int):
        raise ValueError("server.port must be an integer")
    if port <= 0:
        raise ValueError("server.port must be greater than 0")
    return port


def get_frontend_build_dir() -> Path:
    d = _require_string(get_frontend_config(), "build_dir")
    return _CONFIG_DIR / d


def get_logs_dir() -> Path:
    d = _require_string(get_logging_config(), "log_dir")
    p = _CONFIG_DIR / d
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_outputs_dir() -> Path:
    d = _require_string(get_pipeline_config(), "outputs_dir")
    p = _CONFIG_DIR / d
    p.mkdir(parents=True, exist_ok=True)
    return p
