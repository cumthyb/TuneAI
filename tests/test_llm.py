"""
LLM 模块单元测试。

测试策略：
- correct_key_signature:
    - 空输入 → 直接返回默认值，不调用 LLM
    - 正常输入 → mock LLM 返回结构化结果
    - LLM 抛异常 → 回退到正则解析（_fallback_key_parse）
- correct_low_confidence_measure:
    - 正常输入 → mock LLM 返回修正结果
    - LLM 抛异常 → 返回原始 tokens，confidence=0.5
- _fallback_key_parse（内部函数）通过 correct_key_signature 间接覆盖
"""
from unittest.mock import MagicMock, patch

import pytest

from tuneai.core.llm import (
    KeyCorrectionResult,
    MeasureCorrectionResult,
    _fallback_key_parse,
    correct_key_signature,
    correct_low_confidence_measure,
)


# ---------------------------------------------------------------------------
# correct_key_signature
# ---------------------------------------------------------------------------

class TestCorrectKeySignature:

    def test_empty_raw_text_returns_default_without_llm(self):
        """空输入不应调用 LLM，直接返回 1=C 默认值。"""
        with patch("tuneai.core.llm._get_llm") as mock_get:
            result = correct_key_signature("", "target_key=C", "req_test")
        mock_get.assert_not_called()
        assert result.tonic == "C"
        assert result.label == "1=C"
        assert result.confidence < 0.5  # 低置信度标记默认值

    def test_llm_called_with_nonempty_input(self):
        """有内容时应调用 LLM。"""
        expected = KeyCorrectionResult(tonic="G", label="1=G", confidence=0.95)
        mock_structured = MagicMock()
        mock_structured.invoke.return_value = expected
        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured

        with patch("tuneai.core.llm._get_llm", return_value=mock_llm):
            result = correct_key_signature("1=G", "target_key=C", "req_test")

        assert result.tonic == "G"
        assert result.label == "1=G"
        assert result.confidence == pytest.approx(0.95)
        mock_structured.invoke.assert_called_once()

    def test_llm_receives_raw_text_in_prompt(self):
        """LLM prompt 应包含原始 OCR 文字。"""
        expected = KeyCorrectionResult(tonic="F", label="1=F", confidence=0.88)
        mock_structured = MagicMock()
        mock_structured.invoke.return_value = expected
        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured

        with patch("tuneai.core.llm._get_llm", return_value=mock_llm):
            correct_key_signature("1＝F(降)", "target_key=C", "req_test")

        prompt = mock_structured.invoke.call_args[0][0]
        assert "1＝F(降)" in prompt

    def test_llm_exception_falls_back_to_regex(self):
        """LLM 抛异常时应降级到正则解析，不向外抛出。"""
        mock_structured = MagicMock()
        mock_structured.invoke.side_effect = ConnectionError("LLM unavailable")
        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured

        with patch("tuneai.core.llm._get_llm", return_value=mock_llm):
            result = correct_key_signature("1=D", "target_key=C", "req_test")

        # 正则能识别出 D
        assert result.tonic == "D"
        assert result.label == "1=D"

    def test_llm_exception_with_unrecognizable_text_returns_default_c(self):
        """LLM 异常且正则也无法解析时，回退至 1=C。"""
        mock_structured = MagicMock()
        mock_structured.invoke.side_effect = RuntimeError("timeout")
        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured

        with patch("tuneai.core.llm._get_llm", return_value=mock_llm):
            result = correct_key_signature("无法识别的乱码###", "target_key=C", "req_test")

        assert result.tonic == "C"
        assert result.confidence < 0.5

    def test_structured_output_called_with_correct_model(self):
        """with_structured_output 应传入 KeyCorrectionResult。"""
        expected = KeyCorrectionResult(tonic="A", label="1=A", confidence=0.9)
        mock_structured = MagicMock()
        mock_structured.invoke.return_value = expected
        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured

        with patch("tuneai.core.llm._get_llm", return_value=mock_llm):
            correct_key_signature("1=A", "target_key=G", "req_test")

        mock_llm.with_structured_output.assert_called_once_with(KeyCorrectionResult)


# ---------------------------------------------------------------------------
# correct_low_confidence_measure
# ---------------------------------------------------------------------------

