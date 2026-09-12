"""
Prompt templates for the text → chart-JSON extraction.

For local transformer models we build a single prompt string
(using the Qwen/Llama chat template format). Outlines handles
the rest via structured generation.
"""

SYSTEM_INSTRUCTION = """\
You are a data-extraction assistant. Your job is to read plain-text \
descriptions and extract every quantitative data point into a structured \
chart-ready JSON payload.

Rules:
1. Identify ALL numeric values and their associated labels/categories.
2. Choose the most appropriate chart_type for the data.
3. Use clear, concise axis labels derived from the text.
4. Convert written numbers (e.g. "two thousand") to numeric values.
5. Strip currency symbols and commas — store raw numbers.
6. If the text contains multiple distinct datasets, pick the primary one.
7. Preserve the original ordering of data points.
8. The title should be short and descriptive.
9. IMPORTANT: All text outputs (title, xAxis, yAxis, data labels) MUST be translated to and written in Persian (Farsi).\
"""

USER_TEMPLATE = """\
Extract structured chart data from the following text:

---
{text}
---

Return a JSON object with chart_type, title, xAxis, yAxis, and data.\
"""


def build_prompt(text: str) -> str:
    """
    Build a single prompt string for a local instruction-tuned model.

    Uses the ChatML format understood by Qwen, SmolLM, and many others.
    """
    user_content = USER_TEMPLATE.format(text=text)
    return (
        f"<|im_start|>system\n{SYSTEM_INSTRUCTION}<|im_end|>\n"
        f"<|im_start|>user\n{user_content}<|im_end|>\n"
        f"<|im_start|>assistant\n"
    )


def build_messages(text: str) -> list[dict[str, str]]:
    """Build chat messages (kept for compatibility)."""
    return [
        {"role": "system", "content": SYSTEM_INSTRUCTION},
        {"role": "user", "content": USER_TEMPLATE.format(text=text)},
    ]
