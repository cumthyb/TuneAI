"""
音高/移调单元测试。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import pytest

from tuneai.core.music import (
    compute_transpose_delta,
    decode_note,
    encode_note,
    key_prefers_sharps,
    transpose_key,
    transpose_score_ir,
    validate_target_key,
)
from tuneai.schemas.score_ir import KeyInfo, Measure, NoteEvent, ScoreIR


# ---------------------------------------------------------------------------
# compute_transpose_delta
# ---------------------------------------------------------------------------

class TestComputeTransposeDelta:
    def test_g_to_c(self):
        # G(7) → C(0): (0-7)%12=5, 5<=6 → +5
        assert compute_transpose_delta("G", "C") == 5

    def test_d_to_c(self):
        # D(2) → C(0): (0-2)%12=10, 10>6 → -2
        assert compute_transpose_delta("D", "C") == -2

    def test_c_to_f(self):
        # C(0) → F(5): (5-0)%12=5 → +5
        assert compute_transpose_delta("C", "F") == 5

    def test_c_to_gb(self):
        # C(0) → Gb(6): delta=6, <=6 → +6 (or -6 equiv)
        d = compute_transpose_delta("C", "Gb")
        assert d in (6, -6)

    def test_c_to_c(self):
        assert compute_transpose_delta("C", "C") == 0

    def test_a_to_bb(self):
        # A(9) → Bb(10): (10-9)%12=1 → +1
        assert compute_transpose_delta("A", "Bb") == 1


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
# Accidental preference for tritone (offset=6)
# ---------------------------------------------------------------------------

class TestAccidentalPreference:
    def test_tritone_sharp_key(self):
        d, a, o = encode_note(6, prefer_sharps=True)
        assert a == "sharp"
        assert d == 4

    def test_tritone_flat_key(self):
        d, a, o = encode_note(6, prefer_sharps=False)
        assert a == "flat"
        assert d == 5


# ---------------------------------------------------------------------------
# Example A (from docs §8.4): 1=G → 1=C, delta=+5
# Notes "5 6 1" in G → "2 3 5" in C
# ---------------------------------------------------------------------------

def _make_score(tonic: str, degrees: list[int]) -> ScoreIR:
    events = [
        NoteEvent(
            id=f"n{i}",
            degree=d,
            accidental="natural",
            octave_shift=0,
        )
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

    def test_transpose_5_in_G_to_C(self):
        score = _make_score("G", [5, 6, 1])
        result = transpose_score_ir(score, "C")
        events = result.measures[0].events
        assert events[0].degree == 2   # 5 in G → 2 in C
        assert events[1].degree == 3   # 6 in G → 3 in C
        assert events[2].degree == 5   # 1 in G → 5 in C

    def test_target_key_label(self):
        score = _make_score("G", [1])
        result = transpose_score_ir(score, "C")
        assert result.target_key.tonic == "C"
        assert result.target_key.label == "1=C"


# ---------------------------------------------------------------------------
# Example B: 1=D → 1=C (delta=-2)
# ---------------------------------------------------------------------------

class TestExampleB:
    def test_degree1_in_D_to_C(self):
        score = _make_score("D", [1, 2, 3])
        result = transpose_score_ir(score, "C")
        events = result.measures[0].events
        # degree 1 in D (offset=0) → offset=0 in C → degree 1
        assert events[0].degree == 1
        # degree 2 in D (offset=2) → offset=2 in C → degree 2
        assert events[1].degree == 2
        # degree 3 in D (offset=4) → offset=4 in C → degree 3
        assert events[2].degree == 3


# ---------------------------------------------------------------------------
# validate_target_key
# ---------------------------------------------------------------------------

class TestValidateTargetKey:
    def test_valid_keys(self):
        for k in ["C", "C#", "Db", "D", "Eb", "E", "F", "F#", "Gb", "G", "Ab", "A", "Bb", "B"]:
            assert validate_target_key(k)

    def test_invalid_keys(self):
        for k in ["H", "c", "do", "", "X#"]:
            assert not validate_target_key(k)


# ---------------------------------------------------------------------------
# key_prefers_sharps
# ---------------------------------------------------------------------------

class TestKeyPrefersSharps:
    def test_sharp_keys(self):
        for k in ["C", "G", "D", "A", "E", "B", "F#"]:
            assert key_prefers_sharps(k)

    def test_flat_keys(self):
        for k in ["F", "Bb", "Eb", "Ab", "Db", "Gb"]:
            assert not key_prefers_sharps(k)
