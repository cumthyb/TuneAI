"""
音高/移调单元测试。
"""
import pytest

# conftest.py 已将 backend 加入 sys.path

from tuneai.core.domain.music import (
    compute_transpose_delta,
    decode_note,
    encode_note,
    key_prefers_sharps,
    transpose_score_ir,
    validate_target_key,
)
from tuneai.schemas.score_ir import KeyInfo, NoteEvent, ScoreIR


# ---------------------------------------------------------------------------
# compute_transpose_delta
# ---------------------------------------------------------------------------

class TestComputeTransposeDelta:
    def test_g_to_c(self):
        assert compute_transpose_delta("G", "C") == 5

    def test_d_to_c(self):
        assert compute_transpose_delta("D", "C") == -2

    def test_c_to_f(self):
        assert compute_transpose_delta("C", "F") == 5

    def test_c_to_gb_tritone(self):
        d = compute_transpose_delta("C", "Gb")
        assert d in (6, -6)

    def test_identity(self):
        assert compute_transpose_delta("C", "C") == 0

    def test_a_to_bb(self):
        assert compute_transpose_delta("A", "Bb") == 1

    def test_eb_to_c(self):
        # Eb(3) → C(0): (0-3+12)%12=9, 9>6 → -3
        assert compute_transpose_delta("Eb", "C") == -3


# ---------------------------------------------------------------------------
# decode_note / encode_note round-trip
# ---------------------------------------------------------------------------

class TestDecodeEncodeRoundTrip:
    @pytest.mark.parametrize("degree,acc,oct_", [
        (1, "natural", 0),
        (1, "sharp",   0),
        (2, "flat",    0),
        (3, "natural", 1),
        (4, "natural", -1),
        (5, "sharp",   0),
        (6, "flat",    0),
        (7, "natural", 0),
        (7, "natural", -1),
        (1, "natural", 2),
    ])
    def test_round_trip_sharp(self, degree, acc, oct_):
        offset = decode_note(degree, acc, oct_)
        d2, a2, o2 = encode_note(offset, prefer_sharps=True)
        assert decode_note(d2, a2, o2) == offset

    @pytest.mark.parametrize("degree,acc,oct_", [
        (1, "natural", 0),
        (2, "flat",    0),
        (3, "flat",    0),
        (5, "flat",    0),
        (7, "flat",    0),
    ])
    def test_round_trip_flat(self, degree, acc, oct_):
        offset = decode_note(degree, acc, oct_)
        d2, a2, o2 = encode_note(offset, prefer_sharps=False)
        assert decode_note(d2, a2, o2) == offset


# ---------------------------------------------------------------------------
# Accidental preference for tritone (semitone_offset=6)
# ---------------------------------------------------------------------------

class TestAccidentalPreference:
    def test_tritone_sharp_key(self):
        d, a, o = encode_note(6, prefer_sharps=True)
        assert d == 4 and a == "sharp"

    def test_tritone_flat_key(self):
        d, a, o = encode_note(6, prefer_sharps=False)
        assert d == 5 and a == "flat"


# ---------------------------------------------------------------------------
# 辅助
# ---------------------------------------------------------------------------

def _make_score(tonic: str, notes: list[tuple[int, str, int]]) -> ScoreIR:
    """notes: list of (degree, accidental, octave_shift)"""
    events = [
        NoteEvent(id=f"n{i}", degree=d, accidental=a, octave_shift=o)
        for i, (d, a, o) in enumerate(notes)
    ]
    return ScoreIR(
        score_id="test",
        source_key=KeyInfo(label=f"1={tonic}", tonic=tonic),
        target_key=KeyInfo(label=f"1={tonic}", tonic=tonic),
        events=events,
    )


def _nat(degrees: list[int]) -> list[tuple[int, str, int]]:
    """快速构造 natural 音符列表。"""
    return [(d, "natural", 0) for d in degrees]


# ---------------------------------------------------------------------------
# Example A (docs §8.4): 1=G → 1=C, delta=+5
# 音符相对主音的偏移不变，仅按目标调偏好重编码
# G 调 "5 6 1" 的偏移: 7, 9, 0 → C 调对应 degree 5, 6, 1
# ---------------------------------------------------------------------------

class TestExampleA:
    """1=G, notes 5 6 1 → 1=C, notes 5 6 1（偏移相同，大调度数相同）"""

    def test_transpose_567(self):
        score = _make_score("G", _nat([5, 6, 1]))
        result = transpose_score_ir(score, "C")
        ev = result.events
        assert ev[0].degree == 5   # offset 7 → 5 in C
        assert ev[1].degree == 6   # offset 9 → 6 in C
        assert ev[2].degree == 1   # offset 0 → 1 in C

    def test_octave_shift_preserved(self):
        score = _make_score("G", [(1, "natural", 1)])
        result = transpose_score_ir(score, "C")
        assert result.events[0].octave_shift == 1

    def test_target_key_updated(self):
        score = _make_score("G", _nat([1]))
        result = transpose_score_ir(score, "C")
        assert result.target_key.tonic == "C"
        assert result.target_key.label == "1=C"


# ---------------------------------------------------------------------------
# Example B: 1=D → 1=C (delta=-2)
# D 调 degree=3 (F#) offset=4 → C 调: SHARP_ENCODING[4]=(3,"natural") → degree 3
# D 调 degree=1 (D)   offset=0 → C 调: degree 1
# ---------------------------------------------------------------------------

