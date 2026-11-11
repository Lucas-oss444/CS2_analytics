import math
import re
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path

import numpy as np
from PySide6.QtCore import QPointF, QRectF, Qt, QThread, QTimer, QUrl, Signal
from PySide6.QtGui import QColor, QDesktopServices, QFont, QGuiApplication, QImage, QPainter, QPen
from PySide6.QtWidgets import (QComboBox, QDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton,
                               QScrollArea, QVBoxLayout, QWidget)

from . import library
from .coach import MAP_NAMES
from .delegate import REL_ROLE, StripeDelegate
from .demo import CT, TICKRATE
from .replay import RoundTrack, bounds, density, highlights, sites
from .stats import relations
from .theme import ACCENT, BAD, BG, CT_COLOR, LINE, MUTED, T_COLOR, TEXT, fs

SPEEDS = [("0.5x", 0.5), ("1x", 1.0), ("2x", 2.0), ("4x", 4.0)]
CS2_DEFAULT = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\game\csgo")
KEY = "F8"


def label(text, size=13, color=TEXT, bold=False):
    w = QLabel(text)
    w.setWordWrap(True)
    w.setStyleSheet(f"color:{color};font-size:{fs(size)}px;{'font-weight:600;' if bold else ''}background:transparent")
    return w


def clock(ticks):
    s = max(0, int(ticks / TICKRATE))
    return f"{s // 60}:{s % 60:02d}"


def csgo_dir(original):
    for parent in Path(original).parents:
        if parent.name.lower() == "csgo" and parent.parent.name.lower() == "game":
            return parent
    return CS2_DEFAULT if CS2_DEFAULT.exists() else None


def console_name(name):
    return re.sub(r'["\';\r\n\t]', "", name).strip()[:40]


RECORD_ON = ["sv_cheats 1", "cl_drawhud 0", "spec_show_xray 0"]
RECORD_OFF = ["cl_drawhud 1", "spec_show_xray 1"]
RESTORE_KEY, PAUSE_KEY = "F9", "P"


def write_cs2_cfg(original, tick, player, record=False):
    base = csgo_dir(original)
    if base is None:
        raise ValueError("não encontrei a pasta do CS2 neste PC.")
    demo = Path(original)
    try:
        rel = demo.with_suffix("").relative_to(base).as_posix()
    except ValueError:
        raise ValueError("a demo precisa estar dentro da pasta do CS2 (…\\game\\csgo\\replays). "
                         "Copie o arquivo .dem para lá e tente de novo.")
    if not re.fullmatch(r"[\w./-]+", rel):
        raise ValueError("o nome do arquivo da demo tem caracteres que o CS2 não aceita.")
    cfg = base / "cfg"
    cfg.mkdir(exist_ok=True)
    start = max(0, int(tick) - (3 * TICKRATE if record else 0))
    jump = (RECORD_ON if record else []) + [f"demo_gototick {start}"]
    name = console_name(player or "")
    if name:
        jump.append(f'spec_player "{name}"')
    jump += ["spec_mode 1", "demo_resume"]
    (cfg / "cs2analytics_lance.cfg").write_text("\n".join(jump) + "\n", encoding="utf-8")
    (cfg / "cs2analytics_normal.cfg").write_text("\n".join(RECORD_OFF) + "\n", encoding="utf-8")
    binds = f"bind {KEY} \"exec cs2analytics_lance\"\n"
    if record:
        binds += f"bind {RESTORE_KEY} \"exec cs2analytics_normal\"\nbind {PAUSE_KEY} demo_togglepause\n"
    (cfg / "cs2analytics.cfg").write_text(
        f"playdemo {rel}\n{binds}"
        f"echo \"CS2 Analytics: quando a demo abrir, aperte {KEY} para ir ao lance\"\n", encoding="utf-8")
    return rel


NO_WINDOW = 0x08000000


def steam_exe():
    if sys.platform == "win32":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as key:
                exe = Path(winreg.QueryValueEx(key, "SteamExe")[0])
                if exe.name.lower() == "steam.exe" and exe.exists():
                    return exe
        except OSError:
            pass
    for exe in (Path(r"C:\Program Files (x86)\Steam\steam.exe"), Path(r"C:\Program Files\Steam\steam.exe")):
        if exe.exists():
            return exe
    return None


def cs2_running():
    if sys.platform != "win32":
        return False
    try:
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq cs2.exe", "/NH"], capture_output=True, text=True,
                             timeout=5, creationflags=NO_WINDOW).stdout
        return "cs2.exe" in out.lower()
    except (OSError, subprocess.SubprocessError):
        return False


