from __future__ import annotations

import numpy as np

from tuneai.logging_config import get_logger
from tuneai.schemas.request_response import Warning
from tuneai.schemas.score_ir import NoteEvent, ScoreIR

_LOW_CONF_THRESHOLD = 0.7
_VALID_TONICS = {
    "C", "C#", "Db", "D", "D#", "Eb", "E",
    "F", "F#", "Gb", "G", "G#", "Ab", "A", "A#", "Bb", "B",
}


def validate_score_rules(score: ScoreIR) -> list[Warning]:
    log = get_logger("validate")
    warnings: list[Warning] = []

    if not score.source_key.tonic:
        warnings.append(Warning(type="KEY_NOT_FOUND", message="未能识别到调号"))
    elif score.source_key.tonic not in _VALID_TONICS:
        warnings.append(
            Warning(type="INVALID_KEY", message=f"识别到的调号不合法: {score.source_key.tonic!r}")
        )
    if score.target_key.tonic not in _VALID_TONICS:
        warnings.append(
            Warning(type="INVALID_TARGET_KEY", message=f"目标调号不合法: {score.target_key.tonic!r}")
        )
    for ev in score.events:
        if isinstance(ev, NoteEvent) and ev.confidence < _LOW_CONF_THRESHOLD:
            warnings.append(
                Warning(type="low_confidence", message=f"事件 {ev.id} 置信度较低 ({ev.confidence:.2f})")
            )
    if not score.events:
        warnings.append(Warning(type="EMPTY_SCORE", message="乐谱中未识别到任何音符"))
        
    if warnings:
        log.warning(f"validate_score_rules: {len(warnings)} warning(s)")
    return warnings
