from __future__ import annotations

import base64
import re

import cv2
import numpy as np

from tuneai.core.adapters.llm_client import build_chat_openai, get_vision_llm_config
from tuneai.logging_config import get_logger

_KEY_RE = re.compile(r"1\s*[=＝]\s*([A-G][#b♯♭]?)")
_TONIC_RE = re.compile(r"\b([A-G][#b]?)\b")
_PROMPT = (
    "这是一张简谱图片。请识别图中的调号，调号格式为 '1=X'（例如 1=C、1=G、1=Bb、1=F#）。\n"
    "只回答调号本身，例如：1=G\n"
    "如果无法确认，回答：unknown"
)
_llm_instances: dict[tuple[str, str, str], object] = {}


def _create_llm():
    cfg = get_vision_llm_config()
    return build_chat_openai(cfg)


def _get_llm():
    cfg = get_vision_llm_config()
    provider = str(cfg.get("provider")).strip().lower()
    model = str(cfg.get("model")).strip()
    base_url = str(cfg.get("base_url")).strip()
    if not provider or not model or not base_url:
        raise ValueError("vision_llm provider/model/base_url must be configured")
    key = (provider, model, base_url)
    llm = _llm_instances.get(key)
    if llm is None:
        llm = _create_llm()
        _llm_instances[key] = llm
    return llm


def recognize_key_signature(image: np.ndarray) -> str:
    cfg = get_vision_llm_config()
    api_key = cfg.get("api_key")
    if not isinstance(api_key, str) or not api_key.strip():
        raise ValueError("vision_llm.api_key must be configured")
    _, buf = cv2.imencode(".png", image)
    b64 = base64.b64encode(buf.tobytes()).decode()
    from langchain_core.messages import HumanMessage

    llm = _get_llm()
    message = HumanMessage(
        content=[
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
            {"type": "text", "text": _PROMPT},
        ]
    )
    response = llm.invoke([message])
    content = response.content
    if not isinstance(content, str):
        raise ValueError("vision_llm response content must be string")
    return _parse_key(content.strip())


def _parse_key(text: str) -> str:
    match = _KEY_RE.search(text)
    if match:
        return _normalize(match.group(1))
    match = _TONIC_RE.search(text)
    if match:
        return _normalize(match.group(1))
    raise ValueError(f"vision_llm cannot parse key from response: {text!r}")


def _normalize(tonic: str) -> str:
    return tonic.replace("♯", "#").replace("♭", "b")
