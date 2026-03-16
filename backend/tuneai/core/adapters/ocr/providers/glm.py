from __future__ import annotations

from typing import Any

import numpy as np

from tuneai.core.adapters.ocr.providers.multimodal import run_multimodal_ocr
from tuneai.core.adapters.ocr.types import OcrChar


def run_glm_ocr(image: np.ndarray, cfg: dict[str, Any]) -> list[OcrChar]:
    return run_multimodal_ocr(image, cfg, provider_label="glm")
