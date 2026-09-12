#!/usr/bin/env python3
"""
Flask web server for the Text → Chart JSON extractor.

Serves a beautiful single-page UI and exposes an API endpoint
that wraps the Outlines + local transformer extraction pipeline.

No API key required — runs fully offline.
"""

from __future__ import annotations

import json
import os
import traceback

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from flask import Flask, jsonify, render_template, request

from examples import EXAMPLES
from extract import DEFAULT_MODEL, extract_chart_json, get_model, pretty_print

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static",
)

# ── Configuration ──────────────────────────────────────────────────────────

MODEL_NAME = os.environ.get("MODEL_NAME", DEFAULT_MODEL)


@app.route("/")
def index():
    """Serve the main UI."""
    return render_template("index.html")


@app.route("/api/extract", methods=["POST"])
def api_extract():
    """
    Extract structured chart JSON from plain text.

    Expects JSON body: { "text": "..." }
    Returns JSON:      { "success": true, "payload": { ... } }
    """
    body = request.get_json(force=True)
    text = body.get("text", "").strip()

    if not text:
        return jsonify({"success": False, "error": "No text provided."}), 400

    try:
        payload = extract_chart_json(text, MODEL_NAME)
        return jsonify({
            "success": True,
            "payload": payload.model_dump(),
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e),
        }), 500


@app.route("/api/examples", methods=["GET"])
def api_examples():
    """Return the bundled example texts."""
    return jsonify([
        {"label": label, "text": text}
        for label, text in EXAMPLES
    ])


@app.route("/api/model-info", methods=["GET"])
def api_model_info():
    """Return the currently loaded model name."""
    return jsonify({"model": MODEL_NAME})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"\n🚀 Starting Text → Chart JSON server")
    print(f"   Model: {MODEL_NAME}")
    print(f"   URL:   http://localhost:{port}")

    # Pre-load model before starting the server
    print(f"\n⏳ Model loading is deferred until first request.")
    # get_model(MODEL_NAME) # Disabled so the UI can start instantly offline
    print(f"✅ UI ready!\n")

    app.run(host="0.0.0.0", port=port, debug=False)
