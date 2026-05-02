# pandoc_gui/heading_extractor.py
"""Extract headings from Markdown content."""


def extract_headings(content: str) -> list[str]:
    """Extract all markdown headings from content.

    Skips headings inside code blocks.
    Returns list of heading texts (without the leading # markers and whitespace).
    """
    lines = content.split("\n")
    in_code_block = False
    headings = []

    for line in lines:
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        stripped = line.strip()
        if stripped.startswith("#"):
            # Count the heading level
            level = 0
            for ch in stripped:
                if ch == "#":
                    level += 1
                else:
                    break
            # Extract heading text (after # and space)
            text = stripped[level:].strip()
            headings.append(text)

    return headings
