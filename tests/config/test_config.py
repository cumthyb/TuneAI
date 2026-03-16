from pathlib import Path

import tuneai.config as config_module


class TestConfigEnvOverrides:
    def test_provider_based_llm_and_vision_env_overrides(self, monkeypatch):
        base_cfg = {
            "server": {},
            "provider_policy": {"default_provider": "glm"},
            "providers": {
                "glm": {"llm": {}, "vision_llm": {}},
                "qwen": {"llm": {}, "vision_llm": {}},
            },
        }
        monkeypatch.setattr(config_module, "_find_config", lambda: Path("/tmp/config.json"))
        monkeypatch.setattr(config_module, "_load_json", lambda _p: dict(base_cfg))
        monkeypatch.setenv("TUNEAI_LLM_API_KEY", "llm_key")
        monkeypatch.setenv("TUNEAI_VISION_LLM_API_KEY", "v_key")
        monkeypatch.setenv("TUNEAI_LLM_PROVIDER", "glm")
        monkeypatch.setenv("TUNEAI_VISION_LLM_PROVIDER", "qwen")
        monkeypatch.setenv("TUNEAI_LLM_BASE_URL", "https://glm.example/v4")
        monkeypatch.setenv("TUNEAI_VISION_LLM_BASE_URL", "https://qwen.example/v1")
        monkeypatch.setenv("TUNEAI_LLM_MODEL", "glm-4.6")
        monkeypatch.setenv("TUNEAI_VISION_LLM_MODEL", "qwen-vl-max")

        cfg = config_module.load_config()
        assert cfg["providers"]["glm"]["llm"]["api_key"] == "llm_key"
        assert cfg["providers"]["qwen"]["vision_llm"]["api_key"] == "v_key"
        assert cfg["providers"]["glm"]["llm"]["base_url"] == "https://glm.example/v4"
        assert cfg["providers"]["qwen"]["vision_llm"]["base_url"] == "https://qwen.example/v1"
        assert cfg["providers"]["glm"]["llm"]["model"] == "glm-4.6"
        assert cfg["providers"]["qwen"]["vision_llm"]["model"] == "qwen-vl-max"

    def test_ocr_env_overrides_target_provider(self, monkeypatch):
        base_cfg = {
            "server": {},
            "provider_policy": {"default_provider": "glm"},
            "providers": {
                "glm": {},
                "qwen": {"ocr": {}},
            },
        }
        monkeypatch.setattr(config_module, "_find_config", lambda: Path("/tmp/config.json"))
        monkeypatch.setattr(config_module, "_load_json", lambda _p: dict(base_cfg))
        monkeypatch.setenv("TUNEAI_OCR_PROVIDER", "qwen")
        monkeypatch.setenv("TUNEAI_OCR_RUNNER", "pkg.mod:run")
        monkeypatch.setenv("TUNEAI_OCR_ACCESS_KEY_ID", "id")
        monkeypatch.setenv("TUNEAI_OCR_ACCESS_KEY_SECRET", "secret")
        monkeypatch.setenv("TUNEAI_OCR_ENDPOINT", "ocr.example.com")

        cfg = config_module.load_config()
        assert cfg["providers"]["qwen"]["ocr"]["runner"] == "pkg.mod:run"
        assert cfg["providers"]["qwen"]["ocr"]["access_key_id"] == "id"
        assert cfg["providers"]["qwen"]["ocr"]["access_key_secret"] == "secret"
        assert cfg["providers"]["qwen"]["ocr"]["endpoint"] == "ocr.example.com"

    def test_default_provider_can_be_overridden_by_env(self, monkeypatch):
        base_cfg = {
            "server": {},
            "provider_policy": {"default_provider": "glm"},
            "providers": {"glm": {}, "qwen": {}},
        }
        monkeypatch.setattr(config_module, "_find_config", lambda: Path("/tmp/config.json"))
        monkeypatch.setattr(config_module, "_load_json", lambda _p: dict(base_cfg))
        monkeypatch.setenv("TUNEAI_PROVIDER", "qwen")

        cfg = config_module.load_config()
        assert cfg["provider_policy"]["default_provider"] == "qwen"

    def test_invalid_port_env_is_ignored(self, monkeypatch):
        base_cfg = {"server": {"port": 8000}, "provider_policy": {"default_provider": "glm"}, "providers": {"glm": {}}}
        monkeypatch.setattr(config_module, "_find_config", lambda: Path("/tmp/config.json"))
        monkeypatch.setattr(config_module, "_load_json", lambda _p: dict(base_cfg))
        monkeypatch.setenv("TUNEAI_PORT", "invalid")

        cfg = config_module.load_config()
        assert cfg["server"]["port"] == 8000

    def test_missing_default_provider_registration_raises(self, monkeypatch):
        base_cfg = {
            "server": {},
            "provider_policy": {"default_provider": "glm"},
            "providers": {"qwen": {}},
        }
        monkeypatch.setattr(config_module, "_find_config", lambda: Path("/tmp/config.json"))
        monkeypatch.setattr(config_module, "_load_json", lambda _p: dict(base_cfg))

        try:
            config_module.load_config()
            assert False, "expected ValueError"
        except ValueError as exc:
            assert "default_provider is not registered" in str(exc)

    def test_invalid_providers_type_raises(self, monkeypatch):
        base_cfg = {
            "server": {},
            "provider_policy": {"default_provider": "glm"},
            "providers": [],
        }
        monkeypatch.setattr(config_module, "_find_config", lambda: Path("/tmp/config.json"))
        monkeypatch.setattr(config_module, "_load_json", lambda _p: dict(base_cfg))

        try:
            config_module.load_config()
            assert False, "expected ValueError"
        except ValueError as exc:
            assert "providers must be an object" in str(exc)
