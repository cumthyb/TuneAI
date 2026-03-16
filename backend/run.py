"""
应用启动入口。
通过 --mode 显式指定环境：dev（启用热重载）或 prod（关闭热重载）。
"""
import argparse
from pathlib import Path

import uvicorn

_BACKEND_DIR = Path(__file__).resolve().parent


def main() -> None:
    parser = argparse.ArgumentParser(description="TuneAI server entrypoint")
    parser.add_argument(
        "--mode",
        choices=("dev", "prod"),
        default="dev",
        help="Server mode: dev enables reload, prod disables reload.",
    )
    args = parser.parse_args()

    from tuneai.config import get_server_host, get_server_port

    host = get_server_host()
    port = get_server_port()
    is_reload = args.mode == "dev"
    uvicorn.run(
        "tuneai.main:app",
        host=host,
        port=port,
        reload=is_reload,
        reload_dirs=[str(_BACKEND_DIR)] if is_reload else None,
    )


if __name__ == "__main__":
    main()
