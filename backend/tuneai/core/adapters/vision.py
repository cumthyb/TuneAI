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
_llm_instance = None


def _create_llm():
    cfg = get_vision_llm_config()
    return build_chat_openai(
        cfg,
        default_model="vision-model",
        default_temperature=0.0,
        default_max_tokens=64,
        default_timeout_seconds=30,
    )


def _get_llm():
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = _create_llm()
    return _llm_instance


def recognize_key_signature(image: np.ndarray) -> str:
    log = get_logger("vision_llm")
    cfg = get_vision_llm_config()
    if not cfg.get("api_key"):
        log.warning("vision_llm: api_key 未配置，跳过调号识别，使用默认 C 调")
        return "C"
    _, buf = cv2.imencode(".png", image)
    b64 = base64.b64encode(buf.tobytes()).decode()
    try:
        from langchain_core.messages import HumanMessage

        llm = _get_llm()
        message = HumanMessage(
            content=[
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                {"type": "text", "text": _PROMPT},
            ]
        )
        response = llm.invoke([message])
        return _parse_key((response.content or "").strip())
    except Exception as e:
        log.warning(f"vision_llm 调用失败 ({type(e).__name__}: {e})，使用默认 C 调")
        return "C"


def _parse_key(text: str) -> str:
    match = _KEY_RE.search(text)
    if match:
        return _normalize(match.group(1))
    match = _TONIC_RE.search(text)
    if match:
        return _normalize(match.group(1))
    return "C"


def _normalize(tonic: str) -> str:
    return tonic.replace("♯", "#").replace("♭", "b")
