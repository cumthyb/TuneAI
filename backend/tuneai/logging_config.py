"""
结构化日志、request_id、各阶段打点与错误。

日志输出：
  - stderr: 彩色（human）或 JSON（生产）
  - data/logs/tuneai.log: JSON 格式，rolling（10 MB/7 天）
"""
import sys
from contextvars import ContextVar, Token
from typing import Any

from loguru import logger

_request_id_var: ContextVar[str] = ContextVar("request_id", default="")

_setup_done = False

_JSON_FMT = (
    '{{"time":"{time:YYYY-MM-DDTHH:mm:ss.SSSZ}",'
    '"level":"{level}",'
    '"request_id":"{extra[request_id]}",'
    '"module":"{extra[module]}",'
    '"message":"{message}"}}'
)
_HUMAN_FMT = (
    "<green>{time:HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{extra[request_id]}</cyan> | "
    "<cyan>{extra[module]}</cyan> | "
    "{message}"
)


def setup_logging(level: str = "INFO", fmt: str = "json") -> None:
    """
    初始化日志系统（幂等，只执行一次）。
    在 main.py 的 lifespan 中调用，也可在测试中直接调用。
    """
    global _setup_done
    if _setup_done:
        return

    logger.remove()

    # stderr sink
    stderr_fmt = _JSON_FMT if fmt == "json" else _HUMAN_FMT
    logger.add(
        sys.stderr,
        level=level.upper(),
        format=stderr_fmt,
        colorize=(fmt != "json"),
    )

    # 文件 sink（rolling）
    try:
        from tuneai.config import get_logs_dir, get_logging_config
        log_cfg = get_logging_config()
        log_file = get_logs_dir() / log_cfg.get("log_file", "tuneai.log")
        logger.add(
            str(log_file),
            level=level.upper(),
            format=_JSON_FMT,
            rotation=log_cfg.get("rotation", "10 MB"),
            retention=log_cfg.get("retention", "7 days"),
            encoding="utf-8",
        )
    except Exception:
        pass  # 配置未就绪时跳过文件日志

    _setup_done = True


def get_request_id() -> str:
    return _request_id_var.get("")


def bind_request_id(rid: str) -> Token:
    return _request_id_var.set(rid)


def reset_request_id(token: Token) -> None:
    _request_id_var.reset(token)


def get_logger(module: str) -> Any:
    return logger.bind(request_id=get_request_id(), module=module)
