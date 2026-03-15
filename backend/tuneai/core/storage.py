"""
临时存储原图/中间结果/输出图，完成后清理。
"""
import shutil
from pathlib import Path

from tuneai.config import get_pipeline_config

_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def _base_dir() -> Path:
    temp_dir = get_pipeline_config().get("temp_dir", "data/outputs")
    return _ROOT / temp_dir


def get_request_dir(request_id: str) -> Path:
    d = _base_dir() / request_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_input_image(request_id: str, data: bytes) -> Path:
    p = get_request_dir(request_id) / "input.png"
    p.write_bytes(data)
    return p


def save_output_image(request_id: str, data: bytes) -> Path:
    p = get_request_dir(request_id) / "output.png"
    p.write_bytes(data)
    return p


def cleanup(request_id: str) -> None:
    d = _base_dir() / request_id
    if d.exists():
        shutil.rmtree(d, ignore_errors=True)