def launch_cs2():
    if cs2_running():
        return "running"
    exe = steam_exe()
    if exe:
        subprocess.Popen([str(exe), "-applaunch", "730", "+exec", "cs2analytics"],
                         creationflags=NO_WINDOW if sys.platform == "win32" else 0)
        return "launched"
    QDesktopServices.openUrl(QUrl("steam://run/730//+exec%20cs2analytics/"))
    return "url"


def launch_pov(parent, mid, tick, rnd, default_sid=None, record=False):
    m = library.load(mid)
    names = dict(zip(m.roster.sid, m.roster.name))
    r = m.rounds[m.rounds["round"] == rnd].iloc[0]
    players = [(sid, names.get(sid, sid), TEXT) for sid in m.roster[m.roster["round"] == rnd].sid]
    dlg = PovDialog(parent, players, default_sid, f"Round {rnd} · {clock(tick - r.start_tick)}")
    if not dlg.exec():
        return None
    original = str(library.meta(mid).get("original", ""))
    try:
        write_cs2_cfg(original, tick, names.get(dlg.player.currentData(), ""), record)
    except (ValueError, OSError) as e:
        QMessageBox.warning(parent, "Visão do jogador", f"Não foi possível preparar o CS2: {e}")
        return None
    QGuiApplication.clipboard().setText("exec cs2analytics")
    how = launch_cs2()
    if record:
        QMessageBox.information(parent, "Gravar o lance",
                                ("O CS2 já está aberto: no console (tecla '), cole com Ctrl+V o comando exec cs2analytics "
                                 "(já copiado) e aperte Enter.\n\n" if how == "running" else "Abrindo o CS2 com a demo.\n\n")
                                + "Quando a demo carregar:\n"
                                "1. Aperte Shift+F2 para esconder a barra de controle da demo.\n"
                                "2. Comece a gravar (Win+Alt+R, Alt+F9 na NVIDIA ou o OBS).\n"
                                f"3. Aperte {KEY}: o HUD some e a demo volta 3 s antes do lance, na visão do jogador.\n\n"
                                f"{PAUSE_KEY} pausa e continua. {RESTORE_KEY} traz o HUD de volta e Shift+F2 mostra a barra de novo.")
    elif how == "running":
        QMessageBox.information(parent, "Visão do jogador",
                                "O CS2 já está aberto, então ele não recebe o comando sozinho.\n\n"
                                "No CS2, abra o console (tecla ' ou ~), cole com Ctrl+V o comando exec cs2analytics "
                                f"(já copiado) e aperte Enter. Quando a demo carregar, aperte {KEY}.")
    else:
        QMessageBox.information(parent, "Visão do jogador",
                                f"Abrindo o CS2 com a demo. Quando ela carregar, aperte {KEY} para ir ao lance.\n\n"
                                "Se o jogo abrir só no menu, abra o console (tecla ' ou ~), cole com Ctrl+V o comando "
                                "exec cs2analytics (já copiado) e aperte Enter.\n\n"
                                "O console precisa estar ativado em Configurações → Jogo → Ativar console do desenvolvedor.")
    return how


class PosLoader(QThread):
    done = Signal(object, object, str)

    def __init__(self, mid):
        super().__init__()
        self.mid = mid

    def run(self):
        try:
            m = library.load(self.mid)
            self.done.emit(m, library.positions(self.mid), "")
        except Exception as e:
            self.done.emit(None, None, str(e))


