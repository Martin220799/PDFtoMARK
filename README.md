# PDF → Markdown Converter

> ⚠️ **Work in Progress**
> This project is under active development. Currently, **only the Simple mode** (PDF → Markdown via MarkItDown) has been tested and verified. The *LLM* and *LLM-OCR* modes are implemented but not yet validated — features, interfaces, and behavior may change without notice.

Cross-platform desktop app (Windows / Linux / macOS) with three conversion modes.

## Requirements

- Python 3.10+
- [Ollama](https://ollama.com) (for the LLM modes)
- [Poppler](https://poppler.freedesktop.org/) (for the LLM-OCR mode)

## Modes

| Mode | Description | Ollama required | Status |
|---|---|---|---|
| ⚡ Simple | Rule-based MarkItDown, fast | No | ✅ tested |
| 🧠 LLM | MarkItDown + LLM for image descriptions | Yes (multimodal model, e.g. llava) | ⚠️ untested |
| 🔍 LLM-OCR | Pages as image → LLM (ideal for scans) | Yes (multimodal model, e.g. llava) | ⚠️ untested |

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

## Installing Poppler

> ℹ️ **Only required for the LLM and LLM-OCR modes.**
> If you only intend to use the **Simple mode**, you can skip both the Poppler setup below and the Ollama installation — Simple mode runs without any external tools beyond the Python dependencies installed above.

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

## Recommended Ollama models

```bash
ollama pull llava          # general-purpose, multimodal
ollama pull llava-phi3     # smaller, faster
ollama pull llama3.2       # text-only, for Simple/text PDFs
```

## GPU acceleration with AMD (ROCm)

Ollama supports hardware acceleration on AMD GPUs via [ROCm](https://rocm.docs.amd.com/).
Before proceeding, verify that your GPU is listed as supported in the official
[ROCm hardware compatibility matrix](https://rocm.docs.amd.com/projects/install-on-linux/en/latest/reference/system-requirements.html)
and that your kernel/driver stack meets the ROCm prerequisites.

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

> ℹ️ For NVIDIA GPUs, use the standard `ollama/ollama` image together with the NVIDIA Container Toolkit instead; see the [Ollama Docker documentation](https://hub.docker.com/r/ollama/ollama).