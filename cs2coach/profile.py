import math
import os
from dataclasses import dataclass

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QFont, QFontMetricsF, QImage, QLinearGradient, QPainter,
                           QPainterPath, QPen, QPixmap)
from PySide6.QtGui import QFontDatabase, QPolygonF
from PySide6.QtWidgets import QWidget

from .coach import num as n
from .storage import HOME
from .theme import TEXT

PHOTO = HOME / "avatar.png"
MAX_PHOTO_BYTES = 15 * 1024 ** 2
NAME_STYLES = [("normal", "Normal"), ("neon", "Neon"), ("rainbow", "Neon arco-íris")]
COLORS = ["#f5a623", "#58a6ff", "#3fb950", "#f85149", "#a371f7", "#39c5cf"]
NEON_COLORS = ["#00e5ff", "#ff2bd6", "#39ff14", "#ffe600", "#ff8a00", "#ff3355", "#b026ff", "#ffffff"]
FONT_CHOICES = ["Segoe UI", "Bahnschrift", "Segoe UI Black", "Trebuchet MS", "Georgia", "Consolas",
                "Impact", "Segoe Script", "Cascadia Code", "Comic Sans MS"]


@dataclass
class Border:
    key: str
    name: str
    colors: tuple = ()
    unlock: str = ""
    glow: str = ""


BORDERS = [
    Border("none", "Sem borda"),
    Border("classic", "Clássica"),
    Border("neon", "Neon", ("#00e5ff", "#ff2bd6", "#00e5ff"), glow="#00e5ff"),
    Border("ice", "Gelo", ("#ffffff", "#8fd3ff", "#3a8dde", "#ffffff"), glow="#8fd3ff"),
    Border("fire", "Fogo", ("#ffe14d", "#ff7a00", "#ff2a00", "#ffe14d"), glow="#ff6a00"),
    Border("veteran", "Veterano", ("#f0f3f6", "#8b949e", "#4a5058", "#f0f3f6"), "Analise 10 partidas", "#c9d1d9"),
    Border("gold", "Ouro", ("#fff6c2", "#e8b923", "#8a6100", "#fff6c2"), "Rating 1.30+ em uma partida", "#ffcc33"),
    Border("ace", "Ace", ("#f5a623", "#f85149", "#a371f7", "#39c5cf", "#f5a623"), "Faça um ACE", "#f85149"),
    Border("galaxy", "Galáxia", ("#2b1055", "#7597de", "#c86dd7", "#2b1055"), glow="#7b5cff"),
    Border("electric", "Elétrico", ("#e0fbff", "#00b4ff", "#e0fbff", "#00b4ff", "#e0fbff"), glow="#00b4ff"),
    Border("sakura", "Sakura", ("#ffe4ef", "#ff8fb8", "#ffd1e3", "#ff8fb8", "#ffe4ef"), glow="#ff8fb8"),
    Border("toxic", "Tóxico", ("#c6ff00", "#39ff14", "#0f9d58", "#c6ff00"), "HS de 60%+ numa partida (10+ kills)", "#39ff14"),
    Border("diamond", "Diamante", ("#ffffff", "#b9f2ff", "#5ad1ff", "#ffffff", "#b9f2ff"), "Rating 1.50+ numa partida", "#9be7ff"),
    Border("ocean", "Oceano", ("#0a3d62", "#1e90ff", "#7fdbff", "#1e90ff", "#0a3d62"), glow="#1e90ff"),
    Border("sunset", "Pôr do sol", ("#ff5e62", "#ff9966", "#ffd86f", "#ff9966", "#ff5e62"), glow="#ff8a5c"),
    Border("matrix", "Matrix", ("#003b00", "#00ff41", "#008f11", "#00ff41", "#003b00"), glow="#00ff41"),
    Border("quad", "Quad", ("#ff6b6b", "#c92a2a", "#ff6b6b", "#c92a2a", "#ff6b6b"), "Faça um 4K", "#ff4d4d"),
    Border("clutch", "Clutch", ("#d0b3ff", "#7b2ff7", "#2d0b5a", "#7b2ff7", "#d0b3ff"), "Vença um clutch 1v2 ou maior", "#9b5cff"),
    Border("wall", "Muralha", ("#c9ced6", "#6e7681", "#3b4048", "#6e7681", "#c9ced6"), "Sobreviva a 45%+ dos rounds numa partida",
           "#8b949e"),
    Border("carry", "Carregador", ("#ffd43b", "#f76707", "#ffd43b", "#f76707", "#ffd43b"), "ADR 100+ numa partida", "#ff922b"),
    Border("opener", "Abridor", ("#ffc9c9", "#e03131", "#ff8787", "#e03131", "#ffc9c9"),
           "Vença 65%+ das aberturas numa partida (6+ duelos)", "#fa5252"),
    Border("flashbang", "Flashbang", ("#ffffff", "#fff3bf", "#ffffff", "#fff3bf", "#ffffff"),
           "Cegue 1+ inimigo por flash numa partida (6+ flashes)", "#fff9db"),
    Border("marathon", "Maratonista", ("#c3fae8", "#12b886", "#087f5b", "#12b886", "#c3fae8"), "Analise 25 partidas", "#20c997"),
    Border("legend", "Lenda", ("#fff3bf", "#fab005", "#862e9c", "#fab005", "#fff3bf"), "Analise 50 partidas", "#e599f7"),
]

GOALS = {
    "veteran": lambda rows: (len(rows), 10),
    "marathon": lambda rows: (len(rows), 25),
    "legend": lambda rows: (len(rows), 50),
}

FEATS = {
    "gold": lambda js: n(js, "rating") >= 1.3 and n(js, "rounds") >= 10,
    "ace": lambda js: n(js, "k5") >= 1,
    "toxic": lambda js: n(js, "hs_pct") >= 0.6 and n(js, "kpr") * n(js, "rounds") >= 10,
    "diamond": lambda js: n(js, "rating") >= 1.5 and n(js, "rounds") >= 10,
    "quad": lambda js: n(js, "k4") >= 1 or n(js, "k5") >= 1,
    "clutch": lambda js: n(js, "c1vx") >= 1,
    "wall": lambda js: n(js, "survival") >= 0.45 and n(js, "rounds") >= 10,
    "carry": lambda js: n(js, "adr") >= 100 and n(js, "rounds") >= 10,
    "opener": lambda js: n(js, "opening_success") >= 0.65 and n(js, "opening_attempts") >= 6,
    "flashbang": lambda js: n(js, "flash_eff") >= 1.0 and n(js, "flash_thrown") >= 6,
}

