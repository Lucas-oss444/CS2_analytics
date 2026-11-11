from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap, QPolygonF

WEAPONS = {
    "ak47": ("AK-47", "ak"), "m4a1": ("M4A4", "m4"), "m4a1_silencer": ("M4A1-S", "m4"),
    "famas": ("FAMAS", "m4"), "galilar": ("Galil AR", "ak"), "aug": ("AUG", "m4"), "sg556": ("SG 553", "ak"),
    "awp": ("AWP", "sniper"), "ssg08": ("SSG 08", "sniper"), "scar20": ("SCAR-20", "sniper"), "g3sg1": ("G3SG1", "sniper"),
    "deagle": ("Desert Eagle", "deagle"), "revolver": ("R8 Revolver", "deagle"),
    "glock": ("Glock-18", "pistol"), "usp_silencer": ("USP-S", "pistol"), "hkp2000": ("P2000", "pistol"),
    "p250": ("P250", "pistol"), "fiveseven": ("Five-SeveN", "pistol"), "tec9": ("Tec-9", "pistol"),
    "cz75a": ("CZ75-Auto", "pistol"), "elite": ("Dual Berettas", "pistol"),
    "mac10": ("MAC-10", "smg"), "mp9": ("MP9", "smg"), "mp7": ("MP7", "smg"), "mp5sd": ("MP5-SD", "smg"),
    "ump45": ("UMP-45", "smg"), "p90": ("P90", "smg"), "bizon": ("PP-Bizon", "smg"),
    "nova": ("Nova", "shotgun"), "xm1014": ("XM1014", "shotgun"), "mag7": ("MAG-7", "shotgun"),
    "sawedoff": ("Sawed-Off", "shotgun"), "m249": ("M249", "lmg"), "negev": ("Negev", "lmg"),
    "knife": ("Faca", "knife"), "taser": ("Zeus x27", "pistol"),
}

COLORS = {
    "ak": ("#e0a458", "#9c5a1c"), "m4": ("#7fb3e8", "#2f5f99"), "sniper": ("#8fd694", "#2f7a3a"),
    "pistol": ("#c9c9d6", "#5b5b70"), "deagle": ("#f2d16b", "#a07c12"), "smg": ("#e88fb3", "#99305a"),
    "shotgun": ("#e8836b", "#9a3520"), "lmg": ("#b39ae8", "#5a3a99"), "knife": ("#e6edf3", "#6b7a8a"),
}

R = QRectF


def poly(*pts):
    p = QPainterPath()
    p.addPolygon(QPolygonF([QPointF(x, y) for x, y in pts]))
    p.closeSubpath()
    return p


def rects(*rs):
    p = QPainterPath()
    for r in rs:
        p.addRect(R(*r))
    return p


def shape(kind):
    parts = {
        "ak": [poly((4, 18), (30, 16), (30, 28), (8, 34), (4, 32)), rects((28, 14, 50, 12), (76, 17, 38, 4), (104, 12, 3, 6)),
               poly((52, 25), (61, 25), (66, 40), (57, 44)), poly((36, 25), (44, 25), (40, 38), (33, 38))],
        "m4": [rects((4, 16, 20, 12), (20, 19, 10, 5), (28, 13, 46, 13), (40, 8, 22, 5), (74, 15, 22, 8), (94, 18, 22, 3)),
               poly((52, 25), (59, 25), (61, 41), (54, 41)), poly((34, 25), (42, 25), (38, 38), (31, 38))],
        "sniper": [poly((2, 18), (28, 17), (28, 27), (6, 33), (2, 31)), rects((26, 15, 40, 10), (36, 7, 30, 6), (42, 12, 3, 4),
                                                                              (58, 12, 3, 4), (66, 18, 52, 3)),
                   rects((48, 24, 8, 8)), poly((32, 24), (39, 24), (36, 36), (29, 36))],
        "pistol": [rects((30, 13, 52, 11)), poly((36, 23), (50, 23), (46, 42), (32, 42)), rects((49, 23, 9, 2), (56, 23, 2, 7))],
        "deagle": [rects((22, 11, 68, 14), (84, 9, 4, 3)), poly((30, 24), (46, 24), (42, 44), (26, 44)), rects((45, 24, 11, 2),
                                                                                                                 (54, 24, 2, 8))],
        "smg": [rects((10, 16, 20, 3), (10, 24, 20, 3), (10, 16, 3, 11), (28, 13, 46, 13), (72, 17, 20, 4)),
                rects((52, 25, 7, 17)), poly((34, 25), (42, 25), (38, 38), (31, 38))],
        "shotgun": [poly((4, 18), (30, 16), (30, 27), (8, 33), (4, 31)), rects((28, 14, 34, 11), (60, 14, 54, 4), (60, 20, 44, 4),
                                                                               (68, 18, 18, 9)),
                    poly((34, 24), (42, 24), (38, 37), (31, 37))],
        "lmg": [poly((4, 17), (28, 15), (28, 28), (8, 33), (4, 31)), rects((26, 12, 52, 15), (76, 17, 38, 5), (44, 27, 20, 13)),
                poly((90, 22), (93, 22), (100, 40), (97, 40)), poly((93, 22), (96, 22), (88, 40), (85, 40))],
        "knife": [poly((40, 18), (98, 15), (116, 22), (100, 28), (40, 27)), rects((35, 13, 5, 19), (8, 17, 28, 11))],
    }[kind]
    out = QPainterPath()
    for p in parts:
        out = out.united(p)
    return out.simplified()


def category(weapon):
    return WEAPONS.get(weapon, ("", "m4"))[1]


def display(weapon):
    return WEAPONS.get(weapon, (weapon or "", ""))[0]


def sticker(width, weapon):
    width = max(16, int(width))
    height = max(8, int(width * 0.42))
    pm = QPixmap(width, height)
    pm.fill(Qt.transparent)
    g = QPainter(pm)
    g.setRenderHint(QPainter.Antialiasing)
    scale = min((width - 4) / 120, (height - 4) / 50)
    g.translate((width - 120 * scale) / 2, (height - 50 * scale) / 2)
    g.scale(scale, scale)
    kind = category(weapon)
    path = shape(kind)
    light, dark = COLORS[kind]
    g.setPen(QPen(QColor(0, 0, 0, 90), 9, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    g.translate(1, 1.5)
    g.drawPath(path)
    g.translate(-1, -1.5)
    g.setPen(QPen(QColor("#ffffff"), 7, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    g.drawPath(path)
    grad = QLinearGradient(0, 8, 0, 44)
    grad.setColorAt(0, QColor(light))
    grad.setColorAt(1, QColor(dark))
    g.setPen(QPen(QColor(dark).darker(140), 1.2))
    g.setBrush(grad)
    g.drawPath(path)
    g.setClipPath(path)
    g.setPen(Qt.NoPen)
    g.setBrush(QColor(255, 255, 255, 70))
    g.drawRect(R(0, 0, 120, 18))
    g.end()
    return pm
