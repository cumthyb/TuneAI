"""
结果校验（三层）：
  Layer 1  规则校验  —— 本地，无 API 调用，快速
  Layer 2  LLM 文本  —— 用 llm 配置中的文本模型检验转调结果的音乐合理性
  Layer 3  VL 视觉   —— 用 vision_llm 配置中的多模态模型对照原图交叉验证调号

Layer 2/3 失败时只记录 warning，不抛异常，不阻断流程。
"""
from __future__ import annotations

import base64
import json

import cv2
import numpy as np
from pydantic import BaseModel, Field

from tuneai.logging_config import get_logger
from tuneai.schemas.request_response import Warning
from tuneai.schemas.score_ir import NoteEvent, ScoreIR

_LOW_CONF_THRESHOLD = 0.7
_VALID_TONICS = {
    "C", "C#", "Db", "D", "D#", "Eb", "E",
    "F", "F#", "Gb", "G", "G#", "Ab", "A", "A#", "Bb", "B",
}


# ---------------------------------------------------------------------------
# 公开接口
# ---------------------------------------------------------------------------

def validate_score(
    score: ScoreIR,
    original_image: np.ndarray | None = None,
    request_id: str = "",
) -> list[Warning]:
    """
    三层校验，返回 Warning 列表。

    Args:
        score:          转调后的 ScoreIR
        original_image: 预处理后的灰度图（供 VL 视觉校验），None 时跳过第三层
        request_id:     请求 ID，用于日志追踪
    """
    log = get_logger("validate")
    warnings: list[Warning] = []

    # ── Layer 1: 规则校验 ────────────────────────────────────────────────────
    warnings.extend(_rule_checks(score))

    # ── Layer 2: LLM 文本校验 ────────────────────────────────────────────────
    try:
        w = _llm_validate(score, request_id)
        warnings.extend(w)
    except Exception as e:
        log.warning(f"[validate] LLM 校验跳过: {type(e).__name__}: {e}")

    # ── Layer 3: VL 视觉校验 ─────────────────────────────────────────────────
    if original_image is not None:
        try:
            w = _vl_validate(score, original_image, request_id)
            warnings.extend(w)
        except Exception as e:
            log.warning(f"[validate] VL 校验跳过: {type(e).__name__}: {e}")

    if warnings:
        log.warning(f"validate_score: {len(warnings)} warning(s)")

    return warnings


# ---------------------------------------------------------------------------
# Layer 1：规则校验
# ---------------------------------------------------------------------------

def _rule_checks(score: ScoreIR) -> list[Warning]:
    warnings: list[Warning] = []

    if not score.source_key.tonic:
        warnings.append(Warning(type="KEY_NOT_FOUND", message="未能识别调号，已使用默认值 1=C"))
    elif score.source_key.tonic not in _VALID_TONICS:
        warnings.append(Warning(
            type="INVALID_KEY",
            message=f"识别到的调号不合法: {score.source_key.tonic!r}",
        ))

    if score.target_key.tonic not in _VALID_TONICS:
        warnings.append(Warning(
            type="INVALID_TARGET_KEY",
            message=f"目标调号不合法: {score.target_key.tonic!r}",
        ))

    for ev in score.events:
        if isinstance(ev, NoteEvent) and ev.confidence < _LOW_CONF_THRESHOLD:
            warnings.append(Warning(
                type="low_confidence",
                message=f"事件 {ev.id} 置信度较低 ({ev.confidence:.2f})",
            ))

    if not score.events:
        warnings.append(Warning(type="EMPTY_SCORE", message="乐谱中未识别到任何音符"))

    return warnings


# ---------------------------------------------------------------------------
# Layer 2：LLM 文本校验
# ---------------------------------------------------------------------------

class _LLMValidationResult(BaseModel):
    is_valid: bool = Field(description="转调结果是否音乐上合理")
    confidence: float = Field(description="置信度 0-1", ge=0.0, le=1.0)
    issues: list[str] = Field(default_factory=list, description="发现的问题列表（无问题时为空）")
    notes: str = Field(default="", description="补充说明")


