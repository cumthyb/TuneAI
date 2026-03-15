"""
端到端流水线测试。
"""
import base64
import io
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import pytest
import numpy as np


def _make_simple_score_image() -> bytes:
    """生成一张白底黑字的简单简谱测试图（含调号 1=C 和数字 1 2 3）。"""
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new("RGB", (400, 100), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.load_default(size=20)
    except TypeError:
        font = ImageFont.load_default()
    draw.text((10, 40), "1=C  1  2  3  4  5", fill=(0, 0, 0), font=font)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _make_minimal_png() -> bytes:
    b64 = (
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8"
        "z8BQDwADhQGAWjR9awAAAABJRU5ErkJggg=="
    )
    return base64.b64decode(b64)


class TestMusicTranspositionOnly:
    """
    这组测试不需要 OCR/LLM，直接测试音乐移调逻辑。
    """

    def test_transpose_c_to_g(self):
        from tuneai.core.music import transpose_score_ir
        from tuneai.schemas.score_ir import KeyInfo, Measure, NoteEvent, ScoreIR

        events = [NoteEvent(id=f"n{i}", degree=d, accidental="natural", octave_shift=0)
                  for i, d in enumerate([1, 2, 3, 4, 5])]
        score = ScoreIR(
            score_id="test",
            source_key=KeyInfo(label="1=C", tonic="C"),
            target_key=KeyInfo(label="1=C", tonic="C"),
            measures=[Measure(number=1, events=events)],
        )
        result = transpose_score_ir(score, "G")
        assert result.target_key.tonic == "G"
        assert len(result.measures[0].events) == 5

    def test_transpose_identity(self):
        """移调到相同调性，结果应与原始相同。"""
        from tuneai.core.music import transpose_score_ir
        from tuneai.schemas.score_ir import KeyInfo, Measure, NoteEvent, ScoreIR

        events = [NoteEvent(id=f"n{i}", degree=d, accidental="natural", octave_shift=0)
                  for i, d in enumerate([1, 3, 5])]
        score = ScoreIR(
            score_id="test",
            source_key=KeyInfo(label="1=D", tonic="D"),
            target_key=KeyInfo(label="1=D", tonic="D"),
            measures=[Measure(number=1, events=events)],
        )
        result = transpose_score_ir(score, "D")
        for orig, trans in zip(events, result.measures[0].events):
            assert orig.degree == trans.degree
            assert orig.accidental == trans.accidental
            assert orig.octave_shift == trans.octave_shift

    def test_score_ir_serialization(self):
        """ScoreIR 可以正常序列化为 dict。"""
        from tuneai.core.music import transpose_score_ir
        from tuneai.schemas.score_ir import KeyInfo, Measure, NoteEvent, ScoreIR

        events = [NoteEvent(id="n0", degree=1, accidental="natural", octave_shift=0)]
        score = ScoreIR(
            score_id="test",
            source_key=KeyInfo(label="1=C", tonic="C"),
            target_key=KeyInfo(label="1=C", tonic="C"),
            measures=[Measure(number=1, events=events)],
        )
        result = transpose_score_ir(score, "F")
        d = result.model_dump()
        assert "measures" in d
        assert d["target_key"]["tonic"] == "F"


class TestPipelineWithMocks:
    """
    使用 mock 替换 OCR 和 LLM，测试完整 pipeline 的数据流。
    """

    @pytest.fixture(autouse=True)
    def mock_ocr_and_llm(self):
        from tuneai.core.ocr import OCRToken
        from tuneai.core.llm import KeyCorrectionResult, MeasureCorrectionResult
        from tuneai.schemas.score_ir import KeyInfo, Measure, NoteEvent, ScoreIR

        mock_tokens = [
            OCRToken(text="1=C", bbox=[10, 10, 40, 20], confidence=0.95),
            OCRToken(text="1", bbox=[60, 40, 15, 20], confidence=0.92),
            OCRToken(text="2", bbox=[80, 40, 15, 20], confidence=0.90),
            OCRToken(text="3", bbox=[100, 40, 15, 20], confidence=0.91),
        ]

        mock_key_result = KeyCorrectionResult(
            tonic="C", label="1=C", confidence=0.95, notes=""
        )

        mock_measure_result = MeasureCorrectionResult(
            events=[], confidence=0.9, notes=""
        )

        with (
            patch("tuneai.core.ocr._get_ocr") as mock_ocr_fn,
            patch("tuneai.core.llm._get_llm") as mock_llm_fn,
        ):
            mock_ocr = MagicMock()
            mock_ocr.ocr.return_value = [[
                ([[10, 10], [50, 10], [50, 30], [10, 30]], ("1=C", 0.95)),
                ([[60, 40], [75, 40], [75, 60], [60, 60]], ("1", 0.92)),
                ([[80, 40], [95, 40], [95, 60], [80, 60]], ("2", 0.90)),
                ([[100, 40], [115, 40], [115, 60], [100, 60]], ("3", 0.91)),
            ]]
            mock_ocr_fn.return_value = mock_ocr

            mock_llm = MagicMock()
            mock_structured = MagicMock()
            mock_structured.invoke.side_effect = [mock_key_result, mock_measure_result]
            mock_llm.with_structured_output.return_value = mock_structured
            mock_llm_fn.return_value = mock_llm

            yield

    def test_full_pipeline_returns_valid_result(self):
        from tuneai.core.task_manager import run_pipeline

        image_bytes = _make_simple_score_image()
        result = run_pipeline(image_bytes, "G", "req_test001")

        assert result.output_image_b64
        # Must be valid base64
        decoded = base64.b64decode(result.output_image_b64)
        assert len(decoded) > 0

        assert result.score_ir is not None
        assert result.score_ir.target_key.tonic == "G"
        assert result.processing_time_ms >= 0

    def test_pipeline_output_image_is_valid_png(self):
        from tuneai.core.task_manager import run_pipeline
        from PIL import Image

        image_bytes = _make_simple_score_image()
        result = run_pipeline(image_bytes, "F", "req_test002")

        decoded = base64.b64decode(result.output_image_b64)
        img = Image.open(io.BytesIO(decoded))
        assert img.format == "PNG"
