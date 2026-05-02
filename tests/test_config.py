# tests/test_config.py
import json
import pytest
from pathlib import Path


class TestConfig:
    """Tests for the config module."""

    def test_save_and_load_config(self, monkeypatch, tmp_path):
        from pandoc_gui.config import CONFIG_DIR, CONFIG_FILE, save_llm_config, load_llm_config

        # Redirect config to temp dir
        monkeypatch.setattr("pandoc_gui.config.CONFIG_DIR", tmp_path / ".config" / "pandoc-gui")
        config_file = tmp_path / ".config" / "pandoc-gui" / "llm.json"
        monkeypatch.setattr("pandoc_gui.config.CONFIG_FILE", config_file)

        test_config = {
            "api_url": "https://api.example.com/v1/chat/completions",
            "api_key": "sk-test123",
            "model": "gpt-4",
        }

        save_llm_config(test_config)
        assert config_file.exists()

        loaded = load_llm_config()
        assert loaded == test_config

    def test_load_config_file_not_exists(self, monkeypatch, tmp_path):
        from pandoc_gui.config import CONFIG_DIR, CONFIG_FILE, load_llm_config

        monkeypatch.setattr("pandoc_gui.config.CONFIG_DIR", tmp_path / ".config" / "pandoc-gui")
        monkeypatch.setattr("pandoc_gui.config.CONFIG_FILE", tmp_path / ".config" / "pandoc-gui" / "llm.json")

        result = load_llm_config()
        assert result is None

    def test_load_config_invalid_json(self, monkeypatch, tmp_path):
        from pandoc_gui.config import CONFIG_DIR, CONFIG_FILE, load_llm_config

        config_dir = tmp_path / ".config" / "pandoc-gui"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "llm.json"
        config_file.write_text("not valid json{", encoding="utf-8")

        monkeypatch.setattr("pandoc_gui.config.CONFIG_DIR", config_dir)
        monkeypatch.setattr("pandoc_gui.config.CONFIG_FILE", config_file)

        result = load_llm_config()
        assert result is None
