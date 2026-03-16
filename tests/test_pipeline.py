"""
端到端流水线测试。

- TestMusicTranspositionOnly: 纯音乐逻辑，无外部依赖
- TestPipelineWithMocks:       用 mock 替换 OCR/LLM，使用 data/samples/匆匆那年.png
- TestPipelineIntegration:     (可选) 真实 OCR+LLM，需要 --run-integration 标志
"""
import base64
import asyncio
import io
from pathlib import Path
from unittest.mock import patch

import pytest

# conftest.py 已将 backend 加入 sys.path


# ---------------------------------------------------------------------------
# 纯音乐移调逻辑测试（无外部依赖）
# ---------------------------------------------------------------------------

class TestMusicTranspositionOnly:

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


# ---------------------------------------------------------------------------
# Pipeline mock 测试（使用真实样本图，mock OCR/LLM）
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_ocr_and_llm():
    """Mock OCR provider runner，返回固定数字序列。"""
    from tuneai.core.ocr import OcrChar

    chars = [
        OcrChar(text="1", bbox=[100, 50, 15, 20], confidence=0.93),
        OcrChar(text="2", bbox=[120, 50, 15, 20], confidence=0.91),
        OcrChar(text="3", bbox=[140, 50, 15, 20], confidence=0.94),
        OcrChar(text="4", bbox=[160, 50, 15, 20], confidence=0.89),
        OcrChar(text="5", bbox=[180, 50, 15, 20], confidence=0.92),
    ]

    with patch("tuneai.core.ocr.get_ocr_runner", return_value=lambda _img, _cfg: chars):
        yield


class TestPipelineWithMocks:

    def test_full_pipeline_with_sample_image(self, sample_image_bytes, mock_ocr_and_llm):
        """使用 匆匆那年.png 运行完整 pipeline（OCR/LLM 已 mock）。"""
        from tuneai.core.task_manager import run_pipeline

        result = asyncio.run(run_pipeline(sample_image_bytes, "G", "req_test_sample"))

        # 输出 base64 可解码
        decoded = base64.b64decode(result.output_image_b64)
        assert len(decoded) > 0

        # ScoreIR 目标调正确
        assert result.score_ir.target_key.tonic == "G"
        assert result.processing_time_ms >= 0

    def test_pipeline_output_is_valid_png(self, sample_image_bytes, mock_ocr_and_llm):
        """输出图必须是合法的 PNG 文件。"""
        from tuneai.core.task_manager import run_pipeline
        from PIL import Image

        result = asyncio.run(run_pipeline(sample_image_bytes, "F", "req_test_png"))
        decoded = base64.b64decode(result.output_image_b64)
        img = Image.open(io.BytesIO(decoded))
        assert img.format == "PNG"
        assert img.width > 0 and img.height > 0

    def test_pipeline_writes_files_to_request_dir(self, sample_image_bytes, mock_ocr_and_llm, tmp_path):
        """pipeline 应写入 input.png 和 output.png 到请求目录。"""
        from unittest.mock import patch as _patch
        from tuneai.core.task_manager import run_pipeline

        request_id = "req_test_files"

        # 临时覆盖 outputs 目录到 tmp_path
        with _patch("tuneai.core.storage.get_outputs_dir", return_value=tmp_path):
            asyncio.run(run_pipeline(sample_image_bytes, "C", request_id))

        req_dir = tmp_path / request_id
        assert (req_dir / "input.png").exists(), "input.png 应在请求目录中"
        assert (req_dir / "output.png").exists(), "output.png 应在请求目录中"

    def test_pipeline_transpose_g_to_c(self, sample_image_bytes, mock_ocr_and_llm):
        """1=G 简谱移调到 C，ScoreIR target_key 应为 C。"""
        from tuneai.core.task_manager import run_pipeline

        result = asyncio.run(run_pipeline(sample_image_bytes, "C", "req_test_g2c"))
        assert result.score_ir.target_key.tonic == "C"
        assert result.score_ir.target_key.label == "1=C"


# ---------------------------------------------------------------------------
# 可选：真实集成测试（需要 --run-integration 命令行选项）
# ---------------------------------------------------------------------------

def pytest_addoption(parser):
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="运行需要真实 OCR 和 LLM 的集成测试",
    )


@pytest.fixture
def run_integration(request):
    if not request.config.getoption("--run-integration"):
        pytest.skip("需要 --run-integration 标志才能运行")


class TestPipelineIntegration:
    """真实 OCR + LLM 集成测试，需要 --run-integration 且环境已就绪。"""

    def test_real_ocr_on_sample(self, sample_image_bytes, run_integration):
        from tuneai.core.preprocess import preprocess_image
        from tuneai.core.ocr import run_ocr

        binary = preprocess_image(sample_image_bytes)
        tokens = run_ocr(binary)
        assert len(tokens) > 0, "应识别到至少一个 token"

    def test_real_pipeline_on_sample(self, sample_image_bytes, run_integration):
        from tuneai.core.task_manager import run_pipeline

        result = asyncio.run(run_pipeline(sample_image_bytes, "C", "req_integration"))
        assert result.score_ir is not None
        assert result.output_image_b64
