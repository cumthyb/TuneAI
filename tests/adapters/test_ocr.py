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
