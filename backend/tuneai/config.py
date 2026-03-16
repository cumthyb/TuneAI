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
    for name in ("config.json", "config.example.json"):
        p = _CONFIG_DIR / name
        if p.is_file():
            return p
    raise FileNotFoundError(f"未找到 config.json 或 config.example.json，目录: {_CONFIG_DIR}")


def _provider_entry(cfg: dict[str, Any], provider: str) -> dict[str, Any]:
    providers = cfg.get("providers")
    if not isinstance(providers, dict):
        raise ValueError("providers must be an object")
    if provider not in providers:
        raise ValueError(f"provider is not registered: {provider}")
    entry = providers.get(provider)
    if not isinstance(entry, dict):
        raise ValueError(f"provider entry must be an object: {provider}")
    return entry


def _overlay_provider_section(
    cfg: dict[str, Any],
    *,
    provider: str,
    section: str,
    updates: dict[str, Any],
) -> None:
    entry = _provider_entry(cfg, provider)
    section_cfg = entry.setdefault(section, {})
    if not isinstance(section_cfg, dict):
        section_cfg = {}
        entry[section] = section_cfg
    section_cfg.update({k: v for k, v in updates.items() if v is not None})


def load_config() -> dict[str, Any]:
    cfg = _load_json(_find_config())

    if port := os.getenv("TUNEAI_PORT"):
        try:
            cfg.setdefault("server", {})["port"] = int(port)
        except ValueError:
            pass
    if level := os.getenv("TUNEAI_LOG_LEVEL"):
        cfg.setdefault("logging", {})["level"] = level

    policy = cfg.get("provider_policy")
    if not isinstance(policy, dict):
        raise ValueError("provider_policy must be an object")
    default_provider = str(policy.get("default_provider") or "").strip().lower()
    policy["default_provider"] = default_provider

    env_provider = os.getenv("TUNEAI_PROVIDER")
    if env_provider:
        default_provider = env_provider.strip().lower()
        policy["default_provider"] = default_provider

    if not default_provider:
        raise ValueError("default_provider must be explicitly configured")

    providers = cfg.get("providers")
    if not isinstance(providers, dict):
        raise ValueError("providers must be an object")
    if default_provider not in providers:
        raise ValueError(f"default_provider is not registered: {default_provider}")

    text_provider = (os.getenv("TUNEAI_LLM_PROVIDER") or default_provider).strip().lower()
    vision_provider = (os.getenv("TUNEAI_VISION_LLM_PROVIDER") or default_provider).strip().lower()
    ocr_provider = (os.getenv("TUNEAI_OCR_PROVIDER") or default_provider).strip().lower()

    if key := os.getenv("TUNEAI_LLM_API_KEY"):
        _overlay_provider_section(cfg, provider=text_provider, section="llm", updates={"api_key": key})
    if base_url := os.getenv("TUNEAI_LLM_BASE_URL"):
        _overlay_provider_section(cfg, provider=text_provider, section="llm", updates={"base_url": base_url})
    if model := os.getenv("TUNEAI_LLM_MODEL"):
        _overlay_provider_section(cfg, provider=text_provider, section="llm", updates={"model": model})

    if key := os.getenv("TUNEAI_VISION_LLM_API_KEY"):
        _overlay_provider_section(cfg, provider=vision_provider, section="vision_llm", updates={"api_key": key})
    if base_url := os.getenv("TUNEAI_VISION_LLM_BASE_URL"):
        _overlay_provider_section(cfg, provider=vision_provider, section="vision_llm", updates={"base_url": base_url})
    if model := os.getenv("TUNEAI_VISION_LLM_MODEL"):
        _overlay_provider_section(cfg, provider=vision_provider, section="vision_llm", updates={"model": model})

    ocr_updates = {
        "runner": os.getenv("TUNEAI_OCR_RUNNER"),
        "access_key_id": os.getenv("TUNEAI_OCR_ACCESS_KEY_ID"),
        "access_key_secret": os.getenv("TUNEAI_OCR_ACCESS_KEY_SECRET"),
        "endpoint": os.getenv("TUNEAI_OCR_ENDPOINT"),
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


def get_provider_policy() -> dict[str, Any]:
    policy = get_config().get("provider_policy")
    if not isinstance(policy, dict):
        raise ValueError("provider_policy must be an object")
    return policy


def get_default_provider() -> str:
    provider = str(get_provider_policy().get("default_provider") or "").strip().lower()
    if not provider:
        raise ValueError("default_provider must be explicitly configured")
    if provider not in get_providers_config():
        raise ValueError(f"default_provider is not registered: {provider}")
    return provider


def get_providers_config() -> dict[str, Any]:
    providers = get_config().get("providers")
    if not isinstance(providers, dict):
        raise ValueError("providers must be an object")
    return providers


def list_registered_providers() -> list[str]:
    providers = [str(k).strip().lower() for k in get_providers_config().keys() if str(k).strip()]
    return sorted(set(providers))


def get_provider_config(provider: str | None = None) -> dict[str, Any]:
    selected = (provider or get_default_provider()).strip().lower()
    providers = get_providers_config()
    raw = providers.get(selected, {})
    return raw if isinstance(raw, dict) else {}


def get_llm_config(provider: str | None = None) -> dict[str, Any]:
    return get_provider_config(provider).get("llm", {}) or {}


def get_vision_llm_config(provider: str | None = None) -> dict[str, Any]:
    return get_provider_config(provider).get("vision_llm", {}) or {}


def get_ocr_config(provider: str | None = None) -> dict[str, Any]:
    return get_provider_config(provider).get("ocr", {}) or {}


def get_pipeline_config() -> dict[str, Any]:
    return get_config().get("pipeline", {})


def get_logging_config() -> dict[str, Any]:
    return get_config().get("logging", {})


def get_frontend_config() -> dict[str, Any]:
    return get_config().get("frontend", {})


def get_server_host() -> str:
    return get_config().get("server", {}).get("host", "0.0.0.0")


def get_server_port() -> int:
    return get_config().get("server", {}).get("port", 8000)


def get_frontend_mode() -> str:
    return get_frontend_config().get("mode", "build")


def get_frontend_build_dir() -> Path:
    d = get_frontend_config().get("build_dir", "frontend/dist")
    return _CONFIG_DIR / d


def get_logs_dir() -> Path:
    d = get_logging_config().get("log_dir", "data/logs")
    p = _CONFIG_DIR / d
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_samples_dir() -> Path:
    d = get_pipeline_config().get("samples_dir", "data/samples")
    return _CONFIG_DIR / d


def get_outputs_dir() -> Path:
    d = get_pipeline_config().get("outputs_dir", "data/outputs")
    p = _CONFIG_DIR / d
    p.mkdir(parents=True, exist_ok=True)
    return p
