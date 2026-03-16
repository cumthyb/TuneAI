"""API contract tests for current error semantics."""

import asyncio
import contextlib
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

    def test_pipeline_internal_error_returns_500(self, minimal_png_bytes):
        from tuneai.core.application.pipeline import PipelineError

        with patch(
            "tuneai.api.routes.run_pipeline",
            new=AsyncMock(side_effect=PipelineError("PIPELINE_ERROR", "internal")),
        ):
            from tuneai.main import app
            with TestClient(app, raise_server_exceptions=False) as c:
                resp = c.post(
                    "/api/transpose",
                    files={"image": ("score.png", io.BytesIO(minimal_png_bytes), "image/png")},
                    data={"target_key": "C"},
                )
        assert resp.status_code == 500
        assert resp.json()["error_code"] == "PIPELINE_ERROR"


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


class TestProviderRouting:
    def test_meta_returns_provider_lists(self, client):
        with (
            patch("tuneai.api.routes._list_providers_with_llm", return_value=["glm", "qwen"]),
            patch("tuneai.api.routes._list_providers_with_vision_llm", return_value=["glm"]),
            patch("tuneai.api.routes._list_providers_with_ocr", return_value=["qwen"]),
            patch("tuneai.api.routes.get_default_provider", return_value="glm"),
        ):
            resp = client.get("/api/meta")
        assert resp.status_code == 200
        body = resp.json()
        assert body["providers"] == ["glm", "qwen"]
        assert body["llm_providers"] == ["glm", "qwen"]
        assert body["vision_llm_providers"] == ["glm"]
        assert body["ocr_providers"] == ["qwen"]
        assert body["default_provider"] == "glm"
        assert body["default_llm_provider"] == "glm"
        assert body["default_vision_llm_provider"] == "glm"
        assert body["default_ocr_provider"] == "qwen"

    def test_invalid_unified_provider_returns_400(self, client, minimal_png_bytes):
        with (
            patch("tuneai.api.routes._list_providers_with_llm", return_value=["glm", "qwen"]),
            patch("tuneai.api.routes._list_providers_with_vision_llm", return_value=["glm", "qwen"]),
            patch("tuneai.api.routes._list_providers_with_ocr", return_value=["qwen"]),
        ):
            resp = client.post(
                "/api/transpose",
                files={"image": ("score.png", io.BytesIO(minimal_png_bytes), "image/png")},
                data={"target_key": "C", "provider": "glm"},
            )
        assert resp.status_code == 400
        assert resp.json()["error_code"] == "INVALID_OCR_PROVIDER"

    def test_unified_provider_passes_into_provider_overrides(self, client, minimal_png_bytes):
        seen: dict[str, str | None] = {}

        @contextlib.contextmanager
        def _capture(**kwargs):
            seen.update(kwargs)
            yield

        with (
            patch("tuneai.api.routes._list_providers_with_llm", return_value=["glm"]),
            patch("tuneai.api.routes._list_providers_with_vision_llm", return_value=["glm"]),
            patch("tuneai.api.routes._list_providers_with_ocr", return_value=["glm"]),
            patch("tuneai.api.routes.provider_overrides", side_effect=lambda **kw: _capture(**kw)),
        ):
            resp = client.post(
                "/api/transpose",
                files={"image": ("score.png", io.BytesIO(minimal_png_bytes), "image/png")},
                data={"target_key": "C", "provider": "glm"},
            )

        assert resp.status_code == 200
        assert seen == {
            "llm_provider": "glm",
            "vision_llm_provider": "glm",
            "ocr_provider": "glm",
        }
