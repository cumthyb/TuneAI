from __future__ import annotations

import asyncio
import base64
import time
from dataclasses import dataclass, field

from tuneai.core.adapters.llm import correct_low_confidence_events
from tuneai.core.adapters.ocr import run_ocr
from tuneai.core.adapters.vision import recognize_key_signature
from tuneai.core.domain.filter import filter_note_digits
from tuneai.core.domain.music import transpose_score_ir, validate_target_key
from tuneai.core.domain.pitch_adjust import adjust_pitch
from tuneai.core.domain.preprocess import preprocess_image
from tuneai.core.domain.render import render_output
from tuneai.core.domain.validate import validate_score
from tuneai.core.infra.storage import save_input_image, save_output_image
from tuneai.logging_config import get_logger
from tuneai.schemas.request_response import Warning
from tuneai.schemas.score_ir import KeyInfo, NoteEvent, ScoreIR


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


async def run_pipeline(image_bytes: bytes, target_key: str, request_id: str) -> PipelineResult:
    log = get_logger("pipeline")
    t_start = time.monotonic()

    try:
        save_input_image(request_id, image_bytes)
        log.info(f"pipeline start: target_key={target_key}, input_size={len(image_bytes)}")

        t = time.monotonic()
        clean_image = await asyncio.to_thread(preprocess_image, image_bytes)
        log.debug(f"[1/7] preprocess done ({_ms(t)}ms)")

        t = time.monotonic()
        source_tonic, ocr_chars = await asyncio.gather(
            asyncio.to_thread(recognize_key_signature, clean_image),
            asyncio.to_thread(run_ocr, clean_image),
        )
        log.debug(
            f"[2/7] parallel done ({_ms(t)}ms) key={source_tonic!r}, ocr_chars={len(ocr_chars)}"
        )

        t = time.monotonic()
        events = await asyncio.to_thread(filter_note_digits, ocr_chars)
        log.debug(f"[3/7] filter done ({_ms(t)}ms), events={len(events)}")

        if not events:
            raise PipelineError("NO_NOTES_FOUND", "OCR 未识别到任何音符，请检查图片质量")

        warnings: list[Warning] = []
        low_conf = [e for e in events if isinstance(e, NoteEvent) and e.confidence < 0.7]
        if low_conf:
            try:
                events_data = [e.model_dump() for e in events]
                correction = await asyncio.to_thread(
                    correct_low_confidence_events,
                    events_data,
                    source_tonic,
                    request_id,
                )
                if correction.confidence < 0.5:
                    warnings.append(
                        Warning(
                            type="low_confidence",
                            message=f"LLM conf={correction.confidence:.2f}: {correction.notes}",
                        )
                    )
            except Exception as e:
                log.warning(f"llm correction skipped: {e}")
                warnings.append(Warning(type="llm_error", message=str(e)))

        t = time.monotonic()
        if not validate_target_key(source_tonic):
            raise PipelineError("INVALID_SOURCE_KEY", f"无法识别有效原调: {source_tonic!r}")

        score_ir = ScoreIR(
            score_id=request_id,
            source_key=KeyInfo(label=f"1={source_tonic}", tonic=source_tonic, confidence=1.0),
            target_key=KeyInfo(label=f"1={target_key}", tonic=target_key),
            events=events,
        )
        transposed = transpose_score_ir(score_ir, target_key)
        log.debug(f"[4/7] transpose done ({_ms(t)}ms): {source_tonic} -> {target_key}")

        t = time.monotonic()
        warnings.extend(
            await asyncio.to_thread(
                validate_score, transposed, original_image=clean_image, request_id=request_id
            )
        )
        log.debug(f"[5/7] validate done ({_ms(t)}ms), warnings={len(warnings)}")

        t = time.monotonic()
        adjusted, pitch_warnings = await asyncio.to_thread(adjust_pitch, transposed, request_id)
        warnings.extend(pitch_warnings)
        log.debug(f"[6/7] pitch_adjust done ({_ms(t)}ms), pitch_warnings={len(pitch_warnings)}")

        t = time.monotonic()
        output_png_bytes = await asyncio.to_thread(render_output, image_bytes, score_ir, adjusted)
        output_b64 = base64.b64encode(output_png_bytes).decode()
        save_output_image(request_id, output_png_bytes)
        log.debug(f"[7/7] render done ({_ms(t)}ms), warnings={len(warnings)}")

        processing_time_ms = int((time.monotonic() - t_start) * 1000)
        return PipelineResult(
            output_image_b64=output_b64,
            score_ir=adjusted,
            warnings=warnings,
            processing_time_ms=processing_time_ms,
        )
    except PipelineError:
        raise
    except Exception as e:
        log.exception(f"pipeline error: {e}")
        raise PipelineError("PIPELINE_ERROR", str(e)) from e


def _ms(t: float) -> int:
    return int((time.monotonic() - t) * 1000)
