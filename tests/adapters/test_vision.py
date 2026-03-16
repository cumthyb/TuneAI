"""Vision LLM adapter unit tests using real sample image bytes."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from tuneai.core.adapters.vision import recognize_key_signature


class TestRecognizeKeySignature:
    def test_no_api_key_returns_default_c(self, sample_image_array):
        with patch("tuneai.core.adapters.vision.get_vision_llm_config", return_value={"api_key": ""}):
            result = recognize_key_signature(sample_image_array)
        assert result == "C"

    def test_vl_llm_returns_parsed_tonic(self, sample_image_array):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = SimpleNamespace(content="1=G")
        with (
            patch("tuneai.core.adapters.vision.get_vision_llm_config", return_value={"api_key": "k"}),
            patch("tuneai.core.adapters.vision._get_llm", return_value=mock_llm),
        ):
            result = recognize_key_signature(sample_image_array)
        assert result == "G"
        mock_llm.invoke.assert_called_once()

    def test_vl_llm_exception_falls_back_to_c(self, sample_image_array):
        with (
            patch("tuneai.core.adapters.vision.get_vision_llm_config", return_value={"api_key": "k"}),
            patch("tuneai.core.adapters.vision._get_llm", side_effect=RuntimeError("boom")),
        ):
            result = recognize_key_signature(sample_image_array)
        assert result == "C"
