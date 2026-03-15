"""
LLM 模块单元测试（langchain-openai ^1.1 + openai ^2.0）。

测试策略：
  - _structured: mock _get_llm，验证 method 路由（function_calling / json_schema）
  - correct_key_signature:
      空输入 → 直接返回默认值，不调用 LLM
      正常输入 → mock _structured 链，验证 invoke 调用
      LLM 抛异常 → 回退到正则解析
  - correct_low_confidence_measure:
      正常 → mock 返回修正结果
      LLM 异常 → 原样返回 tokens，confidence=0.5
  - _fallback_key_parse: 直接测试各种调号格式与降级行为
  - Pydantic 模型：边界校验
"""
from unittest.mock import MagicMock, patch

import pytest

from tuneai.core.llm import (
    KeyCorrectionResult,
    MeasureCorrectionResult,
    _fallback_key_parse,
    correct_key_signature,
    correct_low_confidence_events,
)


# ---------------------------------------------------------------------------
# 辅助：构造 mock _structured 链
# ---------------------------------------------------------------------------

def _make_structured_mock(return_value):
    """返回 patch tuneai.core.llm._structured 用的 mock。"""
    chain = MagicMock()
    chain.invoke.return_value = return_value
    return chain


# ---------------------------------------------------------------------------
# correct_key_signature
# ---------------------------------------------------------------------------

class TestCorrectKeySignature:

    def test_empty_raw_text_skips_llm(self):
        """空输入不调用 LLM，直接返回低置信度默认值。"""
        with patch("tuneai.core.llm._structured") as mock_s:
            result = correct_key_signature("", "target_key=C", "req_test")
        mock_s.assert_not_called()
        assert result.tonic == "C"
        assert result.label == "1=C"
        assert result.confidence < 0.5

    def test_returns_llm_result(self):
        expected = KeyCorrectionResult(tonic="G", label="1=G", confidence=0.95)
        with patch("tuneai.core.llm._structured", return_value=_make_structured_mock(expected)):
            result = correct_key_signature("1=G", "target_key=C", "req_test")
        assert result.tonic == "G"
        assert result.confidence == pytest.approx(0.95)

    def test_prompt_contains_raw_text(self):
        expected = KeyCorrectionResult(tonic="F", label="1=F", confidence=0.88)
        mock_chain = _make_structured_mock(expected)
        with patch("tuneai.core.llm._structured", return_value=mock_chain):
            correct_key_signature("1＝F(降)", "target_key=C", "req_test")
        prompt = mock_chain.invoke.call_args[0][0]
        assert "1＝F(降)" in prompt

    def test_llm_exception_falls_back_to_regex(self):
        """LLM 异常时降级正则，不向外抛出。"""
        chain = MagicMock()
        chain.invoke.side_effect = ConnectionError("LLM unavailable")
        with patch("tuneai.core.llm._structured", return_value=chain):
            result = correct_key_signature("1=D", "target_key=C", "req_test")
        assert result.tonic == "D"
        assert result.label == "1=D"

    def test_llm_exception_unrecognizable_returns_default_c(self):
        chain = MagicMock()
        chain.invoke.side_effect = RuntimeError("timeout")
        with patch("tuneai.core.llm._structured", return_value=chain):
            result = correct_key_signature("乱码###无法识别", "target_key=C", "req_test")
        assert result.tonic == "C"
        assert result.confidence < 0.5


# ---------------------------------------------------------------------------
# _structured — method 路由
# ---------------------------------------------------------------------------

class TestStructuredMethod:

    def _call_structured(self, method_cfg: str, schema):
        """patch config，验证 with_structured_output 调用参数。"""
        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value = MagicMock()
        with (
            patch("tuneai.core.llm._get_llm", return_value=mock_llm),
            patch(
                "tuneai.config.get_llm_config",
                return_value={"structured_output_method": method_cfg},
            ),
        ):
            from tuneai.core.llm import _structured
            _structured(schema)
        return mock_llm.with_structured_output.call_args

    def test_function_calling_method(self):
        call_args = self._call_structured("function_calling", KeyCorrectionResult)
        kwargs = call_args.kwargs
        assert kwargs.get("method") == "function_calling"

    def test_json_schema_method(self):
        call_args = self._call_structured("json_schema", KeyCorrectionResult)
        kwargs = call_args.kwargs
        assert kwargs.get("method") == "json_schema"
        assert kwargs.get("strict") is True

    def test_default_is_function_calling(self):
        """未配置时默认用 function_calling（最广兼容）。"""
        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value = MagicMock()
        with (
            patch("tuneai.core.llm._get_llm", return_value=mock_llm),
            patch("tuneai.config.get_llm_config", return_value={}),
        ):
            from tuneai.core.llm import _structured
            _structured(KeyCorrectionResult)
        kwargs = mock_llm.with_structured_output.call_args.kwargs
        assert kwargs.get("method") == "function_calling"


# ---------------------------------------------------------------------------
# correct_low_confidence_measure
# ---------------------------------------------------------------------------

