# pandoc_gui/config.py
"""LLM configuration persistence."""

import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "pandoc-gui"
CONFIG_FILE = CONFIG_DIR / "llm.json"


def load_llm_config() -> dict | None:
    """Load LLM config from ~/.config/pandoc-gui/llm.json.

    Returns None if file doesn't exist.
    """
    if not CONFIG_FILE.exists():
        return None
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def save_llm_config(config: dict) -> None:
    """Save LLM config to ~/.config/pandoc-gui/llm.json."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
