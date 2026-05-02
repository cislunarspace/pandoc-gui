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
            fixes.append((original, fixed))
    return fixes


def apply_fixes(content: str, fixes: list[tuple[str, str]]) -> str:
    """Apply heading fixes to markdown content.

    For each (original, fixed) pair, replaces the line that exactly matches
    the original heading with the fixed heading.
    """
    lines = content.split("\n")
    result = []
    for line in lines:
        replaced = False
        for original, fixed in fixes:
            if line.strip() == original.strip():
                result.append(fixed)
                replaced = True
                break
        if not replaced:
            result.append(line)
    return "\n".join(result)
