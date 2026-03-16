"""
LangChain 封装、结构化输出、低置信度纠错与补全。

配置来源：config.json > llm
  base_url                    任意 OpenAI-compatible 端点
  api_key                     对应端点的 API Key
  model                       模型名称（由配置决定）
  temperature / max_tokens / timeout_seconds
"""
from __future__ import annotations

import json
import re

from pydantic import BaseModel, Field

from tuneai.logging_config import get_logger


# ---------------------------------------------------------------------------
# 输出 schema（Pydantic v2）
# ---------------------------------------------------------------------------

class KeyCorrectionResult(BaseModel):
    tonic: str    = Field(description="识别到的主音，如 C、G#、Bb")
    label: str    = Field(description="完整调号标记，如 1=C、1=G#")
    confidence: float = Field(description="置信度 0-1", ge=0.0, le=1.0)
    notes: str    = Field(default="", description="补充说明")


class MeasureCorrectionResult(BaseModel):
    events: list[dict] = Field(description="补全后的事件列表")
    confidence: float  = Field(description="置信度 0-1", ge=0.0, le=1.0)
    notes: str         = Field(default="", description="补充说明")


class PitchAssessmentResult(BaseModel):
    too_high: bool     = Field(description="转调后整体音域是否偏高")
    octave_adjust: int = Field(default=0, description="建议八度调整量（0=不变，-1=降低一个八度）")
    accidental_ratio: float = Field(
        default=0.0, description="半音（非 natural）音符占比 0-1", ge=0.0, le=1.0
    )
    suggested_key: str | None = Field(
        default=None,
        description="半音过多时建议的替代目标调（None=保持当前调）",
    )
    confidence: float  = Field(default=1.0, description="置信度 0-1", ge=0.0, le=1.0)
    notes: str         = Field(default="", description="补充说明")


# ---------------------------------------------------------------------------
# LLM 单例
# ---------------------------------------------------------------------------

_llm_instance = None


def _create_llm():
    from tuneai.core.llm_client import build_chat_openai, get_text_llm_config

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
    """
    返回 with_structured_output 链，统一使用 function_calling。
    """
    llm = _get_llm()
    return llm.with_structured_output(schema, method="function_calling")


# ---------------------------------------------------------------------------
# 任务 A：调号 OCR 纠错（作为视觉识别的 fallback 或独立使用）
# ---------------------------------------------------------------------------

def correct_key_signature(
    raw_text: str,
    context: str = "",
    request_id: str = "",
) -> KeyCorrectionResult:
    """
    给定 OCR / 视觉模型识别到的原始文字，纠正调号格式。
    LLM 失败时自动回退到正则解析。
    """
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
        result = _structured(KeyCorrectionResult).invoke(prompt)
        log.debug(f"key correction: {raw_text!r} → {result.label} (conf={result.confidence:.2f})")
        return result
    except Exception as e:
        log.warning(f"LLM key correction 失败 ({type(e).__name__}: {e})，回退正则解析")
        return _fallback_key_parse(raw_text)


# ---------------------------------------------------------------------------
# 任务 B：低置信度音符补全
# ---------------------------------------------------------------------------

def correct_low_confidence_events(
    events: list[dict],
    active_key: str,
    request_id: str = "",
) -> MeasureCorrectionResult:
    """
    给定低置信度事件列表，补全或纠正音符解析。
    失败时原样返回 events，confidence=0.5，不向外抛出。
    """
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
        result = _structured(MeasureCorrectionResult).invoke(prompt)
        log.debug(f"event correction: {len(events)} events → conf={result.confidence:.2f}")
        return result
    except Exception as e:
        log.warning(f"LLM event correction 失败 ({type(e).__name__}: {e})")
        return MeasureCorrectionResult(
            events=events,
            confidence=0.5,
            notes=f"LLM 调用失败: {type(e).__name__}: {e}",
        )


# ---------------------------------------------------------------------------
# 任务 C：音高范围评估（供 pitch_adjust.py 调用）
# ---------------------------------------------------------------------------

def assess_pitch_range(
    events: list[dict],
    source_key: str,
    target_key: str,
    request_id: str = "",
) -> PitchAssessmentResult:
    """
    评估转调后的音符序列是否整体音域偏高，以及半音是否过多。

    MVP：直接返回"无需调整"的默认结果，不调用 LLM。

    完整实现时：
      - 调用 LLM 分析 events 中 octave_shift 分布与 accidental 比例
      - LLM 返回 too_high / octave_adjust / suggested_key
      - 失败时降级为纯规则判断（octave_shift 均值 > 0.5 视为偏高）
    """
    log = get_logger("llm")
    log.debug(f"assess_pitch_range: MVP stub, {source_key}→{target_key}, {len(events)} events")
    return PitchAssessmentResult(
        too_high=False,
        octave_adjust=0,
        accidental_ratio=0.0,
        suggested_key=None,
        confidence=1.0,
        notes="MVP stub: no assessment performed",
    )


# ---------------------------------------------------------------------------
# 正则回退
# ---------------------------------------------------------------------------

_KEY_RE = re.compile(r"1\s*[=＝一]\s*([A-G][#b♯♭]?)")


def _fallback_key_parse(raw_text: str) -> KeyCorrectionResult:
    m = _KEY_RE.search(raw_text)
    if m:
        tonic = m.group(1).replace("♯", "#").replace("♭", "b")
        return KeyCorrectionResult(
            tonic=tonic, label=f"1={tonic}", confidence=0.6,
            notes="LLM 不可用，正则回退解析",
        )
    return KeyCorrectionResult(
        tonic="C", label="1=C", confidence=0.2,
        notes="正则无法解析，回退默认调 C",
    )