class TestExampleB:
    def test_degree1_d_to_c(self):
        """D 调的 1（offset=0）→ C 调的 1（offset=0 不变）。"""
        score = _make_score("D", _nat([1]))
        result = transpose_score_ir(score, "C")
        assert result.events[0].degree == 1

    def test_degree3_d_to_c(self):
        """D 调的 3（offset=4, F#）→ C 调的 3 natural（offset=4, E）。"""
        score = _make_score("D", _nat([3]))
        result = transpose_score_ir(score, "C")
        ev = result.events[0]
        assert ev.degree == 3
        assert ev.accidental == "natural"

    def test_degree2_d_to_c(self):
        """D 调的 2（offset=2, E）→ C 调的 2（offset=2, D）。"""
        score = _make_score("D", _nat([2]))
        result = transpose_score_ir(score, "C")
        assert result.events[0].degree == 2


# ---------------------------------------------------------------------------
# 等音拼写：升号调 vs 降号调
# ---------------------------------------------------------------------------

class TestEnharmonicSpelling:
    def test_flat_key_prefers_flats(self):
        """F 调（降号调），offset 6 应编为 b5，不是 #4。"""
        d, a, _ = encode_note(6, prefer_sharps=False)
        assert d == 5 and a == "flat"

    def test_sharp_key_prefers_sharps(self):
        """G 调（升号调），offset 1 应编为 #1，不是 b2。"""
        d, a, _ = encode_note(1, prefer_sharps=True)
        assert d == 1 and a == "sharp"

    def test_transpose_accidental_g_to_c_sharp4(self):
        """1=G 调 #4（offset=6）→ 1=C 调应为 #4（C 是升号调）。"""
        score = _make_score("G", [(4, "sharp", 0)])
        result = transpose_score_ir(score, "C")
        ev = result.events[0]
        assert ev.degree == 4 and ev.accidental == "sharp"

    def test_transpose_accidental_g_to_f_b5(self):
        """1=G 调 #4（offset=6）→ 1=F 调应为 b5（F 是降号调）。"""
        score = _make_score("G", [(4, "sharp", 0)])
        result = transpose_score_ir(score, "F")
        ev = result.events[0]
        assert ev.degree == 5 and ev.accidental == "flat"


# ---------------------------------------------------------------------------
# 边界：跨八度临时记号（7# 和 1b）
# ---------------------------------------------------------------------------

class TestOctaveBoundaryAccidentals:
    """
    7# (offset=12) 和 1b (offset=-1) 是跨越八度界的临时记号。
    移调后应正确调整 octave_shift。
    """

    def test_7sharp_becomes_1_octave_up(self):
        """
        7# 相对主音偏移 12 semitones = 下一个八度的主音。
        移调后应编码为 degree=1, natural, octave_shift+1。
        """
        score = _make_score("C", [(7, "sharp", 0)])
        result = transpose_score_ir(score, "C")
        ev = result.events[0]
        assert ev.degree == 1
        assert ev.accidental == "natural"
        assert ev.octave_shift == 1  # 跨八度，+1

    def test_7sharp_with_existing_octave(self):
        """7# 带有 octave_shift=1，移调后 octave_shift 应为 2。"""
        score = _make_score("G", [(7, "sharp", 1)])
        result = transpose_score_ir(score, "C")
        ev = result.events[0]
        assert ev.degree == 1
        assert ev.octave_shift == 2

    def test_1flat_becomes_7_octave_down(self):
        """
        1b 相对主音偏移 -1 semitone = 下方八度的 7 natural。
        移调后应编码为 degree=7, natural, octave_shift-1。
        """
        score = _make_score("C", [(1, "flat", 0)])
        result = transpose_score_ir(score, "C")
        ev = result.events[0]
        assert ev.degree == 7
        assert ev.accidental == "natural"
        assert ev.octave_shift == -1  # 跨八度，-1

    def test_1flat_with_existing_octave(self):
        """1b 带有 octave_shift=-1，移调后 octave_shift 应为 -2。"""
        score = _make_score("C", [(1, "flat", -1)])
        result = transpose_score_ir(score, "C")
        ev = result.events[0]
        assert ev.degree == 7
        assert ev.octave_shift == -2


# ---------------------------------------------------------------------------
# validate_target_key
# ---------------------------------------------------------------------------

class TestValidateTargetKey:
    @pytest.mark.parametrize("key", [
        "C", "C#", "Db", "D", "D#", "Eb", "E",
        "F", "F#", "Gb", "G", "G#", "Ab", "A", "A#", "Bb", "B",
    ])
    def test_valid_keys(self, key):
        assert validate_target_key(key)

    @pytest.mark.parametrize("key", ["H", "c", "do", "", "X#", "C##"])
    def test_invalid_keys(self, key):
        assert not validate_target_key(key)


# ---------------------------------------------------------------------------
# key_prefers_sharps
# ---------------------------------------------------------------------------

class TestKeyPrefersSharps:
    @pytest.mark.parametrize("key", ["C", "G", "D", "A", "E", "B", "F#", "C#"])
    def test_sharp_keys(self, key):
        assert key_prefers_sharps(key)

    @pytest.mark.parametrize("key", ["F", "Bb", "Eb", "Ab", "Db", "Gb"])
    def test_flat_keys(self, key):
        assert not key_prefers_sharps(key)
