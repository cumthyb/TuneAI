"""LLM adapter tests for strict configuration contract."""

from unittest.mock import MagicMock, patch

import pytest

from tuneai.core.adapters.llm import (
    KeyCorrectionResult,
    MeasureCorrectionResult,
    correct_key_signature,
    correct_low_confidence_events,
)
from tuneai.core.adapters.llm_client import build_chat_openai


def _make_structured_mock(return_value):
    chain = MagicMock()
    chain.invoke.return_value = return_value
    return chain


class TestCorrectKeySignature:
    def test_empty_raw_text_raises(self):
        with pytest.raises(ValueError, match="raw_text must be non-empty"):
            correct_key_signature("", "ctx", "req", "qwen")

    def test_returns_llm_result(self):
        expected = KeyCorrectionResult(tonic="G", label="1=G", confidence=0.95, notes="ok")
        with patch("tuneai.core.adapters.llm._structured", return_value=_make_structured_mock(expected)):
            result = correct_key_signature("1=G", "ctx", "req", "qwen")
        assert result.tonic == "G"
        assert result.confidence == pytest.approx(0.95)

    def test_llm_exception_bubbles_up(self):
        chain = MagicMock()
        chain.invoke.side_effect = RuntimeError("boom")
        with patch("tuneai.core.adapters.llm._structured", return_value=chain):
            with pytest.raises(RuntimeError, match="boom"):
                correct_key_signature("1=D", "ctx", "req", "qwen")


class TestCorrectLowConfidenceEvents:
    def test_returns_llm_result(self):
        tokens = [{"id": "n0", "type": "note", "degree": 1, "accidental": "natural", "confidence": 0.9}]
        expected = MeasureCorrectionResult(events=tokens, confidence=0.92, notes="ok")
        with patch("tuneai.core.adapters.llm._structured", return_value=_make_structured_mock(expected)):
            result = correct_low_confidence_events(tokens, "C", "req", "qwen")
        assert result.confidence == pytest.approx(0.92)

    def test_exception_bubbles_up(self):
        tokens = [{"id": "n1", "type": "note", "degree": 3, "accidental": "natural", "confidence": 0.4}]
        chain = MagicMock()
        chain.invoke.side_effect = TimeoutError("timeout")
        with patch("tuneai.core.adapters.llm._structured", return_value=chain):
            with pytest.raises(TimeoutError, match="timeout"):
                correct_low_confidence_events(tokens, "C", "req", "qwen")


class TestStructured:
    def test_always_uses_function_calling(self):
        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value = MagicMock()
        with patch("tuneai.core.adapters.llm._build_llm", return_value=mock_llm):
            from tuneai.core.adapters.llm import _structured
            _structured(KeyCorrectionResult, "qwen")
        assert mock_llm.with_structured_output.call_args.kwargs.get("method") == "function_calling"


class TestPydanticModels:
    def test_confidence_upper_bound(self):
        with pytest.raises(Exception):
            KeyCorrectionResult(tonic="C", label="1=C", confidence=1.5, notes="n")

    def test_confidence_lower_bound(self):
        with pytest.raises(Exception):
            KeyCorrectionResult(tonic="C", label="1=C", confidence=-0.1, notes="n")


class TestLlmClientConfigDriven:
    def _minimal_cfg(self):
        return {
            "client_class": "pkg.mod.Client",
            "client_kwargs": {},
            "provider": "qwen",
            "model": "m",
            "base_url": "https://example/v1",
            "api_key": "k",
            "temperature": 0.1,
            "max_tokens": 128,
            "timeout_seconds": 30,
            "model_kwargs": {},
            "extra_body": {},
        }

    def test_build_chat_openai_requires_explicit_fields(self):
        with pytest.raises(ValueError):
            build_chat_openai({"api_key": "k"})

    def test_build_chat_openai_uses_explicit_base_url(self):
        mock_cls = MagicMock()
        with patch("tuneai.core.adapters.llm_client._resolve_client_class", return_value=mock_cls):
            cfg = self._minimal_cfg()
            cfg["base_url"] = "https://custom/v1"
            build_chat_openai(cfg)
        assert mock_cls.call_args.kwargs["base_url"] == "https://custom/v1"

    def test_passes_model_kwargs_and_extra_body(self):
        mock_cls = MagicMock()
        with patch("tuneai.core.adapters.llm_client._resolve_client_class", return_value=mock_cls):
            cfg = self._minimal_cfg()
            cfg["model_kwargs"] = {"top_p": 0.7}
            cfg["extra_body"] = {"enable_thinking": True}
            build_chat_openai(cfg)
        kwargs = mock_cls.call_args.kwargs
        assert kwargs["model_kwargs"] == {"top_p": 0.7}
        assert kwargs["extra_body"] == {"enable_thinking": True}

    def test_disable_parallel_tool_calls_maps_to_disabled_params(self):
        mock_cls = MagicMock()
        with patch("tuneai.core.adapters.llm_client._resolve_client_class", return_value=mock_cls):
            cfg = self._minimal_cfg()
            cfg["disable_parallel_tool_calls"] = True
            build_chat_openai(cfg)
        assert mock_cls.call_args.kwargs["disabled_params"] == {"parallel_tool_calls": None}
