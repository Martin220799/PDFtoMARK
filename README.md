# PDF → Markdown Converter

Cross-platform desktop app (Windows / Linux / macOS) with three conversion modes.

## Requirements

- Python 3.10+
- [Ollama](https://ollama.com) (for the LLM modes)
- [Poppler](https://poppler.freedesktop.org/) (for the LLM-OCR mode)

## Modes

| Mode | Description | Ollama required | Status |
|---|---|---|---|
| Simple | Rule-based MarkItDown, fast | No | ✅ tested |
| LLM | MarkItDown + LLM for image descriptions | Yes (multimodal model, e.g. llava) | ✅ tested |
| LLM-OCR | Pages as image → LLM (ideal for scans) | Yes (multimodal model, e.g. llava) | ✅ tested |

## Python setup

Install the Python dependencies and launch the application. This step is sufficient to run the **Simple mode** — no further tools are required.

### Installation

```bash
pip install -r requirements.txt
```

### Running

```bash
python main.py
```

## External tools (LLM & LLM-OCR modes)

> ℹ️ **Only required for the LLM and LLM-OCR modes.** Simple mode runs without any external tools beyond the Python dependencies above.

- **Ollama** — required for both LLM modes. See the official [installation guide](https://ollama.com/download) (the Linux install script also sets up GPU acceleration automatically where supported). Then pull a multimodal model, e.g. `ollama pull qwen3-vl:8b`.
- **Poppler** — additionally required for LLM-OCR mode (renders PDF pages to images). See the [Poppler downloads page](https://poppler.freedesktop.org/); on most systems it ships as `poppler-utils` (`sudo dnf install poppler-utils`, `sudo apt install poppler-utils`, or `brew install poppler`).
