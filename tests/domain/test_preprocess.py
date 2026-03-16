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
