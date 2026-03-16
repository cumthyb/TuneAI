"""OCR 模块单元测试（provider/factory 架构）。"""

from unittest.mock import MagicMock, patch

from tuneai.core.adapters.ocr import OcrChar, run_ocr


class TestRunOcr:
    def test_supported_provider_calls_runner(self, sample_image_array):
        sample = [OcrChar(text="1", bbox=[10, 20, 30, 40], confidence=0.9)]
        runner = MagicMock(return_value=sample)

        with (
            patch("tuneai.core.adapters.ocr.get_default_provider", return_value="qwen"),
            patch("tuneai.core.adapters.ocr.get_ocr_config", return_value={"runner": "pkg.mod:run", "k": "v"}),
            patch("tuneai.core.adapters.ocr.get_ocr_runner", return_value=runner),
            patch("tuneai.core.adapters.ocr.get_provider_overrides", return_value=(None, None, None)),
        ):
            result = run_ocr(sample_image_array)

        assert result == sample
        runner.assert_called_once()

    def test_unknown_provider_returns_empty(self, sample_image_array):
        with (
            patch("tuneai.core.adapters.ocr.get_default_provider", return_value="unknown"),
            patch("tuneai.core.adapters.ocr.get_ocr_config", return_value={"runner": ""}),
            patch("tuneai.core.adapters.ocr.get_ocr_runner", return_value=None),
            patch("tuneai.core.adapters.ocr.get_provider_overrides", return_value=(None, None, None)),
        ):
            result = run_ocr(sample_image_array)

        assert result == []

    def test_provider_exception_returns_empty(self, sample_image_array):
        runner = MagicMock(side_effect=RuntimeError("boom"))
        with (
            patch("tuneai.core.adapters.ocr.get_default_provider", return_value="qwen"),
            patch("tuneai.core.adapters.ocr.get_ocr_config", return_value={"runner": "pkg.mod:run"}),
            patch("tuneai.core.adapters.ocr.get_ocr_runner", return_value=runner),
            patch("tuneai.core.adapters.ocr.get_provider_overrides", return_value=(None, None, None)),
        ):
            result = run_ocr(sample_image_array)

        assert result == []

    def test_provider_override_missing_runner_returns_empty(self, sample_image_array):
        with (
            patch("tuneai.core.adapters.ocr.get_default_provider", return_value="qwen"),
            patch("tuneai.core.adapters.ocr.get_ocr_config", return_value={"runner": ""}),
            patch("tuneai.core.adapters.ocr.get_ocr_runner", return_value=None),
            patch("tuneai.core.adapters.ocr.get_provider_overrides", return_value=(None, None, "glm")),
        ):
            result = run_ocr(sample_image_array)

        assert result == []
