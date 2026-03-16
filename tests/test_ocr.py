"""OCR 模块单元测试（provider/factory 架构）。"""

from unittest.mock import MagicMock, patch

import numpy as np

from tuneai.core.ocr import OcrChar, run_ocr


class TestRunOcr:
    def test_supported_provider_calls_runner(self):
        sample = [OcrChar(text="1", bbox=[10, 20, 30, 40], confidence=0.9)]
        runner = MagicMock(return_value=sample)

        with (
            patch("tuneai.config.get_ocr_config", return_value={"provider": "aliyun", "config": {"k": "v"}}),
            patch("tuneai.core.ocr.get_ocr_runner", return_value=runner),
        ):
            result = run_ocr(np.zeros((10, 10), dtype=np.uint8))

        assert result == sample
        runner.assert_called_once()

    def test_unknown_provider_returns_empty(self):
        with (
            patch("tuneai.config.get_ocr_config", return_value={"provider": "unknown", "config": {}}),
            patch("tuneai.core.ocr.get_ocr_runner", return_value=None),
        ):
            result = run_ocr(np.zeros((10, 10), dtype=np.uint8))

        assert result == []

    def test_provider_exception_returns_empty(self):
        runner = MagicMock(side_effect=RuntimeError("boom"))
        with (
            patch("tuneai.config.get_ocr_config", return_value={"provider": "aliyun", "config": {}}),
            patch("tuneai.core.ocr.get_ocr_runner", return_value=runner),
        ):
            result = run_ocr(np.zeros((10, 10), dtype=np.uint8))

        assert result == []
