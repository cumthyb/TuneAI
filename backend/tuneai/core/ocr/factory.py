from __future__ import annotations

import importlib
from collections.abc import Callable
from typing import Any

import numpy as np

from tuneai.core.ocr.types import OcrChar

OCRRunner = Callable[[np.ndarray, dict[str, Any]], list[OcrChar]]


def get_ocr_runner(provider: str, runners: dict[str, str]) -> OCRRunner | None:
    """
    从配置中按 provider 名称动态加载 OCR runner。

    runners 配置格式:
      {
        "aliyun": "tuneai.core.ocr.providers.aliyun:run_aliyun_ocr"
      }
    """
    entrypoint = (runners or {}).get(provider)
    if not entrypoint:
        return None

    module_name, sep, func_name = entrypoint.partition(":")
    if not sep or not module_name or not func_name:
        return None

    try:
        module = importlib.import_module(module_name)
        runner = getattr(module, func_name)
    except Exception:
        return None

    if not callable(runner):
        return None
    return runner
