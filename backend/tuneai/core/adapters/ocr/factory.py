from __future__ import annotations

import importlib
from collections.abc import Callable
from typing import Any

import numpy as np

from tuneai.core.adapters.ocr.types import OcrChar

OCRRunner = Callable[[np.ndarray, dict[str, Any]], list[OcrChar]]


def get_ocr_runner(provider: str, runners: dict[str, str]) -> OCRRunner:
    entrypoint = runners.get(provider)
    if not isinstance(entrypoint, str) or not entrypoint.strip():
        raise ValueError(f"ocr runner is not configured for provider: {provider}")
    module_name, sep, func_name = entrypoint.partition(":")
    if not sep or not module_name or not func_name:
        raise ValueError(f"invalid ocr runner entrypoint: {entrypoint!r}")
    module = importlib.import_module(module_name)
    runner = getattr(module, func_name)
    if not callable(runner):
        raise ValueError(f"ocr runner is not callable: {entrypoint!r}")
    return runner
