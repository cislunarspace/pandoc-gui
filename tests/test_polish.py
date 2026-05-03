# tests/test_polish.py
import pytest


class TestExtractHeadings:
    """Tests for the heading_extractor module."""

    def test_single_title(self):
        from pandoc_gui.heading_extractor import extract_headings
        content = "# Hello World\n\nThis is a paragraph."
        assert extract_headings(content) == ["Hello World"]

    def test_multiple_headings(self):
        from pandoc_gui.heading_extractor import extract_headings
        content = "# Title One\n\n## Title Two\n\n### Title Three"
        assert extract_headings(content) == ["Title One", "Title Two", "Title Three"]

    def test_heading_with_special_chars(self):
        from pandoc_gui.heading_extractor import extract_headings
        content = "# Python|Flask 1.2.3\n\n## 深度学习 (Deep Learning)"
        assert extract_headings(content) == ["Python|Flask 1.2.3", "深度学习 (Deep Learning)"]

    def test_heading_in_code_block_not_extracted(self):
        from pandoc_gui.heading_extractor import extract_headings
        content = """# Real Heading

```
# This is NOT a heading
```

## Another Real Heading
"""
        result = extract_headings(content)
        assert "# This is NOT a heading" not in result
        assert "Real Heading" in result
        assert "Another Real Heading" in result

    def test_empty_content(self):
        from pandoc_gui.heading_extractor import extract_headings
        assert extract_headings("") == []
        assert extract_headings("No headings here") == []

    def test_heading_with_leading_whitespace(self):
        from pandoc_gui.heading_extractor import extract_headings
        content = "  # Heading with space\n\n   ## Indented heading"
        assert extract_headings(content) == ["Heading with space", "Indented heading"]

    def test_heading_with_punctuation(self):
        from pandoc_gui.heading_extractor import extract_headings
        content = "# Hello! How are you?\n\n## What's up?"
        assert extract_headings(content) == ["Hello! How are you?", "What's up?"]


class TestParseFixes:
    """Tests for the heading_fixer module - parse_fixes function."""

    def test_single_fix(self):
        from pandoc_gui.heading_fixer import parse_fixes
        response = "旧标题||新标题"
        assert parse_fixes(response) == [("旧标题", "新标题")]

    def test_multiple_fixes(self):
        from pandoc_gui.heading_fixer import parse_fixes
        response = "1. 标题一||标题一\n2. 标题二||标题二"
        assert parse_fixes(response) == [
            ("1. 标题一", "标题一"),
            ("2. 标题二", "标题二"),
        ]

    def test_escaped_pipe_in_heading(self):
        from pandoc_gui.heading_fixer import parse_fixes
        response = "A \\| B||A or B"
        assert parse_fixes(response) == [("A | B", "A or B")]

    def test_empty_response(self):
        from pandoc_gui.heading_fixer import parse_fixes
        assert parse_fixes("") == []
        assert parse_fixes("   ") == []

    def test_mixed_lines_with_whitespace(self):
        from pandoc_gui.heading_fixer import parse_fixes
        response = "  编号1. 旧||新  \n\n  编号2. 旧||新  "
        result = parse_fixes(response)
        assert len(result) == 2


class TestApplyFixes:
    """Tests for the heading_fixer module - apply_fixes function."""

    def test_apply_single_fix(self):
        from pandoc_gui.heading_fixer import apply_fixes
        content = "# 1. 旧标题\n\n正文"
        fixes = [("1. 旧标题", "旧标题")]
        result = apply_fixes(content, fixes)
        assert "# 1. 旧标题" not in result
        assert "# 旧标题" in result
        assert "正文" in result

    def test_apply_multiple_fixes(self):
        from pandoc_gui.heading_fixer import apply_fixes
        content = "# 1. 标题一\n## 2. 标题二\n### 3. 标题三\n正文"
        fixes = [
            ("1. 标题一", "标题一"),
            ("2. 标题二", "标题二"),
        ]
        result = apply_fixes(content, fixes)
        assert "# 标题一" in result
        assert "## 标题二" in result
        assert "### 3. 标题三" in result

    def test_no_fixes(self):
        from pandoc_gui.heading_fixer import apply_fixes
        content = "# 正常标题\n\n正文"
        result = apply_fixes(content, [])
        assert result == content

    def test_heading_not_found(self):
        from pandoc_gui.heading_fixer import apply_fixes
        content = "# 标题一\n正文"
        fixes = [("不存在的标题", "新标题")]
        result = apply_fixes(content, fixes)
        assert result == content


class TestRemoveHorizontalRules:
    """Tests for remove_horizontal_rules function."""

    def test_removes_standalone_hr(self):
        from pandoc_gui.heading_fixer import remove_horizontal_rules
        content = "标题一\n\n---\n\n标题二"
        result, count = remove_horizontal_rules(content)
        assert count == 1
        assert "---" not in result
        assert "标题一" in result
        assert "标题二" in result

    def test_preserves_code_block_hr(self):
        from pandoc_gui.heading_fixer import remove_horizontal_rules
        content = "标题一\n\n```\n---\n```\n\n标题二"
        result, count = remove_horizontal_rules(content)
        assert count == 0
        assert "```" in result

    def test_preserves_heading_with_hr(self):
        from pandoc_gui.heading_fixer import remove_horizontal_rules
        content = "# --- 标题 ---\n\n---\n\n正文"
        result, count = remove_horizontal_rules(content)
        assert count == 1
        assert "# --- 标题 ---" in result

    def test_preserves_blank_line_after_removal(self):
        from pandoc_gui.heading_fixer import remove_horizontal_rules
        content = "标题一\n\n---\n\n标题二"
        result, count = remove_horizontal_rules(content)
        assert "标题一\n\n标题二" in result

    def test_no_hr_returns_same_content(self):
        from pandoc_gui.heading_fixer import remove_horizontal_rules
        content = "# 标题一\n\n正文一\n\n正文二"
        result, count = remove_horizontal_rules(content)
        assert count == 0
        assert result == content

    def test_multiple_hr_removed(self):
        from pandoc_gui.heading_fixer import remove_horizontal_rules
        content = "标题一\n\n---\n\n标题二\n\n---\n\n标题三"
        result, count = remove_horizontal_rules(content)
        assert count == 2
        assert "---" not in result

    def test_inline_code_hr_preserved(self):
        from pandoc_gui.heading_fixer import remove_horizontal_rules
        content = "标题\n\n`---`\n\n正文"
        result, count = remove_horizontal_rules(content)
        assert count == 0
        assert "`---`" in result

    def test_hr_variant_not_removed(self):
        from pandoc_gui.heading_fixer import remove_horizontal_rules
        content = "标题\n\n- - -\n\n正文"
        result, count = remove_horizontal_rules(content)
        assert count == 0
        assert "- - -" in result
