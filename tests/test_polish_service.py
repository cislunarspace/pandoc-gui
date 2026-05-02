# tests/test_polish_service.py
import pytest
from unittest.mock import patch


class TestPolishService:
    """Tests for the polish_service module."""

    def test_polish_file_returns_fixes(self, tmp_path):
        from pandoc_gui.polish_service import polish_file
        # Create a temp markdown file
        md_file = tmp_path / "test.md"
        md_file.write_text("# 1. 旧标题\n\n正文", encoding="utf-8")

        # Mock the LLM call to return a fix
        mock_llm_config = {"api_url": "http://example.com", "api_key": "test", "model": "test"}

        with patch("pandoc_gui.llm_client.call_llm") as mock_call:
            mock_call.return_value = "# 1. 旧标题||# 旧标题"
            fixes = polish_file(str(md_file), str(tmp_path), mock_llm_config)

        assert len(fixes) == 1
        assert fixes[0] == ("# 1. 旧标题", "# 旧标题")

    def test_polish_file_empty_response(self, tmp_path):
        from pandoc_gui.polish_service import polish_file
        md_file = tmp_path / "test.md"
        md_file.write_text("# 正常标题\n\n正文", encoding="utf-8")

        mock_llm_config = {"api_url": "http://example.com", "api_key": "test", "model": "test"}

        with patch("pandoc_gui.llm_client.call_llm") as mock_call:
            mock_call.return_value = ""
            fixes = polish_file(str(md_file), str(tmp_path), mock_llm_config)

        assert fixes == []

    def test_polish_file_calls_llm_with_correct_headings(self, tmp_path):
        from pandoc_gui.polish_service import polish_file
        md_file = tmp_path / "test.md"
        md_file.write_text("# 标题一\n## 标题二\n\n正文", encoding="utf-8")

        mock_llm_config = {"api_url": "http://example.com", "api_key": "test", "model": "test"}

        with patch("pandoc_gui.llm_client.call_llm") as mock_call:
            mock_call.return_value = ""
            polish_file(str(md_file), str(tmp_path), mock_llm_config)

        # Verify LLM was called with extracted headings
        mock_call.assert_called_once()
        call_args = mock_call.call_args
        headings = call_args[0][3]  # 4th positional arg
        assert "标题一" in headings
        assert "标题二" in headings
