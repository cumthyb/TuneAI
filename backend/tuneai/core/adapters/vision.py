from __future__ import annotations

import base64
import re

import cv2
import numpy as np
from pydantic import BaseModel, Field

from tuneai.core.adapters.llm_client import build_chat_openai, get_vision_llm_config
from tuneai.logging_config import get_logger
from tuneai.schemas.request_response import Warning
from tuneai.schemas.score_ir import ScoreIR

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


class VLValidationResult(BaseModel):
    key_correct: bool = Field(description="图中调号与识别结果是否一致")
    detected_key: str = Field(description="VL 从图中看到的调号，如 G、Bb")
    confidence: float = Field(description="置信度 0-1", ge=0.0, le=1.0)
    notes: str = Field(description="补充说明")


_VL_VALIDATE_PROMPT = (
    "这是一张简谱图片。系统已识别出调号为 {source_key}，目标转调为 {target_key}。\n\n"
    "请完成以下两项视觉验证：\n"
    "1. 图中实际的调号是什么（格式如 1=G、1=Bb）？\n"
    "2. 系统识别的调号 1={source_key} 是否与图中一致？\n\n"
    "直接给出判断，不需要额外解释。"
)


def validate_score_with_vision(score: ScoreIR, original_image: np.ndarray, request_id: str) -> list[Warning]:
    log = get_logger("validate_vision")
    cfg = get_vision_llm_config()
    api_key = cfg.get("api_key")
    if not isinstance(api_key, str) or not api_key.strip():
        raise ValueError("vision_llm.api_key must be configured for validate_score")
    _, buf = cv2.imencode(".png", original_image)
    b64 = base64.b64encode(buf.tobytes()).decode()
    prompt = _VL_VALIDATE_PROMPT.format(source_key=score.source_key.tonic, target_key=score.target_key.tonic)
    from langchain_core.messages import HumanMessage
    llm = _get_llm()
    chain = llm.with_structured_output(VLValidationResult, method="function_calling")
    message = HumanMessage(
        content=[
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
            {"type": "text", "text": prompt},
        ]
    )
    result = chain.invoke([message])
    log.debug(
        f"[validate] VL: key_correct={result.key_correct}, detected={result.detected_key!r}, conf={result.confidence:.2f}"
    )
    if not result.key_correct:
        return [
            Warning(
                type="vl_key_mismatch",
                message=(
                    f"VL 视觉校验：图中调号可能为 1={result.detected_key}，"
                    f"与识别结果 1={score.source_key.tonic} 不符 (conf={result.confidence:.2f})"
                ),
            )
        ]
    return []
