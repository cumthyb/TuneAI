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
_DEFAULT_MAX_IMAGE_SIZE_MB = 20


def _list_providers_with_llm() -> list[str]:
    providers: list[str] = []
    for p in list_supported_providers():
        cfg = get_llm_config(p)
        if isinstance(cfg, dict) and cfg:
            providers.append(p)
    return sorted(set(providers))


def _list_providers_with_vision_llm() -> list[str]:
    providers: list[str] = []
    for p in list_supported_providers():
        cfg = get_vision_llm_config(p)
        if isinstance(cfg, dict) and cfg:
            providers.append(p)
    return sorted(set(providers))


def _list_providers_with_ocr() -> list[str]:
    providers: list[str] = []
    for p in list_supported_providers():
        ocr_cfg = get_ocr_config(p)
        runner = str(ocr_cfg.get("runner", "")).strip()
        if runner:
            providers.append(p)
    return sorted(set(providers))


@router.get("/meta", response_model=ApiMetaResponse)
def get_api_meta() -> ApiMetaResponse:
    llm_providers = _list_providers_with_llm()
    vision_providers = _list_providers_with_vision_llm()
    ocr_providers = _list_providers_with_ocr()
    providers = sorted({*llm_providers, *vision_providers, *ocr_providers})
    default_provider = get_default_provider()
    default_llm_provider = default_provider if default_provider in llm_providers else (llm_providers[0] if llm_providers else "")
    default_vision_provider = (
        default_provider if default_provider in vision_providers else (vision_providers[0] if vision_providers else "")
    )
    default_ocr_provider = default_provider if default_provider in ocr_providers else (ocr_providers[0] if ocr_providers else "")
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
    provider: str | None = Form(default=None),
    llm_provider: str | None = Form(default=None),
    vision_llm_provider: str | None = Form(default=None),
    ocr_provider: str | None = Form(default=None),
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

        provider = provider.strip().lower() if provider else None
        llm_provider = (llm_provider or provider)
        vision_llm_provider = (vision_llm_provider or provider)
        ocr_provider = (ocr_provider or provider)

        allowed_llm_providers = set(_list_providers_with_llm())
        allowed_vision_llm_providers = set(_list_providers_with_vision_llm())
        allowed_ocr_providers = set(_list_providers_with_ocr())

        if llm_provider:
            llm_provider = llm_provider.strip().lower()
            if llm_provider not in allowed_llm_providers:
                return _error_response(
                    status_code=400,
                    error_code="INVALID_LLM_PROVIDER",
                    error_message=f"不支持的 LLM provider: {llm_provider}",
                    request_id=request_id,
                )
        if vision_llm_provider:
            vision_llm_provider = vision_llm_provider.strip().lower()
            if vision_llm_provider not in allowed_vision_llm_providers:
                return _error_response(
                    status_code=400,
                    error_code="INVALID_VISION_LLM_PROVIDER",
                    error_message=f"不支持的 Vision LLM provider: {vision_llm_provider}",
                    request_id=request_id,
                )
        if ocr_provider:
            ocr_provider = ocr_provider.strip().lower()
            if ocr_provider not in allowed_ocr_providers:
                return _error_response(
                    status_code=400,
                    error_code="INVALID_OCR_PROVIDER",
                    error_message=f"不支持的 OCR provider: {ocr_provider}",
                    request_id=request_id,
                )

        timeout_seconds = float(get_pipeline_config().get("request_timeout_seconds", 60))
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


def _get_max_image_size_mb() -> int:
    raw_value = get_pipeline_config().get("max_image_size_mb", _DEFAULT_MAX_IMAGE_SIZE_MB)
    try:
        value = int(raw_value)
    except (TypeError, ValueError):
        return _DEFAULT_MAX_IMAGE_SIZE_MB
    return value if value > 0 else _DEFAULT_MAX_IMAGE_SIZE_MB
