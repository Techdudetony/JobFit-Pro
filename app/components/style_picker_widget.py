"""
StylePickerWidget
------------------

A card grid widget for selecting resume export styles.
Displays 2-per-row clickable cards, each with an SVG thumbnail
preview and style name/description below.

Selecting a card highlights it with the app accent color and
emits styleSelected(str) with the style key.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QSizePolicy, QScrollArea, QFrame,
)
from PyQt6.QtCore import pyqtSignal, Qt, QSize
from PyQt6.QtGui import QPainter, QColor, QPen, QFont
from PyQt6.QtCore import QByteArray
try:
    from PyQt6.QtSvgWidgets import QSvgWidget
    _SVG_AVAILABLE = True
except ImportError:
    QSvgWidget = None
    _SVG_AVAILABLE = False


# ── Style definitions ────────────────────────────────────────────────────────
STYLE_DEFS = [
    {
        "key":   "prestige",
        "name":  "Prestige",
        "desc":  "Your signature style",
        "accent": None,
        "header_align": "center",
        "font_style": "sans",
    },
    {
        "key":   "swiss",
        "name":  "Swiss",
        "desc":  "Minimal, clean, no color",
        "accent": None,
        "header_align": "left",
        "font_style": "sans",
    },
    {
        "key":   "spearmint",
        "name":  "Spearmint",
        "desc":  "Green accent, modern",
        "accent": "#2E8B6E",
        "header_align": "left",
        "font_style": "sans",
    },
    {
        "key":   "coral",
        "name":  "Coral",
        "desc":  "Serif, warm, centered header",
        "accent": "#C0533A",
        "header_align": "center",
        "font_style": "serif",
    },
    {
        "key":   "modern_writer",
        "name":  "Modern Writer",
        "desc":  "Navy, bold, corporate",
        "accent": "#1E3A5F",
        "header_align": "left",
        "font_style": "sans",
    },
]


# ── SVG thumbnail generator ──────────────────────────────────────────────────
def _build_svg(style: dict) -> bytes:
    """
    Generate an SVG miniature resume thumbnail for a given style definition.
    Dimensions: 160 × 210 (US Letter aspect ratio).
    """
    W, H = 160, 210
    accent  = style.get("accent") or "#444444"
    is_center = style["header_align"] == "center"
    is_serif  = style["font_style"] == "serif"
    font_fam  = "Georgia, serif" if is_serif else "Arial, sans-serif"
    txt_color = "#222222"
    rule_color = accent if style["accent"] else "#AAAAAA"
    name_color = accent if style["accent"] else "#111111"

    # Spearmint: left border on headings
    # Coral: bottom border on headings in accent
    # Swiss: grey rules
    # ModernWriter: navy large name, spaced caps
    # Prestige: centered header, black rules

    x_left  = 12
    x_right = W - 12
    content_w = x_right - x_left

    lines = []

    def text(x, y, content, size=5, bold=False, italic=False,
             color=txt_color, anchor="start"):
        weight = "bold" if bold else "normal"
        style_attr = "italic" if italic else "normal"
        lines.append(
            f'<text x="{x}" y="{y}" font-family="{font_fam}" '
            f'font-size="{size}" font-weight="{weight}" '
            f'font-style="{style_attr}" fill="{color}" '
            f'text-anchor="{anchor}">{content}</text>'
        )

    def hrule(y, color="#CCCCCC", stroke_w=0.5):
        lines.append(
            f'<line x1="{x_left}" y1="{y}" x2="{x_right}" y2="{y}" '
            f'stroke="{color}" stroke-width="{stroke_w}"/>'
        )

    def left_bar(y, h=7, color="#2E8B6E"):
        lines.append(
            f'<rect x="{x_left}" y="{y - h + 1}" width="2" height="{h}" fill="{color}"/>'
        )

    def rect_line(x, y, w, h=1.2, color="#DDDDDD"):
        lines.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{color}" rx="0.5"/>')

    # ── Background ──
    lines.append(f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>')

    # ── Name ──
    name_x = W // 2 if is_center else x_left
    name_anchor = "middle" if is_center else "start"
    name_size = 10 if style["key"] == "modern_writer" else 9

    if style["key"] == "modern_writer":
        text(name_x, 22, "YOUR NAME", size=name_size, bold=True,
             color=accent, anchor=name_anchor)
    else:
        text(name_x, 20, "Your Name", size=name_size, bold=True,
             color=name_color, anchor=name_anchor)

    # ── Title / subtitle ──
    subtitle_color = accent if style["accent"] and style["key"] != "coral" else "#666666"
    if style["key"] == "coral":
        subtitle_color = accent
    text(name_x, 27, "Job Title  ·  City, State", size=4.5,
         color=subtitle_color, anchor=name_anchor)

    # ── Contact row ──
    contact_y = 33
    if is_center:
        text(W // 2, contact_y, "email@email.com  |  (555) 555-5555  |  linkedin.com/in/you",
             size=3.5, color="#888888", anchor="middle")
    else:
        text(x_left, contact_y, "email@email.com   (555) 555-5555   linkedin.com/in/you",
             size=3.5, color="#888888")

    # ── Header rule ──
    rule_y = 37
    if style["key"] == "modern_writer":
        lines.append(
            f'<line x1="{x_left}" y1="{rule_y}" x2="{x_right}" y2="{rule_y}" '
            f'stroke="{accent}" stroke-width="1.5"/>'
        )
    else:
        hrule(rule_y, color=rule_color if style["accent"] else "#888888",
              stroke_w=0.7 if not style["accent"] else 0.5)

    # ── Sections ──
    sections = [
        ("SUMMARY",    43,  [70, 55, 65, 50]),
        ("EXPERIENCE", 73,  [80, 60, 70, 65, 55]),
        ("SKILLS",     117, [60, 50, 70]),
        ("EDUCATION",  140, [80, 55]),
    ]

    for sec_name, sec_y, line_widths in sections:
        # Section heading
        if style["key"] == "spearmint":
            left_bar(sec_y, h=6, color=accent)
            text(x_left + 4, sec_y, sec_name, size=4.5, bold=True, color=accent)
        elif style["key"] in ("coral", "modern_writer"):
            text(x_left, sec_y, sec_name, size=4.5, bold=True, color=accent)
            hrule(sec_y + 2, color=accent, stroke_w=0.6)
        else:
            text(x_left, sec_y, sec_name, size=4.5, bold=True, color="#111111")
            hrule(sec_y + 2, color=rule_color, stroke_w=0.5)

        # Content lines (simulated text blocks)
        line_y = sec_y + 8
        for i, lw in enumerate(line_widths):
            # Every other section gets a job title line
            if sec_name == "EXPERIENCE" and i == 0:
                rect_line(x_left, line_y, lw, h=1.8, color="#444444")
                # Date right-aligned
                rect_line(x_right - 20, line_y, 20, h=1.4, color="#AAAAAA")
                line_y += 3.5
                rect_line(x_left, line_y, lw - 20, h=1.2,
                          color=accent if style["accent"] else "#888888")
                line_y += 3.5
            else:
                rect_line(x_left + (4 if sec_name in ("EXPERIENCE", "SUMMARY") else 0),
                          line_y, lw, h=1.2)
                line_y += 3.2

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
        + "".join(lines)
        + "</svg>"
    )
    return svg.encode("utf-8")


# ── Style card ───────────────────────────────────────────────────────────────
class _StyleCard(QWidget):
    clicked = pyqtSignal(str)   # emits style key

    def __init__(self, style_def: dict, parent=None):
        super().__init__(parent)
        self._key      = style_def["key"]
        self._selected = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(QSize(170, 250))
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setObjectName("styleCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # SVG thumbnail
        svg_bytes = _build_svg(style_def)
        if _SVG_AVAILABLE:
            self._svg = QSvgWidget(self)
            self._svg.load(QByteArray(svg_bytes))
            self._svg.setFixedSize(QSize(154, 200))
            layout.addWidget(self._svg)
        else:
            # Fallback: plain label if SVG renderer unavailable
            fallback = QLabel("Preview unavailable")
            fallback.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fallback.setFixedSize(QSize(154, 200))
            fallback.setStyleSheet("color: #64748B; font-size: 9pt;")
            layout.addWidget(fallback)

        # Name label
        self._name_lbl = QLabel(style_def["name"])
        self._name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._name_lbl.setProperty("styleCardName", True)
        layout.addWidget(self._name_lbl)

        # Desc label
        self._desc_lbl = QLabel(style_def["desc"])
        self._desc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._desc_lbl.setProperty("styleCardDesc", True)
        layout.addWidget(self._desc_lbl)

    def set_selected(self, selected: bool):
        self._selected = selected
        self.setProperty("selected", "true" if selected else "false")
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def mousePressEvent(self, event):
        self.clicked.emit(self._key)

    def key(self) -> str:
        return self._key


# ── Grid widget ──────────────────────────────────────────────────────────────
class StylePickerWidget(QWidget):
    styleSelected = pyqtSignal(str)   # emits style key on selection change

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cards: list[_StyleCard] = []
        self._selected_key = "prestige"
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        grid = QGridLayout()
        grid.setSpacing(12)

        for idx, style_def in enumerate(STYLE_DEFS):
            card = _StyleCard(style_def, self)
            card.clicked.connect(self._on_card_clicked)
            self._cards.append(card)
            row = idx // 2
            col = idx % 2
            grid.addWidget(card, row, col, Qt.AlignmentFlag.AlignTop)

        outer.addLayout(grid)

        # Select default
        self._select("prestige")

    def _on_card_clicked(self, key: str):
        self._select(key)
        self.styleSelected.emit(key)

    def _select(self, key: str):
        self._selected_key = key
        for card in self._cards:
            card.set_selected(card.key() == key)

    def selected_key(self) -> str:
        return self._selected_key

    def set_selected(self, key: str):
        self._select(key)