# pandoc_gui/polish_service.py
"""Polish service - orchestrates the heading polish workflow."""

from pathlib import Path

from pandoc_gui.heading_extractor import extract_headings
from pandoc_gui.heading_fixer import parse_fixes


def polish_file(input_path: str, output_dir: str, llm_config: dict) -> list[tuple[str, str]]:
    """Polish headings in a markdown file using LLM.

    Args:
        input_path: Path to the markdown file
        output_dir: Directory where polished file will be saved (not written by this function)
        llm_config: Dict with api_url, api_key, model

    Returns:
        List of (original_heading, fixed_heading) tuples
    """
    # Read the file
    with open(input_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract headings
    headings = extract_headings(content)
    if not headings:
        return []

    # Call LLM
    from pandoc_gui.llm_client import call_llm

    api_url = llm_config["api_url"]
    api_key = llm_config["api_key"]
    model = llm_config["model"]
    response = call_llm(api_url, api_key, model, headings)

    # Parse fixes
    fixes = parse_fixes(response)
    return fixes
