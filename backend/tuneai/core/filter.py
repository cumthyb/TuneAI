"""
后处理过滤（第三步，本地）。
过滤阿里 OCR 结果，只保留识别内容为 0-7 的 bbox，得到干净的音符坐标列表。
"""
from __future__ import annotations

from tuneai.core.ocr import OcrChar
from tuneai.schemas.score_ir import NoteEvent, RestEvent

_NOTE_DIGITS = frozenset("1234567")
_REST_DIGIT = "0"


def filter_note_digits(chars: list[OcrChar]) -> list[NoteEvent | RestEvent]:
    """
    过滤 OcrChar 列表，保留识别内容为单个 0-7 数字的项目。
    0 → RestEvent；1-7 → NoteEvent（初始 accidental=natural, octave_shift=0）。
    """
    events: list[NoteEvent | RestEvent] = []
    for i, ch in enumerate(chars):
        text = ch.text.strip()
        if len(text) != 1:
            continue

        if text in _NOTE_DIGITS:
            events.append(NoteEvent(
                id=f"n{i}",
                degree=int(text),
                accidental="natural",
                octave_shift=0,
                bbox=ch.bbox,
                confidence=ch.confidence,
            ))
        elif text == _REST_DIGIT:
            events.append(RestEvent(
                id=f"r{i}",
                bbox=ch.bbox,
                confidence=ch.confidence,
            ))

    return events
