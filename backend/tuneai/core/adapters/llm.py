from __future__ import annotations

import json
import re

from pydantic import BaseModel, Field

from tuneai.core.adapters.llm_client import build_chat_openai, get_text_llm_config
from tuneai.logging_config import get_logger


class KeyCorrectionResult(BaseModel):
    tonic: str = Field(description="识别到的主音，如 C、G#、Bb")
    label: str = Field(description="完整调号标记，如 1=C、1=G#")
    confidence: float = Field(description="置信度 0-1", ge=0.0, le=1.0)
    notes: str = Field(default="", description="补充说明")


class MeasureCorrectionResult(BaseModel):
    events: list[dict] = Field(description="补全后的事件列表")
    confidence: float = Field(description="置信度 0-1", ge=0.0, le=1.0)
    notes: str = Field(default="", description="补充说明")


class PitchAssessmentResult(BaseModel):
    too_high: bool = Field(description="转调后整体音域是否偏高")
    octave_adjust: int = Field(default=0, description="建议八度调整量（0=不变，-1=降低一个八度）")
    accidental_ratio: float = Field(default=0.0, description="半音占比 0-1", ge=0.0, le=1.0)
    suggested_key: str | None = Field(default=None, description="建议替代目标调")
    confidence: float = Field(default=1.0, description="置信度 0-1", ge=0.0, le=1.0)
    notes: str = Field(default="", description="补充说明")


_llm_instance = None
_KEY_RE = re.compile(r"1\s*[=＝一]\s*([A-G][#b♯♭]?)")


def _create_llm():
    cfg = get_text_llm_config()
    return build_chat_openai(
        cfg,
        default_model="text-model",
        default_temperature=0.1,
        default_max_tokens=1024,
        default_timeout_seconds=30,
    )


def _get_llm():
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = _create_llm()
    return _llm_instance


def _structured(schema: type[BaseModel]):
    llm = _get_llm()
    return llm.with_structured_output(schema, method="function_calling")


def correct_key_signature(raw_text: str, context: str = "", request_id: str = "") -> KeyCorrectionResult:
    log = get_logger("llm")
    if not raw_text:
        log.warning("correct_key_signature: 输入为空，默认 1=C")
        return KeyCorrectionResult(tonic="C", label="1=C", confidence=0.3, notes="输入为空")
    prompt = (
        "你是简谱（数字谱）专家。以下是识别到的调号文字，可能含有识别错误。\n\n"
        f"原始文字: {raw_text!r}\n"
        f"上下文: {context}\n\n"
        "请纠正并提取正确的调号信息。\n"
        "调号格式为 '1=X'，其中 X 是主音（C D E F G A B，可带 # 或 b）。\n"
        "常见 OCR 错误：= 识别为 ＝ 或 一；# 识别为 井；b 识别为 6 或 B。"
    )
    try:
        return _structured(KeyCorrectionResult).invoke(prompt)
    except Exception as e:
        log.warning(f"LLM key correction 失败 ({type(e).__name__}: {e})，回退正则解析")
        return _fallback_key_parse(raw_text)


def correct_low_confidence_events(
    events: list[dict], active_key: str, request_id: str = ""
) -> MeasureCorrectionResult:
    log = get_logger("llm")
    tokens_str = json.dumps(events, ensure_ascii=False, indent=2)
    prompt = (
        "你是简谱（数字谱）专家。以下是 OCR 识别到的音符事件列表（含置信度）：\n\n"
        f"当前调号: 1={active_key}\n"
        f"事件列表:\n{tokens_str}\n\n"
        "请分析并纠正其中低置信度（confidence < 0.7）的音符。\n"
        "返回完整的事件列表，每个事件包含字段：id, type, degree, accidental, octave_shift。\n"
        "如无需修改，原样返回，confidence 设为 1.0。"
    )
    try:
        return _structured(MeasureCorrectionResult).invoke(prompt)
    except Exception as e:
        log.warning(f"LLM event correction 失败 ({type(e).__name__}: {e})")
        return MeasureCorrectionResult(
            events=events,
            confidence=0.5,
            notes=f"LLM 调用失败: {type(e).__name__}: {e}",
        )


def assess_pitch_range(
    events: list[dict],
    source_key: str,
    target_key: str,
    request_id: str = "",
) -> PitchAssessmentResult:
    log = get_logger("llm")
    log.debug(f"assess_pitch_range: MVP stub, {source_key}->{target_key}, {len(events)} events")
    return PitchAssessmentResult(
        too_high=False,
        octave_adjust=0,
        accidental_ratio=0.0,
        suggested_key=None,
        confidence=1.0,
        notes="MVP stub: no assessment performed",
    )


def _fallback_key_parse(raw_text: str) -> KeyCorrectionResult:
    match = _KEY_RE.search(raw_text)
    if match:
        tonic = match.group(1).replace("♯", "#").replace("♭", "b")
        return KeyCorrectionResult(
            tonic=tonic,
            label=f"1={tonic}",
            confidence=0.6,
            notes="LLM 不可用，正则回退解析",
        )
    return KeyCorrectionResult(
        tonic="C",
        label="1=C",
        confidence=0.2,
        notes="正则无法解析，回退默认调 C",
    )
