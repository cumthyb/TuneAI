"""
单次请求完整生命周期（五步流水线）。

流程：
  1. preprocess   本地：灰度化、去噪、deskew
  2. parallel     线上：Qwen-VL（调号）+ 阿里OCR（全字符 bbox）并行
  3. filter       本地：过滤保留 0-7 音符 bbox
  4. transpose    本地：十二平均律转调计算
  5. render       本地：像素回写，导出 PNG
"""
from __future__ import annotations

import asyncio
import base64
import time
from dataclasses import dataclass, field

from tuneai.core.storage import save_input_image, save_output_image
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


async def run_pipeline(
    image_bytes: bytes, target_key: str, request_id: str
) -> PipelineResult:
    log = get_logger("task_manager")
    t_start = time.monotonic()

    try:
        save_input_image(request_id, image_bytes)
        log.info(f"pipeline start: target_key={target_key}, input_size={len(image_bytes)}")

        # ── Stage 1: Preprocess ──────────────────────────────────────────────
        t = time.monotonic()
        from tuneai.core.preprocess import preprocess_image
        clean_image = preprocess_image(image_bytes)
        log.debug(f"[1/5] preprocess done ({_ms(t)}ms)")

        # ── Stage 2: Parallel online calls ──────────────────────────────────
        t = time.monotonic()
        from tuneai.core.qwen_vl import recognize_key_signature
        from tuneai.core.ocr import run_ocr

        source_tonic, ocr_chars = await asyncio.gather(
            asyncio.to_thread(recognize_key_signature, clean_image),
            asyncio.to_thread(run_ocr, clean_image),
        )
        log.debug(
            f"[2/5] parallel done ({_ms(t)}ms) "
            f"key={source_tonic!r}, ocr_chars={len(ocr_chars)}"
        )

        # ── Stage 3: Filter ──────────────────────────────────────────────────
        t = time.monotonic()
        from tuneai.core.filter import filter_note_digits
        events = filter_note_digits(ocr_chars)
        log.debug(f"[3/5] filter done ({_ms(t)}ms), events={len(events)}")

        if not events:
            raise PipelineError("NO_NOTES_FOUND", "OCR 未识别到任何音符，请检查图片质量")

        # ── LLM 低置信度纠错（可选）────────────────────────────────────────
        warnings: list[Warning] = []
        low_conf = [e for e in events if isinstance(e, NoteEvent) and e.confidence < 0.7]
        if low_conf:
            try:
                from tuneai.core.llm import correct_low_confidence_events
                events_data = [e.model_dump() for e in events]
                correction = correct_low_confidence_events(
                    events=events_data,
                    active_key=source_tonic,
                    request_id=request_id,
                )
                if correction.confidence < 0.5:
                    warnings.append(Warning(
                        type="low_confidence",
                        message=f"LLM conf={correction.confidence:.2f}: {correction.notes}",
                    ))
                log.debug(f"llm correction: conf={correction.confidence:.2f}")
            except Exception as e:
                log.warning(f"llm correction skipped: {e}")
                warnings.append(Warning(type="llm_error", message=str(e)))

        # ── Stage 4: Transpose ───────────────────────────────────────────────
        t = time.monotonic()
        from tuneai.core.music import transpose_score_ir, validate_target_key

        if not validate_target_key(source_tonic):
            log.warning(f"unrecognized source key {source_tonic!r}, falling back to C")
            source_tonic = "C"

        score_ir = ScoreIR(
            score_id=request_id,
            source_key=KeyInfo(label=f"1={source_tonic}", tonic=source_tonic, confidence=1.0),
            target_key=KeyInfo(label=f"1={target_key}", tonic=target_key),
            events=events,
        )
        transposed = transpose_score_ir(score_ir, target_key)
        log.debug(f"[4/5] transpose done ({_ms(t)}ms): {source_tonic} → {target_key}")

        # ── Stage 5: Validate ────────────────────────────────────────────────
        t = time.monotonic()
        from tuneai.core.validate import validate_score
        warnings.extend(validate_score(transposed, original_image=clean_image, request_id=request_id))
        log.debug(f"[5/7] validate done ({_ms(t)}ms), warnings={len(warnings)}")

        # ── Stage 6: Pitch Adjust ─────────────────────────────────────────────
        t = time.monotonic()
        from tuneai.core.pitch_adjust import adjust_pitch
        adjusted, pitch_warnings = adjust_pitch(transposed, request_id=request_id)
        warnings.extend(pitch_warnings)
        log.debug(f"[6/7] pitch_adjust done ({_ms(t)}ms), pitch_warnings={len(pitch_warnings)}")

        # ── Stage 7: Render ───────────────────────────────────────────────────
        t = time.monotonic()
        from tuneai.core.render import render_output
        output_png_bytes = render_output(image_bytes, score_ir, adjusted)
        output_b64 = base64.b64encode(output_png_bytes).decode()

        save_output_image(request_id, output_png_bytes)
        log.debug(f"[7/7] render done ({_ms(t)}ms), warnings={len(warnings)}")

        processing_time_ms = int((time.monotonic() - t_start) * 1000)
        log.info(f"pipeline completed in {processing_time_ms}ms, warnings={len(warnings)}")

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
