"""
Worker thread for the PDF → Markdown conversion.
Modes: Simple | LLM-based | LLM-OCR
"""

import base64
import io
from pathlib import Path

import requests
from PySide6.QtCore import QThread, Signal


class ConvertWorker(QThread):
    progress    = Signal(int, int)        # current, total
    file_done   = Signal(str, str, bool)  # path, result_md, success
    log_message = Signal(str)
    finished    = Signal()

    def __init__(self, files, mode, model, ollama_url, output_dir):
        super().__init__()
        self.files      = files
        self.mode       = mode       # "simple" | "llm" | "llm_ocr"
        self.model      = model
        self.ollama_url = ollama_url
        self.output_dir = output_dir
        self._stop      = False

    def stop(self):
        self._stop = True

    def run(self):
        total = len(self.files)
        for i, fpath in enumerate(self.files):
            if self._stop:
                break
            self.log_message.emit(f"▶ Processing: {Path(fpath).name}")
            try:
                md = self._convert(fpath)
                if not (md and md.strip()):
                    # Nothing was extracted. For the text-based modes this
                    # almost always means a scanned/image-only PDF (no text
                    # layer) — point the user at LLM-OCR instead of writing an
                    # empty .md and silently reporting success.
                    hint = self._empty_hint()
                    self.log_message.emit(f"  ✗ No content extracted. {hint}")
                    self.file_done.emit(
                        fpath, f"No content could be extracted.\n\n{hint}", False
                    )
                else:
                    out_name = Path(fpath).stem + ".md"
                    out_path = Path(self.output_dir) / out_name
                    out_path.write_text(md, encoding="utf-8")
                    self.file_done.emit(fpath, md, True)
                    self.log_message.emit(f"  ✓ Saved: {out_path.name}")
            except Exception as e:
                self.file_done.emit(fpath, str(e), False)
                self.log_message.emit(f"  ✗ Error: {e}")
            self.progress.emit(i + 1, total)
        self.finished.emit()

    def _empty_hint(self):
        """A mode-specific explanation for why a conversion produced no text."""
        if self.mode in ("simple", "llm"):
            return (
                "This looks like a scanned / image-only PDF (no text layer). "
                "Try the 'LLM-OCR' mode, which reads each page as an image."
            )
        return (
            "The model returned no text for any page. Check that the selected "
            "model is multimodal (vision-capable) and that Ollama is running."
        )

    def _convert(self, fpath):
        if self.mode == "simple":
            return self._simple(fpath)
        elif self.mode == "llm":
            return self._llm(fpath)
        else:
            return self._llm_ocr(fpath)

    def _simple(self, fpath):
        from markitdown import MarkItDown
        md_conv = MarkItDown()
        result  = md_conv.convert(fpath)
        return result.text_content

    def _llm(self, fpath):
        from markitdown import MarkItDown
        from openai import OpenAI
        client = OpenAI(
            base_url=f"{self.ollama_url}/v1",
            api_key="ollama"
        )
        md_conv = MarkItDown(llm_client=client, llm_model=self.model)
        result  = md_conv.convert(fpath)
        return result.text_content

    def _llm_ocr(self, fpath):
        try:
            from pdf2image import convert_from_path
        except ImportError:
            raise RuntimeError("pdf2image not installed. Please run: pip install pdf2image")

        pages = convert_from_path(fpath, dpi=200)
        md_parts = []

        prompt = (
            "Extract the full content of this page as structured Markdown. "
            "Use #/##/### for headings, Markdown tables for tables, "
            "and lists for bullet points. Output only Markdown, no commentary."
        )

        for i, page in enumerate(pages):
            if self._stop:
                break
            self.log_message.emit(f"    Page {i+1}/{len(pages)} → LLM …")
            buf = io.BytesIO()
            page.save(buf, format="PNG")
            img_b64 = base64.b64encode(buf.getvalue()).decode()

            # Ollama's native /api/chat is used (not the OpenAI-compatible
            # endpoint) because it accepts `options.num_ctx`. A rendered page
            # image consumes ~3000 tokens, so the default 4096-token context
            # leaves no room for the answer — and multimodal "thinking" models
            # (e.g. qwen3-vl) overflow it while reasoning and return empty
            # content. A larger context gives room for image + reasoning +
            # output. Reasoning goes to a separate `thinking` field, so we fall
            # back to it if `content` comes back empty.
            payload = {
                "model": self.model,
                "messages": [{
                    "role": "user",
                    "content": prompt,
                    "images": [img_b64],
                }],
                "stream": False,
                "options": {"num_ctx": 8192, "num_predict": 4096},
            }
            r = requests.post(
                f"{self.ollama_url}/api/chat",
                json=payload,
                timeout=300
            )
            r.raise_for_status()
            msg = r.json().get("message", {})
            content = (msg.get("content") or "").strip() or (msg.get("thinking") or "").strip()
            md_parts.append(f"<!-- Page {i+1} -->\n\n{content}")

        return "\n\n---\n\n".join(md_parts)
