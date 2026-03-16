from pathlib import Path

import tuneai.config as config_module


class TestConfigEnvOverrides:
    def test_llm_and_vision_env_overrides(self, monkeypatch):
        base_cfg = {"server": {}, "llm": {}, "vision_llm": {}, "ocr": {"provider": "qwen"}}
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
        assert cfg["llm"]["api_key"] == "llm_key"
        assert cfg["vision_llm"]["api_key"] == "v_key"
        assert cfg["llm"]["provider"] == "glm"
        assert cfg["vision_llm"]["provider"] == "qwen"
        assert cfg["llm"]["base_url"] == "https://glm.example/v4"
        assert cfg["vision_llm"]["base_url"] == "https://qwen.example/v1"
        assert cfg["llm"]["model"] == "glm-4.6"
        assert cfg["vision_llm"]["model"] == "qwen-vl-max"

    def test_ocr_env_overrides_active_provider(self, monkeypatch):
        base_cfg = {"server": {}, "llm": {}, "vision_llm": {}, "ocr": {"provider": "qwen"}}
        monkeypatch.setattr(config_module, "_find_config", lambda: Path("/tmp/config.json"))
        monkeypatch.setattr(config_module, "_load_json", lambda _p: dict(base_cfg))
        monkeypatch.setenv("TUNEAI_OCR_PROVIDER", "qwen")
        monkeypatch.setenv("TUNEAI_OCR_RUNNER", "pkg.mod:run")
        monkeypatch.setenv("TUNEAI_OCR_ACCESS_KEY_ID", "id")
        monkeypatch.setenv("TUNEAI_OCR_ACCESS_KEY_SECRET", "secret")
        monkeypatch.setenv("TUNEAI_OCR_ENDPOINT", "ocr.example.com")

        cfg = config_module.load_config()
        assert cfg["ocr"]["provider"] == "qwen"
        assert cfg["ocr"]["runners"]["qwen"] == "pkg.mod:run"
        assert cfg["ocr"]["providers"]["qwen"]["access_key_id"] == "id"
        assert cfg["ocr"]["providers"]["qwen"]["access_key_secret"] == "secret"
        assert cfg["ocr"]["providers"]["qwen"]["endpoint"] == "ocr.example.com"

    def test_invalid_port_env_is_ignored(self, monkeypatch):
        base_cfg = {"server": {"port": 8000}, "llm": {}, "vision_llm": {}, "ocr": {"provider": "qwen"}}
        monkeypatch.setattr(config_module, "_find_config", lambda: Path("/tmp/config.json"))
        monkeypatch.setattr(config_module, "_load_json", lambda _p: dict(base_cfg))
        monkeypatch.setenv("TUNEAI_PORT", "invalid")

        cfg = config_module.load_config()
        assert cfg["server"]["port"] == 8000
