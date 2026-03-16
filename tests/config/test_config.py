from pathlib import Path

import pytest

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
        monkeypatch.setenv("TUNEAI_OCR_API_KEY", "ocr_key")
        monkeypatch.setenv("TUNEAI_OCR_BASE_URL", "https://ocr.example.com/v1")
        monkeypatch.setenv("TUNEAI_OCR_MODEL", "glm-4.6v")

        cfg = config_module.load_config()
        assert cfg["providers"]["qwen"]["ocr"]["runner"] == "pkg.mod:run"
        assert cfg["providers"]["qwen"]["ocr"]["api_key"] == "ocr_key"
        assert cfg["providers"]["qwen"]["ocr"]["base_url"] == "https://ocr.example.com/v1"
        assert cfg["providers"]["qwen"]["ocr"]["model"] == "glm-4.6v"

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

    def test_invalid_port_env_raises(self, monkeypatch):
        base_cfg = {"server": {"port": 8000}, "provider_policy": {"default_provider": "glm"}, "providers": {"glm": {}}}
        monkeypatch.setattr(config_module, "_find_config", lambda: Path("/tmp/config.json"))
        monkeypatch.setattr(config_module, "_load_json", lambda _p: dict(base_cfg))
        monkeypatch.setenv("TUNEAI_PORT", "invalid")

        with pytest.raises(ValueError, match="TUNEAI_PORT must be an integer"):
            config_module.load_config()

    def test_missing_default_provider_registration_raises(self, monkeypatch):
        base_cfg = {
            "server": {},
            "provider_policy": {"default_provider": "glm"},
            "providers": {"qwen": {}},
        }
        monkeypatch.setattr(config_module, "_find_config", lambda: Path("/tmp/config.json"))
        monkeypatch.setattr(config_module, "_load_json", lambda _p: dict(base_cfg))

        with pytest.raises(ValueError, match="default_provider is not registered"):
            config_module.load_config()

    def test_invalid_providers_type_raises(self, monkeypatch):
        base_cfg = {
            "server": {},
            "provider_policy": {"default_provider": "glm"},
            "providers": [],
        }
        monkeypatch.setattr(config_module, "_find_config", lambda: Path("/tmp/config.json"))
        monkeypatch.setattr(config_module, "_load_json", lambda _p: dict(base_cfg))

        with pytest.raises(ValueError, match="providers must be an object"):
            config_module.load_config()
