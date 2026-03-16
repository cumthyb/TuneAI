"""LLM module tests aligned with current implementation."""

from unittest.mock import MagicMock, patch

import pytest

from tuneai.core.adapters.llm import (
    KeyCorrectionResult,
    MeasureCorrectionResult,
    PitchAssessmentResult,
    _fallback_key_parse,
    assess_pitch_range,
    correct_key_signature,
    correct_low_confidence_events,
)
from tuneai.core.adapters.llm_client import build_chat_openai


def _make_structured_mock(return_value):
    chain = MagicMock()
    chain.invoke.return_value = return_value
    return chain


class TestCorrectKeySignature:
    def test_empty_raw_text_skips_llm(self):
        with patch("tuneai.core.adapters.llm._structured") as mock_s:
            result = correct_key_signature("", "ctx", "req")
        mock_s.assert_not_called()
        assert result.tonic == "C"
        assert result.label == "1=C"

    def test_returns_llm_result(self):
        expected = KeyCorrectionResult(tonic="G", label="1=G", confidence=0.95)
        with patch("tuneai.core.adapters.llm._structured", return_value=_make_structured_mock(expected)):
            result = correct_key_signature("1=G", "ctx", "req")
        assert result.tonic == "G"
        assert result.confidence == pytest.approx(0.95)

    def test_llm_exception_falls_back_to_regex(self):
        chain = MagicMock()
        chain.invoke.side_effect = RuntimeError("boom")
        with patch("tuneai.core.adapters.llm._structured", return_value=chain):
            result = correct_key_signature("1=D", "ctx", "req")
        assert result.tonic == "D"


class TestCorrectLowConfidenceEvents:
    def test_returns_llm_result(self):
        tokens = [{"id": "n0", "type": "note", "degree": 1, "accidental": "natural", "confidence": 0.9}]
        expected = MeasureCorrectionResult(events=tokens, confidence=0.92, notes="ok")
        with patch("tuneai.core.adapters.llm._structured", return_value=_make_structured_mock(expected)):
            result = correct_low_confidence_events(tokens, "C", "req")
        assert result.confidence == pytest.approx(0.92)

    def test_exception_returns_original(self):
        tokens = [{"id": "n1", "type": "note", "degree": 3, "accidental": "natural", "confidence": 0.4}]
        chain = MagicMock()
        chain.invoke.side_effect = TimeoutError("timeout")
        with patch("tuneai.core.adapters.llm._structured", return_value=chain):
            result = correct_low_confidence_events(tokens, "C", "req")
        assert result.events == tokens
        assert result.confidence == pytest.approx(0.5)


class TestStructured:
    def test_always_uses_function_calling(self):
        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value = MagicMock()
        with patch("tuneai.core.adapters.llm._get_llm", return_value=mock_llm):
            from tuneai.core.adapters.llm import _structured
            _structured(KeyCorrectionResult)
        assert mock_llm.with_structured_output.call_args.kwargs.get("method") == "function_calling"


class TestPitchAssessmentStub:
    def test_assess_pitch_range_returns_stub(self):
        result = assess_pitch_range(events=[], source_key="C", target_key="G")
        assert isinstance(result, PitchAssessmentResult)
        assert result.too_high is False
        assert result.octave_adjust == 0


class TestFallbackKeyParse:
    @pytest.mark.parametrize(
        "text,expected_tonic",
        [("1=C", "C"), ("1=G#", "G#"), ("1=Bb", "Bb"), ("1＝A", "A"), ("1一G", "G")],
    )
    def test_recognizes_formats(self, text, expected_tonic):
        result = _fallback_key_parse(text)
        assert result.tonic == expected_tonic
        assert result.label == f"1={expected_tonic}"

    def test_unrecognizable_returns_default_c(self):
        result = _fallback_key_parse("乱码")
        assert result.tonic == "C"


class TestPydanticModels:
    def test_confidence_upper_bound(self):
        with pytest.raises(Exception):
            KeyCorrectionResult(tonic="C", label="1=C", confidence=1.5)

    def test_confidence_lower_bound(self):
        with pytest.raises(Exception):
            KeyCorrectionResult(tonic="C", label="1=C", confidence=-0.1)


class TestLlmClientConfigDriven:
    def test_qwen_provider_uses_default_base_url(self):
        mock_cls = MagicMock()
        with patch("tuneai.core.adapters.llm_client._resolve_client_class", return_value=mock_cls):
            build_chat_openai(
                {"provider": "qwen", "api_key": "k"},
                default_model="m",
                default_temperature=0.1,
                default_max_tokens=128,
                default_timeout_seconds=30,
            )
        assert (
            mock_cls.call_args.kwargs["base_url"]
            == "https://dashscope.aliyuncs.com/compatible-mode/v1"
        )

    def test_glm_provider_uses_default_base_url(self):
        mock_cls = MagicMock()
        with patch("tuneai.core.adapters.llm_client._resolve_client_class", return_value=mock_cls):
            build_chat_openai(
                {"provider": "glm", "api_key": "k"},
                default_model="m",
                default_temperature=0.1,
                default_max_tokens=128,
                default_timeout_seconds=30,
            )
        assert mock_cls.call_args.kwargs["base_url"] == "https://open.bigmodel.cn/api/paas/v4"

    def test_explicit_base_url_overrides_provider_preset(self):
        mock_cls = MagicMock()
        with patch("tuneai.core.adapters.llm_client._resolve_client_class", return_value=mock_cls):
            build_chat_openai(
                {"provider": "qwen", "base_url": "https://custom/v1", "api_key": "k"},
                default_model="m",
                default_temperature=0.1,
                default_max_tokens=128,
                default_timeout_seconds=30,
            )
        assert mock_cls.call_args.kwargs["base_url"] == "https://custom/v1"

    def test_passes_model_kwargs_and_extra_body(self):
        mock_cls = MagicMock()
        with patch("tuneai.core.adapters.llm_client._resolve_client_class", return_value=mock_cls):
            build_chat_openai(
                {
                    "api_key": "k",
                    "model_kwargs": {"top_p": 0.7},
                    "extra_body": {"enable_thinking": True},
                },
                default_model="m",
                default_temperature=0.1,
                default_max_tokens=128,
                default_timeout_seconds=30,
            )
        kwargs = mock_cls.call_args.kwargs
        assert kwargs["model_kwargs"] == {"top_p": 0.7}
        assert kwargs["extra_body"] == {"enable_thinking": True}

    def test_disable_parallel_tool_calls_maps_to_disabled_params(self):
        mock_cls = MagicMock()
        with patch("tuneai.core.adapters.llm_client._resolve_client_class", return_value=mock_cls):
            build_chat_openai(
                {"api_key": "k", "disable_parallel_tool_calls": True},
                default_model="m",
                default_temperature=0.1,
                default_max_tokens=128,
                default_timeout_seconds=30,
            )
        assert mock_cls.call_args.kwargs["disabled_params"] == {"parallel_tool_calls": None}
