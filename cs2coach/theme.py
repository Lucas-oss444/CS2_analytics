import json
from pathlib import Path

THEMES = {
    "escuro": ("Escuro", "#111318", "#1a1d23", "#272b33", "#e8e8e8", "#7d8590", "#f5a623"),
    "claro": ("Claro", "#f4f5f7", "#ffffff", "#dde1e6", "#1f2328", "#636c76", "#d97706"),
    "meia_noite": ("Meia-noite", "#0b1220", "#121b2e", "#1f2a44", "#e6edf7", "#8193b2", "#4cc2ff"),
    "oled": ("OLED (preto total)", "#000000", "#0b0b0b", "#1c1c1c", "#f2f2f2", "#8a8a8a", "#f5a623"),
    "roxo": ("Roxo", "#16111f", "#201a2d", "#33294a", "#ece6f7", "#9a8cb8", "#b388ff"),
    "floresta": ("Floresta", "#0f1612", "#16201a", "#25342b", "#e4efe7", "#82a08c", "#4ade80"),
    "vermelho": ("Vermelho", "#160f10", "#211718", "#3a2628", "#f3e7e8", "#a88b8e", "#ff5c5c"),
    "areia": ("Areia (claro quente)", "#f3ede3", "#fbf8f2", "#e2d8c8", "#2b241b", "#7a6c58", "#c2410c"),
}
DEFAULT = "escuro"


def chosen():
    try:
        key = json.loads((Path.home() / ".cs2coach" / "config.json").read_text(encoding="utf-8")).get("theme")
    except (OSError, ValueError, AttributeError):
        key = None
    return key if key in THEMES else DEFAULT


def mix(a, b, t):
    ca, cb = (int(a[i:i + 2], 16) for i in (1, 3, 5)), (int(b[i:i + 2], 16) for i in (1, 3, 5))
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(ca, cb))


def light(bg):
    return sum(int(bg[i:i + 2], 16) for i in (1, 3, 5)) > 382


THEME = chosen()
NAME, BG, PANEL, LINE, TEXT, MUTED, ACCENT = THEMES[THEME]
LIGHT = light(BG)
GOOD, BAD = ("#1a7f37", "#cf222e") if LIGHT else ("#3fb950", "#f85149")
CT_COLOR, T_COLOR = ("#0969da", "#9a6700") if LIGHT else ("#58a6ff", "#d29922")
BUTTON, HOVER, PRESSED = mix(PANEL, TEXT, 0.06), mix(PANEL, TEXT, 0.12), mix(BG, TEXT, 0.03)
BORDER, INPUT = mix(PANEL, TEXT, 0.18), mix(PANEL, TEXT, 0.04)
SOFT, BAR = mix(TEXT, MUTED, 0.35), mix(PANEL, TEXT, 0.2)
SELECTED = mix(PANEL, ACCENT, 0.14)
ACCENT_HOVER, ACCENT_PRESSED = mix(ACCENT, "#ffffff", 0.2), mix(ACCENT, "#000000", 0.15)
ON_ACCENT = "#ffffff" if LIGHT else BG


def fs(size):
    return round(size * 1.12)
