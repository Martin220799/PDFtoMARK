"""
Color palettes and the global Qt stylesheet builder.

Two themes are available:
  - "night": the original dark, colorful palette
  - "day":   a black & white (monochrome) light palette

The active theme is held in module state. Call set_theme() to switch, and
stylesheet() / color() to read the current values. Widgets that style
themselves inline should read colors through color(...) so they update when
the theme changes.
"""

# ── Palettes ─────────────────────────────────────────────────────────────────
PALETTES = {
    "night": {
        "DARK_BG":      "#1e1e2e",
        "PANEL_BG":     "#2a2a3e",
        "ACCENT":       "#7c6af7",
        "ACCENT_HOVER": "#9b8ef8",
        "ACCENT_TEXT":  "#ffffff",
        "TEXT_PRIMARY": "#e0e0f0",
        "TEXT_MUTED":   "#888aaa",
        "SUCCESS":      "#50fa7b",
        "WARNING":      "#f1fa8c",
        "ERROR_COLOR":  "#ff5555",
        "BORDER":       "#3a3a5e",
    },
    # Monochrome black & white palette.
    "day": {
        "DARK_BG":      "#ffffff",
        "PANEL_BG":     "#f2f2f2",
        "ACCENT":       "#1a1a1a",
        "ACCENT_HOVER": "#404040",
        "ACCENT_TEXT":  "#ffffff",
        "TEXT_PRIMARY": "#111111",
        "TEXT_MUTED":   "#666666",
        "SUCCESS":      "#2e2e2e",
        "WARNING":      "#555555",
        "ERROR_COLOR":  "#000000",
        "BORDER":       "#c8c8c8",
    },
}

DEFAULT_THEME = "night"
_current = DEFAULT_THEME


def available_themes():
    return list(PALETTES.keys())


def current_theme():
    return _current


def set_theme(name):
    global _current
    if name in PALETTES:
        _current = name


def palette():
    return PALETTES[_current]


def color(key):
    return PALETTES[_current][key]


# ── Stylesheet ───────────────────────────────────────────────────────────────
def build_stylesheet(c):
    return f"""
QMainWindow, QWidget {{
    background-color: {c['DARK_BG']};
    color: {c['TEXT_PRIMARY']};
    font-family: 'Segoe UI', 'Inter', 'Arial', sans-serif;
    font-size: 13px;
}}
QGroupBox {{
    border: 1px solid {c['BORDER']};
    border-radius: 8px;
    margin-top: 14px;
    padding: 12px 10px 10px 10px;
    font-weight: bold;
    color: {c['TEXT_MUTED']};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 6px;
    color: {c['ACCENT']};
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1px;
}}
QPushButton {{
    background-color: {c['ACCENT']};
    color: {c['ACCENT_TEXT']};
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
}}
QPushButton:hover {{
    background-color: {c['ACCENT_HOVER']};
}}
QPushButton:disabled {{
    background-color: {c['BORDER']};
    color: {c['TEXT_MUTED']};
}}
QPushButton#secondary {{
    background-color: {c['PANEL_BG']};
    border: 1px solid {c['BORDER']};
    color: {c['TEXT_PRIMARY']};
}}
QPushButton#secondary:hover {{
    border-color: {c['ACCENT']};
    color: {c['ACCENT']};
}}
QPushButton#danger {{
    background-color: transparent;
    border: 1px solid {c['ERROR_COLOR']};
    color: {c['ERROR_COLOR']};
}}
QPushButton#danger:hover {{
    background-color: {c['ERROR_COLOR']};
    color: {c['ACCENT_TEXT']};
}}
QComboBox {{
    background-color: {c['PANEL_BG']};
    border: 1px solid {c['BORDER']};
    border-radius: 6px;
    padding: 6px 10px;
    color: {c['TEXT_PRIMARY']};
}}
QComboBox:focus {{
    border-color: {c['ACCENT']};
}}
QComboBox::drop-down {{
    border: none;
    padding-right: 8px;
}}
QComboBox QAbstractItemView {{
    background-color: {c['PANEL_BG']};
    border: 1px solid {c['BORDER']};
    padding: 4px;
    selection-background-color: {c['ACCENT']};
    selection-color: {c['ACCENT_TEXT']};
}}
QListWidget {{
    background-color: {c['PANEL_BG']};
    border: 1px solid {c['BORDER']};
    border-radius: 8px;
    padding: 4px;
    outline: none;
}}
QListWidget::item {{
    padding: 8px 12px;
    border-radius: 4px;
    margin: 2px;
}}
QListWidget::item:selected {{
    background-color: {c['ACCENT']};
    color: {c['ACCENT_TEXT']};
}}
QListWidget::item:hover {{
    background-color: {c['BORDER']};
}}
QTextEdit {{
    background-color: {c['PANEL_BG']};
    border: 1px solid {c['BORDER']};
    border-radius: 8px;
    padding: 8px;
    color: {c['TEXT_PRIMARY']};
    font-family: 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
    font-size: 12px;
}}
QProgressBar {{
    background-color: {c['PANEL_BG']};
    border: 1px solid {c['BORDER']};
    border-radius: 4px;
    height: 8px;
    text-align: center;
}}
QProgressBar::chunk {{
    background-color: {c['ACCENT']};
    border-radius: 4px;
}}
QRadioButton {{
    color: {c['TEXT_PRIMARY']};
    spacing: 8px;
}}
QRadioButton::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 8px;
    border: 2px solid {c['BORDER']};
}}
QRadioButton::indicator:checked {{
    background-color: {c['ACCENT']};
    border-color: {c['ACCENT']};
}}
QSplitter::handle {{
    background-color: transparent;
}}
QSplitter::handle:horizontal {{
    width: 12px;
}}
QSplitter::handle:vertical {{
    height: 12px;
}}
QMenu {{
    background-color: {c['PANEL_BG']};
    border: 1px solid {c['BORDER']};
    color: {c['TEXT_PRIMARY']};
    padding: 4px;
}}
QMenu::item {{
    padding: 6px 24px;
    border-radius: 4px;
}}
QMenu::item:selected {{
    background-color: {c['ACCENT']};
    color: {c['ACCENT_TEXT']};
}}
QToolTip {{
    background-color: {c['PANEL_BG']};
    color: {c['TEXT_PRIMARY']};
    border: 1px solid {c['BORDER']};
    padding: 4px;
}}
QStatusBar {{
    background-color: {c['PANEL_BG']};
    border-top: 1px solid {c['BORDER']};
    color: {c['TEXT_MUTED']};
    font-size: 11px;
}}
QScrollBar:vertical {{
    background: {c['PANEL_BG']};
    width: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {c['BORDER']};
    border-radius: 4px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{
    background: {c['ACCENT']};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
"""


def stylesheet():
    return build_stylesheet(PALETTES[_current])
