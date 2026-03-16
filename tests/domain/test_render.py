import io

from PIL import Image

from tuneai.core.domain.render import render_output
from tuneai.schemas.score_ir import KeyInfo, NoteEvent, ScoreIR


class TestRender:
    def _make_png(self) -> bytes:
        img = Image.new("RGB", (120, 40), color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    def _make_scores(self):
        original = ScoreIR(
            score_id="s1",
            source_key=KeyInfo(label="1=C", tonic="C"),
            target_key=KeyInfo(label="1=C", tonic="C"),
            events=[NoteEvent(id="n1", degree=1, accidental="natural", octave_shift=0, bbox=[10, 10, 20, 20])],
        )
        transposed = ScoreIR(
            score_id="s1",
            source_key=KeyInfo(label="1=C", tonic="C"),
            target_key=KeyInfo(label="1=G", tonic="G"),
            events=[NoteEvent(id="n1", degree=2, accidental="natural", octave_shift=0, bbox=[10, 10, 20, 20])],
        )
        return original, transposed

    def test_render_output_returns_png_bytes(self):
        original, transposed = self._make_scores()
        output = render_output(self._make_png(), original, transposed)
        parsed = Image.open(io.BytesIO(output))
        assert parsed.format == "PNG"
        assert parsed.size == (120, 40)
