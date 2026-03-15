"""
音高/移调单元测试。
"""
import pytest

# conftest.py 已将 backend 加入 sys.path

from tuneai.core.music import (
    compute_transpose_delta,
    decode_note,
    encode_note,
    key_prefers_sharps,
    transpose_score_ir,
    validate_target_key,
)
from tuneai.schemas.score_ir import KeyInfo, Measure, NoteEvent, ScoreIR


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
# Example A (docs §8.4): 1=G → 1=C, delta=+5
# Notes "5 6 1" → "2 3 5"
# ---------------------------------------------------------------------------

def _make_score(tonic: str, degrees: list[int]) -> ScoreIR:
    events = [
        NoteEvent(id=f"n{i}", degree=d, accidental="natural", octave_shift=0)
        for i, d in enumerate(degrees)
    ]
    return ScoreIR(
        score_id="test",
        source_key=KeyInfo(label=f"1={tonic}", tonic=tonic),
        target_key=KeyInfo(label=f"1={tonic}", tonic=tonic),
        measures=[Measure(number=1, events=events)],
    )


class TestExampleA:
    """1=G, notes 5 6 1 → 1=C, notes 2 3 5 (delta=+5)"""

    def test_transpose(self):
        score = _make_score("G", [5, 6, 1])
        result = transpose_score_ir(score, "C")
        ev = result.measures[0].events
        assert ev[0].degree == 2   # D in G → D in C = degree 2
        assert ev[1].degree == 3   # E in G → E in C = degree 3
        assert ev[2].degree == 5   # G in G → G in C = degree 5

    def test_octave_shift_preserved(self):
        """移调不改变 octave_shift。"""
        score = _make_score("G", [1])
        result = transpose_score_ir(score, "C")
        assert result.measures[0].events[0].octave_shift == 0

    def test_target_key_updated(self):
        score = _make_score("G", [1])
        result = transpose_score_ir(score, "C")
        assert result.target_key.tonic == "C"
        assert result.target_key.label == "1=C"


# ---------------------------------------------------------------------------
# Example B: 1=D → 1=C (delta=-2)
# ---------------------------------------------------------------------------

class TestExampleB:
    def test_degree1_d_to_c(self):
        """D 调的 1（=D 音）→ C 调的 2（=D 音）。"""
        score = _make_score("D", [1])
        result = transpose_score_ir(score, "C")
        assert result.measures[0].events[0].degree == 2

    def test_degree3_d_to_c(self):
        """D 调的 3（=F#）→ C 调的 #4（F# 在 C 调为升四度）。"""
        score = _make_score("D", [3])
        result = transpose_score_ir(score, "C")
        ev = result.measures[0].events[0]
        assert ev.degree == 4
        assert ev.accidental == "sharp"


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
