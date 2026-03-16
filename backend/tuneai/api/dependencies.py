import uuid

from fastapi import Request

_REQUEST_ID_HEADER = "X-Request-ID"


def new_request_id() -> str:
    return f"req_{uuid.uuid4().hex[:16]}"


async def get_request_id(request: Request) -> str:
    rid = request.headers.get(_REQUEST_ID_HEADER, "").strip()
    return rid if rid else new_request_id()
