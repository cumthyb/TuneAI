"""
从 config.json 加载配置：端口、API Key、Qwen-VL、阿里OCR、流水线、日志等。
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
    # 环境变量覆盖
    if port := os.getenv("TUNEAI_PORT"):
        try:
            cfg.setdefault("server", {})["port"] = int(port)
        except ValueError:
            pass
    if level := os.getenv("TUNEAI_LOG_LEVEL"):
        cfg.setdefault("logging", {})["level"] = level
    if key := os.getenv("TUNEAI_QWEN_VL_API_KEY"):
        cfg.setdefault("qwen_vl", {})["api_key"] = key
    if key := os.getenv("TUNEAI_LLM_API_KEY"):
        cfg.setdefault("llm", {})["api_key"] = key
    if key_id := os.getenv("TUNEAI_ALIBABA_OCR_KEY_ID"):
        cfg.setdefault("alibaba_ocr", {})["access_key_id"] = key_id
    if key_secret := os.getenv("TUNEAI_ALIBABA_OCR_KEY_SECRET"):
        cfg.setdefault("alibaba_ocr", {})["access_key_secret"] = key_secret
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


def get_qwen_vl_config() -> dict[str, Any]:
    return get_config().get("qwen_vl", {})


def get_llm_config() -> dict[str, Any]:
    return get_config().get("llm", {})


def get_alibaba_ocr_config() -> dict[str, Any]:
    return get_config().get("alibaba_ocr", {})


def get_pipeline_config() -> dict[str, Any]:
    return get_config().get("pipeline", {})


def get_logging_config() -> dict[str, Any]:
    return get_config().get("logging", {})


def get_frontend_config() -> dict[str, Any]:
    return get_config().get("frontend", {})


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
