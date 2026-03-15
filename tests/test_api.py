"""
API 契约测试。
"""
import io
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import pytest
from fastapi.testclient import TestClient


def _make_png_bytes() -> bytes:
    """生成一个最小的合法 PNG（1x1 白色像素）。"""
    import base64
    # 1x1 white PNG (minimal valid PNG)
    b64 = (
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8"
        "z8BQDwADhQGAWjR9awAAAABJRU5ErkJggg=="
    )
    return base64.b64decode(b64)


@pytest.fixture
def client():
    # Mock run_pipeline so we don't need actual OCR/LLM in tests
    mock_result = MagicMock()
    mock_result.output_image_b64 = "dGVzdA=="  # "test" base64
    mock_result.score_ir = MagicMock()
    mock_result.score_ir.model_dump.return_value = {"score_id": "test", "measures": []}
    mock_result.warnings = []
    mock_result.processing_time_ms = 42

    with patch("tuneai.api.routes.run_pipeline", return_value=mock_result):
        from tuneai.main import app
        with TestClient(app) as c:
            yield c


class TestTransposeEndpoint:
    def test_missing_fields_returns_422(self, client):
        resp = client.post("/api/transpose")
        assert resp.status_code == 422

    def test_missing_image_returns_422(self, client):
        resp = client.post("/api/transpose", data={"target_key": "C"})
        assert resp.status_code == 422

    def test_missing_target_key_returns_422(self, client):
        png = _make_png_bytes()
        resp = client.post(
            "/api/transpose",
            files={"image": ("test.png", io.BytesIO(png), "image/png")},
        )
        assert resp.status_code == 422

    def test_invalid_target_key_returns_error(self, client):
        png = _make_png_bytes()
        resp = client.post(
            "/api/transpose",
            files={"image": ("test.png", io.BytesIO(png), "image/png")},
            data={"target_key": "X"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is False
        assert body["error_code"] == "INVALID_TARGET_KEY"

    def test_non_image_file_returns_error(self, client):
        resp = client.post(
            "/api/transpose",
            files={"image": ("score.txt", io.BytesIO(b"hello"), "text/plain")},
            data={"target_key": "C"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is False
        assert body["error_code"] == "INVALID_IMAGE_FORMAT"

    def test_valid_request_returns_success(self, client):
        png = _make_png_bytes()
        resp = client.post(
            "/api/transpose",
            files={"image": ("score.png", io.BytesIO(png), "image/png")},
            data={"target_key": "C"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert "output_image" in body
        assert "score_json" in body
        assert "warnings" in body
        assert "processing_time_ms" in body
        assert "request_id" in body

    def test_valid_request_all_keys(self, client):
        """Test a sample of valid keys."""
        png = _make_png_bytes()
        for key in ["C", "D", "Eb", "F#", "Bb", "B"]:
            resp = client.post(
                "/api/transpose",
                files={"image": ("score.png", io.BytesIO(png), "image/png")},
                data={"target_key": key},
            )
            assert resp.status_code == 200
            assert resp.json()["success"] is True

    def test_request_id_propagated(self, client):
        png = _make_png_bytes()
        resp = client.post(
            "/api/transpose",
            files={"image": ("score.png", io.BytesIO(png), "image/png")},
            data={"target_key": "G"},
            headers={"X-Request-ID": "req_custom123"},
        )
        assert resp.status_code == 200
        assert resp.json()["request_id"] == "req_custom123"
