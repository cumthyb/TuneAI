"""
调号换算、12-TET 解码/编码、移调、局部转调、等音策略。
"""
from __future__ import annotations

import copy

from tuneai.schemas.score_ir import (
    BarlineEvent,
    KeyChangeEvent,
    KeyInfo,
    Measure,
    NoteEvent,
    RestEvent,
    ScoreIR,
)

# 简谱音级（1-7）到相对主音的半音偏移
DEGREE_TO_SEMITONE: dict[int, int] = {1: 0, 2: 2, 3: 4, 4: 5, 5: 7, 6: 9, 7: 11}

ACCIDENTAL_DELTA: dict[str, int] = {"natural": 0, "sharp": 1, "flat": -1}

KEY_TO_PC: dict[str, int] = {
    "C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3,
    "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8,
    "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11,
}

# 半音偏移 → (度数, 临时记号) — 升号偏好
_SHARP_ENCODING: dict[int, tuple[int, str]] = {
    0: (1, "natural"), 1: (1, "sharp"), 2: (2, "natural"), 3: (2, "sharp"),
    4: (3, "natural"), 5: (4, "natural"), 6: (4, "sharp"), 7: (5, "natural"),
    8: (5, "sharp"), 9: (6, "natural"), 10: (6, "sharp"), 11: (7, "natural"),
}

# 半音偏移 → (度数, 临时记号) — 降号偏好
_FLAT_ENCODING: dict[int, tuple[int, str]] = {
    0: (1, "natural"), 1: (2, "flat"), 2: (2, "natural"), 3: (3, "flat"),
    4: (3, "natural"), 5: (4, "natural"), 6: (5, "flat"), 7: (5, "natural"),
    8: (6, "flat"), 9: (6, "natural"), 10: (7, "flat"), 11: (7, "natural"),
}

# 偏好升号的调性（包括无升降的 C）
_SHARP_KEYS = {"C", "G", "D", "A", "E", "B", "F#", "C#"}


def key_prefers_sharps(key: str) -> bool:
    return key in _SHARP_KEYS


def compute_transpose_delta(source_key: str, target_key: str) -> int:
    """计算移调半音数，结果在 [-6, 6] 范围内（选择绝对值最小方向）。"""
    src_pc = KEY_TO_PC[source_key]
    tgt_pc = KEY_TO_PC[target_key]
    delta = (tgt_pc - src_pc) % 12
    if delta > 6:
        delta -= 12
    return delta


def decode_note(degree: int, accidental: str, octave_shift: int) -> int:
    """将简谱音符解码为相对主音的半音偏移（含八度）。"""
    semitone = DEGREE_TO_SEMITONE[degree] + ACCIDENTAL_DELTA.get(accidental, 0)
    return semitone + octave_shift * 12


def encode_note(semitone_offset: int, prefer_sharps: bool) -> tuple[int, str, int]:
    """将相对主音的半音偏移编码回 (degree, accidental, octave_shift)。"""
    # 计算八度偏移
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


def pc_to_key(pc: int, prefer_sharps: bool) -> str:
    """将音高类别编号转换为调性名称。"""
    sharps = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    flats  = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]
    table = sharps if prefer_sharps else flats
    return table[pc % 12]


def transpose_key(key: str, delta: int, prefer_sharps: bool) -> str:
    pc = (KEY_TO_PC[key] + delta) % 12
    return pc_to_key(pc, prefer_sharps)


def validate_target_key(key: str) -> bool:
    return key in KEY_TO_PC


def _transpose_note(degree: int, accidental: str, octave_shift: int, delta: int, prefer_sharps: bool) -> tuple[int, str, int]:
    """
    移调单个音符。
    策略：将音符在八度内的半音偏移（0-11）减去 delta（模 12），
    保持 octave_shift 不变。这样 "1" in G → "5" in C 不会产生额外八度点。
    """
    # 在八度范围内的偏移 [0,11]
    offset_in_oct = (DEGREE_TO_SEMITONE[degree] + ACCIDENTAL_DELTA.get(accidental, 0)) % 12
    # 应用移调
    new_offset = (offset_in_oct - delta) % 12
    # 编码新度数和临时记号（保留 octave_shift）
    enc = _SHARP_ENCODING if prefer_sharps else _FLAT_ENCODING
    new_degree, new_acc = enc[new_offset]
    return new_degree, new_acc, octave_shift


def transpose_score_ir(score: ScoreIR, target_key: str) -> ScoreIR:
    """对 ScoreIR 执行移调，返回新的 ScoreIR（不修改原对象）。"""
    source_tonic = score.source_key.tonic
    delta = compute_transpose_delta(source_tonic, target_key)
    prefer_sharps = key_prefers_sharps(target_key)

    new_measures: list[Measure] = []
    # 当前活跃 tonic（支持局部转调）
    active_tonic = source_tonic

    for measure in score.measures:
        new_events = []
        for event in measure.events:
            if isinstance(event, NoteEvent):
                new_degree, new_acc, new_oct = _transpose_note(
                    event.degree, event.accidental, event.octave_shift, delta, prefer_sharps
                )
                new_tonic = transpose_key(active_tonic, delta, prefer_sharps)
                new_event = event.model_copy(update={
                    "degree": new_degree,
                    "accidental": new_acc,
                    "octave_shift": new_oct,
                    "transposed_pitch_pc": (KEY_TO_PC.get(new_tonic, 0) + (DEGREE_TO_SEMITONE[new_degree] + ACCIDENTAL_DELTA.get(new_acc, 0))) % 12,
                    "transposed_pitch_octave": new_oct,
                    "render_tokens": _build_render_tokens(new_degree, new_acc, new_oct),
                })
                new_events.append(new_event)
            elif isinstance(event, KeyChangeEvent):
                new_tonic = transpose_key(event.tonic, delta, prefer_sharps)
                active_tonic = event.tonic  # update active tonic for subsequent notes
                new_label = f"1={new_tonic}"
                new_event = event.model_copy(update={
                    "tonic": new_tonic,
                    "label": new_label,
                })
                new_events.append(new_event)
            else:
                # RestEvent, BarlineEvent — pass through unchanged
                new_events.append(event)
        new_measures.append(Measure(number=measure.number, events=new_events))

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
        measures=new_measures,
    )


def _build_render_tokens(degree: int, accidental: str, octave_shift: int) -> list[str]:
    tokens = []
    if octave_shift > 0:
        tokens.extend(["dot_above"] * octave_shift)
    if accidental == "sharp":
        tokens.append("#")
    elif accidental == "flat":
        tokens.append("b")
    tokens.append(str(degree))
    if octave_shift < 0:
        tokens.extend(["dot_below"] * abs(octave_shift))
    return tokens
