from __future__ import annotations

import base64
import json
from typing import Any

import cv2
import numpy as np
from openai import OpenAI

from tuneai.core.adapters.ocr.types import OcrChar
from tuneai.logging_config import get_logger

_OCR_PROMPT = (
    "You are an OCR engine. Extract all visible text characters from the image and return strict JSON only.\n"
    "Output format:\n"
    "{\n"
    '  "chars": [\n'
    '    {"text": "A", "bbox": [x, y, w, h], "confidence": 0.95}\n'
    "  ]\n"
    "}\n"
    "Rules:\n"
    "1) `chars` must be an array.\n"
    "2) `text` must be a single character.\n"
    "3) `bbox` is integer [x,y,w,h] with positive w,h.\n"
    "4) `confidence` is float in [0,1].\n"
    "5) No markdown, no extra keys, no comments."
)


def run_multimodal_ocr(image: np.ndarray, cfg: dict[str, Any], *, provider_label: str) -> list[OcrChar]:
    api_key = cfg.get("api_key")
    base_url = cfg.get("base_url")
    model = cfg.get("model")
    timeout_seconds = cfg.get("timeout_seconds", 30)
    max_tokens = cfg.get("max_tokens", 4096)
    if not isinstance(api_key, str) or not api_key.strip():
        raise ValueError("ocr.api_key must be configured")
    if not isinstance(base_url, str) or not base_url.strip():
        raise ValueError("ocr.base_url must be configured")
    if not isinstance(model, str) or not model.strip():
        raise ValueError("ocr.model must be configured")
    if not isinstance(timeout_seconds, (int, float)) or float(timeout_seconds) <= 0:
        raise ValueError("ocr.timeout_seconds must be a positive number")
    if not isinstance(max_tokens, int) or max_tokens <= 0:
        raise ValueError("ocr.max_tokens must be a positive integer")

    _, buf = cv2.imencode(".png", image)
    b64 = base64.b64encode(buf.tobytes()).decode()
    client = OpenAI(api_key=api_key, base_url=base_url, timeout=float(timeout_seconds))
    completion = client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": _OCR_PROMPT},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                ],
            }
        ],
    )
    content = completion.choices[0].message.content
    if not isinstance(content, str) or not content.strip():
        raise ValueError("ocr response content must be a non-empty JSON string")
    chars = _parse_ocr_response(content)
    get_logger("ocr").debug(f"ocr({provider_label}): {len(chars)} chars recognized")
    return chars


def _parse_ocr_response(content: str) -> list[OcrChar]:
    data = json.loads(content)
    if not isinstance(data, dict):
        raise ValueError("ocr response must be a JSON object")
    raw_chars = data.get("chars")
    if not isinstance(raw_chars, list):
        raise ValueError("ocr response chars must be a list")
    parsed: list[OcrChar] = []
    for item in raw_chars:
        if not isinstance(item, dict):
            continue
        text = item.get("text")
        bbox = item.get("bbox")
        confidence = item.get("confidence")
        if not isinstance(text, str):
            raise ValueError("ocr char text must be a string")
        if len(text) != 1:
            continue
        if not (isinstance(bbox, list) and len(bbox) == 4):
            raise ValueError("ocr char bbox must be [x, y, w, h]")
        if not all(isinstance(v, (int, float)) for v in bbox):
            raise ValueError("ocr char bbox values must be numeric")
        x, y, w, h = [int(v) for v in bbox]
        if w <= 0 or h <= 0:
            continue
        if not isinstance(confidence, (int, float)):
            raise ValueError("ocr char confidence must be numeric")
        c = float(confidence)
        if c < 0:
            c = 0.0
        if c > 1:
            c = 1.0
        parsed.append(OcrChar(text=text, bbox=[x, y, w, h], confidence=c))
    return parsed