class ReplayView(QWidget):
    picked = Signal(str)

    def __init__(self):
        super().__init__()
        self.setMinimumSize(420, 420)
        self.setCursor(Qt.PointingHandCursor)
        self.match = self.track = self.box = self.bg = self.round = None
        self.sites = {}
        self.colors, self.names = {}, {}
        self.tick = 0
        self.follow = None
        self.clip = None

    def set_match(self, m, positions, colors, names):
        self.match, self.colors, self.names, self.positions = m, colors, names, positions
        self.box = bounds(positions)
        grid = density(positions, self.box)
        rgba = np.zeros((*grid.shape, 4), dtype=np.uint8)
        rgba[..., 0], rgba[..., 1], rgba[..., 2] = 120, 130, 145
        rgba[..., 3] = (np.clip(grid * 2.4, 0, 1) ** 0.8 * 200).astype(np.uint8)
        if "site" in positions:
            zone = density(positions[positions.site != ""], self.box)
            a = np.clip(zone * 3, 0, 1)[..., None]
            rgba[..., :3] = (rgba[..., :3] * (1 - a) + np.array([245, 166, 35]) * a).astype(np.uint8)
            rgba[..., 3] = np.maximum(rgba[..., 3], (a[..., 0] * 90).astype(np.uint8))
        self.bg = QImage(rgba.data, grid.shape[1], grid.shape[0], grid.shape[1] * 4, QImage.Format_RGBA8888).copy()
        self.sites = sites(positions)

    def set_round(self, rnd):
        self.round = self.match.rounds[self.match.rounds["round"] == rnd].iloc[0]
        self.track = RoundTrack(self.positions, int(self.round.start_tick), int(self.round.end_tick) + 3 * TICKRATE)
        self.kills = self.match.kills[self.match.kills["round"] == rnd]
        self.tick = int(self.round.start_tick)
        self.update()

    def area(self, w, h):
        side = min(w, h) - 16
        return QRectF((w - side) / 2, (h - side) / 2, side, side)

    def to_screen(self, rect, x, y):
        x0, y0, size = self.box
        return QPointF(rect.left() + (x - x0) / size * rect.width(), rect.top() + (1 - (y - y0) / size) * rect.height())

    def mousePressEvent(self, e):
        if not self.track:
            return
        rect = self.area(self.width(), self.height())
        best, dist = None, 1e9
        for sid, (x, y, *_rest) in self.track.at(self.tick).items():
            pt = self.to_screen(rect, x, y)
            d = math.hypot(pt.x() - e.position().x(), pt.y() - e.position().y())
            if d < dist:
                best, dist = sid, d
        if best and dist < 30:
            self.follow = best
            self.picked.emit(best)
            self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        self.draw(p, self.width(), self.height(), self.tick)
        p.end()

    def draw(self, p, w, h, tick):
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(0, 0, w, h, QColor(BG))
        if not self.track:
            p.setPen(QColor(MUTED))
            p.drawText(QRectF(0, 0, w, h), Qt.AlignCenter, "Escolha uma partida para assistir")
            return
        rect = self.area(w, h)
        p.drawImage(rect, self.bg)
        big = QFont()
        big.setPixelSize(max(18, int(rect.width() / 22)))
        big.setBold(True)
        p.setFont(big)
        for letter, (x, y) in self.sites.items():
            pt = self.to_screen(rect, x, y)
            box = QRectF(pt.x() - 40, pt.y() - 30, 80, 60)
            p.setPen(QColor(0, 0, 0, 160))
            p.drawText(box.translated(2, 2), Qt.AlignCenter, letter)
            p.setPen(QColor(ACCENT))
            p.drawText(box, Qt.AlignCenter, letter)
        now = self.track.at(tick)
        for k in self.kills.itertuples(index=False):
            age = tick - k.tick
            if 0 <= age <= 2 * TICKRATE and k.attacker in now and k.victim in now:
                c = QColor(self.colors.get(k.attacker, TEXT))
                c.setAlphaF(max(0.0, 1 - age / (2 * TICKRATE)))
                p.setPen(QPen(c, 2, Qt.DashLine))
                p.drawLine(self.to_screen(rect, *now[k.attacker][:2]), self.to_screen(rect, *now[k.victim][:2]))
        font = QFont()
        font.setPixelSize(max(11, int(rect.width() / 60)))
        p.setFont(font)
        r = max(6.0, rect.width() / 85)
        for sid, (x, y, yaw, alive, hp) in now.items():
            pt = self.to_screen(rect, x, y)
            color = QColor(self.colors.get(sid, MUTED))
            if not alive:
                p.setPen(QPen(QColor(MUTED), 2))
                p.drawLine(pt + QPointF(-r * 0.7, -r * 0.7), pt + QPointF(r * 0.7, r * 0.7))
                p.drawLine(pt + QPointF(-r * 0.7, r * 0.7), pt + QPointF(r * 0.7, -r * 0.7))
                continue
            ang = math.radians(-yaw)
            if sid == self.follow:
                p.setPen(QPen(QColor(TEXT), 2))
                p.setBrush(Qt.NoBrush)
                p.drawEllipse(pt, r * 1.9, r * 1.9)
            p.setPen(QPen(color, 2))
            p.drawLine(pt, pt + QPointF(math.cos(ang) * r * 2.6, math.sin(ang) * r * 2.6))
            p.setPen(QPen(QColor(BG), 1.5))
            p.setBrush(color)
            p.drawEllipse(pt, r, r)
            if hp < 100:
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(0, 0, 0, 150))
                p.drawRect(QRectF(pt.x() - r, pt.y() + r + 2, 2 * r, 3))
                p.setBrush(QColor("#3fb950") if hp > 50 else QColor(ACCENT) if hp > 20 else QColor(BAD))
                p.drawRect(QRectF(pt.x() - r, pt.y() + r + 2, 2 * r * hp / 100, 3))
            p.setPen(QColor(TEXT))
            p.drawText(QRectF(pt.x() - 70, pt.y() - r - 19, 140, 16), Qt.AlignCenter, self.names.get(sid, "")[:16])
        p.setPen(QColor(MUTED))
        p.drawText(QRectF(rect.left() + 8, rect.top() + 6, rect.width(), 20), Qt.AlignLeft,
                   f"Round {int(self.round['round'])}  ·  {clock(tick - self.round.start_tick)}")
        if self.clip:
            p.setPen(QColor(ACCENT))
            p.drawText(QRectF(rect.left(), rect.top() + 6, rect.width() - 10, 20), Qt.AlignRight, "✂ criando clipe")


