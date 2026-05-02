# tests/test_gui.py
import os
import pytest
from pathlib import Path


class TestBuildCommand:
    """Tests for the build_command function."""

    def test_single_file_input(self):
        from pandoc_gui.gui import build_command
        cmd = build_command("/path/to/file.md", "/output/file.pdf")
        xelatex_path = str(Path.home() / "texlive" / "2026" / "bin" / "x86_64-linux" / "xelatex")
        assert cmd[0:4] == ["uv", "run", "pandoc", "/path/to/file.md"]
        assert cmd[4] == "-o"
        assert cmd[5] == "/output/file.pdf"
        assert f"--pdf-engine={xelatex_path}" in cmd
        # Template should be present (temp file path)
        template_arg = [a for a in cmd if a.startswith("--template=")]
        assert len(template_arg) == 1


class TestGetOutputPath:
    """Tests for the get_output_path function."""

    def test_simple_filename(self):
        from pandoc_gui.gui import get_output_path
        result = get_output_path("/path/to/file.md", "/output")
        assert result == "/output/file.pdf"

    def test_filename_with_spaces(self):
        from pandoc_gui.gui import get_output_path
        result = get_output_path("/path/to/my document.md", "/output dir")
        assert result == "/output dir/my document.pdf"

    def test_chinese_filename(self):
        from pandoc_gui.gui import get_output_path
        result = get_output_path("/path/to/开题技巧.md", "/output")
        assert result == "/output/开题技巧.pdf"


class TestValidateInput:
    """Tests for the validate_input function."""

    def test_valid_file_path(self, tmp_path):
        from pandoc_gui.gui import validate_input
        f = tmp_path / "test.md"
        f.touch()
        assert validate_input(str(f)) is None

    def test_valid_folder_path(self, tmp_path):
        from pandoc_gui.gui import validate_input
        assert validate_input(str(tmp_path)) is None

    def test_empty_path(self):
        from pandoc_gui.gui import validate_input
        error = validate_input("")
        assert error is not None
        assert "empty" in error.lower() or "required" in error.lower()

    def test_nonexistent_path(self):
        from pandoc_gui.gui import validate_input
        error = validate_input("/nonexistent/path/that/does/not/exist")
        assert error is not None
        assert "not exist" in error.lower() or "found" in error.lower()
