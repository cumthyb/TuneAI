import shutil
from pathlib import Path

from tuneai.config import get_outputs_dir


def get_request_dir(request_id: str) -> Path:
    d = get_outputs_dir() / request_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_input_image(request_id: str, data: bytes) -> Path:
    path = get_request_dir(request_id) / "input.png"
    path.write_bytes(data)
    return path


def save_output_image(request_id: str, data: bytes) -> Path:
    path = get_request_dir(request_id) / "output.png"
    path.write_bytes(data)
    return path


def get_input_path(request_id: str) -> Path:
    return get_outputs_dir() / request_id / "input.png"


def get_output_path(request_id: str) -> Path:
    return get_outputs_dir() / request_id / "output.png"


def cleanup(request_id: str) -> None:
    path = get_outputs_dir() / request_id
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)