EFFECTS = [("none", "Nenhum"), ("spin", "Girar"), ("pulse", "Pulsar"), ("sparkle", "Faíscas")]

AVATARS = [("initials", "Iniciais"), ("crosshair", "Mira"), ("skull", "Caveira"), ("robot", "Robô"), ("ninja", "Ninja"),
           ("crown", "Coroa"), ("bolt", "Raio"), ("ghost", "Fantasma"), ("alien", "Alien"), ("c4", "C4"),
           ("grenade", "Granada"), ("helmet", "Capacete"), ("knife", "Faca"), ("cat", "Gato"), ("fox", "Raposa"),
           ("panda", "Panda"), ("flame", "Chama"), ("star", "Estrela"), ("gem", "Joia")]


def valid_color(value, default):
    return value if isinstance(value, str) and len(value) == 7 and value.startswith("#") and QColor(value).isValid() else default


def available_fonts():
    installed = set(QFontDatabase.families())
    return [f for f in FONT_CHOICES if f in installed]


def unlocked(history_rows, admin=False):
    if admin:
        return {b.key for b in BORDERS}
    got = {b.key for b in BORDERS if not b.unlock}
    got |= {k for k, goal in GOALS.items() if goal(history_rows)[0] >= goal(history_rows)[1]}
    got |= {k for k, feat in FEATS.items() if any(feat(js) for *_, js in history_rows)}
    return got


def progress(history_rows):
    return {k: f"{min(n, total)}/{total}" for k, goal in GOALS.items() for n, total in [goal(history_rows)]}


def initials(name):
    parts = [p for p in "".join(c if c.isalnum() else " " for c in name).split() if p]
    return ("".join(p[0] for p in parts[:2]) or "?").upper()


