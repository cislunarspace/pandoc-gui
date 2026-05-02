# pandoc_gui/heading_fixer.py
"""Parse LLM response and apply heading fixes to Markdown content."""


def parse_fixes(response: str) -> list[tuple[str, str]]:
    """Parse LLM response into list of (original, fixed) heading pairs.

    Format: each line is "original||fixed"
    Escaped pipe: "\\|" becomes "|"
    """
    fixes = []
    for line in response.split("\n"):
        line = line.strip()
        if not line:
            continue
        # Split on || (but not \|)
        # We need to first unescape \| to |, then split on the remaining ||
        unescaped = line.replace("\\|", "|")
        parts = unescaped.split("||")
        if len(parts) == 2:
            original = parts[0].strip()
            fixed = parts[1].strip()
            if original != fixed:
                fixes.append((original, fixed))
    return fixes


def apply_fixes(content: str, fixes: list[tuple[str, str]]) -> str:
    """Apply heading fixes to markdown content.

    For each (original, fixed) pair, replaces the heading line that matches
    the original heading text with the fixed heading, preserving the heading level.
    """
    lines = content.split("\n")
    result = []
    for line in lines:
        stripped = line.strip()
        # Strip leading # markers to get the heading text
        heading_text = stripped
        level = 0
        if stripped.startswith("#"):
            i = 0
            while i < len(stripped) and stripped[i] == "#":
                i += 1
                level = i
            # Skip whitespace after # markers
            start = i
            while start < len(stripped) and stripped[start] in " \t":
                start += 1
            heading_text = stripped[start:]

        replaced = False
        for original, fixed in fixes:
            if heading_text.strip() == original.strip():
                if level > 0:
                    result.append("#" * level + " " + fixed)
                else:
                    result.append(fixed)
                replaced = True
                break
        if not replaced:
            result.append(line)
    return "\n".join(result)
