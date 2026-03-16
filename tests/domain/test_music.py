"""
音高/移调单元测试。
"""
import pytest

from tuneai.core.domain.music import (
    compute_transpose_delta,
    decode_note,
    encode_note,
    key_prefers_sharps,
    transpose_score_ir,
    validate_target_key,
)
from tuneai.schemas.score_ir import KeyInfo, NoteEvent, ScoreIR


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
        assert compute_transpose_delta("Eb", "C") == -3


class TestDecodeEncodeRoundTrip:
    @pytest.mark.parametrize("degree,acc,oct_", [
        (1, "natural", 0),
        (1, "sharp", 0),
        (2, "flat", 0),
        (3, "natural", 1),
        (4, "natural", -1),
        (5, "sharp", 0),
        (6, "flat", 0),
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
        (2, "flat", 0),
        (3, "flat", 0),
        (5, "flat", 0),
        (7, "flat", 0),
    ])
    def test_round_trip_flat(self, degree, acc, oct_):
        offset = decode_note(degree, acc, oct_)
        d2, a2, o2 = encode_note(offset, prefer_sharps=False)
        assert decode_note(d2, a2, o2) == offset


class TestAccidentalPreference:
    def test_tritone_sharp_key(self):
        d, a, o = encode_note(6, prefer_sharps=True)
        assert d == 4 and a == "sharp"

    def test_tritone_flat_key(self):
        d, a, o = encode_note(6, prefer_sharps=False)
        assert d == 5 and a == "flat"


def _make_score(tonic: str, notes: list[tuple[int, str, int]]) -> ScoreIR:
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
    return [(d, "natural", 0) for d in degrees]


class TestExampleA:
    def test_transpose_567(self):
        score = _make_score("G", _nat([5, 6, 1]))
        result = transpose_score_ir(score, "C")
        ev = result.events
        assert (ev[0].degree, ev[0].accidental, ev[0].octave_shift) == (1, "natural", 1)
        assert (ev[1].degree, ev[1].accidental, ev[1].octave_shift) == (2, "natural", 1)
        assert (ev[2].degree, ev[2].accidental, ev[2].octave_shift) == (4, "natural", 0)

    def test_octave_shift_preserved(self):
        score = _make_score("G", [(1, "natural", 1)])
        result = transpose_score_ir(score, "C")
        assert result.events[0].octave_shift == 1

    def test_target_key_updated(self):
        score = _make_score("G", _nat([1]))
        result = transpose_score_ir(score, "C")
        assert result.target_key.tonic == "C"
        assert result.target_key.label == "1=C"


class TestExampleB:
    def test_degree1_d_to_c(self):
        score = _make_score("D", _nat([1]))
        result = transpose_score_ir(score, "C")
        ev = result.events[0]
        assert (ev.degree, ev.accidental, ev.octave_shift) == (6, "sharp", -1)

    def test_degree3_d_to_c(self):
        score = _make_score("D", _nat([3]))
        result = transpose_score_ir(score, "C")
        ev = result.events[0]
        assert ev.degree == 2
        assert ev.accidental == "natural"

    def test_degree2_d_to_c(self):
        score = _make_score("D", _nat([2]))
        result = transpose_score_ir(score, "C")
        assert result.events[0].degree == 1


class TestEnharmonicSpelling:
    def test_flat_key_prefers_flats(self):
        d, a, _ = encode_note(6, prefer_sharps=False)
        assert d == 5 and a == "flat"

    def test_sharp_key_prefers_sharps(self):
        d, a, _ = encode_note(1, prefer_sharps=True)
        assert d == 1 and a == "sharp"

    def test_transpose_accidental_g_to_c_sharp4(self):
        score = _make_score("G", [(4, "sharp", 0)])
        result = transpose_score_ir(score, "C")
        ev = result.events[0]
        assert ev.degree == 7 and ev.accidental == "natural"

    def test_transpose_accidental_g_to_f_b5(self):
        score = _make_score("G", [(4, "sharp", 0)])
        result = transpose_score_ir(score, "F")
        ev = result.events[0]
        assert ev.degree == 3 and ev.accidental == "natural"


class TestOctaveBoundaryAccidentals:
    def test_7sharp_becomes_1_octave_up(self):
        score = _make_score("C", [(7, "sharp", 0)])
        result = transpose_score_ir(score, "C")
        ev = result.events[0]
        assert ev.degree == 1
        assert ev.accidental == "natural"
        assert ev.octave_shift == 1

    def test_7sharp_with_existing_octave(self):
        score = _make_score("G", [(7, "sharp", 1)])
        result = transpose_score_ir(score, "C")
        ev = result.events[0]
        assert ev.degree == 4
        assert ev.octave_shift == 2

    def test_1flat_becomes_7_octave_down(self):
        score = _make_score("C", [(1, "flat", 0)])
        result = transpose_score_ir(score, "C")
        ev = result.events[0]
        assert ev.degree == 7
        assert ev.accidental == "natural"
        assert ev.octave_shift == -1

    def test_1flat_with_existing_octave(self):
        score = _make_score("C", [(1, "flat", -1)])
        result = transpose_score_ir(score, "C")
        ev = result.events[0]
        assert ev.degree == 7
        assert ev.octave_shift == -2


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


class TestKeyPrefersSharps:
    @pytest.mark.parametrize("key", ["C", "G", "D", "A", "E", "B", "F#", "C#"])
    def test_sharp_keys(self, key):
        assert key_prefers_sharps(key)

    @pytest.mark.parametrize("key", ["F", "Bb", "Eb", "Ab", "Db", "Gb"])
    def test_flat_keys(self, key):
        assert not key_prefers_sharps(key)
