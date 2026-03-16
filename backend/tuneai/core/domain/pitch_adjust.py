from __future__ import annotations

from tuneai.logging_config import get_logger
from tuneai.schemas.request_response import Warning
from tuneai.schemas.score_ir import ScoreIR


def adjust_pitch(score: ScoreIR, request_id: str = "") -> tuple[ScoreIR, list[Warning]]:
    log = get_logger("pitch_adjust")
    log.debug(f"[pitch_adjust] MVP stub, request_id={request_id!r}")
    return score, []
