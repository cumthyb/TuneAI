"""
/api/transpose 同步接口、页面路由、统一 JSON、超时与异常。
"""
import asyncio
from typing import Union

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import JSONResponse

from tuneai.api.dependencies import get_request_id
from tuneai.config import get_pipeline_config
from tuneai.core.application.pipeline import PipelineError, run_pipeline
from tuneai.core.domain.music import validate_target_key
from tuneai.core.infra.storage import cleanup
from tuneai.logging_config import bind_request_id, reset_request_id, get_logger
from tuneai.schemas.request_response import (
    TransposeErrorResponse,
    TransposeSuccessResponse,
)

router = APIRouter()

_ALLOWED_CONTENT_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/webp"}


@router.post(
    "/transpose",
    response_model=Union[TransposeSuccessResponse, TransposeErrorResponse],
)
async def transpose(
    image: UploadFile = File(...),
    target_key: str = Form(...),
    request_id: str = Depends(get_request_id),
):
    """同步移调接口，接收图片与目标调，返回结果图与 JSON。"""
    log = get_logger("routes")
    token = bind_request_id(request_id)

    try:
        # Validate target_key
        if not validate_target_key(target_key):
            return _error_response(
                status_code=400,
                error_code="INVALID_TARGET_KEY",
                error_message=f"不支持的目标调: {target_key!r}。合法值示例: C, D, Eb, F#",
                request_id=request_id,
            )

        # Validate image content type
        ct = (image.content_type or "").lower()
        if ct not in _ALLOWED_CONTENT_TYPES:
            return _error_response(
                status_code=415,
                error_code="INVALID_IMAGE_FORMAT",
                error_message=f"不支持的图片格式: {ct}。请上传 PNG 或 JPG 图片。",
                request_id=request_id,
            )

        image_bytes = await image.read()
        if len(image_bytes) == 0:
            return _error_response(
                status_code=400,
                error_code="EMPTY_IMAGE",
                error_message="上传的图片为空",
                request_id=request_id,
            )

        log.info(f"transpose request: target_key={target_key}, size={len(image_bytes)}")

        timeout_seconds = float(get_pipeline_config().get("request_timeout_seconds", 60))
        try:
            result = await asyncio.wait_for(
                run_pipeline(image_bytes, target_key, request_id),
                timeout=timeout_seconds,
            )
        except asyncio.TimeoutError:
            return _error_response(
                status_code=504,
                error_code="REQUEST_TIMEOUT",
                error_message=f"请求处理超时（>{int(timeout_seconds)}s）",
                request_id=request_id,
            )
        except PipelineError as e:
            status_code = 422 if e.error_code == "NO_NOTES_FOUND" else 500
            return _error_response(
                status_code=status_code,
                error_code=e.error_code,
                error_message=e.message,
                request_id=request_id,
            )

        return TransposeSuccessResponse(
            output_image=result.output_image_b64,
            score_json=result.score_ir.model_dump(),
            warnings=result.warnings,
            processing_time_ms=result.processing_time_ms,
            request_id=request_id,
        )

    finally:
        reset_request_id(token)
        if get_pipeline_config().get("cleanup_after_response", True):
            cleanup(request_id)


def _error_response(
    *,
    status_code: int,
    error_code: str,
    error_message: str,
    request_id: str,
) -> JSONResponse:
    payload = TransposeErrorResponse(
        error_code=error_code,
        error_message=error_message,
        request_id=request_id,
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump())
