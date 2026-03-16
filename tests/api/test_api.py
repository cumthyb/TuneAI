"""API contract tests for current error semantics."""

import asyncio
import io
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


def _strict_data(**overrides):
    data = {
        "target_key": "C",
        "llm_provider": "glm",
        "vision_llm_provider": "glm",
        "ocr_provider": "glm",
    }
    data.update(overrides)
    return data


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


@pytest.fixture(autouse=True)
def strict_route_contract():
    with (
        patch("tuneai.api.routes._list_providers_with_llm", return_value=["glm"]),
        patch("tuneai.api.routes._list_providers_with_vision_llm", return_value=["glm"]),
        patch("tuneai.api.routes._list_providers_with_ocr", return_value=["glm"]),
        patch("tuneai.api.routes.get_default_provider", return_value="glm"),
        patch(
            "tuneai.api.routes.get_pipeline_config",
            return_value={
                "max_image_size_mb": 20,
                "request_timeout_seconds": 30,
                "cleanup_after_response": False,
            },
        ),
    ):
        yield


class TestMissingFields:
    def test_no_fields(self, client):
        assert client.post("/api/transpose").status_code == 422

    def test_no_image(self, client):
        assert client.post("/api/transpose", data={"target_key": "C"}).status_code == 422

    def test_no_target_key(self, client, minimal_png_bytes):
        resp = client.post(
            "/api/transpose",
            files={"image": ("test.png", io.BytesIO(minimal_png_bytes), "image/png")},
            data={
                "llm_provider": "glm",
                "vision_llm_provider": "glm",
                "ocr_provider": "glm",
            },
        )
        assert resp.status_code == 422

    def test_missing_provider_fields(self, client, minimal_png_bytes):
        resp = client.post(
            "/api/transpose",
            files={"image": ("test.png", io.BytesIO(minimal_png_bytes), "image/png")},
            data={"target_key": "C"},
        )
        assert resp.status_code == 422


class TestValidationErrors:
    def test_invalid_target_key(self, client, minimal_png_bytes):
        resp = client.post(
            "/api/transpose",
            files={"image": ("test.png", io.BytesIO(minimal_png_bytes), "image/png")},
            data=_strict_data(target_key="X"),
        )
        assert resp.status_code == 400
        assert resp.json()["error_code"] == "INVALID_TARGET_KEY"

    def test_non_image_file(self, client):
        resp = client.post(
            "/api/transpose",
            files={"image": ("score.txt", io.BytesIO(b"hello"), "text/plain")},
            data=_strict_data(),
        )
        assert resp.status_code == 415
        assert resp.json()["error_code"] == "INVALID_IMAGE_FORMAT"

    def test_empty_image(self, client):
        resp = client.post(
            "/api/transpose",
            files={"image": ("score.png", io.BytesIO(b""), "image/png")},
            data=_strict_data(),
        )
        assert resp.status_code == 400
        assert resp.json()["error_code"] == "EMPTY_IMAGE"

    def test_missing_content_type(self, client, minimal_png_bytes):
        resp = client.post(
            "/api/transpose",
            files={"image": ("score.png", io.BytesIO(minimal_png_bytes), "")},
            data=_strict_data(),
        )
        assert resp.status_code == 400
        assert resp.json()["error_code"] == "MISSING_IMAGE_CONTENT_TYPE"


class TestRuntimeErrors:
    def test_pipeline_timeout_returns_504(self, minimal_png_bytes):
        async def _slow(*_args, **_kwargs):
            await asyncio.sleep(0.05)
            return MagicMock()

        with (
            patch(
                "tuneai.api.routes.get_pipeline_config",
                return_value={
                    "max_image_size_mb": 20,
                    "request_timeout_seconds": 0.001,
                    "cleanup_after_response": False,
                },
            ),
            patch("tuneai.api.routes.run_pipeline", new=AsyncMock(side_effect=_slow)),
        ):
            from tuneai.main import app
            with TestClient(app, raise_server_exceptions=False) as c:
                resp = c.post(
                    "/api/transpose",
                    files={"image": ("score.png", io.BytesIO(minimal_png_bytes), "image/png")},
                    data=_strict_data(),
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
                    data=_strict_data(),
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
                    data=_strict_data(),
                )
        assert resp.status_code == 500
        assert resp.json()["error_code"] == "PIPELINE_ERROR"


class TestSuccessResponse:
    def test_response_structure(self, client, minimal_png_bytes):
        resp = client.post(
            "/api/transpose",
            files={"image": ("score.png", io.BytesIO(minimal_png_bytes), "image/png")},
            data=_strict_data(),
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
            data=_strict_data(target_key="G"),
            headers={"X-Request-ID": "req_custom_abc"},
        )
        assert resp.status_code == 200
        assert resp.json()["request_id"] == "req_custom_abc"


