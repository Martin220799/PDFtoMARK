# PDF → Markdown Converter

Cross-platform desktop app (Windows / Linux / macOS) with three conversion modes.

## Requirements

- Python 3.10+
- [Ollama](https://ollama.com) (for the LLM modes)
- [Poppler](https://poppler.freedesktop.org/) (for the LLM-OCR mode)

### Installing Poppler

**Windows:**
```
winget install poppler
```
or manually from https://github.com/oschwartz10612/poppler-windows/releases

**Linux (Fedora):**
```bash
sudo dnf install poppler-utils
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt install poppler-utils
```

**macOS:**
```bash
brew install poppler
```

## Installation

```bash
pip install -r requirements.txt
```

## Running

```bash
python main.py
```

## Modes

| Mode | Description | Ollama required |
|---|---|---|
| ⚡ Simple | Rule-based MarkItDown, fast | No |
| 🧠 LLM | MarkItDown + LLM for image descriptions | Yes (multimodal model, e.g. llava) |
| 🔍 LLM-OCR | Pages as image → LLM (ideal for scans) | Yes (multimodal model, e.g. llava) |

## Recommended Ollama models

```bash
ollama pull llava          # general-purpose, multimodal
ollama pull llava-phi3     # smaller, faster
ollama pull llama3.2       # text-only, for Simple/text PDFs
```

## AMD RX 9070 XT (ROCm)

### Fedora (recommended)

Ollama via Docker with ROCm:
```bash
# Install Docker + ROCm drivers
sudo dnf install docker
sudo systemctl enable --now docker

# Start the Ollama ROCm container
docker run -d --device /dev/kfd --device /dev/dri \
  -v ollama:/root/.ollama -p 11434:11434 \
  --name ollama ollama/ollama:rocm
```

Alternatively, ROCm natively on Fedora:
```bash
sudo dnf install rocm-opencl rocm-hip
# Then install Ollama as usual
curl -fsSL https://ollama.com/install.sh | sh
```

### Ubuntu/Debian

Ollama via Docker with ROCm:
```bash
docker run -d --device /dev/kfd --device /dev/dri \
  -v ollama:/root/.ollama -p 11434:11434 \
  --name ollama ollama/ollama:rocm
```
