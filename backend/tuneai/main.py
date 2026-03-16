"""
FastAPI 应用入口。托管 React（Vite）构建产物，单端口提供页面与 API（方案 A）。
"""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from tuneai.config import get_frontend_build_dir, get_logging_config
from tuneai.logging_config import setup_logging, get_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    log_cfg = get_logging_config()
    level = log_cfg.get("level")
    fmt = log_cfg.get("format")
    if not isinstance(level, str) or not level.strip():
        raise ValueError("logging.level must be a non-empty string")
    if not isinstance(fmt, str) or not fmt.strip():
        raise ValueError("logging.format must be a non-empty string")
    setup_logging(level=level, fmt=fmt)
    get_logger("main").info("TuneAI backend starting")
    yield
    get_logger("main").info("TuneAI backend shutting down")


app = FastAPI(title="TuneAI", lifespan=lifespan)

# API 路由（优先于静态与 SPA）
from tuneai.api.routes import router as api_router  # noqa: E402

app.include_router(api_router, prefix="/api")

# 方案 A：React（Vite）构建产物，单端口
build_dir = get_frontend_build_dir()
if build_dir.is_dir():
    assets_dir = build_dir / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
    index_path = build_dir / "index.html"

    @app.get("/", response_class=HTMLResponse)
    def _serve_index() -> HTMLResponse:
        return HTMLResponse(content=index_path.read_text(encoding="utf-8"))

    @app.api_route("/{full_path:path}", methods=["GET"])
    def _spa_fallback(request: Request, full_path: str):
        if full_path.startswith("api/") or full_path.startswith("assets/"):
            raise StarletteHTTPException(status_code=404)
        if (build_dir / full_path).is_file():
            return FileResponse(build_dir / full_path)
        return FileResponse(index_path, media_type="text/html")

else:
    import logging as _logging
    _logging.warning(
        "frontend/dist 不存在，仅提供 API（开发模式）。"
        "如需前端页面，请在 frontend 目录执行 npm run build。"
    )
