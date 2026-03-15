"""
FastAPI 应用入口。根据 frontend.mode 提供模板页或 React 构建产物（方案 A 单端口）。
"""
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from tuneai.config import (
    get_frontend_build_dir,
    get_frontend_mode,
    get_frontend_static_dir,
    get_frontend_template_dir,
)

app = FastAPI(title="TuneAI")

# API 路由（优先于静态与 SPA）
from tuneai.api.routes import router as api_router

app.include_router(api_router, prefix="/api")


if get_frontend_mode() == "build":
    # 方案 A：React 构建产物，单端口
    build_dir = get_frontend_build_dir()
    if not build_dir.is_dir():
        raise RuntimeError(f"前端构建目录不存在: {build_dir}，请先执行 npm run build")
    app.mount("/assets", StaticFiles(directory=build_dir / "assets"), name="assets")
    # 根路径与静态资源后，其余 GET 返回 index.html（SPA 回退）
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
else:
    # 当前模式：Jinja2 模板 + 静态目录
    from fastapi.templating import Jinja2Templates

    template_dir = get_frontend_template_dir()
    static_dir = get_frontend_static_dir()
    templates = Jinja2Templates(directory=str(template_dir))
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/", response_class=HTMLResponse)
    def _index(request: Request) -> HTMLResponse:
        return templates.TemplateResponse("index.html", {"request": request})

    @app.get("/result", response_class=HTMLResponse)
    def _result(request: Request) -> HTMLResponse:
        return templates.TemplateResponse("result.html", {"request": request})
