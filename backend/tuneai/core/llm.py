"""
LangChain 封装、结构化输出、低置信度纠错与补全。
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

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


_llm_instance = None


def _create_llm():
    from langchain_openai import ChatOpenAI
    from tuneai.config import get_llm_config, get_api_key

    cfg = get_llm_config()
    base_url = cfg.get("base_url") or None
    api_key = cfg.get("api_key") or get_api_key("openai") or "dummy"

    return ChatOpenAI(
        model=cfg.get("model", "gpt-4o-mini"),
        base_url=base_url,
        api_key=api_key,
        temperature=cfg.get("temperature", 0.1),
        max_tokens=cfg.get("max_tokens", 4096),
        timeout=cfg.get("timeout_seconds", 30),
    )


def _get_llm():
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = _create_llm()
    return _llm_instance


def correct_key_signature(
    raw_text: str,
    context: str,
    request_id: str,
) -> KeyCorrectionResult:
    """
    任务 A：给定 OCR 文字和上下文，纠正调号格式。
    如果 raw_text 为空或 LLM 调用失败，返回默认值。
    """
    log = get_logger("llm")

    if not raw_text:
        log.warning("correct_key_signature: empty raw_text, defaulting to C")
        return KeyCorrectionResult(tonic="C", label="1=C", confidence=0.3, notes="OCR未识别到调号")

    try:
        llm = _get_llm()
        structured = llm.with_structured_output(KeyCorrectionResult)

        prompt = (
            f"你是简谱（数字谱）专家。以下是OCR识别到的调号文字：\n\n"
            f"原始文字: {raw_text!r}\n"
            f"上下文: {context}\n\n"
            f"请纠正并提取正确的调号信息。调号格式为 '1=X'，"
            f"其中 X 是主音（C/D/E/F/G/A/B，可带升号#或降号b）。\n"
            f"如果识别文字明显是调号，请纠正其中的OCR错误。"
        )

        result = structured.invoke(prompt)
        log.debug(f"key correction: {raw_text!r} → {result.label} (conf={result.confidence:.2f})")
        return result

    except Exception as e:
        log.warning(f"LLM key correction failed: {e}, falling back to regex parse")
        return _fallback_key_parse(raw_text)


def correct_low_confidence_measure(
    measure_tokens: list[dict],
    image_region_b64: str,
    active_key: str,
    request_id: str,
) -> MeasureCorrectionResult:
    """
    任务 B：给定低置信度 OCR token 列表和图像区域，补全音符解析。
    """
    log = get_logger("llm")

    try:
        llm = _get_llm()
        structured = llm.with_structured_output(MeasureCorrectionResult)

        import json
        tokens_str = json.dumps(measure_tokens, ensure_ascii=False, indent=2)

        prompt = (
            f"你是简谱（数字谱）专家。以下是一个小节的OCR识别结果（含置信度）：\n\n"
            f"当前调号: 1={active_key}\n"
            f"OCR Token列表:\n{tokens_str}\n\n"
            f"请分析这些token，补全或纠正其中低置信度的音符（confidence < 0.7）。"
            f"返回修正后的完整事件列表。每个事件包含 id, type, degree, accidental, octave_shift 等字段。"
        )

        result = structured.invoke(prompt)
        log.debug(f"measure correction: {len(measure_tokens)} tokens → conf={result.confidence:.2f}")
        return result

    except Exception as e:
        log.warning(f"LLM measure correction failed: {e}")
        # 返回原始 tokens 不修改
        return MeasureCorrectionResult(
            events=measure_tokens,
            confidence=0.5,
            notes=f"LLM调用失败: {e}",
        )


def _fallback_key_parse(raw_text: str) -> KeyCorrectionResult:
    """OCR 结果的简单正则回退解析。"""
    import re
    m = re.search(r"1\s*[=＝]\s*([A-G][#b♯♭]?)", raw_text)
    if m:
        tonic = m.group(1).replace("♯", "#").replace("♭", "b")
        return KeyCorrectionResult(
            tonic=tonic,
            label=f"1={tonic}",
            confidence=0.6,
            notes="正则回退解析",
        )
    return KeyCorrectionResult(tonic="C", label="1=C", confidence=0.2, notes="回退至默认调 C")
