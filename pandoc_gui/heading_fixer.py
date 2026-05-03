# pandoc_gui/heading_fixer.py
"""Parse LLM response and apply heading fixes to Markdown content."""


def remove_horizontal_rules(content: str) -> tuple[str, int]:
    """Remove standalone --- horizontal rules from markdown content.

    Rules:
    - Only removes lines where the entire line is ---
    - Skips code blocks (``` delimited)
    - Skips headings (lines starting with #)
    - After removal, preserves one blank line where --- was

    Returns:
        (new_content, count_of_removed_rules)
    """
    lines = content.split("\n")
    result = []
    in_code_block = False
    removed_count = 0
    i = 0

    while i < len(lines):
        line = lines[i]

        # Toggle code block state
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            result.append(line)
            i += 1
            continue

        # Skip processing inside code blocks
        if in_code_block:
            result.append(line)
            i += 1
            continue

        stripped = line.strip()

        # Skip headings (lines starting with #)
        if stripped.startswith("#"):
            result.append(line)
            i += 1
            continue

        # Check if this line is a standalone ---
        if stripped == "---":
            removed_count += 1
            # Only add a blank line if the previous content is NOT already a blank line
            # (i.e., don't double up when --- is already acting as a section break)
            if not result or result[-1].strip() != "":
                result.append("")
            i += 1
            continue

        # Skip blank lines that follow a blank line (prevents triple blank lines
        # when --- is surrounded by blank lines on both sides)
        if stripped == "":
            if result and result[-1].strip() == "":
                # Already a blank line in result, skip this one
                i += 1
                continue
            result.append(line)
            i += 1
            continue

        result.append(line)
        i += 1

    return "\n".join(result), removed_count


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
