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
    success: Literal[True] = True
    output_image: str          # base64-encoded PNG
    score_json: dict[str, Any]
    warnings: list[Warning] = []
    processing_time_ms: int
    request_id: str


class TransposeErrorResponse(BaseModel):
    success: Literal[False] = False
    error_code: str
    error_message: str
    request_id: str
