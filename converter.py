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
                # Save
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

        for i, page in enumerate(pages):
            if self._stop:
                break
            self.log_message.emit(f"    Page {i+1}/{len(pages)} → LLM …")
            buf = io.BytesIO()
            page.save(buf, format="PNG")
            img_b64 = base64.b64encode(buf.getvalue()).decode()

            payload = {
                "model": self.model,
                "messages": [{
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Extract the full content of this page as structured Markdown. "
                                "Use #/##/### for headings, Markdown tables for tables, "
                                "and lists for bullet points. Output only Markdown, no commentary."
                            )
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{img_b64}"}
                        }
                    ]
                }],
                "stream": False
            }
            r = requests.post(
                f"{self.ollama_url}/v1/chat/completions",
                json=payload,
                timeout=120
            )
            r.raise_for_status()
            content = r.json()["choices"][0]["message"]["content"]
            md_parts.append(f"<!-- Page {i+1} -->\n\n{content}")

        return "\n\n---\n\n".join(md_parts)
