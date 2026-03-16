from __future__ import annotations

import numpy as np

from tuneai.core.adapters.ocr.factory import get_ocr_runner
from tuneai.core.adapters.ocr.types import OcrChar
from tuneai.core.adapters.provider_context import get_provider_overrides
from tuneai.config import get_default_provider, get_ocr_config


def run_ocr(image: np.ndarray) -> list[OcrChar]:
    _, _, provider_override = get_provider_overrides()
    configured_provider = get_default_provider()
    provider = provider_override.strip().lower() if isinstance(provider_override, str) else ""
    if not provider:
        provider = configured_provider
    if not provider:
        raise ValueError("ocr provider must be configured")
    provider_cfg = get_ocr_config(provider)
    runner_value = provider_cfg.get("runner")
    if not isinstance(runner_value, str) or not runner_value.strip():
        raise ValueError(f"ocr.runner must be a non-empty string for provider: {provider}")
    runner = get_ocr_runner(provider, {provider: runner_value})
    return runner(image, provider_cfg)


__all__ = ["OcrChar", "run_ocr"]
