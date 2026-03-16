"""
OCR 接入（第二步 B，线上）：全字符 bbox 识别。
通过 ocr.provider 路由到具体实现，输入整张预处理图，输出字符 bbox + 识别内容。
"""
from __future__ import annotations

import numpy as np

from tuneai.core.ocr.factory import get_ocr_runner
from tuneai.core.ocr.types import OcrChar
from tuneai.logging_config import get_logger


def run_ocr(image: np.ndarray) -> list[OcrChar]:
    """
    调用 OCR provider，返回全字符识别结果列表。
    失败时返回空列表（不抛异常），由调用方处理降级。
    """
    log = get_logger("ocr")
    from tuneai.config import get_ocr_config

    cfg = get_ocr_config()
    provider = str(cfg.get("provider", "")).strip().lower()
    runners_cfg = cfg.get("runners") or {}
    providers_cfg = cfg.get("providers") or {}
    provider_cfg = providers_cfg.get(provider) or {}

    if not provider:
        log.warning("ocr: provider 未配置，跳过 OCR")
        return []

    runner = get_ocr_runner(provider, runners_cfg)
    if runner is None:
        log.warning(f"ocr: provider={provider!r} 未注册或 entrypoint 无效，跳过 OCR")
        return []

    try:
        return runner(image, provider_cfg)
    except Exception as e:
        log.warning(f"ocr: provider={provider!r} 调用失败 ({type(e).__name__}: {e})")
        return []


__all__ = ["OcrChar", "run_ocr"]
