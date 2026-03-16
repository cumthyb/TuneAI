"""OCR 模块单元测试。"""

from unittest.mock import MagicMock, patch

import pytest

from tuneai.core.adapters.ocr import OcrChar, run_ocr


class TestRunOcr:
    def test_calls_multimodal_with_provider_config(self, sample_image_array):
        sample = [OcrChar(text="1", bbox=[10, 20, 30, 40], confidence=0.9)]

        with (
            patch("tuneai.core.adapters.ocr.get_ocr_config", return_value={"api_key": "k", "model": "m"}),
            patch("tuneai.core.adapters.ocr.run_multimodal_ocr", return_value=sample) as mock_run,
        ):
            result = run_ocr(sample_image_array, "qwen")

        assert result == sample
        mock_run.assert_called_once_with(
            sample_image_array, {"api_key": "k", "model": "m"}, provider_label="qwen"
        )

    def test_provider_label_matches_provider_arg(self, sample_image_array):
        with (
            patch("tuneai.core.adapters.ocr.get_ocr_config", return_value={"api_key": "k"}),
            patch("tuneai.core.adapters.ocr.run_multimodal_ocr", return_value=[]) as mock_run,
        ):
            run_ocr(sample_image_array, "glm")

        assert mock_run.call_args.kwargs["provider_label"] == "glm"

    def test_provider_exception_bubbles_up(self, sample_image_array):
        with (
            patch("tuneai.core.adapters.ocr.get_ocr_config", return_value={"api_key": "k"}),
            patch("tuneai.core.adapters.ocr.run_multimodal_ocr", side_effect=RuntimeError("boom")),
        ):
            with pytest.raises(RuntimeError, match="boom"):
                run_ocr(sample_image_array, "qwen")


class TestOcrIntegration:
    """集成测试：用真实 API 对《匆匆那年》样本图片运行 OCR。

    运行方式：
        .venv/bin/pytest tests/adapters/test_ocr.py -v --run-integration
    """

    def test_real_ocr_returns_chars(self, sample_image_bytes, run_integration):
        """OCR 应返回非空字符列表，且每个字符结构合法。"""
        import numpy as np

        from tuneai.config import get_default_provider
        from tuneai.core.domain.preprocess import preprocess_image

        provider = get_default_provider()
        image = preprocess_image(sample_image_bytes)
        assert isinstance(image, np.ndarray) and image.ndim == 2

        chars = run_ocr(image, provider)

        assert len(chars) > 0, "OCR 未返回任何字符"
        for char in chars:
            assert isinstance(char, OcrChar)
            assert len(char.text) == 1
            assert len(char.bbox) == 4
            assert char.bbox[2] > 0 and char.bbox[3] > 0, f"bbox w/h 非正: {char}"
            assert 0.0 <= char.confidence <= 1.0, f"confidence 超出范围: {char}"

    def test_real_ocr_detects_jianpu_notes(self, sample_image_bytes, run_integration):
        """OCR 结果中应包含简谱音符数字（1-7 中至少 3 种）。"""
        from tuneai.config import get_default_provider
        from tuneai.core.domain.preprocess import preprocess_image

        provider = get_default_provider()
        image = preprocess_image(sample_image_bytes)
        chars = run_ocr(image, provider)

        note_digits = {c.text for c in chars if c.text in "1234567"}
        assert len(note_digits) >= 3, (
            f"识别到的音符种类不足（期望 ≥3，实际: {sorted(note_digits)}）"
        )
