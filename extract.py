#!/usr/bin/env python3
"""
Text → Structured Chart JSON extractor.

Uses the Outlines library (https://github.com/dottxt-ai/outlines) with a
LOCAL transformer model — no API key, no internet required at runtime.

The model is loaded once and reused for all requests.

Usage:
    python extract.py                          # interactive mode
    python extract.py --text "..."             # inline text
    python extract.py --file report.txt        # read from file
    python extract.py --examples               # run bundled examples
    python extract.py --model Qwen/Qwen2.5-1.5B-Instruct --text "..."
"""

from __future__ import annotations

import argparse
import json
import sys
import textwrap

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

import outlines
from transformers import AutoModelForCausalLM, AutoTokenizer

from prompt import build_prompt
from schema import ChartPayload


# ── Defaults ────────────────────────────────────────────────────────────────

# Small but capable instruction-tuned model (runs easily on CPU)
DEFAULT_MODEL = "HuggingFaceTB/SmolLM-135M-Instruct"


# ── Model cache (singleton) ─────────────────────────────────────────────────

_loaded_models: dict[str, object] = {}


def get_model(model_name: str = DEFAULT_MODEL):
    """
    Load a transformer model + tokenizer, wrapped by Outlines.

    The model is cached so subsequent calls reuse the same instance.
    """
    import os
    if model_name.startswith(("./", "/", "../")) and not os.path.exists(model_name):
        raise ValueError(
            f"\n\n❌ Offline model directory '{model_name}' not found.\n"
            f"Please create the directory and place the model files there, or use a HuggingFace repo ID.\n"
        )

    if model_name not in _loaded_models:
        print(f"⏳ Loading model '{model_name}' (this may take a moment on first run)...")
        ollama_url = os.environ.get("OLLAMA_URL")
        if ollama_url:
            print(f"🔌 Connecting to remote server at {ollama_url}...")
            import ollama
            # The ollama client expects the host without /v1
            host_url = ollama_url.replace("/v1", "").replace("/v1/", "")
            client = ollama.Client(host=host_url)
            model = outlines.models.from_ollama(client, model_name)
        else:
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            transformer = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype="auto",
                device_map="auto",
            )
            model = outlines.from_transformers(transformer, tokenizer)
        _loaded_models[model_name] = model
        print(f"✅ Model '{model_name}' loaded and ready.")
    return _loaded_models[model_name]


# ── Core extraction function ────────────────────────────────────────────────


def extract_chart_json(
    text: str,
    model_name: str = DEFAULT_MODEL,
) -> ChartPayload:
    """
    Extract a structured ChartPayload from arbitrary plain text.

    Uses Outlines' structured generation to guarantee the LLM output
    conforms to the ChartPayload Pydantic schema. The LLM *cannot*
    produce invalid JSON.

    Args:
        text:       The plain-text input containing data to extract.
        model_name: HuggingFace model ID (default: Qwen2.5-0.5B-Instruct).

    Returns:
        A validated ChartPayload instance.
    """
    # 1. Get the Outlines-wrapped model (cached)
    model = get_model(model_name)

    # 2. Build the prompt string
    prompt = build_prompt(text)

    import os
    kwargs = {"options": {"num_predict": 1024}} if os.environ.get("OLLAMA_URL") else {"max_new_tokens": 1024}
    
    # 3. Call the model with the Pydantic type as the output constraint.
    #    Outlines guarantees the response conforms to ChartPayload.
    result = model(prompt, ChartPayload, **kwargs)
    # 4. Parse & validate
    payload = ChartPayload.model_validate_json(result)
    return payload


# ── Pretty printing ─────────────────────────────────────────────────────────


def pretty_print(payload: ChartPayload) -> str:
    """Return indented JSON string."""
    return json.dumps(payload.model_dump(), indent=2, ensure_ascii=False)


# ── CLI ─────────────────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract structured chart JSON from plain text using Outlines (local, offline).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              python extract.py --text "January had 2500 signups, February 3400, March 4200."
              python extract.py --file quarterly_report.txt
              python extract.py --examples
              python extract.py --model Qwen/Qwen2.5-1.5B-Instruct --text "Revenue was $1M in Q1."
        """),
    )
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument(
        "--text", "-t",
        type=str,
        help="Plain text to extract chart data from.",
    )
    input_group.add_argument(
        "--file", "-f",
        type=str,
        help="Path to a text file to read input from.",
    )
    input_group.add_argument(
        "--examples", "-e",
        action="store_true",
        help="Run all bundled example texts.",
    )
    parser.add_argument(
        "--model", "-m",
        type=str,
        default=DEFAULT_MODEL,
        help=f"HuggingFace model ID (default: {DEFAULT_MODEL}).",
    )
    return parser


def interactive_input() -> str:
    """Prompt the user for multi-line text input."""
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  Text → Chart JSON Extractor  (powered by Outlines)        ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print("║  Paste your text below, then press Enter twice to submit.  ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()

    lines: list[str] = []
    empty_count = 0
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == "":
            empty_count += 1
            if empty_count >= 2:
                break
            lines.append(line)
        else:
            empty_count = 0
            lines.append(line)

    text = "\n".join(lines).strip()
    if not text:
        print("No input provided. Exiting.")
        sys.exit(0)
    return text


def run_single(text: str, model_name: str) -> None:
    """Extract and print chart JSON for a single text."""
    print(f"\n📝 Input text ({len(text)} chars):")
    print(f"   {text[:120]}{'...' if len(text) > 120 else ''}")
    print(f"\n🔄 Extracting with {model_name}...\n")

    payload = extract_chart_json(text, model_name)
    output = pretty_print(payload)

    print("✅ Structured Chart JSON:")
    print("─" * 60)
    print(output)
    print("─" * 60)
    print()


def run_examples(model_name: str) -> None:
    """Run all bundled examples."""
    from examples import EXAMPLES

    print(f"\n🧪 Running {len(EXAMPLES)} examples with {model_name}...\n")
    print("=" * 60)

    for i, (label, text) in enumerate(EXAMPLES, 1):
        print(f"\n{'='*60}")
        print(f"  Example {i}/{len(EXAMPLES)}: {label}")
        print(f"{'='*60}")
        run_single(text, model_name)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # Pre-load the model
    get_model(args.model)

    if args.examples:
        run_examples(args.model)
    elif args.text:
        run_single(args.text, args.model)
    elif args.file:
        with open(args.file, "r") as f:
            text = f.read().strip()
        if not text:
            print("File is empty. Exiting.")
            sys.exit(1)
        run_single(text, args.model)
    else:
        # Interactive mode
        text = interactive_input()
        run_single(text, args.model)


if __name__ == "__main__":
    main()
