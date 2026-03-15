"""
低置信度标记、规则一致性、端到端校验。
"""
from __future__ import annotations

from tuneai.logging_config import get_logger
from tuneai.schemas.request_response import Warning
from tuneai.schemas.score_ir import NoteEvent, ScoreIR

_LOW_CONF_THRESHOLD = 0.7
_VALID_TONICS = {
    "C", "C#", "Db", "D", "D#", "Eb", "E",
    "F", "F#", "Gb", "G", "G#", "Ab", "A", "A#", "Bb", "B",
}


def validate_score(score: ScoreIR) -> list[Warning]:
    """
    校验 ScoreIR，返回 Warning 列表（不抛异常）。
    """
    log = get_logger("validate")
    warnings: list[Warning] = []

    # 1. 调号识别成功
    if not score.source_key.tonic:
        warnings.append(Warning(
            type="KEY_NOT_FOUND",
            message="未能识别调号，已使用默认值 1=C",
        ))
    elif score.source_key.tonic not in _VALID_TONICS:
        warnings.append(Warning(
            type="INVALID_KEY",
            message=f"识别到的调号不合法: {score.source_key.tonic!r}",
        ))

    # 2. 目标调号合法性
    if score.target_key.tonic not in _VALID_TONICS:
        warnings.append(Warning(
            type="INVALID_TARGET_KEY",
            message=f"目标调号不合法: {score.target_key.tonic!r}",
        ))

    # 3. 低置信度事件
    for measure in score.measures:
        for ev in measure.events:
            if isinstance(ev, NoteEvent) and ev.confidence < _LOW_CONF_THRESHOLD:
                warnings.append(Warning(
                    type="low_confidence",
                    measure=measure.number,
                    message=(
                        f"小节 {measure.number} 中音符 id={ev.id} "
                        f"置信度较低 ({ev.confidence:.2f})"
                    ),
                ))

    # 4. 无小节内容警告
    if not score.measures or all(not m.events for m in score.measures):
        warnings.append(Warning(
            type="EMPTY_SCORE",
            message="乐谱中未识别到任何音符",
        ))

    if warnings:
        log.warning(f"validate_score: {len(warnings)} warning(s)")

    return warnings
