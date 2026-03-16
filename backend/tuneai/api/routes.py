"""
/api/transpose 同步接口、页面路由、统一 JSON、超时与异常。
"""
import asyncio
from typing import Union

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import JSONResponse

from tuneai.api.dependencies import get_request_id
from tuneai.config import (
    get_default_provider,
    get_llm_config,
    get_ocr_config,
    get_pipeline_config,
    get_vision_llm_config,
)
from tuneai.core.application.pipeline import PipelineError, run_pipeline
from tuneai.core.adapters.llm_client import list_supported_providers
from tuneai.core.adapters.provider_context import provider_overrides
from tuneai.core.domain.music import validate_target_key
from tuneai.core.infra.storage import cleanup
from tuneai.logging_config import bind_request_id, reset_request_id, get_logger
from tuneai.schemas.request_response import (
    ApiMetaResponse,
    TransposeErrorResponse,
    TransposeSuccessResponse,
)

router = APIRouter()

_ALLOWED_CONTENT_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/webp"}
_ALLOWED_FORMAT_HINT = "PNG、JPG 或 WEBP"


def _list_providers_with_llm() -> list[str]:
    providers: list[str] = []
    for p in list_supported_providers():
        try:
            cfg = get_llm_config(p)
        except ValueError:
            continue
        if isinstance(cfg, dict) and cfg:
            providers.append(p)
    return sorted(set(providers))


def _list_providers_with_vision_llm() -> list[str]:
    providers: list[str] = []
    for p in list_supported_providers():
        try:
            cfg = get_vision_llm_config(p)
        except ValueError:
            continue
        if isinstance(cfg, dict) and cfg:
            providers.append(p)
    return sorted(set(providers))


def _list_providers_with_ocr() -> list[str]:
    providers: list[str] = []
    for p in list_supported_providers():
        try:
            ocr_cfg = get_ocr_config(p)
        except ValueError:
            continue
        runner = str(ocr_cfg.get("runner")).strip()
        if runner:
            providers.append(p)
    return sorted(set(providers))


def _pick_default_provider(candidates: list[str], preferred: str, capability: str) -> str:
    if not candidates:
        raise ValueError(f"no providers configured for {capability}")
    if preferred in candidates:
        return preferred
    return candidates[0]


@router.get("/meta", response_model=ApiMetaResponse)
def get_api_meta() -> ApiMetaResponse:
    configured_default = get_default_provider()
    llm_providers = _list_providers_with_llm()
    vision_providers = _list_providers_with_vision_llm()
    ocr_providers = _list_providers_with_ocr()
    providers = sorted(set(llm_providers) & set(vision_providers) & set(ocr_providers))
    default_llm_provider = _pick_default_provider(llm_providers, configured_default, "llm")
    default_vision_provider = _pick_default_provider(vision_providers, configured_default, "vision_llm")
    default_ocr_provider = _pick_default_provider(ocr_providers, configured_default, "ocr")
    default_provider = _pick_default_provider(providers, configured_default, "llm+vision_llm+ocr")
    return ApiMetaResponse(
        allowed_image_types=sorted(_ALLOWED_CONTENT_TYPES),
        max_image_size_mb=_get_max_image_size_mb(),
        providers=providers,
        default_provider=default_provider,
        llm_providers=llm_providers,
        vision_llm_providers=vision_providers,
        ocr_providers=ocr_providers,
        default_llm_provider=default_llm_provider,
        default_vision_llm_provider=default_vision_provider,
        default_ocr_provider=default_ocr_provider,
    )


