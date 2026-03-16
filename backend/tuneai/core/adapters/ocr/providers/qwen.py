from __future__ import annotations

import io
import json
from typing import Any

import cv2
import numpy as np

from tuneai.core.adapters.ocr.types import OcrChar
from tuneai.logging_config import get_logger


def run_qwen_ocr(image: np.ndarray, cfg: dict[str, Any]) -> list[OcrChar]:
    access_key_id = cfg.get("access_key_id")
    access_key_secret = cfg.get("access_key_secret")
    endpoint = cfg.get("endpoint")
    if not isinstance(access_key_id, str) or not access_key_id.strip():
        raise ValueError("ocr.access_key_id must be configured")
    if not isinstance(access_key_secret, str) or not access_key_secret.strip():
        raise ValueError("ocr.access_key_secret must be configured")
    if not isinstance(endpoint, str) or not endpoint.strip():
        raise ValueError("ocr.endpoint must be configured")
    _, buf = cv2.imencode(".png", image)
    image_bytes = buf.tobytes()
    from alibabacloud_ocr_api20210707 import models as ocr_models
    from alibabacloud_ocr_api20210707.client import Client
    from alibabacloud_tea_openapi import models as openapi_models

    openapi_cfg = openapi_models.Config(
        access_key_id=access_key_id,
        access_key_secret=access_key_secret,
        endpoint=endpoint,
    )
    client = Client(openapi_cfg)
    request = ocr_models.RecognizeGeneralRequest(body=io.BytesIO(image_bytes))
    response = client.recognize_general(request)
    chars = _parse_response(response)
    get_logger("ocr").debug(f"ocr(qwen): {len(chars)} chars recognized")
    return chars


def _parse_response(response: Any) -> list[OcrChar]:
    chars: list[OcrChar] = []
    raw = getattr(response.body, "data", None)
    if not raw:
        return chars
    data = json.loads(raw) if isinstance(raw, str) else raw
    if not isinstance(data, dict):
        raise ValueError("ocr response data must be an object")
    blocks = data.get("blocks")
    if not isinstance(blocks, list):
        raise ValueError("ocr response blocks must be a list")
    for block in blocks:
        if not isinstance(block, dict):
            continue
        raw_text = block.get("text")
        if not isinstance(raw_text, str):
            raise ValueError("ocr block text must be string")
        text = raw_text.strip()
        if not text:
            continue
        raw_confidence = block.get("confidence")
        if not isinstance(raw_confidence, (int, float)):
            raise ValueError("ocr block confidence must be numeric")
        confidence = float(raw_confidence)
        bbox = _extract_bbox(block)
        if bbox is None:
            continue
        for ch in text:
            chars.append(OcrChar(text=ch, bbox=bbox, confidence=confidence))
    return chars


def _extract_bbox(block: dict[str, Any]) -> list[int] | None:
    coord = block.get("blockCoordinate")
    if coord is not None:
        if not isinstance(coord, dict):
            raise ValueError("ocr blockCoordinate must be an object")
        points = ("pointTopLeft", "pointTopRight", "pointBottomLeft", "pointBottomRight")
        xs = [coord[k]["x"] for k in points]
        ys = [coord[k]["y"] for k in points]
        return [int(min(xs)), int(min(ys)), int(max(xs) - min(xs)), int(max(ys) - min(ys))]
    return None
