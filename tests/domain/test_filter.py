from tuneai.core.adapters.ocr.types import OcrChar
from tuneai.core.domain.filter import filter_note_digits


class TestFilter:
    def test_filter_note_digits_keeps_0_to_7(self):
        chars = [
            OcrChar(text="1", bbox=[0, 0, 10, 10], confidence=0.9),
            OcrChar(text="0", bbox=[12, 0, 10, 10], confidence=0.8),
            OcrChar(text="A", bbox=[24, 0, 10, 10], confidence=0.9),
            OcrChar(text="12", bbox=[36, 0, 10, 10], confidence=0.9),
        ]
        events = filter_note_digits(chars)
        assert len(events) == 2
        assert events[0].type == "note"
        assert events[1].type == "rest"