class TestProviderRouting:
    def test_meta_default_provider_falls_back_when_default_has_no_ocr(self, client):
        with (
            patch("tuneai.api.routes._list_providers_with_llm", return_value=["glm", "qwen"]),
            patch("tuneai.api.routes._list_providers_with_vision_llm", return_value=["glm", "qwen"]),
            patch("tuneai.api.routes._list_providers_with_ocr", return_value=["glm"]),
            patch("tuneai.api.routes.get_default_provider", return_value="qwen"),
        ):
            resp = client.get("/api/meta")
        assert resp.status_code == 200
        body = resp.json()
        assert body["providers"] == ["glm"]
        assert body["llm_providers"] == ["glm", "qwen"]
        assert body["vision_llm_providers"] == ["glm", "qwen"]
        assert body["ocr_providers"] == ["glm"]
        assert body["default_provider"] == "glm"
        assert body["default_llm_provider"] == "qwen"
        assert body["default_vision_llm_provider"] == "qwen"
        assert body["default_ocr_provider"] == "glm"

    def test_meta_returns_provider_lists_when_consistent(self, client):
        with (
            patch("tuneai.api.routes._list_providers_with_llm", return_value=["glm", "qwen"]),
            patch("tuneai.api.routes._list_providers_with_vision_llm", return_value=["glm", "qwen"]),
            patch("tuneai.api.routes._list_providers_with_ocr", return_value=["glm", "qwen"]),
            patch("tuneai.api.routes.get_default_provider", return_value="glm"),
        ):
            resp = client.get("/api/meta")
        assert resp.status_code == 200
        body = resp.json()
        assert body["providers"] == ["glm", "qwen"]
        assert body["llm_providers"] == ["glm", "qwen"]
        assert body["vision_llm_providers"] == ["glm", "qwen"]
        assert body["ocr_providers"] == ["glm", "qwen"]
        assert body["default_provider"] == "glm"
        assert body["default_llm_provider"] == "glm"
        assert body["default_vision_llm_provider"] == "glm"
        assert body["default_ocr_provider"] == "glm"

    def test_meta_ocr_enumeration_excludes_qwen_without_ocr(self, client):
        with (
            patch("tuneai.api.routes._list_providers_with_llm", return_value=["glm", "qwen"]),
            patch("tuneai.api.routes._list_providers_with_vision_llm", return_value=["glm", "qwen"]),
            patch("tuneai.api.routes._list_providers_with_ocr", return_value=["glm"]),
            patch("tuneai.api.routes.get_default_provider", return_value="glm"),
        ):
            resp = client.get("/api/meta")
        assert resp.status_code == 200
        body = resp.json()
        assert body["ocr_providers"] == ["glm"]
        assert body["providers"] == ["glm"]

    def test_invalid_unified_provider_returns_400(self, client, minimal_png_bytes):
        with (
            patch("tuneai.api.routes._list_providers_with_llm", return_value=["glm", "qwen"]),
            patch("tuneai.api.routes._list_providers_with_vision_llm", return_value=["glm", "qwen"]),
            patch("tuneai.api.routes._list_providers_with_ocr", return_value=["qwen"]),
        ):
            resp = client.post(
                "/api/transpose",
                files={"image": ("score.png", io.BytesIO(minimal_png_bytes), "image/png")},
                data=_strict_data(provider="glm", llm_provider="glm", vision_llm_provider="glm", ocr_provider="glm"),
            )
        assert resp.status_code == 400
        assert resp.json()["error_code"] == "INVALID_OCR_PROVIDER"

    def test_providers_passed_to_pipeline(self, minimal_png_bytes):
        mock_result = MagicMock()
        mock_result.output_image_b64 = "dGVzdA=="
        mock_result.score_ir = MagicMock()
        mock_result.score_ir.model_dump.return_value = {"score_id": "test", "events": []}
        mock_result.warnings = []
        mock_result.processing_time_ms = 0

        mock_pipeline = AsyncMock(return_value=mock_result)
        with (
            patch("tuneai.api.routes._list_providers_with_llm", return_value=["glm"]),
            patch("tuneai.api.routes._list_providers_with_vision_llm", return_value=["glm"]),
            patch("tuneai.api.routes._list_providers_with_ocr", return_value=["glm"]),
            patch("tuneai.api.routes.run_pipeline", new=mock_pipeline),
            patch(
                "tuneai.api.routes.get_pipeline_config",
                return_value={"max_image_size_mb": 20, "request_timeout_seconds": 30, "cleanup_after_response": False},
            ),
        ):
            from tuneai.main import app
            with MagicMock():
                pass
            with patch("tuneai.main.app", app):
                from fastapi.testclient import TestClient
                with TestClient(app, raise_server_exceptions=False) as c:
                    resp = c.post(
                        "/api/transpose",
                        files={"image": ("score.png", io.BytesIO(minimal_png_bytes), "image/png")},
                        data=_strict_data(provider="glm", llm_provider="glm", vision_llm_provider="glm", ocr_provider="glm"),
                    )

        assert resp.status_code == 200
        call_kwargs = mock_pipeline.call_args.kwargs
        assert call_kwargs["llm_provider"] == "glm"
        assert call_kwargs["vision_llm_provider"] == "glm"
        assert call_kwargs["ocr_provider"] == "glm"
