"""
FastAPI 应用入口。托管 React（Vite）构建产物，单端口提供页面与 API（方案 A）。
"""
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from tuneai.config import get_frontend_build_dir

app = FastAPI(title="TuneAI")

# API 路由（优先于静态与 SPA）
from tuneai.api.routes import router as api_router

app.include_router(api_router, prefix="/api")

# 方案 A：React（Vite）构建产物，单端口
build_dir = get_frontend_build_dir()
if not build_dir.is_dir():
    raise RuntimeError(f"前端构建目录不存在: {build_dir}，请先在 frontend 目录执行 npm run build")
app.mount("/assets", StaticFiles(directory=build_dir / "assets"), name="assets")
index_path = build_dir / "index.html"


@app.get("/", response_class=HTMLResponse)
def _serve_index() -> HTMLResponse:
    return HTMLResponse(content=(index_path.read_text(encoding="utf-8")))


@app.api_route("/{full_path:path}", methods=["GET"])
def _spa_fallback(request: Request, full_path: str):
    if full_path.startswith("api/") or full_path.startswith("assets/"):
        raise StarletteHTTPException(status_code=404)
    if (build_dir / full_path).is_file():
        return FileResponse(build_dir / full_path)
    return FileResponse(index_path, media_type="text/html")
