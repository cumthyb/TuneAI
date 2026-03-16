from unittest.mock import patch

from tuneai.core.domain.validate import validate_score
from tuneai.schemas.score_ir import KeyInfo, NoteEvent, ScoreIR


class TestValidate:
    def test_rule_warnings_for_invalid_keys_and_empty_score(self):
        score = ScoreIR(
            score_id="s1",
            source_key=KeyInfo(label="1=H", tonic="H"),
            target_key=KeyInfo(label="1=X", tonic="X"),
            events=[],
        )
        with patch("tuneai.config.get_llm_config", return_value={}):
            warnings = validate_score(score, original_image=None)
        types = {w.type for w in warnings}
        assert "INVALID_KEY" in types
        assert "INVALID_TARGET_KEY" in types
        assert "EMPTY_SCORE" in types

    def test_rule_warning_for_low_confidence_note(self):
        score = ScoreIR(
            score_id="s1",
            source_key=KeyInfo(label="1=C", tonic="C"),
            target_key=KeyInfo(label="1=G", tonic="G"),
            events=[NoteEvent(id="n1", degree=1, accidental="natural", octave_shift=0, confidence=0.2)],
        )
        with patch("tuneai.config.get_llm_config", return_value={}):
            warnings = validate_score(score, original_image=None)
        assert any(w.type == "low_confidence" for w in warnings)