class TestCorrectLowConfidenceMeasure:

    _sample_tokens = [
        {"id": "n0", "type": "note", "degree": 1, "accidental": "natural", "confidence": 0.95},
        {"id": "n1", "type": "note", "degree": 3, "accidental": "natural", "confidence": 0.45},
    ]

    def test_returns_llm_result_on_success(self):
        expected = MeasureCorrectionResult(
            events=self._sample_tokens,
            confidence=0.92,
            notes="LLM纠正了第2个音符",
        )
        mock_structured = MagicMock()
        mock_structured.invoke.return_value = expected
        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured

        with patch("tuneai.core.llm._get_llm", return_value=mock_llm):
            result = correct_low_confidence_measure(
                measure_tokens=self._sample_tokens,
                image_region_b64="aGVsbG8=",
                active_key="C",
                request_id="req_test",
            )

        assert result.confidence == pytest.approx(0.92)
        assert result.events == self._sample_tokens
        mock_structured.invoke.assert_called_once()

    def test_llm_prompt_contains_active_key(self):
        """Prompt 应包含当前调号信息。"""
        mock_structured = MagicMock()
        mock_structured.invoke.return_value = MeasureCorrectionResult(
            events=[], confidence=0.8
        )
        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured

        with patch("tuneai.core.llm._get_llm", return_value=mock_llm):
            correct_low_confidence_measure(
                measure_tokens=self._sample_tokens,
                image_region_b64="",
                active_key="Bb",
                request_id="req_test",
            )

        prompt = mock_structured.invoke.call_args[0][0]
        assert "Bb" in prompt

    def test_llm_exception_returns_original_tokens_with_low_confidence(self):
        """LLM 异常时，应原样返回 tokens，confidence=0.5，不抛出。"""
        mock_structured = MagicMock()
        mock_structured.invoke.side_effect = TimeoutError("LLM timeout")
        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured

        with patch("tuneai.core.llm._get_llm", return_value=mock_llm):
            result = correct_low_confidence_measure(
                measure_tokens=self._sample_tokens,
                image_region_b64="",
                active_key="G",
                request_id="req_test",
            )

        assert result.events == self._sample_tokens
        assert result.confidence == pytest.approx(0.5)
        assert "timeout" in result.notes.lower() or "LLM" in result.notes

    def test_structured_output_called_with_correct_model(self):
        mock_structured = MagicMock()
        mock_structured.invoke.return_value = MeasureCorrectionResult(events=[], confidence=0.9)
        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured

        with patch("tuneai.core.llm._get_llm", return_value=mock_llm):
            correct_low_confidence_measure([], "", "C", "req_test")

        mock_llm.with_structured_output.assert_called_once_with(MeasureCorrectionResult)


# ---------------------------------------------------------------------------
# _fallback_key_parse（正则回退解析）
# ---------------------------------------------------------------------------

class TestFallbackKeyParse:

    @pytest.mark.parametrize("text,expected_tonic", [
        ("1=C",        "C"),
        ("1=G#",       "G#"),
        ("1=Bb",       "Bb"),
        ("1 = F",      "F"),
        ("调性: 1=D",  "D"),
        ("1＝A",       "A"),
        ("1=Eb",       "Eb"),
    ])
    def test_recognizes_various_formats(self, text, expected_tonic):
        result = _fallback_key_parse(text)
        assert result.tonic == expected_tonic
        assert result.label == f"1={expected_tonic}"
        assert result.confidence > 0

    @pytest.mark.parametrize("text", [
        "无调号文字",
        "abcdefg",
        "12345",
        "",
    ])
    def test_unrecognizable_returns_default_c(self, text):
        result = _fallback_key_parse(text)
        assert result.tonic == "C"
        assert result.label == "1=C"
        assert result.confidence < 0.4

    def test_unicode_accidentals_normalized(self):
        """♯ 和 ♭ 应规范化为 # 和 b。"""
        result = _fallback_key_parse("1=G♯")
        assert result.tonic == "G#"

        result2 = _fallback_key_parse("1=B♭")
        assert result2.tonic == "Bb"


# ---------------------------------------------------------------------------
# KeyCorrectionResult / MeasureCorrectionResult 模型校验
# ---------------------------------------------------------------------------

class TestPydanticModels:

    def test_key_correction_confidence_bounds(self):
        with pytest.raises(Exception):
            KeyCorrectionResult(tonic="C", label="1=C", confidence=1.5)
        with pytest.raises(Exception):
            KeyCorrectionResult(tonic="C", label="1=C", confidence=-0.1)

    def test_key_correction_notes_optional(self):
        result = KeyCorrectionResult(tonic="G", label="1=G", confidence=0.9)
        assert result.notes == ""

    def test_measure_correction_events_list(self):
        result = MeasureCorrectionResult(events=[{"id": "n0"}], confidence=0.8)
        assert len(result.events) == 1