class Timeline(QWidget):
    seek = Signal(int)

    def __init__(self):
        super().__init__()
        self.setFixedHeight(46)
        self.setCursor(Qt.PointingHandCursor)
        self.start = self.end = self.tick = 0
        self.marks = []
        self.clip = None

    def set_range(self, start, end, marks):
        self.start, self.end, self.marks = start, end, marks
        self.update()

    def x_of(self, tick):
        span = max(1, self.end - self.start)
        return 10 + (tick - self.start) / span * (self.width() - 20)

    def tick_of(self, x):
        span = max(1, self.end - self.start)
        return int(self.start + (x - 10) / max(1, self.width() - 20) * span)

    def mousePressEvent(self, e):
        self.seek.emit(max(self.start, min(self.end, self.tick_of(e.position().x()))))

    def mouseMoveEvent(self, e):
        self.mousePressEvent(e)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        y = self.height() / 2 + 6
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(LINE))
        p.drawRoundedRect(QRectF(10, y - 4, self.width() - 20, 8), 4, 4)
        if self.clip:
            a, b = sorted(self.clip)
            p.setBrush(QColor(245, 166, 35, 90))
            p.drawRoundedRect(QRectF(self.x_of(a), y - 10, max(4, self.x_of(b) - self.x_of(a)), 20), 4, 4)
            p.setBrush(QColor(ACCENT))
            for t in (a, b):
                p.drawRect(QRectF(self.x_of(t) - 1.5, y - 12, 3, 24))
        p.setBrush(QColor(ACCENT))
        p.drawRoundedRect(QRectF(10, y - 4, max(0, self.x_of(self.tick) - 10), 8), 4, 4)
        for t, color in self.marks:
            p.setBrush(QColor(color))
            p.setPen(QPen(QColor(BG), 1.5))
            p.drawEllipse(QPointF(self.x_of(t), y - 15), 5, 5)
        p.setPen(QPen(QColor(BG), 2))
        p.setBrush(QColor(TEXT))
        p.drawEllipse(QPointF(self.x_of(self.tick), y), 8, 8)
        p.end()


class KillRow(QWidget):
    def __init__(self, text, color, on_jump, on_clip):
        super().__init__()
        lay = QHBoxLayout(self)
        lay.setContentsMargins(6, 2, 2, 2)
        jump = QPushButton(text)
        jump.setObjectName("killrow")
        jump.setStyleSheet(f"color:{color}")
        jump.setToolTip("Ir para este lance")
        jump.clicked.connect(on_jump)
        clip = QPushButton("✂")
        clip.setObjectName("chip")
        clip.setToolTip("Clipar esta kill (5 s antes até 2 s depois)")
        clip.setFixedWidth(40)
        clip.clicked.connect(on_clip)
        lay.addWidget(jump, 1)
        lay.addWidget(clip)


class ClipCard(QFrame):
    def __init__(self, clip, who, page):
        super().__init__()
        self.setObjectName("clipcard")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(6)
        kind = "⭐ Destaque automático" if clip.get("auto") else "✂ Seu clipe"
        lay.addWidget(label(clip["name"], 13, bold=True))
        dur = (clip["end"] - clip["start"]) / TICKRATE
        lay.addWidget(label(f"{kind} · Round {clip['round']} · {dur:.0f} s" + (f" · {who}" if who else ""), 11, MUTED))
        row = QHBoxLayout()
        row.setSpacing(6)
        for text, tip, fn in (("▶ Ver", "Assistir o clipe aqui", page.play_clip), ("👁 No CS2", "Ver na visão do jogador, no CS2", page.open_cs2),
                              ("🎥 Gravar", "Abrir no CS2 sem HUD, na visão do jogador, pronto para gravar a tela", page.record_clip)):
            b = QPushButton(text)
            b.setToolTip(tip)
            b.clicked.connect(lambda _, f=fn: f(clip))
            row.addWidget(b)
        if not clip.get("auto"):
            d = QPushButton("🗑")
            d.setToolTip("Apagar clipe")
            d.setFixedWidth(44)
            d.clicked.connect(lambda: page.delete_clip(clip))
            row.addWidget(d)
        lay.addLayout(row)


