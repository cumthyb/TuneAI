from __future__ import annotations

import numpy as np

from tuneai.config import get_ocr_config
from tuneai.core.adapters.ocr.multimodal import run_multimodal_ocr
from tuneai.core.adapters.ocr.types import OcrChar


def run_ocr(image: np.ndarray, provider: str) -> list[OcrChar]:
    cfg = get_ocr_config(provider)
    return run_multimodal_ocr(image, cfg, provider_label=provider)


__all__ = ["OcrChar", "run_ocr"]
