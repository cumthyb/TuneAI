"""
调号换算、12-TET 解码/编码、移调、等音策略。

移调原理（十二平均律）：
  设 offset_in_oct = 音符相对原主音的半音偏移（0-11）
     delta         = tgt_pc - src_pc（模 12）= 主音音高类之差

  音符绝对音高类：abs_pc = (src_pc + offset_in_oct) % 12
  平移后绝对音高：abs_pc_new = (abs_pc + delta) % 12
  相对新主音偏移：new_offset = (abs_pc_new - tgt_pc) % 12
                             = (src_pc + offset_in_oct + delta - tgt_pc) % 12
                             = offset_in_oct   ← delta 与 tgt_pc - src_pc 抵消

  结论：音符相对主音的偏移量不变，只需按目标调的升降号偏好重新编码。
  delta 仅用于推算新调名（transpose_key），不用于音符本身的转换。
"""
from __future__ import annotations

from tuneai.schemas.score_ir import (
    KeyInfo,
    NoteEvent,
    RestEvent,
    ScoreIR,
)

# 简谱音级（1-7）到相对主音的半音偏移（大调音阶）
DEGREE_TO_SEMITONE: dict[int, int] = {1: 0, 2: 2, 3: 4, 4: 5, 5: 7, 6: 9, 7: 11}

ACCIDENTAL_DELTA: dict[str, int] = {"natural": 0, "sharp": 1, "flat": -1}

KEY_TO_PC: dict[str, int] = {
    "C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3,
    "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8,
    "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11,
}

# 半音偏移（0-11）→ (度数, 临时记号)，升号偏好
_SHARP_ENCODING: dict[int, tuple[int, str]] = {
    0: (1, "natural"), 1: (1, "sharp"),  2: (2, "natural"), 3: (2, "sharp"),
    4: (3, "natural"), 5: (4, "natural"), 6: (4, "sharp"),  7: (5, "natural"),
    8: (5, "sharp"),   9: (6, "natural"), 10: (6, "sharp"), 11: (7, "natural"),
}

# 半音偏移（0-11）→ (度数, 临时记号)，降号偏好
_FLAT_ENCODING: dict[int, tuple[int, str]] = {
    0: (1, "natural"), 1: (2, "flat"),   2: (2, "natural"), 3: (3, "flat"),
    4: (3, "natural"), 5: (4, "natural"), 6: (5, "flat"),   7: (5, "natural"),
    8: (6, "flat"),    9: (6, "natural"), 10: (7, "flat"),  11: (7, "natural"),
}

# 偏好升号的调性（含无升降的 C）
_SHARP_KEYS = {"C", "G", "D", "A", "E", "B", "F#", "C#"}


def key_prefers_sharps(key: str) -> bool:
    return key in _SHARP_KEYS


def compute_transpose_delta(source_key: str, target_key: str) -> int:
    """
    计算从原调到目标调的半音数，范围 [-6, 6]（选绝对值最小方向）。
    仅用于推算新调名（transpose_key），不用于音符偏移计算。
    """
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
    sharps = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    flats  = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]
    return (sharps if prefer_sharps else flats)[pc % 12]


def transpose_key(key: str, delta: int, prefer_sharps: bool) -> str:
    """将调名按 delta 半音平移（用于更新调号标记）。"""
    pc = (KEY_TO_PC[key] + delta) % 12
    return pc_to_key(pc, prefer_sharps)


def validate_target_key(key: str) -> bool:
    return key in KEY_TO_PC


def _transpose_note(
    degree: int, accidental: str, octave_shift: int,
    prefer_sharps: bool,
) -> tuple[int, str, int]:
    """
    移调单个音符。

    原理：音符相对主音的半音偏移（offset_in_oct）在移调后不变——
    原调主音和音符均平移同一个 delta，相对位置抵消。
    因此只需按目标调的升降号偏好对相同 offset 重新编码。

    示例（1=G → 1=C）：
      "5" in G: offset = DEGREE_TO_SEMITONE[5] = 7
      SHARP_ENCODING[7] = (5, "natural") → "5" in C  ✓
      （绝对音高 D→G，即上移 5 个半音）

    边界处理：
      degree=7, accidental="sharp"  → raw_offset=12 → 跨八度向上，octave_shift +1
      degree=1, accidental="flat"   → raw_offset=-1 → 跨八度向下，octave_shift -1
    """
    raw_offset = DEGREE_TO_SEMITONE[degree] + ACCIDENTAL_DELTA.get(accidental, 0)
    # Python floor-division 正确处理负数：(-1)//12 == -1，12//12 == 1
    octave_adj = raw_offset // 12
    enc = _SHARP_ENCODING if prefer_sharps else _FLAT_ENCODING
    new_degree, new_acc = enc[raw_offset % 12]
    return new_degree, new_acc, octave_shift + octave_adj


def count_accidentals(score: ScoreIR) -> int:
    """统计 ScoreIR 中非 natural 的音符数量（半音使用量）。"""
    return sum(
        1 for e in score.events
        if isinstance(e, NoteEvent) and e.accidental != "natural"
    )


def shift_octave(score: ScoreIR, delta: int) -> ScoreIR:
    """
    将 ScoreIR 中所有音符的 octave_shift 整体平移 delta 个八度。
    delta=-1 表示整体降低一个八度；不修改原对象。
    """
    new_events = []
    for event in score.events:
        if isinstance(event, NoteEvent):
            new_events.append(event.model_copy(update={
                "octave_shift": event.octave_shift + delta,
            }))
        else:
            new_events.append(event)
    return score.model_copy(update={"events": new_events})


def transpose_score_ir(score: ScoreIR, target_key: str) -> ScoreIR:
    """对 ScoreIR 执行移调，返回新的 ScoreIR（不修改原对象）。"""
    prefer_sharps = key_prefers_sharps(target_key)

    new_events = []
    for event in score.events:
        if isinstance(event, NoteEvent):
            new_degree, new_acc, new_oct = _transpose_note(
                event.degree, event.accidental, event.octave_shift, prefer_sharps
            )
            new_events.append(event.model_copy(update={
                "degree": new_degree,
                "accidental": new_acc,
                "octave_shift": new_oct,
            }))
        else:
            # RestEvent — 休止符不参与移调
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