class PovDialog(QDialog):
    def __init__(self, parent, players, current, moment):
        super().__init__(parent)
        self.setWindowTitle("Visão do jogador")
        self.setMinimumWidth(520)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 22, 24, 20)
        lay.setSpacing(10)
        lay.addWidget(label("👁  Ver pela tela do jogador", 17, bold=True))
        lay.addWidget(label("A visão em primeira pessoa só existe dentro do CS2. O app abre a demo no jogo e deixa tudo "
                            f"pronto: quando a partida carregar, é só apertar <b>{KEY}</b> para ir direto ao lance, "
                            "na tela do jogador escolhido.", 12, MUTED))
        lay.addWidget(label("Jogador", 12, MUTED))
        self.player = QComboBox()
        for sid, name, color in players:
            self.player.addItem(name, sid)
        self.player.setCurrentIndex(max(0, self.player.findData(current)))
        lay.addWidget(self.player)
        lay.addWidget(label(f"Momento: {moment}", 12, MUTED))
        steps = label(f"<b>1.</b> Clique em Abrir no CS2.<br><b>2.</b> Espere a demo carregar.<br><b>3.</b> Aperte <b>{KEY}</b>.<br>"
                      f"<span style='color:{MUTED}'>Se o CS2 já estiver aberto, abra o console e digite "
                      "<code>exec cs2analytics</code>.</span>", 12)
        steps.setTextFormat(Qt.RichText)
        lay.addWidget(steps)
        row = QHBoxLayout()
        cancel = QPushButton("Cancelar")
        cancel.clicked.connect(self.reject)
        go = QPushButton("🎮  Abrir no CS2")
        go.setObjectName("primary")
        go.clicked.connect(self.accept)
        row.addStretch()
        row.addWidget(cancel)
        row.addWidget(go)
        lay.addLayout(row)


