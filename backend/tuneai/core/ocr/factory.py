from __future__ import annotations

from collections.abc import Callable
from typing import Any

import numpy as np

from tuneai.core.ocr.providers.aliyun import run_aliyun_ocr
from tuneai.core.ocr.types import OcrChar

OCRRunner = Callable[[np.ndarray, dict[str, Any]], list[OcrChar]]


def get_ocr_runner(provider: str) -> OCRRunner | None:
    registry: dict[str, OCRRunner] = {
        "aliyun": run_aliyun_ocr,
    }
    return registry.get(provider)