def import_photo(path):
    if os.path.getsize(path) > MAX_PHOTO_BYTES:
        raise ValueError("imagem grande demais (máx. 15 MB).")
    img = QImage(path)
    if img.isNull():
        raise ValueError("não foi possível abrir essa imagem.")
    side = min(img.width(), img.height())
    img = img.copy((img.width() - side) // 2, (img.height() - side) // 2, side, side)
    img = img.scaled(256, 256, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
    if not img.save(str(PHOTO), "PNG"):
        raise ValueError("não foi possível salvar a foto.")


def remove_photo():
    PHOTO.unlink(missing_ok=True)


def soft(w, h, draw, factor):
    small = QImage(max(1, int(w / factor)), max(1, int(h / factor)), QImage.Format_ARGB32_Premultiplied)
    small.fill(Qt.transparent)
    p = QPainter(small)
    p.setRenderHint(QPainter.Antialiasing)
    p.scale(small.width() / w, small.height() / h)
    draw(p)
    p.end()
    mid = small.scaled(max(1, int(w / 2)), max(1, int(h / 2)), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
    return mid.scaled(int(w), int(h), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)


def ring_brush(border, center, color, angle=90):
    if not border.colors:
        return QBrush(color)
    grad = QConicalGradient(center, angle)
    for i, c in enumerate(border.colors):
        grad.setColorAt(i / (len(border.colors) - 1), QColor(c))
    return QBrush(grad)


def at(c, r, deg):
    a = math.radians(deg)
    return QPointF(c.x() + r * math.cos(a), c.y() + r * math.sin(a))


def star(c, r, points=5, inner=0.45, rotation=-90):
    return QPolygonF([at(c, r if i % 2 == 0 else r * inner, rotation + i * 180 / points) for i in range(points * 2)])


def ornaments(p, border, c, r, ring, size):
    s = size / 100
    if border.key == "fire":
        for deg in range(-170, -9, 20):
            base, tip = at(c, r, deg), at(c, r + ring * (1.9 if deg % 40 else 2.6), deg + 6)
            left, right = at(c, r - ring * 0.2, deg - 8), at(c, r - ring * 0.2, deg + 8)
            flame = QPainterPath(left)
            flame.quadTo(at(c, r + ring * 0.8, deg - 9), tip)
            flame.quadTo(at(c, r + ring * 0.8, deg + 11), right)
            flame.closeSubpath()
            g = QLinearGradient(base, tip)
            g.setColorAt(0, QColor("#ff2a00"))
            g.setColorAt(0.6, QColor("#ff9a00"))
            g.setColorAt(1, QColor("#fff2a0"))
            p.fillPath(flame, g)
    elif border.key == "ice":
        pen = QPen(QColor("#e8f7ff"), max(1.0, 1.6 * s), Qt.SolidLine, Qt.RoundCap)
        p.setPen(pen)
        for deg in range(-90, 270, 60):
            a, b = at(c, r + ring * 0.4, deg), at(c, r + ring * 2.0, deg)
            p.drawLine(a, b)
            for side in (-1, 1):
                p.drawLine(at(c, r + ring * 1.35, deg), at(c, r + ring * 1.85, deg + side * 7))
        p.setPen(Qt.NoPen)
        for deg in range(-60, 270, 60):
            p.setBrush(QColor(255, 255, 255, 200))
            p.drawEllipse(at(c, r + ring * 1.2, deg), 1.2 * s, 1.2 * s)
    elif border.key == "veteran":
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#30363d"))
        for deg in range(0, 360, 30):
            p.drawEllipse(at(c, r, deg), ring * 0.22, ring * 0.22)
        chevron = QPen(QColor("#e6edf3"), max(1.5, 3 * s), Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        p.setPen(chevron)
        for i in range(2):
            y = c.y() + r + ring * (0.9 + i * 0.95)
            path = QPainterPath(QPointF(c.x() - 9 * s, y - 4 * s))
            path.lineTo(c.x(), y + 1.5 * s)
            path.lineTo(c.x() + 9 * s, y - 4 * s)
            p.drawPath(path)
    elif border.key == "gold":
        hl = QPen(QColor(255, 255, 255, 170), max(1.0, ring * 0.25), Qt.SolidLine, Qt.RoundCap)
        p.setPen(hl)
        p.setBrush(Qt.NoBrush)
        rect = QRectF(c.x() - r, c.y() - r, 2 * r, 2 * r)
        p.drawArc(rect.adjusted(-ring * 0.25, -ring * 0.25, ring * 0.25, ring * 0.25), 100 * 16, 70 * 16)
        p.setPen(QPen(QColor("#8a6100"), max(0.8, 0.8 * s)))
        for deg, k in ((-90, 1.0), (-122, 0.7), (-58, 0.7)):
            g = QLinearGradient(at(c, r + ring * 2, deg), at(c, r, deg))
            g.setColorAt(0, QColor("#fff6c2"))
            g.setColorAt(1, QColor("#e8b923"))
            p.setBrush(g)
            p.drawPolygon(star(at(c, r + ring * 0.9, deg), ring * 1.15 * k, 4, 0.38, deg))
    elif border.key == "ace":
        p.setPen(QPen(QColor("#111318"), max(0.8, 0.8 * s)))
        for i, deg in enumerate(range(-140, -39, 25)):
            p.setBrush(QColor(["#f5a623", "#f85149", "#a371f7", "#39c5cf", "#3fb950"][i]))
            p.drawPolygon(star(at(c, r + ring * 1.25, deg), ring * (1.05 if deg == -90 else 0.85)))
    elif border.key == "neon":
        p.setPen(Qt.NoPen)
        for deg, col in ((-45, "#00e5ff"), (135, "#ff2bd6")):
            p.setBrush(QColor(col))
            p.drawEllipse(at(c, r, deg), ring * 0.45, ring * 0.45)


def more_ornaments(p, border, c, r, ring, size, phase):
    s = size / 100
    if border.key == "galaxy":
        p.setPen(Qt.NoPen)
        for i in range(14):
            deg = (i * 137.5 + phase * 60) % 360
            dist = r + ring * (0.6 + (i % 4) * 0.45)
            a = 0.35 + 0.65 * abs(math.sin(phase * math.tau + i))
            p.setBrush(QColor(255, 255, 255, int(255 * a)))
            p.drawPolygon(star(at(c, dist, deg), ring * (0.35 + (i % 3) * 0.15), 4, 0.35, deg))
    elif border.key == "electric":
        pen = QPen(QColor("#e0fbff"), max(1.0, 1.4 * s), Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        for k in range(5):
            base = k * 72 + phase * 90
            path = QPainterPath(at(c, r + ring * 0.4, base))
            for j in range(1, 5):
                path.lineTo(at(c, r + ring * (0.4 + j * 0.42), base + (9 if j % 2 else -9)))
            p.drawPath(path)
    elif border.key == "sakura":
        p.setPen(Qt.NoPen)
        for i, deg in enumerate(range(-160, 200, 45)):
            ctr = at(c, r + ring * 0.9, deg + phase * 40)
            for k in range(5):
                petal = QPainterPath()
                tip = at(ctr, ring * 1.35, deg + k * 72)
                petal.moveTo(ctr)
                petal.quadTo(at(ctr, ring * 1.0, deg + k * 72 - 38), tip)
                petal.quadTo(at(ctr, ring * 1.0, deg + k * 72 + 38), ctr)
                p.fillPath(petal, QColor("#ff9ec4" if i % 2 else "#ff5f9e"))
            p.setBrush(QColor("#fff3a0"))
            p.drawEllipse(ctr, ring * 0.18, ring * 0.18)
    elif border.key == "toxic":
        p.setPen(Qt.NoPen)
        for i, deg in enumerate(range(30, 160, 22)):
            length = ring * (1.0 + 0.9 * abs(math.sin(i * 1.7 + phase * math.tau)))
            top = at(c, r, deg)
            drop = QPainterPath(at(c, r - ring * 0.3, deg - 8))
            drop.lineTo(at(c, r + length, deg))
            drop.lineTo(at(c, r - ring * 0.3, deg + 8))
            drop.closeSubpath()
            p.fillPath(drop, QColor("#39ff14"))
            p.setBrush(QColor("#c6ff00"))
            p.drawEllipse(at(c, r + length, deg), ring * 0.45, ring * 0.45)
    elif border.key == "diamond":
        p.setPen(QPen(QColor("#ffffff"), max(0.8, 0.8 * s)))
        for i, deg in enumerate(range(-90, 270, 45)):
            g = QLinearGradient(at(c, r + ring * 2.2, deg), at(c, r, deg))
            g.setColorAt(0, QColor("#ffffff"))
            g.setColorAt(1, QColor("#5ad1ff"))
            p.setBrush(g)
            k = 1.5 if deg == -90 else 1.05
            pt = at(c, r + ring * 0.85, deg)
            gem = QPolygonF([at(pt, ring * k, deg), at(pt, ring * 0.55 * k, deg + 90),
                             at(pt, ring * 0.7 * k, deg + 180), at(pt, ring * 0.55 * k, deg - 90)])
            p.drawPolygon(gem)


def new_ornaments(p, border, c, r, ring, size, phase):
    s = size / 100
    k = border.key
    if k == "ocean":
        p.setPen(Qt.NoPen)
        for i in range(9):
            t = (phase + i / 9) % 1.0
            deg = 20 + i * 16
            p.setBrush(QColor(200, 240, 255, int(220 * (1 - t))))
            p.drawEllipse(at(c, r + ring * (0.3 + t * 2.0), deg), ring * (0.25 + 0.2 * (i % 3)), ring * (0.25 + 0.2 * (i % 3)))
        wave = QPainterPath(at(c, r + ring * 0.9, 200))
        for j in range(1, 15):
            wave.lineTo(at(c, r + ring * (0.9 + 0.45 * math.sin(j * 1.3 + phase * math.tau)), 200 + j * 10))
        p.setPen(QPen(QColor("#7fdbff"), max(1.0, 1.4 * s), Qt.SolidLine, Qt.RoundCap))
        p.setBrush(Qt.NoBrush)
        p.drawPath(wave)
    elif k == "sunset":
        sun = at(c, r + ring * 0.2, -90)
        p.setPen(QPen(QColor("#ffd86f"), max(1.0, 1.6 * s), Qt.SolidLine, Qt.RoundCap))
        for deg in range(-170, -9, 20):
            p.drawLine(at(c, r + ring * 0.8, deg), at(c, r + ring * (1.6 + 0.4 * (deg % 40 == 0)), deg))
        p.setPen(Qt.NoPen)
        g = QLinearGradient(QPointF(sun.x(), sun.y() - ring * 1.4), QPointF(sun.x(), sun.y() + ring * 1.4))
        g.setColorAt(0, QColor("#fff3b0"))
        g.setColorAt(1, QColor("#ff7b54"))
        p.setBrush(g)
        p.drawEllipse(sun, ring * 1.3, ring * 1.3)
    elif k == "matrix":
        font = QFont("Consolas")
        font.setPixelSize(max(5, int(ring * 1.1)))
        font.setBold(True)
        p.setFont(font)
        for i in range(16):
            deg = i * 22.5
            t = (phase * 2 + i * 0.37) % 1.0
            p.setPen(QColor(0, 255, 65, int(255 * (1 - t))))
            pt = at(c, r + ring * (0.7 + t * 1.6), deg)
            p.drawText(QRectF(pt.x() - ring, pt.y() - ring, 2 * ring, 2 * ring), Qt.AlignCenter, "01"[(i + int(phase * 20)) % 2])
    elif k == "quad":
        p.setPen(QPen(QColor("#2b0a0a"), max(0.8, 0.8 * s)))
        for i, deg in enumerate((-135, -105, -75, -45)):
            p.save()
            p.translate(at(c, r + ring * 1.15, deg))
            p.rotate(deg + 90)
            g = QLinearGradient(0, -ring * 1.3, 0, ring * 0.6)
            g.setColorAt(0, QColor("#ffe066"))
            g.setColorAt(1, QColor("#c92a2a"))
            p.setBrush(g)
            bullet = QPainterPath(QPointF(-ring * 0.38, ring * 0.6))
            bullet.lineTo(-ring * 0.38, -ring * 0.5)
            bullet.quadTo(0, -ring * 1.5, ring * 0.38, -ring * 0.5)
            bullet.lineTo(ring * 0.38, ring * 0.6)
            bullet.closeSubpath()
            p.drawPath(bullet)
            p.restore()
    elif k == "clutch":
        bottom = at(c, r + ring * 0.6, 90)
        w = ring * 1.6
        shield = QPainterPath(QPointF(bottom.x() - w, bottom.y() - w * 0.9))
        shield.lineTo(bottom.x() + w, bottom.y() - w * 0.9)
        shield.lineTo(bottom.x() + w, bottom.y())
        shield.quadTo(bottom.x() + w, bottom.y() + w * 0.9, bottom.x(), bottom.y() + w * 1.4)
        shield.quadTo(bottom.x() - w, bottom.y() + w * 0.9, bottom.x() - w, bottom.y())
        shield.closeSubpath()
        g = QLinearGradient(bottom.x(), bottom.y() - w, bottom.x(), bottom.y() + w * 1.4)
        g.setColorAt(0, QColor("#d0b3ff"))
        g.setColorAt(1, QColor("#5b1fc2"))
        p.setPen(QPen(QColor("#1a0b33"), max(0.8, 0.8 * s)))
        p.setBrush(g)
        p.drawPath(shield)
        p.setBrush(QColor("#ffffff"))
        p.drawPolygon(star(QPointF(bottom.x(), bottom.y() + w * 0.1), w * 0.55, 5, 0.45))
        p.setPen(Qt.NoPen)
        for deg in (-90, -30, -150):
            a = 0.5 + 0.5 * math.sin(phase * math.tau + deg)
            p.setBrush(QColor(208, 179, 255, int(120 + 135 * a)))
            gem = at(c, r, deg)
            p.drawPolygon(QPolygonF([at(gem, ring * 0.8, deg), at(gem, ring * 0.45, deg + 90),
                                     at(gem, ring * 0.8, deg + 180), at(gem, ring * 0.45, deg - 90)]))
    elif k == "wall":
        p.setPen(QPen(QColor("#22262c"), max(0.8, 0.7 * s)))
        for i in range(24):
            deg = i * 15 + (7.5 if i % 2 else 0)
            p.save()
            p.translate(at(c, r + ring * (0.55 if i % 2 else 0.0), deg))
            p.rotate(deg + 90)
            p.setBrush(QColor("#8b949e" if i % 3 else "#6e7681"))
            p.drawRect(QRectF(-ring * 0.9, -ring * 0.32, ring * 1.8, ring * 0.64))
            p.restore()
    elif k == "carry":
        p.setPen(Qt.NoPen)
        top = at(c, r, -90)
        for i in range(3):
            y = top.y() - ring * (0.6 + i * 0.85)
            a = 0.45 + 0.55 * abs(math.sin(phase * math.tau - i * 0.6))
            p.setBrush(QColor(255, 146 + i * 30, 43, int(255 * a)))
            p.drawPolygon(QPolygonF([QPointF(top.x() - ring * 1.4, y + ring * 0.7), QPointF(top.x(), y - ring * 0.2),
                                     QPointF(top.x() + ring * 1.4, y + ring * 0.7), QPointF(top.x() + ring * 1.4, y + ring * 1.15),
                                     QPointF(top.x(), y + ring * 0.25), QPointF(top.x() - ring * 1.4, y + ring * 1.15)]))
    elif k == "opener":
        for deg in (-45, 135):
            base, tip = at(c, r - ring * 0.4, deg), at(c, r + ring * 2.4, deg)
            p.setPen(QPen(QColor("#ffe3e3"), max(1.2, ring * 0.35), Qt.SolidLine, Qt.RoundCap))
            p.drawLine(base, tip)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#e03131"))
            p.drawPolygon(QPolygonF([at(tip, ring * 0.9, deg), at(tip, ring * 0.6, deg + 120), at(tip, ring * 0.6, deg - 120)]))
    elif k == "flashbang":
        a = 0.5 + 0.5 * math.sin(phase * math.tau * 2)
        p.setPen(QPen(QColor(255, 249, 219, int(150 + 105 * a)), max(1.0, 1.5 * s), Qt.SolidLine, Qt.RoundCap))
        for deg in range(0, 360, 15):
            long = deg % 45 == 0
            p.drawLine(at(c, r + ring * 0.7, deg), at(c, r + ring * ((1.6 if long else 1.15) + 0.5 * a), deg))
    elif k in ("marathon", "legend"):
        leaf = QColor("#12b886") if k == "marathon" else QColor("#fab005")
        p.setPen(Qt.NoPen)
        for side in (-1, 1):
            for j in range(6):
                deg = 90 + side * (25 + j * 17)
                pt = at(c, r + ring * 0.9, deg)
                p.save()
                p.translate(pt)
                p.rotate(deg + side * 60)
                p.setBrush(leaf.lighter(100 + j * 8))
                p.drawEllipse(QPointF(0, 0), ring * 0.95, ring * 0.42)
                p.restore()
        if k == "legend":
            top = at(c, r + ring * 0.9, -90)
            w = ring * 1.5
            p.setBrush(QColor("#fab005"))
            p.setPen(QPen(QColor("#5f3dc4"), max(0.8, 0.8 * s)))
            p.drawPolygon(QPolygonF([QPointF(top.x() - w, top.y() + w * 0.5), QPointF(top.x() - w, top.y() - w * 0.5),
                                     QPointF(top.x() - w * 0.5, top.y()), QPointF(top.x(), top.y() - w * 0.8),
                                     QPointF(top.x() + w * 0.5, top.y()), QPointF(top.x() + w, top.y() - w * 0.5),
                                     QPointF(top.x() + w, top.y() + w * 0.5)]))
            p.setBrush(QColor("#e599f7"))
            p.drawEllipse(top, w * 0.22, w * 0.22)


def sparkles(p, c, r, ring, phase):
    p.setPen(Qt.NoPen)
    for i in range(7):
        t = (phase * 1.3 + i / 7) % 1.0
        deg = i * 51.4 + phase * 30
        a = math.sin(t * math.pi)
        p.setBrush(QColor(255, 255, 255, int(230 * a)))
        p.drawPolygon(star(at(c, r + ring * (0.3 + t * 1.6), deg), ring * (0.35 + 0.5 * a), 4, 0.3, deg))


def draw_avatar_art(p, key, rect, color):
    c = rect.center()
    w = rect.width()
    white, dark = QColor("#ffffff"), color.darker(250)
    p.setPen(Qt.NoPen)
    if key == "crosshair":
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(white, w * 0.07))
        p.drawEllipse(c, w * 0.26, w * 0.26)
        for deg in (0, 90, 180, 270):
            p.drawLine(at(c, w * 0.12, deg), at(c, w * 0.40, deg))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#f85149"))
        p.drawEllipse(c, w * 0.05, w * 0.05)
    elif key == "skull":
        p.setBrush(white)
        p.drawEllipse(QPointF(c.x(), c.y() - w * 0.06), w * 0.27, w * 0.25)
        p.drawRoundedRect(QRectF(c.x() - w * 0.15, c.y() + w * 0.08, w * 0.30, w * 0.18), w * 0.04, w * 0.04)
        p.setBrush(dark)
        for dx in (-0.11, 0.11):
            p.drawEllipse(QPointF(c.x() + w * dx, c.y() - w * 0.06), w * 0.075, w * 0.085)
        p.drawPolygon(QPolygonF([QPointF(c.x(), c.y() + w * 0.02), QPointF(c.x() - w * 0.04, c.y() + w * 0.09),
                                 QPointF(c.x() + w * 0.04, c.y() + w * 0.09)]))
        for dx in (-0.075, 0, 0.075):
            p.drawRect(QRectF(c.x() + w * dx - w * 0.012, c.y() + w * 0.15, w * 0.024, w * 0.11))
    elif key == "robot":
        p.setBrush(white)
        p.drawRoundedRect(QRectF(c.x() - w * 0.27, c.y() - w * 0.2, w * 0.54, w * 0.42), w * 0.08, w * 0.08)
        p.drawRect(QRectF(c.x() - w * 0.02, c.y() - w * 0.33, w * 0.04, w * 0.13))
        p.drawEllipse(QPointF(c.x(), c.y() - w * 0.34), w * 0.05, w * 0.05)
        p.setBrush(QColor("#39c5cf"))
        for dx in (-0.12, 0.12):
            p.drawEllipse(QPointF(c.x() + w * dx, c.y() - w * 0.03), w * 0.07, w * 0.07)
        p.setBrush(dark)
        p.drawRoundedRect(QRectF(c.x() - w * 0.14, c.y() + w * 0.09, w * 0.28, w * 0.06), w * 0.03, w * 0.03)
    elif key == "ninja":
        p.setBrush(QColor("#1c1f26"))
        p.drawEllipse(c, w * 0.32, w * 0.32)
        p.setBrush(QColor("#f1c8a0"))
        p.drawRoundedRect(QRectF(c.x() - w * 0.25, c.y() - w * 0.1, w * 0.5, w * 0.15), w * 0.07, w * 0.07)
        p.setBrush(QColor("#1c1f26"))
        for dx in (-0.1, 0.1):
            p.drawEllipse(QPointF(c.x() + w * dx, c.y() - w * 0.025), w * 0.04, w * 0.035)
        p.setBrush(QColor("#f85149"))
        p.drawRect(QRectF(c.x() - w * 0.32, c.y() - w * 0.2, w * 0.64, w * 0.06))
        p.drawPolygon(QPolygonF([QPointF(c.x() + w * 0.3, c.y() - w * 0.2), QPointF(c.x() + w * 0.45, c.y() - w * 0.28),
                                 QPointF(c.x() + w * 0.42, c.y() - w * 0.12)]))
    elif key == "crown":
        p.setBrush(QColor("#ffcc33"))
        p.drawPolygon(QPolygonF([QPointF(c.x() - w * 0.3, c.y() + w * 0.18), QPointF(c.x() - w * 0.3, c.y() - w * 0.14),
                                 QPointF(c.x() - w * 0.15, c.y() + w * 0.02), QPointF(c.x(), c.y() - w * 0.24),
                                 QPointF(c.x() + w * 0.15, c.y() + w * 0.02), QPointF(c.x() + w * 0.3, c.y() - w * 0.14),
                                 QPointF(c.x() + w * 0.3, c.y() + w * 0.18)]))
        p.setBrush(QColor("#f85149"))
        p.drawEllipse(QPointF(c.x(), c.y() + w * 0.08), w * 0.05, w * 0.05)
        p.setBrush(white)
        for dx, dy in ((-0.3, -0.16), (0, -0.26), (0.3, -0.16)):
            p.drawEllipse(QPointF(c.x() + w * dx, c.y() + w * dy), w * 0.04, w * 0.04)
    elif key == "bolt":
        p.setBrush(QColor("#ffe600"))
        p.drawPolygon(QPolygonF([QPointF(c.x() + w * 0.06, c.y() - w * 0.34), QPointF(c.x() - w * 0.2, c.y() + w * 0.04),
                                 QPointF(c.x() - w * 0.01, c.y() + w * 0.04), QPointF(c.x() - w * 0.08, c.y() + w * 0.34),
                                 QPointF(c.x() + w * 0.2, c.y() - w * 0.06), QPointF(c.x() + w * 0.01, c.y() - w * 0.06)]))
    elif key == "ghost":
        p.setBrush(white)
        body = QPainterPath(QPointF(c.x() - w * 0.24, c.y() + w * 0.28))
        body.lineTo(c.x() - w * 0.24, c.y() - w * 0.04)
        body.arcTo(QRectF(c.x() - w * 0.24, c.y() - w * 0.28, w * 0.48, w * 0.48), 180, -180)
        body.lineTo(c.x() + w * 0.24, c.y() + w * 0.28)
        for i in range(4):
            x = c.x() + w * 0.24 - (i + 1) * w * 0.12
            body.quadTo(QPointF(x + w * 0.06, c.y() + w * (0.18 if i % 2 == 0 else 0.34)), QPointF(x, c.y() + w * 0.28))
        p.drawPath(body)
        p.setBrush(dark)
        for dx in (-0.09, 0.09):
            p.drawEllipse(QPointF(c.x() + w * dx, c.y() - w * 0.04), w * 0.045, w * 0.06)
    elif key == "alien":
        p.setBrush(QColor("#7ee787"))
        head = QPainterPath()
        head.addEllipse(QPointF(c.x(), c.y() - w * 0.04), w * 0.27, w * 0.3)
        p.drawPath(head)
        p.setBrush(QColor("#0d1117"))
        for dx, rot in ((-0.12, 25), (0.12, -25)):
            p.save()
            p.translate(c.x() + w * dx, c.y() - w * 0.02)
            p.rotate(rot)
            p.drawEllipse(QPointF(0, 0), w * 0.1, w * 0.055)
            p.restore()
        p.drawRoundedRect(QRectF(c.x() - w * 0.05, c.y() + w * 0.14, w * 0.1, w * 0.025), w * 0.01, w * 0.01)

    elif key == "c4":
        p.setBrush(QColor("#8d6e3f"))
        p.drawRoundedRect(QRectF(c.x() - w * 0.3, c.y() - w * 0.2, w * 0.6, w * 0.42), w * 0.04, w * 0.04)
        p.setBrush(QColor("#2b2b2b"))
        p.drawRect(QRectF(c.x() - w * 0.2, c.y() - w * 0.13, w * 0.4, w * 0.13))
        p.setPen(QColor("#ff3b30"))
        font = QFont("Consolas")
        font.setPixelSize(max(4, int(w * 0.1)))
        font.setBold(True)
        p.setFont(font)
        p.drawText(QRectF(c.x() - w * 0.2, c.y() - w * 0.13, w * 0.4, w * 0.13), Qt.AlignCenter, "7355")
        p.setPen(Qt.NoPen)
        for i in range(3):
            p.setBrush(QColor(["#f85149", "#58a6ff", "#3fb950"][i]))
            p.drawRect(QRectF(c.x() - w * 0.2 + i * w * 0.15, c.y() + w * 0.05, w * 0.1, w * 0.1))
        p.setPen(QPen(QColor("#f85149"), w * 0.025))
        p.setBrush(Qt.NoBrush)
        wire = QPainterPath(QPointF(c.x() + w * 0.3, c.y() - w * 0.1))
        wire.quadTo(QPointF(c.x() + w * 0.42, c.y() - w * 0.3), QPointF(c.x() + w * 0.18, c.y() - w * 0.3))
        p.drawPath(wire)
    elif key == "grenade":
        p.setBrush(QColor("#9aa5b1"))
        p.drawRoundedRect(QRectF(c.x() - w * 0.14, c.y() - w * 0.14, w * 0.28, w * 0.44), w * 0.07, w * 0.07)
        p.setBrush(QColor("#5c6670"))
        p.drawRect(QRectF(c.x() - w * 0.1, c.y() - w * 0.24, w * 0.2, w * 0.11))
        p.setBrush(white)
        p.drawRect(QRectF(c.x() - w * 0.14, c.y() + w * 0.02, w * 0.28, w * 0.06))
        p.setPen(QPen(QColor("#d4d9de"), w * 0.03))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QPointF(c.x() + w * 0.17, c.y() - w * 0.24), w * 0.07, w * 0.07)
        p.drawLine(QPointF(c.x() + w * 0.1, c.y() - w * 0.2), QPointF(c.x() + w * 0.2, c.y() + w * 0.05))
    elif key == "helmet":
        p.setBrush(QColor("#556b2f"))
        dome = QPainterPath(QPointF(c.x() - w * 0.32, c.y() + w * 0.08))
        dome.arcTo(QRectF(c.x() - w * 0.32, c.y() - w * 0.3, w * 0.64, w * 0.76), 180, -180)
        dome.lineTo(c.x() + w * 0.38, c.y() + w * 0.12)
        dome.lineTo(c.x() - w * 0.38, c.y() + w * 0.12)
        dome.closeSubpath()
        p.drawPath(dome)
        p.setBrush(QColor("#3d4f1f"))
        p.drawRect(QRectF(c.x() - w * 0.38, c.y() + w * 0.08, w * 0.76, w * 0.07))
        p.setPen(QPen(QColor("#2b2b2b"), w * 0.03))
        p.drawLine(QPointF(c.x() - w * 0.24, c.y() + w * 0.15), QPointF(c.x() - w * 0.1, c.y() + w * 0.32))
        p.drawLine(QPointF(c.x() + w * 0.24, c.y() + w * 0.15), QPointF(c.x() + w * 0.1, c.y() + w * 0.32))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 255, 255, 60))
        p.drawEllipse(QPointF(c.x() - w * 0.1, c.y() - w * 0.12), w * 0.08, w * 0.05)
    elif key == "knife":
        p.save()
        p.translate(c)
        p.rotate(-40)
        g = QLinearGradient(0, -w * 0.05, 0, w * 0.05)
        g.setColorAt(0, QColor("#f0f3f6"))
        g.setColorAt(1, QColor("#8b949e"))
        p.setBrush(g)
        p.drawPolygon(QPolygonF([QPointF(-w * 0.05, -w * 0.05), QPointF(w * 0.38, -w * 0.05),
                                 QPointF(w * 0.3, w * 0.06), QPointF(-w * 0.05, w * 0.06)]))
        p.setBrush(QColor("#1c1f26"))
        p.drawRoundedRect(QRectF(-w * 0.36, -w * 0.06, w * 0.3, w * 0.12), w * 0.04, w * 0.04)
        p.setBrush(QColor("#f5a623"))
        p.drawRect(QRectF(-w * 0.08, -w * 0.1, w * 0.04, w * 0.2))
        p.restore()
    elif key == "cat":
        p.setBrush(QColor("#2b2d31"))
        for side in (-1, 1):
            p.drawPolygon(QPolygonF([QPointF(c.x() + side * w * 0.3, c.y() - w * 0.05), QPointF(c.x() + side * w * 0.26, c.y() - w * 0.36),
                                     QPointF(c.x() + side * w * 0.06, c.y() - w * 0.16)]))
        p.drawEllipse(QPointF(c.x(), c.y() + w * 0.04), w * 0.3, w * 0.26)
        p.setBrush(QColor("#a6e22e"))
        for dx in (-0.12, 0.12):
            p.drawEllipse(QPointF(c.x() + w * dx, c.y()), w * 0.06, w * 0.07)
        p.setBrush(QColor("#ff8fb8"))
        p.drawPolygon(QPolygonF([QPointF(c.x() - w * 0.035, c.y() + w * 0.1), QPointF(c.x() + w * 0.035, c.y() + w * 0.1),
                                 QPointF(c.x(), c.y() + w * 0.14)]))
        p.setPen(QPen(QColor(255, 255, 255, 160), w * 0.012))
        for side in (-1, 1):
            for dy in (0.12, 0.17):
                p.drawLine(QPointF(c.x() + side * w * 0.08, c.y() + w * dy), QPointF(c.x() + side * w * 0.3, c.y() + w * (dy - 0.03)))
    elif key == "fox":
        p.setBrush(QColor("#f76707"))
        p.drawPolygon(QPolygonF([QPointF(c.x() - w * 0.32, c.y() - w * 0.3), QPointF(c.x() - w * 0.12, c.y() - w * 0.14),
                                 QPointF(c.x() + w * 0.12, c.y() - w * 0.14), QPointF(c.x() + w * 0.32, c.y() - w * 0.3),
                                 QPointF(c.x() + w * 0.3, c.y() + w * 0.02), QPointF(c.x(), c.y() + w * 0.32),
                                 QPointF(c.x() - w * 0.3, c.y() + w * 0.02)]))
        p.setBrush(white)
        for side in (-1, 1):
            p.drawPolygon(QPolygonF([QPointF(c.x() + side * w * 0.3, c.y() + w * 0.02), QPointF(c.x() + side * w * 0.05, c.y() + w * 0.08),
                                     QPointF(c.x(), c.y() + w * 0.32)]))
        p.setBrush(QColor("#1c1f26"))
        for dx in (-0.12, 0.12):
            p.drawEllipse(QPointF(c.x() + w * dx, c.y() - w * 0.04), w * 0.04, w * 0.045)
        p.drawEllipse(QPointF(c.x(), c.y() + w * 0.27), w * 0.045, w * 0.035)
    elif key == "panda":
        p.setBrush(QColor("#1c1f26"))
        for dx in (-0.23, 0.23):
            p.drawEllipse(QPointF(c.x() + w * dx, c.y() - w * 0.22), w * 0.1, w * 0.1)
        p.setBrush(white)
        p.drawEllipse(QPointF(c.x(), c.y() + w * 0.02), w * 0.3, w * 0.27)
        p.setBrush(QColor("#1c1f26"))
        for dx, rot in ((-0.11, -25), (0.11, 25)):
            p.save()
            p.translate(c.x() + w * dx, c.y() - w * 0.01)
            p.rotate(rot)
            p.drawEllipse(QPointF(0, 0), w * 0.065, w * 0.09)
            p.restore()
        p.drawEllipse(QPointF(c.x(), c.y() + w * 0.11), w * 0.045, w * 0.03)
        p.setBrush(white)
        for dx in (-0.11, 0.11):
            p.drawEllipse(QPointF(c.x() + w * dx, c.y() - w * 0.02), w * 0.022, w * 0.022)
    elif key == "flame":
        flame = QPainterPath(QPointF(c.x(), c.y() + w * 0.32))
        flame.cubicTo(QPointF(c.x() - w * 0.34, c.y() + w * 0.28), QPointF(c.x() - w * 0.3, c.y() - w * 0.1), QPointF(c.x() - w * 0.06, c.y() - w * 0.36))
        flame.cubicTo(QPointF(c.x() - w * 0.02, c.y() - w * 0.14), QPointF(c.x() + w * 0.14, c.y() - w * 0.2), QPointF(c.x() + w * 0.12, c.y() - w * 0.3))
        flame.cubicTo(QPointF(c.x() + w * 0.36, c.y() - w * 0.06), QPointF(c.x() + w * 0.32, c.y() + w * 0.28), QPointF(c.x(), c.y() + w * 0.32))
        g = QLinearGradient(c.x(), c.y() - w * 0.36, c.x(), c.y() + w * 0.32)
        g.setColorAt(0, QColor("#ffe066"))
        g.setColorAt(0.5, QColor("#ff922b"))
        g.setColorAt(1, QColor("#e03131"))
        p.fillPath(flame, g)
        inner = QPainterPath(QPointF(c.x(), c.y() + w * 0.3))
        inner.cubicTo(QPointF(c.x() - w * 0.16, c.y() + w * 0.26), QPointF(c.x() - w * 0.12, c.y() + w * 0.02), QPointF(c.x(), c.y() - w * 0.08))
        inner.cubicTo(QPointF(c.x() + w * 0.12, c.y() + w * 0.02), QPointF(c.x() + w * 0.16, c.y() + w * 0.26), QPointF(c.x(), c.y() + w * 0.3))
        p.fillPath(inner, QColor("#fff3bf"))
    elif key == "star":
        g = QLinearGradient(c.x(), c.y() - w * 0.34, c.x(), c.y() + w * 0.3)
        g.setColorAt(0, QColor("#fff3bf"))
        g.setColorAt(1, QColor("#fab005"))
        p.setBrush(g)
        p.drawPolygon(star(QPointF(c.x(), c.y() + w * 0.03), w * 0.36, 5, 0.45))
        p.setBrush(QColor(255, 255, 255, 140))
        p.drawPolygon(star(QPointF(c.x() - w * 0.06, c.y() - w * 0.04), w * 0.08, 4, 0.35, 0))
    elif key == "gem":
        top, mid, bot = c.y() - w * 0.22, c.y() - w * 0.06, c.y() + w * 0.32
        p.setBrush(QColor("#5ad1ff"))
        p.drawPolygon(QPolygonF([QPointF(c.x() - w * 0.32, mid), QPointF(c.x() + w * 0.32, mid), QPointF(c.x(), bot)]))
        p.setBrush(QColor("#b9f2ff"))
        p.drawPolygon(QPolygonF([QPointF(c.x() - w * 0.18, top), QPointF(c.x() + w * 0.18, top),
                                 QPointF(c.x() + w * 0.32, mid), QPointF(c.x() - w * 0.32, mid)]))
        p.setPen(QPen(QColor(255, 255, 255, 170), w * 0.015))
        for x0, x1 in ((-0.18, -0.1), (0.18, 0.1), (0, 0)):
            p.drawLine(QPointF(c.x() + w * x0, top), QPointF(c.x() + w * x1 * 0.5, mid))
        p.drawLine(QPointF(c.x() - w * 0.1, mid), QPointF(c.x(), bot))
        p.drawLine(QPointF(c.x() + w * 0.1, mid), QPointF(c.x(), bot))


def avatar(size, profile, phase=0.0):
    border = next((b for b in BORDERS if b.key == profile.get("border")), BORDERS[1])
    color = QColor(valid_color(profile.get("color"), COLORS[0]))
    effect = profile.get("effect", "none")
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.SmoothPixmapTransform)
    c = QPointF(size / 2, size / 2)
    decorated = border.key not in ("none", "classic")
    ring = 0 if border.key == "none" else max(2.0, size * (0.055 if decorated else 0.07))
    r = size / 2 - (size * 0.14 if decorated or effect != "none" else ring / 2)
    angle = 90 + (phase * 360 if effect == "spin" else 0)
    brush = ring_brush(border, c, color, angle)
    glow = border.glow or (color.name() if effect == "pulse" else "")
    if glow:
        strength = 0.55 + 0.45 * math.sin(phase * math.tau) if effect == "pulse" else 1.0
        halo = soft(size, size, lambda q: (q.setPen(QPen(QColor(glow), ring * (2.0 + 1.4 * strength) if ring else size * 0.05)),
                                           q.drawEllipse(c, r, r)), 5)
        p.setOpacity(strength)
        p.drawImage(0, 0, halo)
        p.setOpacity(1.0)
    if ring:
        p.setPen(QPen(brush, ring))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(c, r, r)
        if border.key == "ace":
            p.setPen(QPen(brush, max(1.0, ring * 0.35)))
            p.drawEllipse(c, r - ring * 1.25, r - ring * 1.25)
        p.save()
        if effect == "spin" and border.key in ("fire", "ice", "gold", "ace", "neon", "veteran"):
            p.translate(c)
            p.rotate(phase * 360)
            p.translate(-c)
        ornaments(p, border, c, r, ring, size)
        p.restore()
        more_ornaments(p, border, c, r, ring, size, phase)
        new_ornaments(p, border, c, r, ring, size, phase)
    if effect == "sparkle":
        sparkles(p, c, r, max(ring, size * 0.05), phase)
    inset = ring / 2 + ring * (1.9 if border.key == "ace" else 0.5)
    inner = QRectF(c.x() - r + inset, c.y() - r + inset, 2 * (r - inset), 2 * (r - inset)) if ring \
        else QRectF(c.x() - r, c.y() - r, 2 * r, 2 * r)
    path = QPainterPath()
    path.addEllipse(inner)
    p.save()
    p.setClipPath(path)
    photo = QImage(str(PHOTO)) if profile.get("photo") and PHOTO.exists() else QImage()
    art = profile.get("avatar", "initials")
    if not photo.isNull():
        p.drawImage(inner, photo)
    elif art in dict(AVATARS) and art != "initials":
        g = QLinearGradient(inner.topLeft(), inner.bottomRight())
        g.setColorAt(0, color.darker(130))
        g.setColorAt(1, color.darker(230))
        p.fillPath(path, g)
        draw_avatar_art(p, art, inner, color)
    else:
        p.fillPath(path, color.darker(160))
        font = QFont()
        font.setBold(True)
        font.setPixelSize(max(6, int(inner.height() * 0.38)))
        p.setFont(font)
        p.setPen(QColor("#ffffff"))
        p.drawText(inner, Qt.AlignCenter, initials(profile.get("name") or "?"))
    p.restore()
    p.end()
    return pm