class ReplayPage(QWidget):
    def __init__(self, main):
        super().__init__()
        self.main = main
        self.mid = self.match = None
        self.stop_at = None
        self.names = {}
        self.view = ReplayView()
        self.view.picked.connect(self.player_picked)
        self.timeline = Timeline()
        self.timeline.seek.connect(self.jump)

        self.match_box = QComboBox()
        self.match_box.setMinimumWidth(320)
        self.match_box.setItemDelegate(StripeDelegate(self.match_box))
        self.match_box.currentIndexChanged.connect(self.pick_match)
        self.round_box = QComboBox()
        self.round_box.currentIndexChanged.connect(self.pick_round)
        self.mode_2d = QPushButton("🗺  Visão 2D")
        self.mode_pov = QPushButton("👁  Visão do jogador")
        for b in (self.mode_2d, self.mode_pov):
            b.setObjectName("chip")
            b.setCheckable(True)
        self.mode_2d.setChecked(True)
        self.mode_2d.clicked.connect(lambda: self.mode_2d.setChecked(True))
        self.mode_pov.clicked.connect(self.open_pov)

        self.play_btn = QPushButton("▶  Play")
        self.play_btn.setObjectName("primary")
        self.play_btn.setMinimumWidth(120)
        self.play_btn.clicked.connect(self.toggle)
        back = QPushButton("⏪ 5 s")
        back.clicked.connect(lambda: self.jump(self.view.tick - 5 * TICKRATE))
        fwd = QPushButton("5 s ⏩")
        fwd.clicked.connect(lambda: self.jump(self.view.tick + 5 * TICKRATE))
        self.speed = QComboBox()
        for name, v in SPEEDS:
            self.speed.addItem(name, v)
        self.speed.setCurrentIndex(1)
        self.time = label("", 12, MUTED)
        self.status = label("", 12, MUTED)
        self.follow_label = label("Clique num jogador no mapa para segui-lo.", 11, MUTED)

        self.kill_list = QVBoxLayout()
        self.kill_list.setSpacing(2)
        self.clip_list = QVBoxLayout()
        self.clip_list.setSpacing(8)

        self.creator = QFrame()
        self.creator.setObjectName("card")
        cl = QVBoxLayout(self.creator)
        cl.setContentsMargins(14, 12, 14, 12)
        cl.addWidget(label("✂  Novo clipe", 14, ACCENT, True))
        cl.addWidget(label("A faixa laranja na linha do tempo é o seu clipe. Ajuste os pontos e salve.", 11, MUTED))
        marks = QVBoxLayout()
        marks.setSpacing(6)
        self.start_btn = QPushButton()
        self.end_btn = QPushButton()
        self.start_btn.clicked.connect(lambda: self.set_edge(0))
        self.end_btn.clicked.connect(lambda: self.set_edge(1))
        marks.addWidget(self.start_btn)
        marks.addWidget(self.end_btn)
        cl.addLayout(marks)
        self.length = label("", 12, MUTED)
        cl.addWidget(self.length)
        self.clip_name = QLineEdit()
        self.clip_name.setPlaceholderText("Nome do clipe (opcional)")
        cl.addWidget(self.clip_name)
        actions = QHBoxLayout()
        preview = QPushButton("▶ Testar")
        preview.clicked.connect(self.preview_draft)
        cancel = QPushButton("Cancelar")
        cancel.clicked.connect(self.cancel_draft)
        save = QPushButton("💾 Salvar")
        save.setObjectName("primary")
        save.clicked.connect(self.save_draft)
        actions.addWidget(preview)
        actions.addWidget(cancel)
        actions.addWidget(save)
        cl.addLayout(actions)
        self.creator.hide()

        new_clip = QPushButton("✂  Criar clipe deste momento")
        new_clip.setObjectName("primary")
        new_clip.setMinimumHeight(40)
        new_clip.clicked.connect(self.new_draft)
        self.new_clip_btn = new_clip

        side = QVBoxLayout()
        side.setSpacing(8)
        side.addWidget(label("Como clipar", 14, bold=True))
        side.addWidget(label("• Clique em <b>✂</b> ao lado de uma kill para clipar o lance na hora.<br>"
                             "• Ou pause no momento que quiser e use <b>Criar clipe deste momento</b>.<br>"
                             "• As ⭐ são as melhores jogadas que o app encontrou sozinho.", 12, MUTED))
        side.addWidget(new_clip)
        side.addWidget(self.creator)
        side.addWidget(label("Kills do round", 14, bold=True))
        side.addLayout(self.kill_list)
        side.addWidget(label("Clipes desta partida", 14, bold=True))
        side.addLayout(self.clip_list)
        side.addStretch()
        holder = QWidget()
        holder.setLayout(side)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidget(holder)
        scroll.setFixedWidth(380)
        side.setContentsMargins(0, 0, 10, 0)

        top = QHBoxLayout()
        top.addWidget(label("Replay", 18, bold=True))
        top.addSpacing(10)
        top.addWidget(self.match_box)
        top.addWidget(self.round_box)
        top.addStretch()
        top.addWidget(self.mode_2d)
        top.addWidget(self.mode_pov)
        controls = QHBoxLayout()
        for w in (self.play_btn, back, fwd, self.speed):
            controls.addWidget(w)
        controls.addStretch()
        controls.addWidget(self.time)
        left = QVBoxLayout()
        left.addWidget(self.view, 1)
        left.addWidget(self.follow_label)
        left.addWidget(self.timeline)
        left.addLayout(controls)
        body = QHBoxLayout()
        body.setSpacing(16)
        body.addLayout(left, 1)
        body.addWidget(scroll)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 18, 28, 18)
        lay.setSpacing(8)
        lay.addLayout(top)
        lay.addWidget(self.status)
        lay.addLayout(body, 1)

        self.timer = QTimer(self)
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.step)
        self.draft = None
        self.want = None
        self.pending = None

    def refresh(self):
        entries = library.entries()
        current = self.main.current_ids[0] if self.main.current_ids else None
        self.match_box.blockSignals(True)
        self.match_box.clear()
        for e in entries:
            name = MAP_NAMES.get(e.get("map"), str(e.get("map")))
            score = e.get("scores", {}).get(self.main.me) if self.main.me else None
            when = datetime.fromtimestamp(float(e.get("played_at", 0))).strftime("%d/%m %H:%M")
            self.match_box.addItem(f"{name} · {when}" + (f" · {score[0]}–{score[1]}" if score else ""), e["id"])
            color = MUTED if not score or score[0] == score[1] else CT_COLOR if score[0] > score[1] else BAD
            self.match_box.setItemData(self.match_box.count() - 1, color, REL_ROLE)
        self.match_box.setCurrentIndex(max(0, self.match_box.findData(self.want or self.mid or current)))
        self.match_box.blockSignals(False)
        if self.match_box.count() and self.match_box.currentData() != self.mid:
            self.pick_match()
        if not entries:
            self.status.setText("Nenhuma demo salva. Adicione uma em Minhas demos.")
        elif self.match is not None and self.match_box.currentData() == self.mid:
            self.fill_clips()

    def show_clip(self, mid, clip, action):
        self.want, self.pending = mid, (clip, action)
        if self.mid == mid and self.match is not None:
            return self.run_pending()
        idx = self.match_box.findData(mid)
        if idx >= 0 and self.match_box.currentIndex() != idx:
            self.match_box.setCurrentIndex(idx)
        else:
            self.pick_match()

    def run_pending(self):
        if not self.pending:
            return
        clip, action = self.pending
        self.pending = self.want = None
        self.play_clip(clip)

    def pick_match(self):
        color = self.match_box.currentData(REL_ROLE)
        self.match_box.setStyleSheet(f"QComboBox {{ color: {color}; }}" if color else "")
        mid = self.match_box.currentData()
        if not mid or (getattr(self, "loader", None) and self.loader.isRunning()):
            return
        self.pause()
        self.status.setText("Preparando o replay… (na primeira vez o app lê as posições da demo original)")
        self.loader = PosLoader(mid)
        self.loader.done.connect(lambda m, pos, err, mid=mid: self.loaded(mid, m, pos, err))
        self.loader.start()

    def loaded(self, mid, m, positions, err):
        if err:
            self.status.setText(err)
            self.view.track = None
            self.view.update()
            return
        self.mid, self.match = mid, m
        me = self.main.me
        rel = relations([m], me) if me and me in set(m.roster.sid) else {}
        first = m.roster[m.roster["round"] == m.roster["round"].min()]
        start_team = dict(zip(first.sid, first.team))
        colors = {}
        for sid in set(m.roster.sid):
            kind = rel.get(sid)
            colors[sid] = ACCENT if kind == "me" else CT_COLOR if kind == "ally" else BAD if kind == "enemy" else \
                (CT_COLOR if start_team.get(sid) == CT else T_COLOR)
        self.names = dict(zip(m.roster.sid, m.roster.name))
        self.view.follow = me if me in self.names else None
        self.view.set_match(m, positions, colors, self.names)
        legend = "Dourado = você · Azul = aliados · Vermelho = inimigos" if rel else "Azul = começou de CT · Laranja = começou de TR"
        self.status.setText(f"{MAP_NAMES.get(m.map_name, m.map_name)} · {len(m.rounds)} rounds · {legend}")
        self.round_box.blockSignals(True)
        self.round_box.clear()
        for r in m.rounds["round"]:
            self.round_box.addItem(f"Round {r}", int(r))
        self.round_box.blockSignals(False)
        self.pick_round()
        self.fill_clips()
        self.player_picked(self.view.follow)
        if self.want and self.want != mid:
            idx = self.match_box.findData(self.want)
            self.match_box.blockSignals(True)
            self.match_box.setCurrentIndex(idx)
            self.match_box.blockSignals(False)
            return self.pick_match()
        if self.pending:
            self.run_pending()

    def pick_round(self):
        rnd = self.round_box.currentData()
        if rnd is None or self.match is None:
            return
        self.pause()
        self.cancel_draft()
        self.view.set_round(rnd)
        r = self.view.round
        marks = [(int(k.tick), self.view.colors.get(k.attacker, MUTED)) for k in self.view.kills.itertuples(index=False)]
        self.timeline.set_range(int(r.start_tick), int(r.end_tick) + 3 * TICKRATE, marks)
        self.timeline.tick = int(r.start_tick)
        self.fill_kills()
        self.update_time()

    def clear(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

    def fill_kills(self):
        self.clear(self.kill_list)
        start = self.view.round.start_tick
        for k in self.view.kills.itertuples(index=False):
            killer = self.names.get(k.attacker, "Mundo") if k.attacker else "Mundo"
            victim = self.names.get(k.victim, "?")
            text = f"{clock(k.tick - start)}  {killer[:12]} ➜ {victim[:12]}" + (" 🎯" if k.headshot else "")
            row = KillRow(text, self.view.colors.get(k.attacker, TEXT),
                          lambda _=None, t=int(k.tick): self.jump(t - 3 * TICKRATE),
                          lambda _=None, t=int(k.tick), a=killer, v=victim: self.clip_kill(t, a, v))
            self.kill_list.addWidget(row)
        if not len(self.view.kills):
            self.kill_list.addWidget(label("Nenhuma kill neste round.", 12, MUTED))

    def all_clips(self):
        sid = self.main.me if self.main.me in self.names else None
        return library.clips(self.mid)[::-1] + highlights(self.match, sid)

    def fill_clips(self):
        self.clear(self.clip_list)
        clips = self.all_clips()
        for c in clips:
            who = self.names.get(c.get("sid"), "") if c.get("auto") else ""
            self.clip_list.addWidget(ClipCard(c, who[:14], self))
        if not clips:
            self.clip_list.addWidget(label("Nenhum clipe ainda. Use ✂ numa kill para criar o primeiro.", 12, MUTED))

    def player_picked(self, sid):
        if sid:
            self.follow_label.setText(f"Seguindo: <b style='color:{self.view.colors.get(sid, TEXT)}'>{self.names.get(sid, '')}</b>"
                                      " · clique em outro jogador no mapa para trocar.")

    def toggle(self):
        if self.timer.isActive():
            self.pause()
        else:
            if self.view.round is not None and self.view.tick >= self.timeline.end:
                self.jump(int(self.view.round.start_tick))
            self.timer.start()
            self.play_btn.setText("⏸  Pausar")

    def pause(self):
        self.timer.stop()
        self.stop_at = None
        self.play_btn.setText("▶  Play")

    def step(self):
        if self.view.track is None:
            return self.pause()
        nxt = self.view.tick + self.speed.currentData() * TICKRATE * 0.05
        limit = self.stop_at or self.timeline.end
        if nxt >= limit:
            nxt = limit
            self.pause()
        self.set_tick(nxt)

    def set_tick(self, tick):
        self.view.tick = tick
        self.timeline.tick = tick
        self.view.update()
        self.timeline.update()
        self.update_time()

    def jump(self, tick):
        if self.view.round is None:
            return
        self.set_tick(max(self.timeline.start, min(self.timeline.end, int(tick))))

    def update_time(self):
        r = self.view.round
        if r is not None:
            self.time.setText(f"{clock(self.view.tick - r.start_tick)} / {clock(self.timeline.end - r.start_tick)}")

    def go_round(self, rnd):
        if self.round_box.currentData() != rnd:
            self.round_box.setCurrentIndex(self.round_box.findData(rnd))

    def play_clip(self, clip):
        self.go_round(clip["round"])
        self.jump(clip["start"])
        if not self.timer.isActive():
            self.toggle()
        self.stop_at = clip["end"]

    def clip_kill(self, tick, killer, victim):
        self.save_clip_data(f"{killer} ➜ {victim}", int(self.view.round["round"]),
                            max(self.timeline.start, tick - 5 * TICKRATE), min(self.timeline.end, tick + 2 * TICKRATE))

    def new_draft(self):
        if self.view.round is None:
            return
        self.pause()
        now = int(self.view.tick)
        self.draft = [max(self.timeline.start, now - 5 * TICKRATE), min(self.timeline.end, now + 3 * TICKRATE)]
        self.clip_name.clear()
        self.creator.show()
        self.new_clip_btn.hide()
        self.view.clip = self.timeline.clip = self.draft
        self.update_draft()

    def update_draft(self):
        a, b = self.draft
        start = self.view.round.start_tick
        self.start_btn.setText(f"⏮  Início em {clock(a - start)} · marcar agora")
        self.end_btn.setText(f"⏭  Fim em {clock(b - start)} · marcar agora")
        self.length.setText(f"Duração: {(b - a) / TICKRATE:.0f} s")
        self.timeline.update()
        self.view.update()

    def set_edge(self, i):
        if not self.draft:
            return
        self.draft[i] = int(self.view.tick)
        if self.draft[0] > self.draft[1]:
            self.draft.reverse()
        self.update_draft()

    def preview_draft(self):
        if self.draft:
            a, b = self.draft
            self.jump(a)
            if not self.timer.isActive():
                self.toggle()
            self.stop_at = b

    def cancel_draft(self):
        self.draft = None
        self.view.clip = self.timeline.clip = None
        self.creator.hide()
        self.new_clip_btn.show()
        self.timeline.update()
        self.view.update()

    def save_draft(self):
        a, b = self.draft
        if b - a < TICKRATE:
            return QMessageBox.information(self, "Clipes", "O clipe precisa ter pelo menos 1 segundo.")
        rnd = int(self.view.round["round"])
        self.save_clip_data(self.clip_name.text().strip() or f"Lance do round {rnd}", rnd, a, b)
        self.cancel_draft()

    def save_clip_data(self, name, rnd, start, end):
        items = library.clips(self.mid)
        items.append({"id": uuid.uuid4().hex, "name": name, "round": rnd, "start": int(start), "end": int(end),
                      "sid": self.main.me or ""})
        library.save_clips(self.mid, items)
        self.fill_clips()
        self.status.setText(f"✂ Clipe salvo: {name}. Ele está no topo da lista de clipes.")

    def delete_clip(self, clip):
        if QMessageBox.question(self, "Clipes", f"Apagar o clipe \"{clip['name']}\"?") == QMessageBox.Yes:
            library.save_clips(self.mid, [c for c in library.clips(self.mid) if c["id"] != clip["id"]])
            self.fill_clips()

    def players_now(self):
        rnd = int(self.view.round["round"])
        sids = self.match.roster[self.match.roster["round"] == rnd].sid
        return [(s, self.names.get(s, s), self.view.colors.get(s, TEXT)) for s in sids]

    def record_clip(self, clip):
        self.open_pov(clip, record=True)

    def open_pov(self, clip=None, record=False):
        self.mode_pov.setChecked(False)
        self.mode_2d.setChecked(True)
        if self.view.round is None:
            return
        is_clip = isinstance(clip, dict)
        tick = clip["start"] if is_clip else int(self.view.tick)
        rnd = clip["round"] if is_clip else int(self.view.round["round"])
        who = (clip.get("sid") if is_clip else None) or self.view.follow
        self.pause()
        if launch_pov(self, self.mid, tick, rnd, who, record):
            self.status.setText(f"🎮 Abrindo o CS2… quando a demo carregar, aperte {KEY}.")

    def open_cs2(self, clip):
        self.open_pov(clip)
