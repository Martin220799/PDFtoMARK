"""
PDF → Markdown Converter
Cross-platform desktop app (PySide6)
Modes: Simple | LLM-based | LLM-OCR

Entry point. The application is split across several modules:
  theme.py          – colors + stylesheet
  ollama_client.py  – Ollama API helper
  converter.py      – ConvertWorker (background thread)
  widgets.py        – reusable GUI elements (DropListWidget)
  main_window.py    – MainWindow
"""

import sys

from PySide6.QtWidgets import QApplication

import theme
from main_window import MainWindow


# ── Entry point ──────────────────────────────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(theme.stylesheet())
    app.setApplicationName("PDF → Markdown")
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
