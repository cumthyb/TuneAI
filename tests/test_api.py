"""
API 契约测试。

使用 conftest 中的 minimal_png_bytes / sample_image_bytes fixture。
所有测试均 mock run_pipeline，不依赖 OCR/LLM。
"""
import io
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    """FastAPI TestClient，mock 掉 run_pipeline。"""
    mock_result = MagicMock()
    mock_result.output_image_b64 = "dGVzdA=="   # base64("test")
    mock_result.score_ir = MagicMock()
    mock_result.score_ir.model_dump.return_value = {"score_id": "test", "measures": []}
    mock_result.warnings = []
    mock_result.processing_time_ms = 42

    with patch("tuneai.api.routes.run_pipeline", return_value=mock_result):
        from tuneai.main import app
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c


# ---------------------------------------------------------------------------
# 422: 缺少必填字段
# ---------------------------------------------------------------------------

class TestMissingFields:

    def test_no_fields(self, client):
        resp = client.post("/api/transpose")
        assert resp.status_code == 422

    def test_no_image(self, client):
        resp = client.post("/api/transpose", data={"target_key": "C"})
        assert resp.status_code == 422

    def test_no_target_key(self, client, minimal_png_bytes):
        resp = client.post(
            "/api/transpose",
            files={"image": ("test.png", io.BytesIO(minimal_png_bytes), "image/png")},
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# 业务错误：target_key / 文件格式不合法
# ---------------------------------------------------------------------------

class TestValidationErrors:

    def test_invalid_target_key(self, client, minimal_png_bytes):
        resp = client.post(
            "/api/transpose",
            files={"image": ("test.png", io.BytesIO(minimal_png_bytes), "image/png")},
            data={"target_key": "X"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is False
        assert body["error_code"] == "INVALID_TARGET_KEY"
        assert "request_id" in body

    def test_non_image_file(self, client):
        resp = client.post(
            "/api/transpose",
            files={"image": ("score.txt", io.BytesIO(b"hello"), "text/plain")},
            data={"target_key": "C"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is False
        assert body["error_code"] == "INVALID_IMAGE_FORMAT"

    def test_all_valid_keys(self, client, minimal_png_bytes):
        """所有合法调名都应通过校验，返回 success=True。"""
        for key in ["C", "C#", "Db", "D", "Eb", "E", "F", "F#", "Gb", "G", "Ab", "A", "Bb", "B"]:
            resp = client.post(
                "/api/transpose",
                files={"image": ("s.png", io.BytesIO(minimal_png_bytes), "image/png")},
                data={"target_key": key},
            )
            assert resp.status_code == 200, f"key={key}"
            assert resp.json()["success"] is True, f"key={key}"


# ---------------------------------------------------------------------------
# 正常成功响应结构校验
# ---------------------------------------------------------------------------

class TestSuccessResponse:

    def test_response_structure(self, client, minimal_png_bytes):
        resp = client.post(
            "/api/transpose",
            files={"image": ("score.png", io.BytesIO(minimal_png_bytes), "image/png")},
            data={"target_key": "C"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert "output_image" in body
        assert "score_json" in body
        assert "warnings" in body
        assert isinstance(body["warnings"], list)
        assert "processing_time_ms" in body
        assert "request_id" in body

    def test_request_id_propagated_from_header(self, client, minimal_png_bytes):
        resp = client.post(
            "/api/transpose",
            files={"image": ("score.png", io.BytesIO(minimal_png_bytes), "image/png")},
            data={"target_key": "G"},
            headers={"X-Request-ID": "req_custom_abc"},
        )
        assert resp.status_code == 200
        assert resp.json()["request_id"] == "req_custom_abc"

    def test_auto_generated_request_id(self, client, minimal_png_bytes):
        resp = client.post(
            "/api/transpose",
            files={"image": ("score.png", io.BytesIO(minimal_png_bytes), "image/png")},
            data={"target_key": "F"},
        )
        assert resp.status_code == 200
        rid = resp.json()["request_id"]
        assert rid.startswith("req_"), rid

    def test_sample_image_success(self, client, sample_image_bytes):
        """用真实样本图 匆匆那年.png 测试 API 正常响应结构（pipeline 已 mock）。"""
        resp = client.post(
            "/api/transpose",
            files={"image": ("匆匆那年.png", io.BytesIO(sample_image_bytes), "image/png")},
            data={"target_key": "C"},
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True
