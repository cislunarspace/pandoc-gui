# pandoc_gui/llm_client.py
"""LLM client for calling OpenAI-compatible APIs."""

import urllib.request
import urllib.error
import json


def call_llm(api_url: str, api_key: str, model: str, headings: list[str]) -> str:
    """Call LLM to polish markdown headings.

    Args:
        api_url: Full URL to the /v1/chat/completions endpoint
        api_key: API key for authentication
        model: Model name to use
        headings: List of heading texts to send for polishing

    Returns:
        LLM response text
    """
    system_prompt = (
        "你是 Markdown 标题优化助手。检测并修复标题中的手动编号，只返回需要修复的标题。"
        "需要检测的编号模式包括：\n"
        "1. 中文数字编号：一、二、三、...（如'一、'、'二、'）\n"
        "2. 阿拉伯数字编号：1. 1.1 1.1.1 ...（如'1.'、'1.1.'）\n"
        "3. 括号码编号：（1）（2）...（如'（1）'、'（2）'）\n"
        "返回格式：原标题||修复后标题，每行一个。"
        "如果某标题无需修复则省略该行。"
        "标题中的管道符用 \\| 转义。"
    )

    user_content = "以下是需要检测的标题（每行一个）：\n" + "\n".join(headings)

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        api_url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            response_data = json.loads(resp.read().decode("utf-8"))
            return response_data["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        raise RuntimeError(f"LLM API error {e.code}: {error_body}") from e
    except (urllib.error.URLError, OSError) as e:
        raise RuntimeError(f"LLM API request failed: {e}") from e
