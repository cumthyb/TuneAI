"""
从 config.json 加载配置：端口、API Key、LLM、OCR、流水线、日志等级等。
优先使用项目根目录的 config.json，不存在则用 config.example.json；敏感项可由环境变量覆盖。
"""
import json
import os
from pathlib import Path
from typing import Any

# 项目根目录（backend/tuneai/config.py -> 根目录）
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


def load_config() -> dict[str, Any]:
    path = _find_config()
    cfg = _load_json(path)
    # 环境变量覆盖（常用于 API Key、端口等）
    if api_keys := os.getenv("TUNEAI_OPENAI_API_KEY"):
        cfg.setdefault("api_keys", {})["openai"] = api_keys
    if api_keys := os.getenv("TUNEAI_ANTHROPIC_API_KEY"):
        cfg.setdefault("api_keys", {})["anthropic"] = api_keys
    if port := os.getenv("TUNEAI_PORT"):
        try:
            cfg.setdefault("server", {})["port"] = int(port)
        except ValueError:
            pass
    if level := os.getenv("TUNEAI_LOG_LEVEL"):
        cfg.setdefault("logging", {})["level"] = level
    return cfg


# 单例，首次访问时加载
_config: dict[str, Any] | None = None


def get_config() -> dict[str, Any]:
    global _config
    if _config is None:
        _config = load_config()
    return _config


def get_server_host() -> str:
    return get_config().get("server", {}).get("host", "0.0.0.0")


def get_server_port() -> int:
    return get_config().get("server", {}).get("port", 8000)


def get_api_key(service: str) -> str:
    return get_config().get("api_keys", {}).get(service, "") or os.getenv(f"TUNEAI_{service.upper()}_API_KEY", "")


def get_llm_config() -> dict[str, Any]:
    return get_config().get("llm", {})


def get_ocr_config() -> dict[str, Any]:
    return get_config().get("ocr", {})


def get_pipeline_config() -> dict[str, Any]:
    return get_config().get("pipeline", {})


def get_logging_config() -> dict[str, Any]:
    return get_config().get("logging", {})


def get_frontend_config() -> dict[str, Any]:
    return get_config().get("frontend", {})


def get_frontend_mode() -> str:
    """前端模式，仅支持 'build'（React/Vite 构建产物，方案 A 单端口）。"""
    return get_frontend_config().get("mode", "build")


def get_frontend_build_dir() -> Path:
    """React 构建输出目录，相对项目根（如 frontend/dist）。"""
    d = get_frontend_config().get("build_dir", "frontend/dist")
    return _CONFIG_DIR / d


def get_frontend_template_dir() -> Path:
    """已废弃：仅保留以兼容旧 config，前端现为 React+Vite 构建。"""
    d = get_frontend_config().get("template_dir", "frontend/templates")
    return _CONFIG_DIR / d


def get_frontend_static_dir() -> Path:
    """已废弃：仅保留以兼容旧 config，前端现为 React+Vite 构建。"""
    d = get_frontend_config().get("static_dir", "frontend/static")
    return _CONFIG_DIR / d
