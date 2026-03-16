"""API contract tests for current error semantics."""

import asyncio
import io
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    mock_result = MagicMock()
    mock_result.output_image_b64 = "dGVzdA=="
    mock_result.score_ir = MagicMock()
    mock_result.score_ir.model_dump.return_value = {"score_id": "test", "events": []}
    mock_result.warnings = []
    mock_result.processing_time_ms = 42

    with patch("tuneai.api.routes.run_pipeline", new=AsyncMock(return_value=mock_result)):
        from tuneai.main import app

        with TestClient(app, raise_server_exceptions=False) as c:
            yield c


class TestMissingFields:
    def test_no_fields(self, client):
        assert client.post("/api/transpose").status_code == 422

    def test_no_image(self, client):
        assert client.post("/api/transpose", data={"target_key": "C"}).status_code == 422

    def test_no_target_key(self, client, minimal_png_bytes):
        resp = client.post(
            "/api/transpose",
            files={"image": ("test.png", io.BytesIO(minimal_png_bytes), "image/png")},
        )
        assert resp.status_code == 422


class TestValidationErrors:
    def test_invalid_target_key(self, client, minimal_png_bytes):
        resp = client.post(
            "/api/transpose",
            files={"image": ("test.png", io.BytesIO(minimal_png_bytes), "image/png")},
            data={"target_key": "X"},
        )
        assert resp.status_code == 400
        assert resp.json()["error_code"] == "INVALID_TARGET_KEY"

    def test_non_image_file(self, client):
        resp = client.post(
            "/api/transpose",
            files={"image": ("score.txt", io.BytesIO(b"hello"), "text/plain")},
            data={"target_key": "C"},
        )
        assert resp.status_code == 415
        assert resp.json()["error_code"] == "INVALID_IMAGE_FORMAT"

    def test_empty_image(self, client):
        resp = client.post(
            "/api/transpose",
            files={"image": ("score.png", io.BytesIO(b""), "image/png")},
            data={"target_key": "C"},
        )
        assert resp.status_code == 400
        assert resp.json()["error_code"] == "EMPTY_IMAGE"


class TestRuntimeErrors:
    def test_pipeline_timeout_returns_504(self, minimal_png_bytes):
        async def _slow(*_args, **_kwargs):
            await asyncio.sleep(0.05)
            return MagicMock()

        with (
            patch("tuneai.api.routes.get_pipeline_config", return_value={"request_timeout_seconds": 0.001}),
            patch("tuneai.api.routes.run_pipeline", new=AsyncMock(side_effect=_slow)),
        ):
            from tuneai.main import app
            with TestClient(app, raise_server_exceptions=False) as c:
                resp = c.post(
                    "/api/transpose",
                    files={"image": ("score.png", io.BytesIO(minimal_png_bytes), "image/png")},
                    data={"target_key": "C"},
                )
        assert resp.status_code == 504
        assert resp.json()["error_code"] == "REQUEST_TIMEOUT"

    def test_pipeline_no_notes_returns_422(self, minimal_png_bytes):
        from tuneai.core.application.pipeline import PipelineError

        with patch(
            "tuneai.api.routes.run_pipeline",
            new=AsyncMock(side_effect=PipelineError("NO_NOTES_FOUND", "no notes")),
        ):
            from tuneai.main import app
            with TestClient(app, raise_server_exceptions=False) as c:
                resp = c.post(
                    "/api/transpose",
                    files={"image": ("score.png", io.BytesIO(minimal_png_bytes), "image/png")},
                    data={"target_key": "C"},
                )
        assert resp.status_code == 422
        assert resp.json()["error_code"] == "NO_NOTES_FOUND"


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
        assert isinstance(body["warnings"], list)
        assert "output_image" in body
        assert "score_json" in body
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
