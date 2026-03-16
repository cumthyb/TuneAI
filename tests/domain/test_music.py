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
        # G: 5=D, 6=E, 1=G → C: D=2, E=3, G=5
        score = _make_score("G", _nat([5, 6, 1]))
        result = transpose_score_ir(score, "C")
        ev = result.events
        assert (ev[0].degree, ev[0].accidental, ev[0].octave_shift) == (2, "natural", 1)
        assert (ev[1].degree, ev[1].accidental, ev[1].octave_shift) == (3, "natural", 1)
        assert (ev[2].degree, ev[2].accidental, ev[2].octave_shift) == (5, "natural", 0)

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
        # D major degree 1 = D → C major: D = 2
        score = _make_score("D", _nat([1]))
        result = transpose_score_ir(score, "C")
        ev = result.events[0]
        assert (ev.degree, ev.accidental, ev.octave_shift) == (2, "natural", 0)

    def test_degree3_d_to_c(self):
        # D major degree 3 = F# → C major: F# = #4
        score = _make_score("D", _nat([3]))
        result = transpose_score_ir(score, "C")
        ev = result.events[0]
        assert ev.degree == 4
        assert ev.accidental == "sharp"

    def test_degree2_d_to_c(self):
        # D major degree 2 = E → C major: E = 3
        score = _make_score("D", _nat([2]))
        result = transpose_score_ir(score, "C")
        assert result.events[0].degree == 3


class TestEnharmonicSpelling:
    def test_flat_key_prefers_flats(self):
        d, a, _ = encode_note(6, prefer_sharps=False)
        assert d == 5 and a == "flat"

    def test_sharp_key_prefers_sharps(self):
        d, a, _ = encode_note(1, prefer_sharps=True)
        assert d == 1 and a == "sharp"

    def test_transpose_accidental_g_to_c_sharp4(self):
        # G major degree 4# = C# → C major: C# = #1
        score = _make_score("G", [(4, "sharp", 0)])
        result = transpose_score_ir(score, "C")
        ev = result.events[0]
        assert (ev.degree, ev.accidental, ev.octave_shift) == (1, "sharp", 1)

    def test_transpose_accidental_g_to_f_sharp4(self):
        # G major degree 4# = C# → F major: C = degree 5, C# = #5
        score = _make_score("G", [(4, "sharp", 0)])
        result = transpose_score_ir(score, "F")
        ev = result.events[0]
        assert (ev.degree, ev.accidental, ev.octave_shift) == (5, "sharp", 0)


class TestOctaveBoundaryAccidentals:
    def test_7sharp_becomes_1_octave_up(self):
        score = _make_score("C", [(7, "sharp", 0)])
        result = transpose_score_ir(score, "C")
        ev = result.events[0]
        assert ev.degree == 1
        assert ev.accidental == "natural"
        assert ev.octave_shift == 1

    def test_7sharp_with_existing_octave(self):
        # G major degree 7# oct+1 = G (two octaves up) → C major: G = 5
        score = _make_score("G", [(7, "sharp", 1)])
        result = transpose_score_ir(score, "C")
        ev = result.events[0]
        assert ev.degree == 5
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


def _parse_ref(s: str) -> list[tuple[int, str]]:
    """Parse a reference like '#4 5 b7' into [(4,'sharp'), (5,'natural'), (7,'flat')]."""
    result = []
    for tok in s.split():
        if tok.startswith("#"):
            result.append((int(tok[1:]), "sharp"))
        elif tok.startswith("b"):
            result.append((int(tok[1:]), "flat"))
        else:
            result.append((int(tok), "natural"))
    return result


# Canonical reference table: each key's full ascending scale (8 notes, 1-7 + octave)
# expressed in C major numbered notation.
#
# C大调  1 2 3 4 5 6 7 1
# G大调  5 6 7 1 2 3 #4 5
# D大调  2 3 #4 5 6 7 #1 2
# A大调  6 7 #1 2 3 #4 #5 6
# E大调  3 #4 #5 6 7 #1 #2 3
# B大调  7 #1 #2 3 #4 #5 #6 7
# F大调  4 5 6 b7 1 2 3 4
# bB大调 b7 1 2 b3 4 5 6 b7
# bE大调 b3 4 5 b6 b7 1 2 b3
# bA大调 b6 b7 1 b2 b3 4 5 b6
# bD大调 b2 b3 4 b5 b6 b7 1 b2
# bG大调 b5 b6 b7 b1 b2 b3 4 b5
_REKEY_TABLE: list[tuple[str, str]] = [
    ("C",  "1 2 3 4 5 6 7 1"),
    ("G",  "5 6 7 1 2 3 #4 5"),
    ("D",  "2 3 #4 5 6 7 #1 2"),
    ("A",  "6 7 #1 2 3 #4 #5 6"),
    ("E",  "3 #4 #5 6 7 #1 #2 3"),
    ("B",  "7 #1 #2 3 #4 #5 #6 7"),
    ("F",  "4 5 6 b7 1 2 3 4"),
    ("Bb", "b7 1 2 b3 4 5 6 b7"),
    ("Eb", "b3 4 5 b6 b7 1 2 b3"),
    ("Ab", "b6 b7 1 b2 b3 4 5 b6"),
    ("Db", "b2 b3 4 b5 b6 b7 1 b2"),
    ("Gb", "b5 b6 b7 b1 b2 b3 4 b5"),
]


class TestScaleReKeyingToC:
    """Verify full 8-note scale re-keying against the canonical reference table.

    Each row of the mapping table is a separate parametrized test case.
    The 8th note (octave repeat) is included to verify octave-boundary handling.
    """

    @staticmethod
    def _full_scale_degrees(source: str) -> list[tuple[int, str]]:
        notes = _nat(list(range(1, 8))) + [(1, "natural", 1)]
        score = _make_score(source, notes)
        result = transpose_score_ir(score, "C")
        return [(e.degree, e.accidental) for e in result.events]

    @pytest.mark.parametrize("source_key,expected_ref", _REKEY_TABLE, ids=[k for k, _ in _REKEY_TABLE])
    def test_scale_to_c(self, source_key: str, expected_ref: str):
        actual = self._full_scale_degrees(source_key)
        expected = _parse_ref(expected_ref)
        assert actual == expected, (
            f"{source_key} -> C:\n"
            f"  expected: {expected_ref}\n"
            f"  actual:   {' '.join(_fmt(d, a) for d, a in actual)}"
        )


def _fmt(degree: int, accidental: str) -> str:
    if accidental == "sharp":
        return f"#{degree}"
    if accidental == "flat":
        return f"b{degree}"
    return str(degree)


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
