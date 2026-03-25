"""
配置中心：Pydantic BaseSettings 模式，config.json 加载后经 Pydantic 验证，
解决测试隔离问题和全局可变状态。
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

_CONFIG_DIR = Path(__file__).resolve().parent.parent.parent


# ─── JSON 加载（不涉及 env 覆盖）───────────────────────────────────────────────

def _load_json(path: Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _find_config() -> Path:
    p = _CONFIG_DIR / "config.json"
    if p.is_file():
        return p
    raise FileNotFoundError(f"未找到 config.json，目录: {_CONFIG_DIR}")


# ─── Pydantic 模型定义 ────────────────────────────────────────────────────────

class LLMProviderModel(BaseModel):
    api_key: str = ""
    base_url: str = ""
    model: str = ""
    temperature: float = 0.1
    max_tokens: int = 1024
    timeout_seconds: float = 30.0
    client_class: str = "langchain_openai.ChatOpenAI"
    client_kwargs: dict[str, Any] = Field(default_factory=dict)
    model_kwargs: dict[str, Any] = Field(default_factory=dict)
    extra_body: dict[str, Any] = Field(default_factory=dict)
    disable_parallel_tool_calls: bool = False


class VisionLLMProviderModel(BaseModel):
    api_key: str = ""
    base_url: str = ""
    model: str = ""
    timeout_seconds: float = 30.0
    client_class: str = "langchain_openai.ChatOpenAI"
    client_kwargs: dict[str, Any] = Field(default_factory=dict)
    model_kwargs: dict[str, Any] = Field(default_factory=dict)
    extra_body: dict[str, Any] = Field(default_factory=dict)


class OCRProviderModel(BaseModel):
    api_key: str = ""
    base_url: str = ""
    model: str = ""
    timeout_seconds: float = 30.0
    max_tokens: int = 4096


class ProviderEntryModel(BaseModel):
    llm: LLMProviderModel | None = None
    vision_llm: VisionLLMProviderModel | None = None
    ocr: OCRProviderModel | None = None


class ServerConfigModel(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000


class FrontendConfigModel(BaseModel):
    build_dir: str = "frontend/dist"
    dev_port: int = 5173


class ProviderPolicyModel(BaseModel):
    default_provider: str = ""


class PipelineConfigModel(BaseModel):
    request_timeout_seconds: int = 60
    max_image_size_mb: int = 20
    outputs_dir: str = "data/outputs"
    cleanup_after_response: bool = True


class LoggingConfigModel(BaseModel):
    level: str = "INFO"
    format: str = "json"
    log_dir: str = "data/logs"
    log_file: str = "tuneai.log"
    rotation: str = "10 MB"
    retention: str = "7 days"


class TuneAIConfig(BaseModel):
    server: ServerConfigModel = Field(default_factory=ServerConfigModel)
    frontend: FrontendConfigModel = Field(default_factory=FrontendConfigModel)
    provider_policy: ProviderPolicyModel = Field(default_factory=ProviderPolicyModel)
    providers: dict[str, ProviderEntryModel] = Field(default_factory=dict)
    pipeline: PipelineConfigModel = Field(default_factory=PipelineConfigModel)
    logging: LoggingConfigModel = Field(default_factory=LoggingConfigModel)


# ─── 辅助函数 ─────────────────────────────────────────────────────────────────

def _normalize_provider_name(name: str) -> str:
    normalized = name.strip().lower()
    if not normalized:
        raise ValueError("provider name must be non-empty")
    return normalized


def _require_string(parent: dict[str, Any], key: str) -> str:
    value = parent.get(key)
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    s = value.strip()
    if not s:
        raise ValueError(f"{key} must be a non-empty string")
    return s


def _require_object(parent: dict[str, Any], key: str) -> dict[str, Any]:
    value = parent.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"{key} must be an object")
    return value


# ─── 配置加载（带 env 覆盖）────────────────────────────────────────────────────

def _apply_env_overrides(cfg: dict[str, Any]) -> None:
    """将环境变量覆盖到 cfg dict（in-place）。"""
    # server.port
    if port := os.getenv("TUNEAI_PORT"):
        try:
            _require_object(cfg, "server")["port"] = int(port)
        except ValueError:
            raise ValueError("TUNEAI_PORT must be an integer") from None
    # logging.level
    if level := os.getenv("TUNEAI_LOG_LEVEL"):
        _require_object(cfg, "logging")["level"] = level

    # provider_policy.default_provider
    policy = _require_object(cfg, "provider_policy")
    default_provider = _normalize_provider_name(_require_string(policy, "default_provider"))
    if env_provider := os.getenv("TUNEAI_PROVIDER"):
        default_provider = _normalize_provider_name(env_provider)

    providers = _require_object(cfg, "providers")
    if default_provider not in providers:
        raise ValueError(f"default_provider is not registered: {default_provider}")

    # Write back resolved default_provider (env override or original)
    policy["default_provider"] = default_provider

    # per-provider env overrides
    text_provider = os.getenv("TUNEAI_LLM_PROVIDER", default_provider)
    vision_provider = os.getenv("TUNEAI_VISION_LLM_PROVIDER", default_provider)
    ocr_provider = os.getenv("TUNEAI_OCR_PROVIDER", default_provider)

    for prov, section, env_prefix in [
        (text_provider, "llm", "TUNEAI_LLM"),
        (vision_provider, "vision_llm", "TUNEAI_VISION_LLM"),
        (ocr_provider, "ocr", "TUNEAI_OCR"),
    ]:
        normalized = _normalize_provider_name(prov)
        if normalized not in providers:
            continue
        entry = providers[normalized]
        if not isinstance(entry, dict):
            continue
        sec = entry.get(section)
        if not isinstance(sec, dict):
            continue
        for key in ("api_key", "base_url", "model"):
            if val := os.getenv(f"{env_prefix}_{key.upper()}"):
                sec[key] = val


def load_config() -> TuneAIConfig:
    """
    加载 config.json，应用环境变量覆盖，返回强类型的 TuneAIConfig 实例。
    每次调用返回新的实例（不共享状态）。
    """
    raw = _load_json(_find_config())
    if not isinstance(raw, dict):
        raise ValueError("config root must be an object")

    # 先应用 env 覆盖到原始 dict
    _apply_env_overrides(raw)

    # Pydantic 验证并转换（复制一份避免污染原始 raw）
    return TuneAIConfig.model_validate(raw)


# ─── 全局配置实例（lifespan 管理）──────────────────────────────────────────────

_config: TuneAIConfig | None = None


def get_config() -> TuneAIConfig:
    """返回全局 TuneAIConfig 实例（由 lifespan 初始化）。"""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def reset_config() -> None:
    """重置全局配置（用于测试隔离）。"""
    global _config
    _config = None


def set_config(cfg: TuneAIConfig) -> None:
    """设置全局配置实例（用于测试注入）。"""
    global _config
    _config = cfg


def reload_config() -> TuneAIConfig:
    """清除全局缓存并重新加载 config.json。用于运行时热更新。"""
    global _config
    _config = None
    _config = load_config()
    return _config


# ─── 各域配置访问器 ───────────────────────────────────────────────────────────

def get_default_provider() -> str:
    return get_config().provider_policy.default_provider


def list_registered_providers() -> list[str]:
    providers = get_config().providers
    return sorted(str(k).strip().lower() for k in providers.keys() if str(k).strip())


def get_llm_config(provider: str | None = None) -> dict[str, Any]:
    p = _normalize_provider_name(provider if provider is not None else get_default_provider())
    entry = get_config().providers.get(p)
    if entry is None:
        raise ValueError(f"provider is not registered: {p}")
    llm = entry.llm
    if llm is None:
        raise ValueError(f"no llm config for provider: {p}")
    return llm.model_dump()


def get_vision_llm_config(provider: str | None = None) -> dict[str, Any]:
    p = _normalize_provider_name(provider if provider is not None else get_default_provider())
    entry = get_config().providers.get(p)
    if entry is None:
        raise ValueError(f"provider is not registered: {p}")
    vl = entry.vision_llm
    if vl is None:
        raise ValueError(f"no vision_llm config for provider: {p}")
    return vl.model_dump()


def get_ocr_config(provider: str | None = None) -> dict[str, Any]:
    p = _normalize_provider_name(provider if provider is not None else get_default_provider())
    entry = get_config().providers.get(p)
    if entry is None:
        raise ValueError(f"provider is not registered: {p}")
    ocr = entry.ocr
    if ocr is None:
        raise ValueError(f"no ocr config for provider: {p}")
    return ocr.model_dump()


def get_pipeline_config() -> dict[str, Any]:
    return get_config().pipeline.model_dump()


def get_logging_config() -> dict[str, Any]:
    return get_config().logging.model_dump()


def get_frontend_config() -> dict[str, Any]:
    return get_config().frontend.model_dump()


def get_server_host() -> str:
    return get_config().server.host


def get_server_port() -> int:
    return get_config().server.port


def get_frontend_build_dir() -> Path:
    return _CONFIG_DIR / get_config().frontend.build_dir


def get_logs_dir() -> Path:
    p = _CONFIG_DIR / get_config().logging.log_dir
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_outputs_dir() -> Path:
    p = _CONFIG_DIR / get_config().pipeline.outputs_dir
    p.mkdir(parents=True, exist_ok=True)
    return p
