from datetime import datetime

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QImage, QLinearGradient, QPainter, QPen

from . import profile as prof
from . import weapons as wp
from .coach import MAP_NAMES
from .replay import highlights
from .stats import team_scores
from .theme import ACCENT, BAD, BG, GOOD, LINE, MUTED, PANEL, TEXT

W, H = 1200, 630


def font(size, bold=False):
    f = QFont()
    f.setPixelSize(size)
    f.setBold(bold)
    return f


def background(g, img):
    grad = QLinearGradient(0, 0, W, H)
    grad.setColorAt(0, QColor(PANEL))
    grad.setColorAt(1, QColor(BG))
    g.fillRect(img.rect(), grad)
    g.setPen(Qt.NoPen)
    g.setBrush(QColor(ACCENT))
    g.drawRect(QRectF(0, 0, 14, H))


def box(g, rect, label, value, accent=False):
    g.setPen(QPen(QColor(LINE), 2))
    g.setBrush(QColor(PANEL))
    g.drawRoundedRect(rect, 16, 16)
    g.setPen(QColor(MUTED))
    g.setFont(font(18, True))
    g.drawText(QRectF(rect.x(), rect.y() + 12, rect.width(), 28), Qt.AlignCenter, label)
    g.setPen(QColor(ACCENT if accent else TEXT))
    g.setFont(font(38 if len(value) < 9 else 26, True))
    g.drawText(QRectF(rect.x() + 6, rect.y() + 40, rect.width() - 12, rect.height() - 50), Qt.AlignCenter, value)


def pct(v):
    return "—" if v is None else f"{v:.0%}"


def profile_card(profile, name, career, qualities, weapon=None, weapon_stats=None, achievements=(0, 0)):
    img = QImage(W, H, QImage.Format_ARGB32)
    img.fill(QColor(BG))
    g = QPainter(img)
    g.setRenderHint(QPainter.Antialiasing)
    g.setRenderHint(QPainter.TextAntialiasing)
    background(g, img)
    g.drawPixmap(60, 50, prof.avatar(190, profile, 0.0))
    g.setPen(QColor(TEXT))
    g.setFont(font(52, True))
    g.drawText(QRectF(280, 50, W - 330, 70), Qt.AlignLeft | Qt.AlignVCenter, name or "Jogador")
    fav, team = profile.get("fav_player", ""), profile.get("fav_team", "")
    g.setPen(QColor(MUTED))
    g.setFont(font(24))
    g.drawText(QRectF(280, 118, W - 330, 36), Qt.AlignLeft | Qt.AlignVCenter,
               (f"❤ {fav}" + (f" · {team}" if team else "")) if fav else f"{career['matches']} partidas analisadas")
    if weapon:
        g.drawPixmap(280, 160, wp.sticker(150, weapon))
        g.setPen(QColor(TEXT))
        g.setFont(font(28, True))
        g.drawText(QRectF(445, 160, W - 500, 36), Qt.AlignLeft | Qt.AlignVCenter, wp.display(weapon))
        g.setPen(QColor(MUTED))
        g.setFont(font(20))
        line = "Arma favorita"
        if weapon_stats:
            line = f"{weapon_stats['kills']} abates · {weapon_stats['hs_pct']:.0%} HS"
            if weapon_stats.get("accuracy") is not None:
                line += f" · {weapon_stats['accuracy']:.0%} precisão"
        g.drawText(QRectF(445, 196, W - 500, 30), Qt.AlignLeft | Qt.AlignVCenter, line)

    rating = career.get("rating")
    stats = [("RATING MÉDIO", "—" if rating is None else f"{rating:.2f}"), ("PARTIDAS", str(career["matches"])),
             ("VITÓRIAS", pct(career.get("winrate"))), ("HS", pct(career.get("hs_pct"))),
             ("MELHOR MAPA", career.get("best_map") or "—")]
    bw = (W - 120 - 4 * 20) / 5
    for i, (label, value) in enumerate(stats):
        box(g, QRectF(60 + i * (bw + 20), 270, bw, 130), label, value, i == 0)

    g.setPen(QColor(TEXT))
    g.setFont(font(24, True))
    g.drawText(QRectF(60, 420, 400, 36), Qt.AlignLeft | Qt.AlignVCenter, "Qualidades")
    x = 60
    g.setFont(font(20, True))
    if not qualities:
        g.setPen(QColor(MUTED))
        g.setFont(font(20))
        g.drawText(QRectF(60, 462, W - 120, 44), Qt.AlignLeft | Qt.AlignVCenter,
                   "Jogue mais partidas para o app destacar seus pontos fortes.")
    for q, value in qualities[:3]:
        text = f"✔ {q}: {value}"
        w = min(g.fontMetrics().horizontalAdvance(text) + 36, W - 60 - x)
        if w < 120:
            break
        g.setPen(QPen(QColor(GOOD), 2))
        g.setBrush(QColor(PANEL))
        g.drawRoundedRect(QRectF(x, 462, w, 44), 22, 22)
        g.setPen(QColor(GOOD))
        g.drawText(QRectF(x + 18, 462, w - 36, 44), Qt.AlignLeft | Qt.AlignVCenter,
                   g.fontMetrics().elidedText(text, Qt.ElideRight, int(w - 36)))
        x += w + 14

    done, total = achievements
    g.setPen(QColor(MUTED))
    g.setFont(font(20))
    extra = f"🏆 {done} de {total} conquistas"
    if career.get("aces"):
        extra += f" · {int(career['aces'])} ace{'s' if career['aces'] > 1 else ''}"
    g.drawText(QRectF(60, 550, W - 120, 40), Qt.AlignLeft | Qt.AlignVCenter, extra)
    g.drawText(QRectF(60, 550, W - 120, 40), Qt.AlignRight | Qt.AlignVCenter, "CS2 Analytics")
    g.end()
    return img


