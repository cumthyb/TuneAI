"""
单次请求生命周期、调用 pipeline、临时结果、耗时与错误日志。

数据流：
  前端 → image_bytes → save_input_image() → pipeline → save_output_image() → base64 → 前端
  每个请求独立目录：data/outputs/{request_id}/input.png, output.png
  完成后由 routes.py 调用 storage.cleanup() 删除临时目录。
"""
from __future__ import annotations

import base64
import time
from dataclasses import dataclass, field

import cv2
import numpy as np

from tuneai.core.storage import save_input_image, save_output_image
from tuneai.logging_config import get_logger
from tuneai.schemas.request_response import Warning
from tuneai.schemas.score_ir import NoteEvent, ScoreIR


class PipelineError(Exception):
    def __init__(self, error_code: str, message: str):
        super().__init__(message)
        self.error_code = error_code
        self.message = message


@dataclass
class PipelineResult:
    output_image_b64: str
    score_ir: ScoreIR
    warnings: list[Warning] = field(default_factory=list)
    processing_time_ms: int = 0


def run_pipeline(image_bytes: bytes, target_key: str, request_id: str) -> PipelineResult:
    log = get_logger("task_manager")
    t_start = time.monotonic()

    try:
        # 写入输入图（data/outputs/{request_id}/input.png）
        save_input_image(request_id, image_bytes)
        log.info(f"pipeline start: target_key={target_key}, input_size={len(image_bytes)}")

        # Stage 1: Preprocess
        t = time.monotonic()
        from tuneai.core.preprocess import preprocess_image
        binary_img = preprocess_image(image_bytes)
        log.debug(f"[1/9] preprocess done ({int((time.monotonic()-t)*1000)}ms)")

        # Stage 2: Layout detection
        t = time.monotonic()
        from tuneai.core.layout import detect_lines, detect_barlines
        lines = detect_lines(binary_img)
        log.debug(f"[2/9] layout done ({int((time.monotonic()-t)*1000)}ms), lines={len(lines)}")

        # Stage 3: OCR
        t = time.monotonic()
        from tuneai.core.ocr import run_ocr, extract_key_signature, extract_note_digits
        all_tokens = run_ocr(binary_img)
        key_token = extract_key_signature(all_tokens)
        note_tokens = extract_note_digits(all_tokens)
        log.debug(f"[3/9] ocr done ({int((time.monotonic()-t)*1000)}ms), tokens={len(all_tokens)}, key={key_token.text if key_token else 'None'}")

        # Stage 4: Symbol detection
        t = time.monotonic()
        from tuneai.core.symbols import detect_octave_dots, detect_duration_marks, detect_accidentals
        octave_dots, duration_marks, accidentals, barline_xs = [], [], [], []
        for line in lines:
            octave_dots.extend(detect_octave_dots(binary_img, line))
            duration_marks.extend(detect_duration_marks(binary_img, line))
            accidentals.extend(detect_accidentals(binary_img, line))
            barline_xs.extend(detect_barlines(binary_img, line))
        log.debug(f"[4/9] symbols done ({int((time.monotonic()-t)*1000)}ms), dots={len(octave_dots)}, bars={len(barline_xs)}")

        # Stage 5: LLM key correction
        t = time.monotonic()
        from tuneai.core.llm import correct_key_signature
        raw_key_text = key_token.text if key_token else ""
        key_result = correct_key_signature(
            raw_text=raw_key_text,
            context=f"target_key={target_key}",
            request_id=request_id,
        )
        log.debug(f"[5/9] llm key correction done ({int((time.monotonic()-t)*1000)}ms), key={key_result.label} (conf={key_result.confidence:.2f})")

        # Stage 6: Parser
        t = time.monotonic()
        from tuneai.core.parser import parse_score
        from tuneai.core.ocr import OCRToken
        corrected_key_token = OCRToken(
            text=key_result.label,
            bbox=[0, 0, 0, 0],
            confidence=key_result.confidence,
        ) if key_result.label else key_token

        score_ir = parse_score(note_tokens, {
            "octave_dots": octave_dots,
            "duration_marks": duration_marks,
            "accidentals": accidentals,
            "barlines": barline_xs,
        }, corrected_key_token)
        log.debug(f"[6/9] parser done ({int((time.monotonic()-t)*1000)}ms), measures={len(score_ir.measures)}")

        # Stage 7: LLM low-confidence measure correction
        t = time.monotonic()
        from tuneai.core.llm import correct_low_confidence_measure
        warnings: list[Warning] = []
        for measure in score_ir.measures:
            low_conf = [e for e in measure.events if isinstance(e, NoteEvent) and e.confidence < 0.7]
            if low_conf:
                _, buf = cv2.imencode(".png", binary_img)
                img_b64 = base64.b64encode(buf.tobytes()).decode()
                tokens_data = [e.model_dump() for e in measure.events]
                try:
                    correction = correct_low_confidence_measure(
                        measure_tokens=tokens_data,
                        image_region_b64=img_b64,
                        active_key=score_ir.source_key.tonic,
                        request_id=request_id,
                    )
                    if correction.confidence < 0.5:
                        warnings.append(Warning(
                            type="low_confidence",
                            measure=measure.number,
                            message=f"LLM conf={correction.confidence:.2f}: {correction.notes}",
                        ))
                except Exception as e:
                    log.warning(f"LLM measure correction failed for measure {measure.number}: {e}")
                    warnings.append(Warning(type="llm_error", measure=measure.number, message=str(e)))
        log.debug(f"[7/9] llm measure correction done ({int((time.monotonic()-t)*1000)}ms)")

        # Stage 8: Music transposition
        t = time.monotonic()
        from tuneai.core.music import transpose_score_ir
        transposed = transpose_score_ir(score_ir, target_key)
        log.debug(f"[8/9] transpose done ({int((time.monotonic()-t)*1000)}ms), {score_ir.source_key.tonic} → {target_key}")

        # Stage 9: Validate + Render
        t = time.monotonic()
        from tuneai.core.validate import validate_score
        val_warnings = validate_score(transposed)
        warnings.extend(val_warnings)

        nparr = np.frombuffer(image_bytes, dtype=np.uint8)
        original_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        from tuneai.core.render import render_output
        output_png_bytes = render_output(original_img, score_ir, transposed)
        output_b64 = base64.b64encode(output_png_bytes).decode()

        # 写入输出图（data/outputs/{request_id}/output.png）
        save_output_image(request_id, output_png_bytes)
        log.debug(f"[9/9] validate+render done ({int((time.monotonic()-t)*1000)}ms), warnings={len(warnings)}")

        processing_time_ms = int((time.monotonic() - t_start) * 1000)
        log.info(f"pipeline completed in {processing_time_ms}ms, warnings={len(warnings)}")

        return PipelineResult(
            output_image_b64=output_b64,
            score_ir=transposed,
            warnings=warnings,
            processing_time_ms=processing_time_ms,
        )

    except PipelineError:
        raise
    except Exception as e:
        log.exception(f"pipeline error: {e}")
        raise PipelineError("PIPELINE_ERROR", str(e)) from e
