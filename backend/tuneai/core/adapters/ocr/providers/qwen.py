from __future__ import annotations

import io
import json
from typing import Any

import cv2
import numpy as np

from tuneai.core.adapters.ocr.types import OcrChar
from tuneai.logging_config import get_logger


def run_qwen_ocr(image: np.ndarray, cfg: dict[str, Any]) -> list[OcrChar]:
    log = get_logger("ocr")
    if not cfg.get("access_key_id") or not cfg.get("access_key_secret"):
        log.warning("ocr(qwen): access_key 未配置，跳过 OCR")
        return []
    _, buf = cv2.imencode(".png", image)
    image_bytes = buf.tobytes()
    try:
        from alibabacloud_ocr_api20210707 import models as ocr_models
        from alibabacloud_ocr_api20210707.client import Client
        from alibabacloud_tea_openapi import models as openapi_models

        openapi_cfg = openapi_models.Config(
            access_key_id=cfg.get("access_key_id", ""),
            access_key_secret=cfg.get("access_key_secret", ""),
            endpoint=cfg.get("endpoint", "ocr-api.cn-hangzhou.aliyuncs.com"),
        )
        client = Client(openapi_cfg)
        request = ocr_models.RecognizeGeneralRequest(body=io.BytesIO(image_bytes))
        response = client.recognize_general(request)
        chars = _parse_response(response)
        log.debug(f"ocr(qwen): {len(chars)} chars recognized")
        return chars
    except Exception as e:
        log.warning(f"ocr(qwen) 调用失败 ({type(e).__name__}: {e})")
        return []


def _parse_response(response: Any) -> list[OcrChar]:
    chars: list[OcrChar] = []
    try:
        raw = getattr(response.body, "data", None) or ""
        if not raw:
            return chars
        data = json.loads(raw) if isinstance(raw, str) else raw
        blocks = data.get("blocks", [])
        for block in blocks:
            text = (block.get("text") or block.get("blockText") or "").strip()
            if not text:
                continue
            confidence = float(block.get("confidence", 1.0))
            bbox = _extract_bbox(block)
            if bbox is None:
                continue
            for ch in text:
                chars.append(OcrChar(text=ch, bbox=bbox, confidence=confidence))
    except Exception as e:
        get_logger("ocr").debug(f"ocr(qwen) parse error: {e}")
    return chars


def _extract_bbox(block: dict[str, Any]) -> list[int] | None:
    coord = block.get("blockCoordinate")
    if coord:
        try:
            xs = [coord[k]["x"] for k in ("pointTopLeft", "pointTopRight", "pointBottomLeft", "pointBottomRight")]
            ys = [coord[k]["y"] for k in ("pointTopLeft", "pointTopRight", "pointBottomLeft", "pointBottomRight")]
            return [int(min(xs)), int(min(ys)), int(max(xs) - min(xs)), int(max(ys) - min(ys))]
        except Exception:
            pass
    rect = block.get("textRectangle")
    if rect:
        try:
            return [int(rect["x"]), int(rect["y"]), int(rect["width"]), int(rect["height"])]
        except Exception:
            pass
    if all(k in block for k in ("x", "y", "w", "h")):
        return [int(block["x"]), int(block["y"]), int(block["w"]), int(block["h"])]
    return None