@router.post(
    "/transpose",
    response_model=Union[TransposeSuccessResponse, TransposeErrorResponse],
)
async def transpose(
    image: UploadFile = File(...),
    target_key: str = Form(...),
    provider: str = Form(...),
    llm_provider: str = Form(...),
    vision_llm_provider: str = Form(...),
    ocr_provider: str = Form(...),
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
        if not isinstance(image.content_type, str) or not image.content_type.strip():
            return _error_response(
                status_code=400,
                error_code="MISSING_IMAGE_CONTENT_TYPE",
                error_message="上传图片缺少 Content-Type",
                request_id=request_id,
            )
        ct = image.content_type.strip().lower()
        if ct not in _ALLOWED_CONTENT_TYPES:
            return _error_response(
                status_code=415,
                error_code="INVALID_IMAGE_FORMAT",
                error_message=f"不支持的图片格式: {ct}。请上传 {_ALLOWED_FORMAT_HINT} 图片。",
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
        max_image_size_mb = _get_max_image_size_mb()
        if len(image_bytes) > max_image_size_mb * 1024 * 1024:
            return _error_response(
                status_code=413,
                error_code="IMAGE_TOO_LARGE",
                error_message=f"图片大小不能超过 {max_image_size_mb}MB",
                request_id=request_id,
            )

        log.info(f"transpose request: target_key={target_key}, size={len(image_bytes)}")

        provider = provider.strip().lower()
        llm_provider = llm_provider.strip().lower()
        vision_llm_provider = vision_llm_provider.strip().lower()
        ocr_provider = ocr_provider.strip().lower()
        if not provider or not llm_provider or not vision_llm_provider or not ocr_provider:
            return _error_response(
                status_code=400,
                error_code="MISSING_PROVIDER",
                error_message="provider / llm_provider / vision_llm_provider / ocr_provider 均为必填",
                request_id=request_id,
            )

        allowed_llm_providers = set(_list_providers_with_llm())
        allowed_vision_llm_providers = set(_list_providers_with_vision_llm())
        allowed_ocr_providers = set(_list_providers_with_ocr())

        if llm_provider not in allowed_llm_providers:
            return _error_response(
                status_code=400,
                error_code="INVALID_LLM_PROVIDER",
                error_message=f"不支持的 LLM provider: {llm_provider}",
                request_id=request_id,
            )
        if vision_llm_provider not in allowed_vision_llm_providers:
            return _error_response(
                status_code=400,
                error_code="INVALID_VISION_LLM_PROVIDER",
                error_message=f"不支持的 Vision LLM provider: {vision_llm_provider}",
                request_id=request_id,
            )
        if ocr_provider not in allowed_ocr_providers:
            return _error_response(
                status_code=400,
                error_code="INVALID_OCR_PROVIDER",
                error_message=f"不支持的 OCR provider: {ocr_provider}",
                request_id=request_id,
            )

        timeout_seconds = _get_request_timeout_seconds()
        try:
            with provider_overrides(
                llm_provider=llm_provider,
                vision_llm_provider=vision_llm_provider,
                ocr_provider=ocr_provider,
            ):
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
            success=True,
            output_image=result.output_image_b64,
            score_json=result.score_ir.model_dump(),
            warnings=result.warnings,
            processing_time_ms=result.processing_time_ms,
            request_id=request_id,
        )

    finally:
        reset_request_id(token)
        if _get_cleanup_after_response():
            cleanup(request_id)


def _error_response(
    *,
    status_code: int,
    error_code: str,
    error_message: str,
    request_id: str,
) -> JSONResponse:
    payload = TransposeErrorResponse(
        success=False,
        error_code=error_code,
        error_message=error_message,
        request_id=request_id,
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump())


def _get_max_image_size_mb() -> int:
    raw_value = get_pipeline_config().get("max_image_size_mb")
    if not isinstance(raw_value, int) or raw_value <= 0:
        raise ValueError("pipeline.max_image_size_mb must be a positive integer")
    return raw_value


def _get_request_timeout_seconds() -> float:
    raw_value = get_pipeline_config().get("request_timeout_seconds")
    if not isinstance(raw_value, (int, float)) or raw_value <= 0:
        raise ValueError("pipeline.request_timeout_seconds must be a positive number")
    return float(raw_value)


def _get_cleanup_after_response() -> bool:
    raw_value = get_pipeline_config().get("cleanup_after_response")
    if not isinstance(raw_value, bool):
        raise ValueError("pipeline.cleanup_after_response must be a boolean")
    return raw_value
