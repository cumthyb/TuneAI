"""
OCR 模块单元测试。

测试策略：
- run_ocr: mock PaddleOCR 引擎，测试 token 解析逻辑（polygon→bbox、置信度过滤）
- extract_key_signature: 纯函数，直接测试各种调号格式的识别
- extract_note_digits: 纯函数，测试 0-7 数字过滤逻辑
"""
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from tuneai.core.ocr import OCRToken, extract_key_signature, extract_note_digits, run_ocr


# ---------------------------------------------------------------------------
# 辅助：构造假 OCR 结果（PaddleOCR 格式）
# ---------------------------------------------------------------------------

def _paddle_line(x, y, w, h, text, conf):
    """构造单条 PaddleOCR 结果行：[polygon, (text, conf)]"""
    polygon = [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]
    return [polygon, (text, conf)]


def _mock_ocr_engine(lines):
    """返回 mock PaddleOCR 实例，ocr() 返回指定行列表。"""
    engine = MagicMock()
    engine.ocr.return_value = [lines]
    return engine


# ---------------------------------------------------------------------------
# run_ocr
# ---------------------------------------------------------------------------

class TestRunOcr:

    def test_returns_tokens_with_correct_bbox(self):
        lines = [_paddle_line(10, 20, 50, 30, "1=C", 0.95)]
        with patch("tuneai.core.ocr._get_ocr", return_value=_mock_ocr_engine(lines)):
            img = np.zeros((100, 200), dtype=np.uint8)
            tokens = run_ocr(img)
        assert len(tokens) == 1
        tok = tokens[0]
        assert tok.text == "1=C"
        assert tok.bbox == [10, 20, 50, 30]
        assert tok.confidence == pytest.approx(0.95)

    def test_multiple_tokens(self):
        lines = [
            _paddle_line(0, 10, 40, 20, "1=G", 0.92),
            _paddle_line(50, 10, 15, 20, "1",   0.88),
            _paddle_line(70, 10, 15, 20, "2",   0.91),
        ]
        with patch("tuneai.core.ocr._get_ocr", return_value=_mock_ocr_engine(lines)):
            tokens = run_ocr(np.zeros((50, 200), dtype=np.uint8))
        assert len(tokens) == 3
        assert [t.text for t in tokens] == ["1=G", "1", "2"]

    def test_strips_whitespace_from_text(self):
        lines = [_paddle_line(0, 0, 40, 20, "  1=C  ", 0.90)]
        with patch("tuneai.core.ocr._get_ocr", return_value=_mock_ocr_engine(lines)):
            tokens = run_ocr(np.zeros((50, 200), dtype=np.uint8))
        assert tokens[0].text == "1=C"

    def test_empty_result_returns_empty_list(self):
        engine = MagicMock()
        engine.ocr.return_value = [None]
        with patch("tuneai.core.ocr._get_ocr", return_value=engine):
            tokens = run_ocr(np.zeros((50, 200), dtype=np.uint8))
        assert tokens == []

    def test_ocr_exception_returns_empty_list(self):
        engine = MagicMock()
        engine.ocr.side_effect = RuntimeError("OCR failed")
        with patch("tuneai.core.ocr._get_ocr", return_value=engine):
            tokens = run_ocr(np.zeros((50, 200), dtype=np.uint8))
        assert tokens == []

    def test_malformed_line_skipped(self):
        """格式错误的行应跳过，不影响其他 token 解析。"""
        lines = [
            None,                                              # None 行
            _paddle_line(0, 0, 40, 20, "1=C", 0.95),          # 正常行
            "not_a_valid_line",                                # 字符串（格式错）
        ]
        with patch("tuneai.core.ocr._get_ocr", return_value=_mock_ocr_engine(lines)):
            tokens = run_ocr(np.zeros((50, 200), dtype=np.uint8))
        assert len(tokens) == 1
        assert tokens[0].text == "1=C"

    def test_bbox_computed_from_polygon_extremes(self):
        """bbox 应取 polygon 四个顶点的最小外接矩形。"""
        # 非矩形 polygon（梯形）
        polygon = [[5, 10], [60, 8], [58, 35], [3, 37]]
        line = [polygon, ("5", 0.85)]
        engine = _mock_ocr_engine([line])
        with patch("tuneai.core.ocr._get_ocr", return_value=engine):
            tokens = run_ocr(np.zeros((50, 100), dtype=np.uint8))
        assert len(tokens) == 1
        x, y, w, h = tokens[0].bbox
        assert x == 3   # min x
        assert y == 8   # min y
        assert w == 60 - 3  # max_x - min_x
        assert h == 37 - 8  # max_y - min_y

    def test_run_ocr_with_real_sample_image(self, sample_image_bytes):
        """
        用 匆匆那年.png 作为输入，测试 run_ocr 的图像解码和 token 解析流程。
        PaddleOCR 引擎仍 mock（返回固定结果），验证从图像字节到 OCRToken 的完整链路。
        """
        import cv2
        nparr = np.frombuffer(sample_image_bytes, dtype=np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
        assert img is not None, "样本图片应能正常解码"

        # Mock OCR 返回一组典型的简谱识别结果
        lines = [
            _paddle_line(20, 15, 60, 25, "1=G",  0.94),
            _paddle_line(100, 50, 15, 22, "5",   0.91),
            _paddle_line(120, 50, 15, 22, "6",   0.88),
            _paddle_line(140, 50, 15, 22, "1",   0.93),
        ]
        with patch("tuneai.core.ocr._get_ocr", return_value=_mock_ocr_engine(lines)):
            tokens = run_ocr(img)

        assert len(tokens) == 4
        key_tok = extract_key_signature(tokens)
        note_toks = extract_note_digits(tokens)
        assert key_tok is not None and key_tok.text == "1=G"
        assert len(note_toks) == 3
        assert [t.text for t in note_toks] == ["5", "6", "1"]


# ---------------------------------------------------------------------------
# extract_key_signature
# ---------------------------------------------------------------------------

class TestExtractKeySignature:

    def _tok(self, text, conf=0.90, bbox=None):
        return OCRToken(text=text, bbox=bbox or [0, 0, 50, 20], confidence=conf)

    def test_standard_format(self):
        tokens = [self._tok("1=C")]
        result = extract_key_signature(tokens)
        assert result is not None
        assert result.text == "1=C"

    def test_with_sharp(self):
        tokens = [self._tok("1=G#")]
        assert extract_key_signature(tokens) is not None

    def test_with_flat(self):
        tokens = [self._tok("1=Bb")]
        assert extract_key_signature(tokens) is not None

    def test_fullwidth_equals(self):
        """全角等号 ＝ 也应被识别。"""
        tokens = [self._tok("1＝D")]
        assert extract_key_signature(tokens) is not None

    def test_with_spaces_around_equals(self):
        tokens = [self._tok("1 = F")]
        assert extract_key_signature(tokens) is not None

    def test_no_key_signature_returns_none(self):
        tokens = [self._tok("1"), self._tok("2"), self._tok("3")]
        assert extract_key_signature(tokens) is None

    def test_empty_tokens_returns_none(self):
        assert extract_key_signature([]) is None

    def test_returns_highest_confidence(self):
        tokens = [
            self._tok("1=C", conf=0.70),
            self._tok("1=G", conf=0.95),
            self._tok("1=D", conf=0.80),
        ]
        result = extract_key_signature(tokens)
        assert result.text == "1=G"

    def test_key_embedded_in_longer_text(self):
        """调号嵌在长文字中（OCR 可能把整行识别为一个 token）。"""
        tokens = [self._tok("调性: 1=F# (升F大调)")]
        result = extract_key_signature(tokens)
        assert result is not None

    def test_invalid_note_name_not_matched(self):
        """H 不是合法音名，不应匹配。"""
        tokens = [self._tok("1=H")]
        assert extract_key_signature(tokens) is None


# ---------------------------------------------------------------------------
# extract_note_digits
# ---------------------------------------------------------------------------

class TestExtractNoteDigits:

    def _tok(self, text, conf=0.90):
        return OCRToken(text=text, bbox=[0, 0, 15, 20], confidence=conf)

    def test_digits_1_to_7(self):
        tokens = [self._tok(str(i)) for i in range(1, 8)]
        result = extract_note_digits(tokens)
        assert len(result) == 7
        assert [t.text for t in result] == ["1", "2", "3", "4", "5", "6", "7"]

    def test_zero_included(self):
        """0 是休止符，应被包含。"""
        tokens = [self._tok("0")]
        assert len(extract_note_digits(tokens)) == 1

    def test_multi_digit_excluded(self):
        tokens = [self._tok("12"), self._tok("23"), self._tok("1")]
        result = extract_note_digits(tokens)
        assert len(result) == 1
        assert result[0].text == "1"

    def test_8_and_9_excluded(self):
        tokens = [self._tok("8"), self._tok("9")]
        assert extract_note_digits(tokens) == []

    def test_key_signature_excluded(self):
        tokens = [self._tok("1=C"), self._tok("3")]
        result = extract_note_digits(tokens)
        assert len(result) == 1
        assert result[0].text == "3"

    def test_empty_tokens(self):
        assert extract_note_digits([]) == []

    def test_mixed_batch(self):
        tokens = [
            self._tok("1=G"),
            self._tok("1"),
            self._tok("2"),
            self._tok("3"),
            self._tok("abc"),
            self._tok("0"),
            self._tok("7"),
            self._tok("11"),
        ]
        result = extract_note_digits(tokens)
        assert [t.text for t in result] == ["1", "2", "3", "0", "7"]
