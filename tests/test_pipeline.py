"""Pipeline tests aligned with current events-based ScoreIR."""

import asyncio
import base64
import io
from unittest.mock import patch

import pytest

from tuneai.schemas.score_ir import KeyInfo, NoteEvent, ScoreIR


@pytest.fixture
def mock_ocr_and_llm():
    from tuneai.core.adapters.ocr import OcrChar

    chars = [
        OcrChar(text="1", bbox=[100, 50, 15, 20], confidence=0.93),
        OcrChar(text="2", bbox=[120, 50, 15, 20], confidence=0.91),
        OcrChar(text="3", bbox=[140, 50, 15, 20], confidence=0.94),
        OcrChar(text="4", bbox=[160, 50, 15, 20], confidence=0.89),
        OcrChar(text="5", bbox=[180, 50, 15, 20], confidence=0.92),
    ]
    with patch("tuneai.core.adapters.ocr.get_ocr_runner", return_value=lambda _img, _cfg: chars):
        yield


class TestMusicTranspositionOnly:
    def test_transpose_c_to_g(self):
        from tuneai.core.domain.music import transpose_score_ir

        events = [NoteEvent(id=f"n{i}", degree=d, accidental="natural", octave_shift=0) for i, d in enumerate([1, 2, 3, 4, 5])]
        score = ScoreIR(
            score_id="test",
            source_key=KeyInfo(label="1=C", tonic="C"),
            target_key=KeyInfo(label="1=C", tonic="C"),
            events=events,
        )
        result = transpose_score_ir(score, "G")
        assert result.target_key.tonic == "G"
        assert len(result.events) == 5

    def test_score_ir_serialization_uses_events(self):
        from tuneai.core.domain.music import transpose_score_ir

        score = ScoreIR(
            score_id="test",
            source_key=KeyInfo(label="1=C", tonic="C"),
            target_key=KeyInfo(label="1=C", tonic="C"),
            events=[NoteEvent(id="n0", degree=1, accidental="natural", octave_shift=0)],
        )
        result = transpose_score_ir(score, "F")
        dumped = result.model_dump()
        assert "events" in dumped
        assert "measures" not in dumped
        assert dumped["target_key"]["tonic"] == "F"


class TestPipelineWithMocks:
    def test_full_pipeline_with_sample_image(self, sample_image_bytes, mock_ocr_and_llm):
        from tuneai.core.application.pipeline import run_pipeline

        result = asyncio.run(run_pipeline(sample_image_bytes, "G", "req_test_sample"))
        decoded = base64.b64decode(result.output_image_b64)
        assert len(decoded) > 0
        assert result.score_ir.target_key.tonic == "G"
        assert result.processing_time_ms >= 0

    def test_pipeline_output_is_valid_png(self, sample_image_bytes, mock_ocr_and_llm):
        from PIL import Image
        from tuneai.core.application.pipeline import run_pipeline

        result = asyncio.run(run_pipeline(sample_image_bytes, "F", "req_test_png"))
        img = Image.open(io.BytesIO(base64.b64decode(result.output_image_b64)))
        assert img.format == "PNG"
        assert img.width > 0 and img.height > 0

    def test_pipeline_writes_files_to_request_dir(self, sample_image_bytes, mock_ocr_and_llm, tmp_path):
        from tuneai.core.application.pipeline import run_pipeline

        request_id = "req_test_files"
        with patch("tuneai.core.infra.storage.get_outputs_dir", return_value=tmp_path):
            asyncio.run(run_pipeline(sample_image_bytes, "C", request_id))
        req_dir = tmp_path / request_id
        assert (req_dir / "input.png").exists()
        assert (req_dir / "output.png").exists()


@pytest.fixture
def run_integration(request):
    if not request.config.getoption("run_integration"):
        pytest.skip("requires --run-integration")


class TestPipelineIntegration:
    def test_real_ocr_on_sample(self, sample_image_bytes, run_integration):
        from tuneai.core.adapters.ocr import run_ocr
        from tuneai.core.domain.preprocess import preprocess_image

        binary = preprocess_image(sample_image_bytes)
        assert len(run_ocr(binary)) > 0

    def test_real_pipeline_on_sample(self, sample_image_bytes, run_integration):
        from tuneai.core.application.pipeline import run_pipeline

        result = asyncio.run(run_pipeline(sample_image_bytes, "C", "req_integration"))
        assert result.score_ir is not None
        assert result.output_image_b64
