"""
结构化日志、request_id、各阶段打点与错误。
"""
import sys
from contextvars import ContextVar, Token
from typing import Any

from loguru import logger

_request_id_var: ContextVar[str] = ContextVar("request_id", default="")

_setup_done = False


def setup_logging(level: str = "INFO", fmt: str = "json") -> None:
    global _setup_done
    if _setup_done:
        return
    logger.remove()
    if fmt == "json":
        log_fmt = (
            '{{"time":"{time:YYYY-MM-DDTHH:mm:ss.SSSZ}",'
            '"level":"{level}",'
            '"request_id":"{extra[request_id]}",'
            '"module":"{extra[module]}",'
            '"message":"{message}"}}'
        )
    else:
        log_fmt = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{extra[request_id]}</cyan> | "
            "<cyan>{extra[module]}</cyan> | "
            "{message}"
        )
    logger.add(
        sys.stderr,
        level=level.upper(),
        format=log_fmt,
        colorize=(fmt != "json"),
    )
    _setup_done = True


def get_request_id() -> str:
    return _request_id_var.get("")


def bind_request_id(rid: str) -> Token:
    return _request_id_var.set(rid)


def reset_request_id(token: Token) -> None:
    _request_id_var.reset(token)


def get_logger(module: str) -> Any:
    return logger.bind(request_id=get_request_id(), module=module)
