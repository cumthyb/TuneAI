import io

import numpy as np
from PIL import Image

from tuneai.core.domain.preprocess import preprocess_image


class TestPreprocess:
    def test_invalid_image_bytes_raises(self):
        try:
            preprocess_image(b"not-an-image")
            assert False, "expected ValueError"
        except ValueError:
            assert True

    def test_valid_image_returns_grayscale_array(self):
        img = Image.new("RGB", (32, 32), color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        arr = preprocess_image(buf.getvalue())
        assert isinstance(arr, np.ndarray)
        assert arr.ndim == 2
        assert arr.dtype == np.uint8


class TestPreprocessWithSample:
    """用真实样本图片（匆匆那年.png）验证预处理结果。

    运行方式：
        make test-preprocess
    """

    def test_sample_returns_grayscale_array(self, sample_image_bytes):
        arr = preprocess_image(sample_image_bytes)
        assert isinstance(arr, np.ndarray)
        assert arr.ndim == 2
        assert arr.dtype == np.uint8

    def test_sample_output_size_is_reasonable(self, sample_image_bytes):
        arr = preprocess_image(sample_image_bytes)
        h, w = arr.shape
        assert w >= 100 and h >= 100, f"输出尺寸过小: {w}×{h}"

    def test_sample_pixel_range(self, sample_image_bytes):
        arr = preprocess_image(sample_image_bytes)
        assert arr.min() >= 0 and arr.max() <= 255
        # 简谱图片应同时存在深色笔画和浅色背景
        assert arr.min() < 50, "未检测到深色笔画像素"
        assert arr.max() > 200, "未检测到浅色背景像素"
