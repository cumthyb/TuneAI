"""
开发服务器入口。启动 FastAPI，挂载 frontend 模板与静态资源。
需在项目根目录执行：poetry run python run.py
"""
import sys
from pathlib import Path

# 保证 backend 在路径中（未 poetry install 时可直接 python run.py）
_ROOT = Path(__file__).resolve().parent
_BACKEND = _ROOT / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

import uvicorn

if __name__ == "__main__":
    from tuneai.config import get_server_host, get_server_port
    host = get_server_host()
    port = get_server_port()
    uvicorn.run(
        "tuneai.main:app",
        host=host,
        port=port,
        reload=True,
        reload_dirs=[str(_BACKEND)],
    )
