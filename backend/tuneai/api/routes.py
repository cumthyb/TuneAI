"""
/api/transpose 同步接口、页面路由、统一 JSON、超时与异常。
"""
from fastapi import APIRouter

router = APIRouter()


@router.post("/transpose")
def transpose():
    """同步移调接口，接收图片与目标调，返回结果图与 JSON。"""
    return {"success": False, "error_code": "NOT_IMPLEMENTED", "message": "待实现"}
