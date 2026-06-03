"""
Reusable GUI elements.
"""

from pathlib import Path

from PySide6.QtWidgets import (
    QListWidget, QListWidgetItem, QFileDialog, QAbstractItemView, QCheckBox
)
from PySide6.QtCore import Qt, Signal, QRect, QSize
from PySide6.QtGui import (
    QDragEnterEvent, QDropEvent, QColor, QPainter, QImage, QFont, QFontDatabase
)

import theme

# Custom item-data role storing a file's conversion status.
STATUS_ROLE = Qt.UserRole + 1


def best_emoji_font(test_char):
    """Return the first installed font family that actually *renders* test_char.

    Qt's stylesheet font-family doesn't accept fallback lists, and some emoji
    fonts (e.g. Noto Color Emoji / COLRv1) draw nothing on certain Qt+FreeType
    builds. We probe candidates by rendering the glyph and checking for pixels,
    so we end up with a single family name that is guaranteed to show.
    """
    prefs = [
        "Segoe UI Emoji", "Apple Color Emoji", "Noto Emoji",
        "Symbola", "Noto Sans Symbols 2", "Noto Color Emoji",
    ]
    available = set(QFontDatabase.families())
    white = QColor("white").rgb()

    def renders(family):
        img = QImage(28, 28, QImage.Format_ARGB32)
        img.fill(QColor("white"))
        f = QFont(family)
        f.setPixelSize(22)
        p = QPainter(img)
        p.setFont(f)
        p.drawText(img.rect(), Qt.AlignCenter, test_char)
        p.end()
        return any(
            img.pixelColor(x, y).rgb() != white
            for y in range(28) for x in range(28)
        )

    for fam in prefs:
        if fam in available and renders(fam):
            return fam
    for fam in prefs:
        if fam in available:
            return fam
    return ""


# ── Day / Night slide switch ─────────────────────────────────────────────────
class ToggleSwitch(QCheckBox):
    """A small iOS-style slide switch (a checkable button)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.NoFocus)
        self._track_on  = QColor("#7c6af7")
        self._track_off = QColor("#888aaa")
        self._knob      = QColor("#ffffff")

    def set_colors(self, track_on, track_off, knob):
        self._track_on  = QColor(track_on)
        self._track_off = QColor(track_off)
        self._knob      = QColor(knob)
        self.update()

    def sizeHint(self):
        return QSize(52, 28)

    def hitButton(self, pos):
        return self.rect().contains(pos)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = self.rect()
        track_h = r.height() - 6
        track = QRect(2, (r.height() - track_h) // 2, r.width() - 4, track_h)
        radius = track_h / 2
        p.setPen(Qt.NoPen)
        p.setBrush(self._track_on if self.isChecked() else self._track_off)
        p.drawRoundedRect(track, radius, radius)

        d = track_h - 4
        x = (track.right() - d - 1) if self.isChecked() else (track.left() + 2)
        y = track.top() + 2
        p.setBrush(self._knob)
        p.drawEllipse(x, y, d, d)
        p.end()


# ── Drag & drop file list ────────────────────────────────────────────────────
class DropListWidget(QListWidget):
    files_added = Signal(list)

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DropOnly)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self._files = []
        self._placeholder = ""

    def setPlaceholderText(self, text):
        self._placeholder = text
        self.viewport().update()

    def paintEvent(self, e):
        super().paintEvent(e)
        if self.count() == 0 and self._placeholder:
            painter = QPainter(self.viewport())
            painter.setPen(QColor(theme.color("TEXT_MUTED")))
            painter.drawText(self.viewport().rect(), Qt.AlignCenter, self._placeholder)
            painter.end()

    def dragEnterEvent(self, e: QDragEnterEvent):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dragMoveEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e: QDropEvent):
        paths = []
        for url in e.mimeData().urls():
            p = url.toLocalFile()
            if p.lower().endswith(".pdf") and p not in self._files:
                paths.append(p)
        if paths:
            self._add_files(paths)
            self.files_added.emit(paths)

    def add_files_from_dialog(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Select PDFs", "", "PDF Files (*.pdf)"
        )
        new = [p for p in paths if p not in self._files]
        if new:
            self._add_files(new)
            self.files_added.emit(new)

    def _add_files(self, paths):
        for p in paths:
            self._files.append(p)
            name = Path(p).name
            size = Path(p).stat().st_size / 1024
            item = QListWidgetItem(f"  ▪ {name}  ({size:.0f} KB)")
            item.setData(Qt.UserRole, p)
            item.setData(STATUS_ROLE, "pending")
            item.setForeground(QColor(theme.color("TEXT_PRIMARY")))
            self.addItem(item)

    def remove_selected(self):
        for item in self.selectedItems():
            p = item.data(Qt.UserRole)
            if p in self._files:
                self._files.remove(p)
            self.takeItem(self.row(item))

    def clear_all(self):
        self._files.clear()
        self.clear()

    def get_files(self):
        return list(self._files)

    def mark_done(self, fpath, success):
        for i in range(self.count()):
            item = self.item(i)
            if item.data(Qt.UserRole) == fpath:
                name = Path(fpath).name
                size = Path(fpath).stat().st_size / 1024
                item.setData(STATUS_ROLE, "ok" if success else "fail")
                if success:
                    item.setText(f"  ✓ {name}  ({size:.0f} KB)")
                    item.setForeground(QColor(theme.color("SUCCESS")))
                else:
                    item.setText(f"  ✗ {name}  ({size:.0f} KB)")
                    item.setForeground(QColor(theme.color("ERROR_COLOR")))
                break

    def restyle(self):
        """Re-apply item colors for the current theme (call after a theme switch)."""
        for i in range(self.count()):
            item = self.item(i)
            status = item.data(STATUS_ROLE)
            if status == "ok":
                item.setForeground(QColor(theme.color("SUCCESS")))
            elif status == "fail":
                item.setForeground(QColor(theme.color("ERROR_COLOR")))
            else:
                item.setForeground(QColor(theme.color("TEXT_PRIMARY")))
        self.viewport().update()
