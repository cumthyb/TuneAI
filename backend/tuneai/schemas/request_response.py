"""
API 请求/响应 Pydantic 模型。
"""
from typing import Any, Literal, Optional

from pydantic import BaseModel


class Warning(BaseModel):
    type: str
    measure: Optional[int] = None
    message: str


class TransposeSuccessResponse(BaseModel):
    success: Literal[True]
    output_image: str          # base64-encoded PNG
    score_json: dict[str, Any]
    warnings: list[Warning]
    processing_time_ms: int
    request_id: str


class TransposeErrorResponse(BaseModel):
    success: Literal[False]
    error_code: str
    error_message: str
    request_id: str


class ApiMetaResponse(BaseModel):
    allowed_image_types: list[str]
    max_image_size_mb: int
    llm_providers: list[str]
    vision_llm_providers: list[str]
    ocr_providers: list[str]
    default_llm_provider: str
    default_vision_llm_provider: str
    default_ocr_provider: str