class TestCorrectLowConfidenceEvents:

    _sample_tokens = [
        {"id": "n0", "type": "note", "degree": 1, "accidental": "natural", "confidence": 0.95},
        {"id": "n1", "type": "note", "degree": 3, "accidental": "natural", "confidence": 0.45},
    ]

    def test_returns_llm_result(self):
        expected = MeasureCorrectionResult(
            events=self._sample_tokens, confidence=0.92, notes="已纠正"
        )
        with patch("tuneai.core.llm._structured", return_value=_make_structured_mock(expected)):
            result = correct_low_confidence_events(
                self._sample_tokens, "C", "req_test"
            )
        assert result.confidence == pytest.approx(0.92)

    def test_prompt_contains_active_key(self):
        expected = MeasureCorrectionResult(events=[], confidence=0.9)
        mock_chain = _make_structured_mock(expected)
        with patch("tuneai.core.llm._structured", return_value=mock_chain):
            correct_low_confidence_events(self._sample_tokens, "Bb", "req_test")
        prompt = mock_chain.invoke.call_args[0][0]
        assert "Bb" in prompt

    def test_llm_exception_returns_original_tokens(self):
        chain = MagicMock()
        chain.invoke.side_effect = TimeoutError("LLM timeout")
        with patch("tuneai.core.llm._structured", return_value=chain):
            result = correct_low_confidence_events(
                self._sample_tokens, "G", "req_test"
            )
        assert result.events == self._sample_tokens
        assert result.confidence == pytest.approx(0.5)
        assert "TimeoutError" in result.notes or "timeout" in result.notes.lower()

    def test_empty_tokens(self):
        """空 token 列表也能正常处理。"""
        expected = MeasureCorrectionResult(events=[], confidence=1.0)
        with patch("tuneai.core.llm._structured", return_value=_make_structured_mock(expected)):
            result = correct_low_confidence_events([], "C", "req_test")
        assert result.events == []


# ---------------------------------------------------------------------------
# _create_llm — Ollama 兼容参数
# ---------------------------------------------------------------------------

class TestCreateLlm:

    def test_disabled_params_set_when_configured(self):
        """disable_parallel_tool_calls=true 时，disabled_params 应传给 ChatOpenAI。"""
        mock_cls = MagicMock()
        cfg = {
            "model": "llama3",
            "base_url": "http://localhost:11434/v1",
            "api_key": "ollama",
            "temperature": 0.1,
            "max_tokens": 2048,
            "timeout_seconds": 30,
            "disable_parallel_tool_calls": True,
        }
        with (
            patch("tuneai.config.get_llm_config", return_value=cfg),
            patch("langchain_openai.ChatOpenAI", mock_cls),
        ):
            from tuneai.core.llm import _create_llm
            _create_llm()

        call_kwargs = mock_cls.call_args.kwargs
        assert call_kwargs.get("disabled_params") == {"parallel_tool_calls": None}

    def test_disabled_params_none_when_not_configured(self):
        """未配置时 disabled_params 应为 None。"""
        mock_cls = MagicMock()
        cfg = {
            "model": "gpt-4o-mini",
            "temperature": 0.1,
            "max_tokens": 4096,
            "timeout_seconds": 30,
            "disable_parallel_tool_calls": False,
        }
        with (
            patch("tuneai.config.get_llm_config", return_value=cfg),
            patch("langchain_openai.ChatOpenAI", mock_cls),
        ):
            from tuneai.core.llm import _create_llm
            _create_llm()

        call_kwargs = mock_cls.call_args.kwargs
        assert call_kwargs.get("disabled_params") is None

    def test_timeout_passed_as_float(self):
        """timeout 应以 float 传给 ChatOpenAI（openai 2.x 要求）。"""
        mock_cls = MagicMock()
        cfg = {"model": "gpt-4o-mini", "timeout_seconds": 45}
        with (
            patch("tuneai.config.get_llm_config", return_value=cfg),
            patch("langchain_openai.ChatOpenAI", mock_cls),
        ):
            from tuneai.core.llm import _create_llm
            _create_llm()

        timeout = mock_cls.call_args.kwargs.get("timeout")
        assert isinstance(timeout, float)
        assert timeout == 45.0


# ---------------------------------------------------------------------------
# _fallback_key_parse
# ---------------------------------------------------------------------------

class TestFallbackKeyParse:

    @pytest.mark.parametrize("text,expected_tonic", [
        ("1=C",          "C"),
        ("1=G#",         "G#"),
        ("1=Bb",         "Bb"),
        ("1 = F",        "F"),
        ("调性: 1=D",    "D"),
        ("1＝A",         "A"),
        ("1=Eb",         "Eb"),
        ("1一G",         "G"),   # OCR 误把 = 识别为 一
    ])
    def test_recognizes_formats(self, text, expected_tonic):
        result = _fallback_key_parse(text)
        assert result.tonic == expected_tonic
        assert result.label == f"1={expected_tonic}"
        assert result.confidence > 0

    @pytest.mark.parametrize("text", ["无调号", "abcdefg", "12345", ""])
    def test_unrecognizable_returns_default_c(self, text):
        result = _fallback_key_parse(text)
        assert result.tonic == "C"
        assert result.confidence < 0.4

    def test_unicode_sharp_normalized(self):
        assert _fallback_key_parse("1=G♯").tonic == "G#"

    def test_unicode_flat_normalized(self):
        assert _fallback_key_parse("1=B♭").tonic == "Bb"


# ---------------------------------------------------------------------------
# Pydantic 模型边界
# ---------------------------------------------------------------------------

class TestPydanticModels:

    def test_confidence_upper_bound(self):
        with pytest.raises(Exception):
            KeyCorrectionResult(tonic="C", label="1=C", confidence=1.5)

    def test_confidence_lower_bound(self):
        with pytest.raises(Exception):
            KeyCorrectionResult(tonic="C", label="1=C", confidence=-0.1)

    def test_notes_defaults_to_empty(self):
        r = KeyCorrectionResult(tonic="G", label="1=G", confidence=0.9)
        assert r.notes == ""

    def test_measure_correction_events_list(self):
        r = MeasureCorrectionResult(events=[{"id": "n0"}], confidence=0.8)
        assert len(r.events) == 1
