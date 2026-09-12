# Text → Chart JSON Extractor

Extracts structured, chart-ready JSON from **any** plain text using [Outlines](https://github.com/dottxt-ai/outlines) for guaranteed structured generation.

**Fully offline** — runs a local transformer model. No API keys, no internet required at runtime.

## How it works

1. You feed **any** plain text containing data (user signups, revenue, survey results, etc.)
2. Outlines + a local transformer produces a **guaranteed-valid** JSON payload conforming to a Pydantic schema
3. The output is a chart-ready `ChartPayload` with chart type, title, axes, and data points
4. A live chart preview is rendered in the browser

## Setup

```bash
# Install dependencies
pip install -r requirements.txt
```

The default model (`Qwen/Qwen2.5-0.5B-Instruct`, ~1GB) is downloaded automatically on first run and cached locally. After that, no internet is needed.

## Usage

### Web UI
```bash
python app.py
# Open http://localhost:5000
```

### CLI — interactive mode
```bash
python extract.py
```

### CLI — pass text directly
```bash
python extract.py --text "January had 2,500 signups, February 3,400, March 4,200."
```

### CLI — read from a file
```bash
python extract.py --file report.txt
```

### CLI — run bundled examples
```bash
python extract.py --examples
```

### Use a different model
```bash
# CLI
python extract.py --model Qwen/Qwen2.5-1.5B-Instruct --text "..."

# Web UI
MODEL_NAME=Qwen/Qwen2.5-1.5B-Instruct python app.py
```

## Example

**Input:**
> The platform saw strong, consistent growth in new user signups throughout the first quarter. We started the year with 2,500 new users in January. This momentum continued into February with 3,400 signups, and we closed out the quarter peaking at 4,200 new users in March.

**Output:**
```json
{
  "chart_type": "time_series",
  "title": "Q1 User Signups",
  "xAxis": "month",
  "yAxis": "signups",
  "data": [
    {"month": "January", "signups": 2500},
    {"month": "February", "signups": 3400},
    {"month": "March", "signups": 4200}
  ]
}
```

## Project Structure

```
├── app.py            # Flask web server (Web UI)
├── extract.py        # Core extraction logic + CLI
├── schema.py         # Pydantic models (ChartPayload)
├── prompt.py         # Prompt templates
├── examples.py       # Bundled test texts
├── requirements.txt  # Python dependencies
├── templates/
│   └── index.html    # Web UI template
├── static/
│   ├── style.css     # Styles
│   └── app.js        # Client-side logic
└── README.md
```