def _llm_validate(score: ScoreIR, request_id: str) -> list[Warning]:
    """
    用文本 LLM 检验：
    - 调号转换是否音乐上合理
    - 音符序列是否存在明显异常（如大量临时升降号暗示调号识别可能有误）
    """
    log = get_logger("validate")

    from tuneai.config import get_llm_config
    if not get_llm_config().get("api_key"):
        log.debug("[validate] llm api_key 未配置，跳过文本校验")
        return []

    # 取前 20 个音符事件作为样本，避免 prompt 过长
    sample = [
        {"id": e.id, "degree": e.degree,
         "accidental": e.accidental, "octave_shift": e.octave_shift}
        for e in score.events
        if isinstance(e, NoteEvent)
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

    try:
        from tuneai.core.llm_client import build_chat_openai, get_text_llm_config

        cfg = get_text_llm_config()
        llm = build_chat_openai(
            cfg,
            default_model="text-model",
            default_temperature=0.0,
            default_max_tokens=512,
            default_timeout_seconds=30,
        )
        chain = llm.with_structured_output(_LLMValidationResult, method="function_calling")
        result: _LLMValidationResult = chain.invoke(prompt)

        log.debug(
            f"[validate] LLM: is_valid={result.is_valid}, "
            f"conf={result.confidence:.2f}, issues={result.issues}"
        )

        if not result.is_valid or result.issues:
            return [Warning(
                type="llm_validation",
                message=f"LLM 校验发现问题 (conf={result.confidence:.2f}): "
                        + "; ".join(result.issues) if result.issues else result.notes,
            )]
    except Exception as e:
        log.warning(f"[validate] LLM structured output 失败: {e}")

    return []


# ---------------------------------------------------------------------------
# Layer 3：VL 视觉校验
# ---------------------------------------------------------------------------

class _VLValidationResult(BaseModel):
    key_correct: bool = Field(description="图中调号与识别结果是否一致")
    detected_key: str = Field(description="VL 从图中看到的调号，如 G、Bb")
    confidence: float = Field(description="置信度 0-1", ge=0.0, le=1.0)
    notes: str = Field(default="", description="补充说明")


_VL_PROMPT = (
    "这是一张简谱图片。系统已识别出调号为 {source_key}，目标转调为 {target_key}。\n\n"
    "请完成以下两项视觉验证：\n"
    "1. 图中实际的调号是什么（格式如 1=G、1=Bb）？\n"
    "2. 系统识别的调号 1={source_key} 是否与图中一致？\n\n"
    "直接给出判断，不需要额外解释。"
)


def _vl_validate(
    score: ScoreIR,
    original_image: np.ndarray,
    request_id: str,
) -> list[Warning]:
    """
    用 VL 多模态模型对照原图交叉验证调号识别是否正确。
    """
    log = get_logger("validate")

    from tuneai.core.llm_client import get_vision_llm_config

    cfg = get_vision_llm_config()
    if not cfg.get("api_key"):
        log.debug("[validate] vision_llm api_key 未配置，跳过 VL 校验")
        return []

    # 编码图像
    _, buf = cv2.imencode(".png", original_image)
    b64 = base64.b64encode(buf.tobytes()).decode()

    prompt = _VL_PROMPT.format(
        source_key=score.source_key.tonic,
        target_key=score.target_key.tonic,
    )

    try:
        from langchain_core.messages import HumanMessage
        from tuneai.core.llm_client import build_chat_openai

        llm = build_chat_openai(
            cfg,
            default_model="vision-model",
            default_temperature=0.0,
            default_max_tokens=128,
            default_timeout_seconds=30,
        )
        chain = llm.with_structured_output(_VLValidationResult, method="function_calling")

        message = HumanMessage(content=[
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
            {"type": "text", "text": prompt},
        ])
        result: _VLValidationResult = chain.invoke([message])

        log.debug(
            f"[validate] VL: key_correct={result.key_correct}, "
            f"detected={result.detected_key!r}, conf={result.confidence:.2f}"
        )

        if not result.key_correct:
            return [Warning(
                type="vl_key_mismatch",
                message=(
                    f"VL 视觉校验：图中调号可能为 1={result.detected_key}，"
                    f"与识别结果 1={score.source_key.tonic} 不符 "
                    f"(conf={result.confidence:.2f})"
                ),
            )]
    except Exception as e:
        log.warning(f"[validate] VL structured output 失败: {e}")

    return []
