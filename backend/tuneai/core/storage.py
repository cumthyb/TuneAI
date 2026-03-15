"""
临时存储原图/中间结果/输出图，完成后清理。

目录结构（每次请求独立子目录）：
  data/outputs/{request_id}/
    ├── input.png      # 前端上传的原始图片（pipeline 开始时写入）
    └── output.png     # 转调后输出图片（pipeline 结束时写入）

开发测试时，样本图片位于 data/samples/，可直接读取。
"""
import shutil
from pathlib import Path

from tuneai.config import get_outputs_dir


def get_request_dir(request_id: str) -> Path:
    """返回本次请求的临时工作目录，不存在则创建。"""
    d = get_outputs_dir() / request_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_input_image(request_id: str, data: bytes) -> Path:
    """将前端上传的原始图片写入 data/outputs/{request_id}/input.png。"""
    p = get_request_dir(request_id) / "input.png"
    p.write_bytes(data)
    return p


def save_output_image(request_id: str, data: bytes) -> Path:
    """将转调结果图写入 data/outputs/{request_id}/output.png。"""
    p = get_request_dir(request_id) / "output.png"
    p.write_bytes(data)
    return p


def get_input_path(request_id: str) -> Path:
    """获取输入图路径（不保证存在）。"""
    return get_outputs_dir() / request_id / "input.png"


def get_output_path(request_id: str) -> Path:
    """获取输出图路径（不保证存在）。"""
    return get_outputs_dir() / request_id / "output.png"


def cleanup(request_id: str) -> None:
    """删除本次请求的所有临时文件（cleanup_after_response=True 时调用）。"""
    d = get_outputs_dir() / request_id
    if d.exists():
        shutil.rmtree(d, ignore_errors=True)
