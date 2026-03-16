from __future__ import annotations

from tuneai.core.adapters.ocr.types import OcrChar
from tuneai.schemas.score_ir import NoteEvent, RestEvent

_NOTE_DIGITS = frozenset("1234567")
_REST_DIGIT = "0"


def filter_note_digits(chars: list[OcrChar]) -> list[NoteEvent | RestEvent]:
    events: list[NoteEvent | RestEvent] = []
    for i, ch in enumerate(chars):
        text = ch.text.strip()
        if len(text) != 1:
            continue
        if text in _NOTE_DIGITS:
            events.append(
                NoteEvent(
                    id=f"n{i}",
                    degree=int(text),
                    accidental="natural",
                    octave_shift=0,
                    bbox=ch.bbox,
                    confidence=ch.confidence,
                )
            )
        elif text == _REST_DIGIT:
            events.append(RestEvent(id=f"r{i}", bbox=ch.bbox, confidence=ch.confidence))
    return events
