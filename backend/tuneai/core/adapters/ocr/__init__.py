from __future__ import annotations

import numpy as np

from tuneai.core.adapters.ocr.factory import get_ocr_runner
from tuneai.core.adapters.ocr.types import OcrChar
from tuneai.core.adapters.provider_context import get_provider_overrides
from tuneai.config import get_default_provider, get_ocr_config
from tuneai.logging_config import get_logger


def run_ocr(image: np.ndarray) -> list[OcrChar]:
    log = get_logger("ocr")

    _, _, provider_override = get_provider_overrides()
    configured_provider = get_default_provider()
    provider = provider_override or configured_provider
    provider_cfg = get_ocr_config(provider)

    if not provider:
        log.warning("ocr: provider 未配置，跳过 OCR")
        return []

    runner = get_ocr_runner(provider, {provider: str(provider_cfg.get("runner", ""))})

    if runner is None:
        log.warning(f"ocr: provider={provider!r} 未注册或 entrypoint 无效，跳过 OCR")
        return []

    try:
        return runner(image, provider_cfg)
    except Exception as e:
        log.warning(f"ocr: provider={provider!r} 调用失败 ({type(e).__name__}: {e})")
        return []


__all__ = ["OcrChar", "run_ocr"]