class NameLabel(QWidget):
    def __init__(self, height=36, max_size=18):
        super().__init__()
        self.setFixedHeight(height)
        self.max_size = max_size
        self.data = {}
        self.phase = 0.0
        self.timer = QTimer(self)
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.tick)

    def set_profile(self, data):
        self.data = dict(data)
        if self.data.get("name_style") == "rainbow":
            self.timer.start()
        else:
            self.timer.stop()
        self.update()

    def tick(self):
        self.phase = (self.phase + 0.006) % 1.0
        self.update()

    def brush(self, rect, core=False):
        if self.data.get("name_style") == "rainbow":
            g = QLinearGradient(rect.left(), 0, rect.right(), 0)
            for i in range(7):
                c = QColor.fromHsvF((self.phase + i / 6) % 1.0, 0.55 if core else 0.95, 1.0)
                g.setColorAt(i / 6, c)
            return QBrush(g)
        if self.data.get("name_style") == "neon":
            c = QColor(valid_color(self.data.get("neon_color"), valid_color(self.data.get("color"), COLORS[0])))
            if core:
                c = QColor.fromRgbF(*(v + (1 - v) * 0.55 for v in c.getRgbF()[:3]))
            return QBrush(c)
        return QBrush(QColor(TEXT))

    def paintEvent(self, _):
        text = self.data.get("name") or "Seu perfil"
        glow = self.data.get("name_style") in ("neon", "rainbow")
        font = QFont(self.data.get("font") or self.font().family())
        font.setBold(True)
        room = self.width() - (20 if glow else 4)
        size = self.max_size
        while size > 9:
            font.setPixelSize(size)
            if QFontMetricsF(font).horizontalAdvance(text) <= room:
                break
            size -= 1
        font.setPixelSize(size)
        path = QPainterPath()
        path.addText(0, 0, font, text)
        box = path.boundingRect()
        path.translate(self.width() / 2 - box.center().x(), self.height() / 2 - box.center().y())
        box = path.boundingRect()
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.TextAntialiasing)
        if glow:
            dpr = self.devicePixelRatioF()
            w, h = self.width() * dpr, self.height() * dpr

            def draw(q, width):
                q.scale(dpr, dpr)
                q.setPen(QPen(self.brush(box), width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                q.setBrush(self.brush(box))
                q.drawPath(path)
            neon = QColor(valid_color(self.data.get("neon_color"), valid_color(self.data.get("color"), COLORS[0])))
            dim = 0.45 if self.data.get("name_style") == "neon" and neon.lightnessF() > 0.85 else 1.0
            for factor, width, opacity in ((7, 5, 0.9 * dim), (3, 2, dim)):
                img = soft(w, h, lambda q, width=width: draw(q, width), factor)
                img.setDevicePixelRatio(dpr)
                p.setOpacity(opacity)
                p.drawImage(0, 0, img)
            p.setOpacity(1.0)
        p.fillPath(path, self.brush(box, core=glow))
        p.end()
