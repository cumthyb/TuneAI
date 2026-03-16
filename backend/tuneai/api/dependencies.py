"""
请求 ID、超时等依赖。
"""
import uuid

from fastapi import Request

from tuneai.config import get_logging_config


def new_request_id() -> str:
    return f"req_{uuid.uuid4().hex[:16]}"


async def get_request_id(request: Request) -> str:
    header_name = get_logging_config().get("request_id_header")
    if not isinstance(header_name, str) or not header_name.strip():
        raise ValueError("logging.request_id_header must be a non-empty string")
    rid_raw = request.headers.get(header_name)
    if isinstance(rid_raw, str) and rid_raw.strip():
        rid = rid_raw.strip()
        return rid
    return new_request_id()
