"""
Main GUI: MainWindow.
"""

from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox,
    QProgressBar, QTextEdit, QFileDialog, QGroupBox, QRadioButton,
    QButtonGroup, QSplitter, QFrame, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

import theme
from converter import ConvertWorker
from widgets import DropListWidget, ToggleSwitch, best_emoji_font
from ollama_client import fetch_ollama_models


# ── Main GUI ─────────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF → Markdown Converter")
        self.setMinimumSize(1040, 700)
        self.resize(1240, 780)

        self._worker       = None
        self._output_dir   = str(Path.home() / "Downloads")
        self._preview_md   = {}
        self._status_state = "muted"   # "muted" | "ok" | "fail"
        self._hints        = []

        self._build_ui()
        self._refresh_models()

    # ── UI construction ────────────────────────────────────────────────────────
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 8)
        root.setSpacing(12)

        # Header
        hdr = QHBoxLayout()
        self._title = QLabel("PDF → Markdown")
        self._title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        self._title.setStyleSheet(f"color: {theme.color('ACCENT')};")
        hdr.addWidget(self._title)
        hdr.addStretch()

        # Day / Night slide toggle (centered)
        theme_box = QHBoxLayout()
        theme_box.setSpacing(6)
        # Pick a font that actually renders our symbols on this machine, then
        # pin it via stylesheet (QSS font-family takes precedence over setFont).
        emoji_fam = best_emoji_font("🕶")
        emoji_css = (f"font-family: '{emoji_fam}'; " if emoji_fam else "") + "font-size: 16px;"
        flash = QLabel("✴")   # starburst = blinding "flashbang" bright Day theme
        flash.setStyleSheet(emoji_css)
        flash.setToolTip("Day theme (flashbang)")
        theme_box.addWidget(flash)
        self._toggle = ToggleSwitch()
        self._toggle.setChecked(theme.current_theme() == "night")
        self._toggle.set_colors(
            theme.color("ACCENT"), theme.color("TEXT_MUTED"), "#ffffff"
        )
        self._toggle.setToolTip("Switch between Day and Night theme")
        self._toggle.toggled.connect(self._toggle_theme)
        theme_box.addWidget(self._toggle)
        shades = QLabel("🕶")   # sunglasses = chill dark Night theme
        shades.setStyleSheet(emoji_css)
        shades.setToolTip("Night theme (sunglasses)")
        theme_box.addWidget(shades)
        hdr.addLayout(theme_box)
        hdr.addStretch()

        self._status_dot = QLabel("●")
        self._status_dot.setStyleSheet(f"color: {theme.color('TEXT_MUTED')}; font-size: 10px;")
        self._status_label = QLabel("Ollama not connected")
        self._status_label.setStyleSheet(f"color: {theme.color('TEXT_MUTED')}; font-size: 11px;")
        hdr.addWidget(self._status_dot)
        hdr.addWidget(self._status_label)

        refresh_btn = QPushButton("⟳ Models")
        refresh_btn.setObjectName("secondary")
        refresh_btn.setFixedWidth(100)
        refresh_btn.clicked.connect(self._refresh_models)
        hdr.addWidget(refresh_btn)
        root.addLayout(hdr)

        # Separator
        self._sep = QFrame()
        self._sep.setFrameShape(QFrame.HLine)
        self._sep.setStyleSheet(f"color: {theme.color('BORDER')};")
        root.addWidget(self._sep)

        # Main splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(12)
        root.addWidget(splitter)

        # ── Left column ────────────────────────────────────────────────────────
        left = QWidget()
        left.setMinimumWidth(250)
        left_l = QVBoxLayout(left)
        left_l.setContentsMargins(0, 0, 0, 0)
        left_l.setSpacing(10)

        # Mode selection
        mode_group = QGroupBox("Conversion Mode")
        mode_l = QVBoxLayout(mode_group)
        mode_l.setSpacing(6)

        self._btn_group = QButtonGroup()
        modes = [
            ("simple",  "»  Simple",  "Rule-based via MarkItDown – fast, no LLM required"),
            ("llm",     "✦  LLM",      "MarkItDown + LLM for image descriptions (multimodal)"),
            ("llm_ocr", "⌕  LLM-OCR", "Pages → image → LLM (best for scanned PDFs)"),
        ]
        self._mode_radios = {}
        for val, label, tooltip in modes:
            rb = QRadioButton(label)
            rb.setToolTip(tooltip)
            rb.setProperty("mode_val", val)
            self._btn_group.addButton(rb)
            self._mode_radios[val] = rb
            mode_l.addWidget(rb)

            hint = QLabel(f"   {tooltip}")
            hint.setWordWrap(True)
            hint.setStyleSheet(f"color: {theme.color('TEXT_MUTED')}; font-size: 11px; margin-left: 24px;")
            self._hints.append(hint)
            mode_l.addWidget(hint)

        self._mode_radios["simple"].setChecked(True)
        left_l.addWidget(mode_group)

        # Model selection
        model_group = QGroupBox("Ollama Model")
        model_l = QVBoxLayout(model_group)

        url_row = QHBoxLayout()
        url_row.addWidget(QLabel("URL:"))
        self._ollama_url = QComboBox()
        self._ollama_url.setEditable(True)
        self._ollama_url.addItems(["http://localhost:11434"])
        url_row.addWidget(self._ollama_url)
        model_l.addLayout(url_row)

        model_row = QHBoxLayout()
        model_row.addWidget(QLabel("Model:"))
        self._model_combo = QComboBox()
        self._model_combo.addItem("(no Ollama)")
        model_row.addWidget(self._model_combo)
        model_l.addLayout(model_row)

        left_l.addWidget(model_group)

        # Output directory
        out_group = QGroupBox("Output Directory")
        out_l = QHBoxLayout(out_group)
        self._out_label = QLabel(self._output_dir)
        self._out_label.setStyleSheet(f"color: {theme.color('TEXT_MUTED')}; font-size: 11px;")
        self._out_label.setWordWrap(True)
        out_l.addWidget(self._out_label)
        choose_out = QPushButton("…")
        choose_out.setObjectName("secondary")
        choose_out.setFixedWidth(32)
        choose_out.clicked.connect(self._choose_output_dir)
        out_l.addWidget(choose_out)
        left_l.addWidget(out_group)

        left_l.addStretch()

        # Start / Stop
        btn_row = QHBoxLayout()
        self._start_btn = QPushButton("▶  Convert")
        self._start_btn.setFixedHeight(40)
        self._start_btn.clicked.connect(self._start)
        btn_row.addWidget(self._start_btn)

        self._stop_btn = QPushButton("■  Stop")
        self._stop_btn.setObjectName("danger")
        self._stop_btn.setFixedHeight(40)
        self._stop_btn.setEnabled(False)
        self._stop_btn.clicked.connect(self._stop)
        btn_row.addWidget(self._stop_btn)
        left_l.addLayout(btn_row)

        self._progress = QProgressBar()
        self._progress.setValue(0)
        left_l.addWidget(self._progress)

        splitter.addWidget(left)

        # ── Middle column: file list ───────────────────────────────────────────
        mid = QWidget()
        mid.setMinimumWidth(260)
        mid_l = QVBoxLayout(mid)
        mid_l.setContentsMargins(0, 0, 0, 0)
        mid_l.setSpacing(6)

        self._file_list = DropListWidget()
        self._file_list.setPlaceholderText("Drag PDFs here or click '+ Add' …")
        self._file_list.currentItemChanged.connect(self._on_file_selected)

        file_hdr = QHBoxLayout()
        file_hdr.addWidget(QLabel("▤  PDF Files"))
        file_hdr.addStretch()

        add_btn = QPushButton("+ Add")
        add_btn.setObjectName("secondary")
        add_btn.setFixedHeight(28)
        add_btn.clicked.connect(lambda: self._file_list.add_files_from_dialog())
        file_hdr.addWidget(add_btn)

        rm_btn = QPushButton("− Remove")
        rm_btn.setObjectName("secondary")
        rm_btn.setFixedHeight(28)
        rm_btn.clicked.connect(self._file_list.remove_selected)
        file_hdr.addWidget(rm_btn)

        clear_btn = QPushButton("✕ Clear")
        clear_btn.setObjectName("danger")
        clear_btn.setFixedHeight(28)
        clear_btn.clicked.connect(self._file_list.clear_all)
        file_hdr.addWidget(clear_btn)
        mid_l.addLayout(file_hdr)
        mid_l.addWidget(self._file_list)

        splitter.addWidget(mid)

        # ── Right column: log + preview ────────────────────────────────────────
        right = QWidget()
        right.setMinimumWidth(340)
        right_l = QVBoxLayout(right)
        right_l.setContentsMargins(0, 0, 0, 0)
        right_l.setSpacing(6)

        right_splitter = QSplitter(Qt.Vertical)
        right_splitter.setChildrenCollapsible(False)
        right_splitter.setHandleWidth(12)

        # Log
        log_widget = QWidget()
        log_l = QVBoxLayout(log_widget)
        log_l.setContentsMargins(0, 0, 0, 0)
        log_l.setSpacing(6)
        log_l.addWidget(QLabel("≡  Log"))
        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setMinimumHeight(120)
        log_l.addWidget(self._log)
        right_splitter.addWidget(log_widget)

        # Preview
        prev_widget = QWidget()
        prev_l = QVBoxLayout(prev_widget)
        prev_l.setContentsMargins(0, 0, 0, 0)
        prev_l.setSpacing(6)
        prev_l.addWidget(QLabel("◉  Markdown Preview"))
        self._preview = QTextEdit()
        self._preview.setReadOnly(True)
        self._preview.setPlaceholderText("Select a file from the list …")
        prev_l.addWidget(self._preview)
        right_splitter.addWidget(prev_widget)

        # Give the log a fixed-ish slice up top and let the preview take the rest,
        # so the log doesn't start collapsed at the bottom.
        right_splitter.setStretchFactor(0, 0)
        right_splitter.setStretchFactor(1, 1)
        right_splitter.setSizes([200, 560])

        right_l.addWidget(right_splitter)
        splitter.addWidget(right)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 2)
        splitter.setSizes([280, 380, 500])

        # Status bar
        self.statusBar().showMessage("Ready")

    # ── Theme ────────────────────────────────────────────────────────────────
    def _toggle_theme(self, checked):
        theme.set_theme("night" if checked else "day")
        self._apply_theme()

    def _apply_theme(self):
        app = QApplication.instance()
        if app:
            app.setStyleSheet(theme.stylesheet())
        # Re-apply the inline-styled widgets that don't pick up the global sheet.
        self._title.setStyleSheet(f"color: {theme.color('ACCENT')};")
        self._sep.setStyleSheet(f"color: {theme.color('BORDER')};")
        self._out_label.setStyleSheet(f"color: {theme.color('TEXT_MUTED')}; font-size: 11px;")
        for h in self._hints:
            h.setStyleSheet(f"color: {theme.color('TEXT_MUTED')}; font-size: 11px; margin-left: 24px;")
        self._toggle.set_colors(theme.color("ACCENT"), theme.color("TEXT_MUTED"), "#ffffff")
        self._apply_status_style()
        self._file_list.restyle()

    def _apply_status_style(self):
        if self._status_state == "ok":
            c = theme.color("SUCCESS")
        elif self._status_state == "fail":
            c = theme.color("ERROR_COLOR")
        else:
            c = theme.color("TEXT_MUTED")
        self._status_dot.setStyleSheet(f"color: {c}; font-size: 10px;")
        self._status_label.setStyleSheet(f"color: {c}; font-size: 11px;")

    # ── Logic ────────────────────────────────────────────────────────────────
    def _refresh_models(self):
        url = self._ollama_url.currentText().strip()
        models = fetch_ollama_models(url)
        self._model_combo.clear()
        if models:
            self._model_combo.addItems(models)
            self._status_state = "ok"
            self._status_label.setText(f"Ollama connected  ({len(models)} models)")
            self.statusBar().showMessage(f"{len(models)} models loaded.")
        else:
            self._model_combo.addItem("(no Ollama)")
            self._status_state = "fail"
            self._status_label.setText("Ollama not connected")
            self.statusBar().showMessage("Ollama not reachable – Simple mode available.")
        self._apply_status_style()

    def _choose_output_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Output Directory", self._output_dir)
        if d:
            self._output_dir = d
            self._out_label.setText(d)

    def _get_mode(self):
        for rb in self._mode_radios.values():
            if rb.isChecked():
                return rb.property("mode_val")
        return "simple"

    def _start(self):
        files = self._file_list.get_files()
        if not files:
            QMessageBox.warning(self, "No Files", "Please add PDFs first.")
            return

        mode  = self._get_mode()
        model = self._model_combo.currentText()
        url   = self._ollama_url.currentText().strip()

        if mode in ("llm", "llm_ocr") and model == "(no Ollama)":
            QMessageBox.warning(
                self, "No Model",
                "LLM modes require a running Ollama and a selected model."
            )
            return

        self._progress.setMaximum(len(files))
        self._progress.setValue(0)
        self._start_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)
        self._log.clear()
        self._preview_md.clear()
        self._preview.clear()

        self._worker = ConvertWorker(files, mode, model, url, self._output_dir)
        self._worker.progress.connect(self._on_progress)
        self._worker.file_done.connect(self._on_file_done)
        self._worker.log_message.connect(self._on_log)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

        self.statusBar().showMessage(f"Converting {len(files)} file(s) …")

    def _stop(self):
        if self._worker:
            self._worker.stop()
        self._stop_btn.setEnabled(False)
        self.statusBar().showMessage("Stopping …")

    def _on_progress(self, current, total):
        self._progress.setValue(current)

    def _on_file_done(self, fpath, result, success):
        self._file_list.mark_done(fpath, success)
        if success:
            self._preview_md[fpath] = result
            # Show the preview right away: if this file is selected, refresh it;
            # otherwise select it so the user sees a result without an extra click.
            current = self._file_list.currentItem()
            if current is not None and current.data(Qt.UserRole) == fpath:
                self._show_preview(fpath)
            elif current is None:
                self._select_file(fpath)

    def _on_log(self, msg):
        self._log.append(msg)

    def _on_finished(self):
        self._start_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        done = sum(1 for v in self._preview_md.values())
        total = len(self._file_list.get_files())
        self.statusBar().showMessage(
            f"Done: {done}/{total} successful → {self._output_dir}"
        )

    def _on_file_selected(self, current, previous):
        if current is None:
            return
        fpath = current.data(Qt.UserRole)
        if fpath in self._preview_md:
            self._show_preview(fpath)
        else:
            self._preview.setPlaceholderText("Not converted yet …")
            self._preview.clear()

    # ── Preview helpers ────────────────────────────────────────────────────────
    def _show_preview(self, fpath):
        """Render the converted Markdown of a file in the preview pane."""
        self._preview.setMarkdown(self._preview_md.get(fpath, ""))

    def _select_file(self, fpath):
        """Select the list item for a given path (triggers the preview)."""
        for i in range(self._file_list.count()):
            item = self._file_list.item(i)
            if item.data(Qt.UserRole) == fpath:
                self._file_list.setCurrentItem(item)
                self._show_preview(fpath)
                break