def match_card(m, sid, p, profile, name):
    mine, theirs = team_scores(m).get(sid, [0, 0])
    plays = highlights(m, sid, limit=1)
    img = QImage(W, H, QImage.Format_ARGB32)
    img.fill(QColor(BG))
    g = QPainter(img)
    g.setRenderHint(QPainter.Antialiasing)
    g.setRenderHint(QPainter.TextAntialiasing)
    grad = QLinearGradient(0, 0, W, H)
    grad.setColorAt(0, QColor(PANEL))
    grad.setColorAt(1, QColor(BG))
    g.fillRect(img.rect(), grad)
    g.setPen(Qt.NoPen)
    g.setBrush(QColor(ACCENT))
    g.drawRect(QRectF(0, 0, 14, H))

    g.drawPixmap(60, 60, prof.avatar(200, profile, 0.0))
    g.setPen(QColor(TEXT))
    g.setFont(font(54, True))
    g.drawText(QRectF(290, 70, W - 340, 70), Qt.AlignLeft | Qt.AlignVCenter, name)
    when = datetime.fromtimestamp(float(m.played_at or 0)).strftime("%d/%m/%Y")
    g.setPen(QColor(MUTED))
    g.setFont(font(26))
    g.drawText(QRectF(290, 145, W - 340, 40), Qt.AlignLeft | Qt.AlignVCenter,
               f"{MAP_NAMES.get(m.map_name, m.map_name)} · {when}")
    result = GOOD if mine > theirs else BAD if mine < theirs else MUTED
    g.setPen(QColor(result))
    g.setFont(font(64, True))
    g.drawText(QRectF(290, 185, 500, 80), Qt.AlignLeft | Qt.AlignVCenter, f"{mine} – {theirs}")
    g.setFont(font(24, True))
    g.drawText(QRectF(560, 185, 400, 80), Qt.AlignLeft | Qt.AlignVCenter,
               "VITÓRIA" if mine > theirs else "DERROTA" if mine < theirs else "EMPATE")

    stats = [("RATING", f"{p['rating']:.2f}"), ("K / D / A", f"{int(p['kills'])} / {int(p['deaths'])} / {int(p['assists'])}"),
             ("ADR", f"{p['adr']:.0f}"), ("HS", f"{p['hs_pct']:.0%}"), ("KAST", f"{p['kast']:.0%}")]
    box_w = (W - 120 - 4 * 20) / 5
    for i, (label, value) in enumerate(stats):
        x = 60 + i * (box_w + 20)
        g.setPen(QPen(QColor(LINE), 2))
        g.setBrush(QColor(PANEL))
        g.drawRoundedRect(QRectF(x, 310, box_w, 150), 16, 16)
        g.setPen(QColor(MUTED))
        g.setFont(font(20, True))
        g.drawText(QRectF(x, 325, box_w, 30), Qt.AlignCenter, label)
        g.setPen(QColor(ACCENT if i == 0 else TEXT))
        g.setFont(font(44 if i != 1 else 36, True))
        g.drawText(QRectF(x, 360, box_w, 80), Qt.AlignCenter, value)

    g.setPen(QColor(TEXT))
    g.setFont(font(26, True))
    best = f"⭐ Melhor jogada: {plays[0]['name']} no round {plays[0]['round']}" if plays else "⭐ Sem jogada destaque nesta partida"
    g.drawText(QRectF(60, 490, W - 120, 50), Qt.AlignLeft | Qt.AlignVCenter, best)
    g.setPen(QColor(MUTED))
    g.setFont(font(20))
    g.drawText(QRectF(60, 560, W - 120, 40), Qt.AlignRight | Qt.AlignVCenter, "CS2 Analytics")
    g.end()
    return img
