"""
pytest 共享 fixture。

目录约定：
  data/samples/   — 开发/测试用样本简谱图片（版本控制）
  data/outputs/   — 运行时临时目录，每个请求一个子目录
  data/logs/      — 日志文件
"""
import sys
from pathlib import Path

# 保证后端包可导入
_BACKEND = Path(__file__).resolve().parent.parent / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

import pytest

# 项目根目录
ROOT = Path(__file__).resolve().parent.parent
TEST_CONFIG_PATH = ROOT / "config.json"
EXAMPLE_CONFIG_PATH = ROOT / "config.example.json"

# 样本图片目录
SAMPLES_DIR = ROOT / "data" / "samples"

# 主测试样本："匆匆那年.png"
SAMPLE_IMAGE_PATH = SAMPLES_DIR / "匆匆那年.png"


def pytest_addoption(parser):
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="run integration tests with real OCR/LLM providers",
    )


# ---------------------------------------------------------------------------
# 基础 fixture
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def sample_image_path() -> Path:
    """返回样本简谱图片路径（匆匆那年.png）。"""
    if not SAMPLE_IMAGE_PATH.exists():
        pytest.skip(f"样本图片不存在: {SAMPLE_IMAGE_PATH}")
    return SAMPLE_IMAGE_PATH


@pytest.fixture(scope="session")
def sample_image_bytes(sample_image_path: Path) -> bytes:
    """读取样本简谱图片字节。"""
    return sample_image_path.read_bytes()


@pytest.fixture(scope="session")
def sample_image_array(sample_image_bytes: bytes):
    """将样本简谱图片解码为 OpenCV 灰度图像。"""
    import cv2
    import numpy as np

    arr = np.frombuffer(sample_image_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
    if img is None:
        pytest.skip("样本图片解码失败")
    return img


@pytest.fixture(scope="session")
def minimal_png_bytes() -> bytes:
    """最小合法 PNG（1×1 白色像素），用于 API 格式校验测试。"""
    import base64
    b64 = (
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8"
        "z8BQDwADhQGAWjR9awAAAABJRU5ErkJggg=="
    )
    return base64.b64decode(b64)


@pytest.fixture(autouse=True, scope="session")
def ensure_test_config():
    created = False
    if not TEST_CONFIG_PATH.exists():
        if not EXAMPLE_CONFIG_PATH.exists():
            pytest.fail(f"缺少测试配置模板: {EXAMPLE_CONFIG_PATH}")
        TEST_CONFIG_PATH.write_bytes(EXAMPLE_CONFIG_PATH.read_bytes())
        created = True
    yield
    if created and TEST_CONFIG_PATH.exists():
        TEST_CONFIG_PATH.unlink()


@pytest.fixture
def run_integration(request):
    """集成测试守卫：未传 --run-integration 则跳过。"""
    if not request.config.getoption("run_integration"):
        pytest.skip("requires --run-integration")


@pytest.fixture(autouse=True, scope="session")
def setup_logging_once(ensure_test_config):
    """测试期间启用 human-readable 日志（stderr），跳过文件日志。"""
    from tuneai.logging_config import setup_logging
    setup_logging(level="DEBUG", fmt="human")
