"""Vision LLM adapter unit tests using real sample image bytes."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from tuneai.core.adapters.vision import recognize_key_signature


class TestRecognizeKeySignature:
    def test_no_api_key_raises(self, sample_image_array):
        with patch("tuneai.core.adapters.vision.get_vision_llm_config", return_value={"api_key": ""}):
            with pytest.raises(ValueError, match="vision_llm.api_key must be configured"):
                recognize_key_signature(sample_image_array, "qwen")

    def test_vl_llm_returns_parsed_tonic(self, sample_image_array):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = SimpleNamespace(content="1=G")
        with (
            patch("tuneai.core.adapters.vision.get_vision_llm_config", return_value={"api_key": "k"}),
            patch("tuneai.core.adapters.vision._get_llm", return_value=mock_llm),
        ):
            result = recognize_key_signature(sample_image_array, "qwen")
        assert result == "G"
        mock_llm.invoke.assert_called_once()

    def test_vl_llm_exception_bubbles_up(self, sample_image_array):
        with (
            patch("tuneai.core.adapters.vision.get_vision_llm_config", return_value={"api_key": "k"}),
            patch("tuneai.core.adapters.vision._get_llm", side_effect=RuntimeError("boom")),
        ):
            with pytest.raises(RuntimeError, match="boom"):
                recognize_key_signature(sample_image_array, "qwen")
