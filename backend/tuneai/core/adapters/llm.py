from __future__ import annotations

import json

from pydantic import BaseModel, Field

from tuneai.core.adapters.llm_client import build_chat_openai, get_text_llm_config
from tuneai.logging_config import get_logger
from tuneai.schemas.request_response import Warning
from tuneai.schemas.score_ir import NoteEvent, ScoreIR


class KeyCorrectionResult(BaseModel):
    tonic: str = Field(description="识别到的主音，如 C、G#、Bb")
    label: str = Field(description="完整调号标记，如 1=C、1=G#")
    confidence: float = Field(description="置信度 0-1", ge=0.0, le=1.0)
    notes: str = Field(description="补充说明")


class MeasureCorrectionResult(BaseModel):
    events: list[dict] = Field(description="补全后的事件列表")
    confidence: float = Field(description="置信度 0-1", ge=0.0, le=1.0)
    notes: str = Field(description="补充说明")


class PitchAssessmentResult(BaseModel):
    too_high: bool = Field(description="转调后整体音域是否偏高")
    octave_adjust: int = Field(description="建议八度调整量（0=不变，-1=降低一个八度）")
    accidental_ratio: float = Field(description="半音占比 0-1", ge=0.0, le=1.0)
    suggested_key: str | None = Field(description="建议替代目标调")
    confidence: float = Field(description="置信度 0-1", ge=0.0, le=1.0)
    notes: str = Field(description="补充说明")


_llm_instances: dict[tuple[str, str, str], object] = {}


def _create_llm():
    cfg = get_text_llm_config()
    return build_chat_openai(cfg)


def _get_llm():
    cfg = get_text_llm_config()
    provider = str(cfg.get("provider")).strip().lower()
    model = str(cfg.get("model")).strip()
    base_url = str(cfg.get("base_url")).strip()
    if not provider or not model or not base_url:
        raise ValueError("llm provider/model/base_url must be configured")
    key = (provider, model, base_url)
    llm = _llm_instances.get(key)
    if llm is None:
        llm = _create_llm()
        _llm_instances[key] = llm
    return llm


def _structured(schema: type[BaseModel]):
    llm = _get_llm()
    return llm.with_structured_output(schema, method="function_calling")


def correct_key_signature(raw_text: str, context: str, request_id: str) -> KeyCorrectionResult:
    if not raw_text:
        raise ValueError("raw_text must be non-empty")
    prompt = (
        "你是简谱（数字谱）专家。以下是识别到的调号文字，可能含有识别错误。\n\n"
        f"原始文字: {raw_text!r}\n"
        f"上下文: {context}\n\n"
        "请纠正并提取正确的调号信息。\n"
        "调号格式为 '1=X'，其中 X 是主音（C D E F G A B，可带 # 或 b）。\n"
        "常见 OCR 错误：= 识别为 ＝ 或 一；# 识别为 井；b 识别为 6 或 B。"
    )
    return _structured(KeyCorrectionResult).invoke(prompt)


def correct_low_confidence_events(
    events: list[dict], active_key: str, request_id: str
) -> MeasureCorrectionResult:
    tokens_str = json.dumps(events, ensure_ascii=False, indent=2)
    prompt = (
        "你是简谱（数字谱）专家。以下是 OCR 识别到的音符事件列表（含置信度）：\n\n"
        f"当前调号: 1={active_key}\n"
        f"事件列表:\n{tokens_str}\n\n"
        "请分析并纠正其中低置信度（confidence < 0.7）的音符。\n"
        "返回完整的事件列表，每个事件包含字段：id, type, degree, accidental, octave_shift。\n"
        "如无需修改，原样返回，confidence 设为 1.0。"
    )
    return _structured(MeasureCorrectionResult).invoke(prompt)


def assess_pitch_range(
    events: list[dict],
    source_key: str,
    target_key: str,
    request_id: str,
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


class LLMValidationResult(BaseModel):
    is_valid: bool = Field(description="转调结果是否音乐上合理")
    confidence: float = Field(description="置信度 0-1", ge=0.0, le=1.0)
    issues: list[str] = Field(default_factory=list, description="发现的问题列表（无问题时为空）")
    notes: str = Field(description="补充说明")


def validate_score_with_llm(score: ScoreIR, request_id: str) -> list[Warning]:
    log = get_logger("validate_llm")
    cfg = get_text_llm_config()
    api_key = cfg.get("api_key")
    if not isinstance(api_key, str) or not api_key.strip():
        raise ValueError("llm.api_key must be configured for validate_score")
    sample = [
        {"id": e.id, "degree": e.degree, "accidental": e.accidental, "octave_shift": e.octave_shift}
        for e in score.events if isinstance(e, NoteEvent)
    ][:20]
    prompt = (
        "你是简谱（数字谱）专家。请检验以下移调结果是否音乐上合理。\n\n"
        f"原调: 1={score.source_key.tonic}\n"
        f"目标调: 1={score.target_key.tonic}\n"
        f"音符样本（前20个）:\n{json.dumps(sample, ensure_ascii=False)}\n\n"
        "请判断：\n"
        "1. 调号转换是否正确（原调 → 目标调 的音程关系是否合理）\n"
        "2. 音符序列中是否存在可疑模式（如大量 #/b 临时记号，可能暗示调号识别有误）\n"
        "3. 整体是否符合简谱转调的音乐规律"
    )
    result: LLMValidationResult = _structured(LLMValidationResult).invoke(prompt)
    log.debug(
        f"[validate] LLM: is_valid={result.is_valid}, conf={result.confidence:.2f}, issues={result.issues}"
    )
    if not result.is_valid or result.issues:
        return [
            Warning(
                type="llm_validation",
                message=(
                    f"LLM 校验发现问题 (conf={result.confidence:.2f}): "
                    + "; ".join(result.issues)
                    if result.issues
                    else result.notes
                ),
            )
        ]
    return []
