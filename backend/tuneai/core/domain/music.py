from __future__ import annotations

from tuneai.schemas.score_ir import (
    KeyInfo,
    NoteEvent,
    ScoreIR,
)

DEGREE_TO_SEMITONE: dict[int, int] = {1: 0, 2: 2, 3: 4, 4: 5, 5: 7, 6: 9, 7: 11}
ACCIDENTAL_DELTA: dict[str, int] = {"natural": 0, "sharp": 1, "flat": -1}

KEY_TO_PC: dict[str, int] = {
    "C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3,
    "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8,
    "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11,
}

_SHARP_ENCODING: dict[int, tuple[int, str]] = {
    0: (1, "natural"), 1: (1, "sharp"), 2: (2, "natural"), 3: (2, "sharp"),
    4: (3, "natural"), 5: (4, "natural"), 6: (4, "sharp"), 7: (5, "natural"),
    8: (5, "sharp"), 9: (6, "natural"), 10: (6, "sharp"), 11: (7, "natural"),
}

_FLAT_ENCODING: dict[int, tuple[int, str]] = {
    0: (1, "natural"), 1: (2, "flat"), 2: (2, "natural"), 3: (3, "flat"),
    4: (3, "natural"), 5: (4, "natural"), 6: (5, "flat"), 7: (5, "natural"),
    8: (6, "flat"), 9: (6, "natural"), 10: (7, "flat"), 11: (7, "natural"),
}

_SHARP_KEYS = {"C", "G", "D", "A", "E", "B", "F#", "C#"}


def key_prefers_sharps(key: str) -> bool:
    return key in _SHARP_KEYS


def compute_transpose_delta(source_key: str, target_key: str) -> int:
    src_pc = KEY_TO_PC[source_key]
    tgt_pc = KEY_TO_PC[target_key]
    delta = (tgt_pc - src_pc) % 12
    if delta > 6:
        delta -= 12
    return delta


def decode_note(degree: int, accidental: str, octave_shift: int) -> int:
    semitone = DEGREE_TO_SEMITONE[degree] + ACCIDENTAL_DELTA.get(accidental, 0)
    return semitone + octave_shift * 12


def encode_note(semitone_offset: int, prefer_sharps: bool) -> tuple[int, str, int]:
    octave_shift = 0
    offset = semitone_offset
    while offset < 0:
        offset += 12
        octave_shift -= 1
    while offset >= 12:
        offset -= 12
        octave_shift += 1
    enc = _SHARP_ENCODING if prefer_sharps else _FLAT_ENCODING
    degree, accidental = enc[offset]
    return degree, accidental, octave_shift


def validate_target_key(key: str) -> bool:
    return key in KEY_TO_PC


def _transpose_note(
    degree: int,
    accidental: str,
    octave_shift: int,
    prefer_sharps: bool,
) -> tuple[int, str, int]:
    raw_offset = DEGREE_TO_SEMITONE[degree] + ACCIDENTAL_DELTA.get(accidental, 0)
    octave_adj = raw_offset // 12
    enc = _SHARP_ENCODING if prefer_sharps else _FLAT_ENCODING
    new_degree, new_acc = enc[raw_offset % 12]
    return new_degree, new_acc, octave_shift + octave_adj


def count_accidentals(score: ScoreIR) -> int:
    return sum(1 for e in score.events if isinstance(e, NoteEvent) and e.accidental != "natural")


def shift_octave(score: ScoreIR, delta: int) -> ScoreIR:
    new_events = []
    for event in score.events:
        if isinstance(event, NoteEvent):
            new_events.append(event.model_copy(update={"octave_shift": event.octave_shift + delta}))
        else:
            new_events.append(event)
    return score.model_copy(update={"events": new_events})


def transpose_score_ir(score: ScoreIR, target_key: str) -> ScoreIR:
    prefer_sharps = key_prefers_sharps(target_key)
    new_events = []
    for event in score.events:
        if isinstance(event, NoteEvent):
            new_degree, new_acc, new_oct = _transpose_note(
                event.degree, event.accidental, event.octave_shift, prefer_sharps
            )
            new_events.append(
                event.model_copy(
                    update={"degree": new_degree, "accidental": new_acc, "octave_shift": new_oct}
                )
            )
        else:
            new_events.append(event)

    new_target_key = KeyInfo(
        label=f"1={target_key}",
        tonic=target_key,
        mode=score.source_key.mode,
        bbox=score.source_key.bbox,
        confidence=score.source_key.confidence,
    )

    return ScoreIR(
        score_id=score.score_id,
        source_key=score.source_key,
        target_key=new_target_key,
        events=new_events,
    )
