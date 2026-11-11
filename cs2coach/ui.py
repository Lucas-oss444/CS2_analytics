import html
import os
import re
import sys
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtCore import QEasingCurve, QEvent, QObject, QSize, Qt, QThread, QTimer, QUrl, QVariantAnimation, Signal
from PySide6.QtGui import QColor, QPixmap, QDesktopServices, QGuiApplication, QIcon, QPalette
from PySide6.QtWidgets import (QApplication, QCheckBox, QCompleter, QToolTip, QComboBox, QFileDialog, QFrame, QGridLayout, QHBoxLayout, QHeaderView,
                               QInputDialog, QLabel, QListWidget, QMainWindow, QMessageBox, QProgressBar, QPushButton, QScrollArea,
                               QStackedWidget, QTableWidget, QTableWidgetItem, QToolButton, QVBoxLayout, QWidget)

from .coach import (COMMANDS, COMMUNITY_MAPS, CONSISTENCY, PRO_TIPS, consistency, DRILL_CMD, DRILL_PRO, HELP, MAP_NAMES, MINUTES, diagnose, drill_text, glossary_for, has_tips,
                    plan_markdown, pro_tip, set_favorite, suggest_schedule, TEAMS, verdict, weekly_plan)
from .demo import NON_GUNS, load_demo
from .stats import METRICS, combine, match_stats, relations, rivals
from . import library
from . import profile as prof
from .delegate import REL_ROLE, StripeDelegate
from .dialogs import ProfileDialog, ThemeDialog, UpdateDialog
from .clips_ui import ClipsPage
from .replay_ui import ReplayPage
from . import progress as prog
from .card import match_card, profile_card
from . import weapons as wp
from .storage import HOME, History, load_config, save_config
from .updater import current_version
from .theme import (ACCENT, ACCENT_HOVER, ACCENT_PRESSED, BAD, BAR, BG, BORDER, BUTTON, CT_COLOR, GOOD, HOVER, INPUT, LINE,
                    MUTED, ON_ACCENT, PANEL, PRESSED, SELECTED, SOFT, T_COLOR, TEXT, fs, mix)

matplotlib.rcParams["axes.titlecolor"] = MUTED

CSS = (f"<style>td,th{{padding:5px 18px 5px 0}} th{{color:{MUTED};font-weight:normal;text-align:left}}"
       f" .muted{{color:{MUTED}}} .good{{color:{GOOD}}} .bad{{color:{BAD}}} h3{{margin:12px 0 4px}}</style>")
REPLAYS = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\game\csgo\replays")
ICON = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent)) / "assets" / "icon.png"
ASSETS = ICON.parent
LEVEL = {"good": GOOD, "warn": ACCENT, "bad": BAD, "muted": MUTED}
DAYS = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]


def fmt(key, value):
    return METRICS[key][1].format(value) if key in METRICS else str(value)


def compare(key, value, ref):
    if ref is None or key not in METRICS:
        return ""
    better = (value >= ref) == METRICS[key][2]
    return f'<span style="color:{GOOD if better else BAD}">{"▲" if value >= ref else "▼"}</span> ' \
           f'<span style="color:{MUTED}">lobby {fmt(key, ref)}</span>'


def table(headers, rows):
    head = "".join(f"<th>{h}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f"<table cellspacing=0><tr>{head}</tr>{body}</table>"


def label(text="", size=13, color=TEXT, bold=False):
    w = QLabel(text)
    w.setWordWrap(True)
    w.setTextFormat(Qt.RichText)
    w.setStyleSheet(f"color:{color};font-size:{fs(size)}px;{'font-weight:600;' if bold else ''}background:transparent")
    return w


def clear(layout):
    while layout.count():
        item = layout.takeAt(0)
        if item.widget():
            item.widget().setParent(None)


class Chart(FigureCanvasQTAgg):
    def __init__(self, height=2.6):
        self.fig = Figure(figsize=(7, height), facecolor=PANEL, layout="constrained")
        super().__init__(self.fig)
        self.setMinimumHeight(int(height * 90))

    def axes(self):
        self.fig.clear()
        ax = self.fig.add_subplot()
        ax.set_facecolor(PANEL)
        ax.tick_params(colors=MUTED, labelsize=10, length=0)
        for side, spine in ax.spines.items():
            spine.set_visible(side == "bottom")
            spine.set_color(LINE)
        ax.grid(axis="y", color=LINE, linewidth=0.6)
        ax.set_axisbelow(True)
        ax.xaxis.label.set_color(MUTED)
        return ax


REL_COLORS = {"me": ACCENT, "ally": CT_COLOR, "enemy": BAD, "mixed": MUTED}


class HelpIcon(QLabel):
    def __init__(self, entries=()):
        super().__init__("?")
        self.setObjectName("help")
        self.setAlignment(Qt.AlignCenter)
        self.setFixedSize(20, 20)
        self.setCursor(Qt.WhatsThisCursor)
        self.set(entries)

    def set(self, entries):
        self.entries = [(n, d) for n, d in entries if d]
        self.setVisible(bool(self.entries))
        self.setToolTip(self.html())

    def html(self):
        return ("<div style='max-width:360px'>" + "".join(
            f"<p style='margin:0 0 6px 0'><b>{html.escape(n)}</b><br>{html.escape(d)}</p>" for n, d in self.entries) + "</div>")

    def enterEvent(self, e):
        QToolTip.showText(self.mapToGlobal(self.rect().bottomLeft()), self.html(), self)
        super().enterEvent(e)


def help_row(widget, entries):
    row = QHBoxLayout()
    row.setSpacing(6)
    row.addWidget(widget, 1)
    row.addWidget(HelpIcon(entries), alignment=Qt.AlignTop)
    return row


class Card(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("card")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(4)
        self.title, self.value = label(size=12, color=MUTED), label(size=26, bold=True)
        self.badge, self.ref = QLabel(), label(size=11, color=MUTED)
        row = QHBoxLayout()
        row.setSpacing(8)
        row.addWidget(self.badge)
        row.addWidget(self.ref, 1)
        self.help = HelpIcon()
        top = QHBoxLayout()
        top.setSpacing(6)
        top.addWidget(self.title)
        top.addWidget(self.help)
        top.addStretch()
        lay.addLayout(top)
        lay.addWidget(self.value)
        lay.addLayout(row)

    def set(self, key, value, ref=None, p=None):
        self.title.setText(METRICS[key][0])
        self.help.set([(METRICS[key][0], HELP.get(key, ""))])
        self.value.setText(fmt(key, value))
        v = verdict(key, value, p)
        self.badge.setVisible(bool(v))
        if v:
            color = LEVEL[v[1]]
            self.badge.setText(v[0])
            rgb = ",".join(str(int(color[i:i + 2], 16)) for i in (1, 3, 5))
            self.badge.setStyleSheet(f"color:{color};background:rgba({rgb},0.14);border:1px solid rgba({rgb},0.45);"
                                     "border-radius:9px;padding:1px 8px;font-size:13px;font-weight:600")
        self.ref.setText(f"média do lobby {fmt(key, ref)}" if ref is not None else "")


class Details(QWidget):
    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.btn = QPushButton("Mostrar detalhes  ▾")
        self.btn.setObjectName("toggle")
        self.btn.setCheckable(True)
        self.btn.toggled.connect(self.toggle)
        self.body = label()
        self.body.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.body.hide()
        lay.addWidget(self.btn, alignment=Qt.AlignLeft)
        lay.addWidget(self.body)

    def toggle(self, on):
        self.body.setVisible(on)
        self.btn.setText("Ocultar detalhes  ▴" if on else "Mostrar detalhes  ▾")

    def set(self, html):
        self.body.setText(CSS + html)


class Page(QScrollArea):
    def __init__(self, title, cards=4, chart=True):
        super().__init__()
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        inner = QWidget()
        self.lay = QVBoxLayout(inner)
        self.lay.setContentsMargins(28, 20, 28, 28)
        self.lay.setSpacing(16)
        self.lay.addWidget(label(title, 20, bold=True))
        row = QHBoxLayout()
        row.setSpacing(12)
        self.cards = [Card() for _ in range(cards)]
        for c in self.cards:
            row.addWidget(c)
        if cards:
            self.lay.addLayout(row)
        self.extra = QVBoxLayout()
        self.extra.setSpacing(10)
        self.lay.addLayout(self.extra)
        self.chart = Chart() if chart else None
        if chart:
            self.lay.addWidget(self.chart)
        self.details = Details()
        self.lay.addWidget(self.details)
        self.lay.addStretch()
        self.setWidget(inner)

    def fill(self, keys, p, lobby):
        for card, key in zip(self.cards, keys):
            card.set(key, p[key], lobby.get(key), p)


class Loader(QThread):
    done = Signal(list, list, list, str)
    progress = Signal(str)

    def __init__(self, paths=(), ids=()):
        super().__init__()
        self.paths, self.ids = list(paths), list(ids)

    def run(self):
        matches, stats, ids, errors = [], [], [], []
        jobs = [(p, None) for p in self.paths] + [(None, i) for i in self.ids]
        for n, (path, mid) in enumerate(jobs, 1):
            name = Path(path).name if path else mid[:8]
            self.progress.emit(f"{'Lendo' if path else 'Abrindo'} {name} ({n}/{len(jobs)})…")
            try:
                if path:
                    m = load_demo(path)
                    mid, _ = library.save(m, path)
                else:
                    m = library.load(mid)
                matches.append(m)
                stats.append(match_stats(m))
                ids.append(mid)
            except (KeyboardInterrupt, SystemExit):
                raise
            except BaseException as e:
                errors.append(f"{name}: {e}")
        self.done.emit(matches, stats, ids, "\n".join(errors))


class Main(QMainWindow):
    SECTIONS = ["🗂  Minhas demos", "📊  Resumo", "🎬  Replay", "🎞  Clipes", "🎯  Treino", "⚔️  Duelos", "✛  Mira", "💣  Utilitárias", "📈  Evolução", "👥  Social", "🏆  Partida"]

    def __init__(self):
        super().__init__()
        self.setWindowTitle("CS2 Analytics")
        self.resize(1180, 800)
        self.setAcceptDrops(True)
        self.cfg = load_config()
        me = self.cfg.get("me") or self.cfg.get("steamid")
        self.me = me if isinstance(me, str) and me.isdigit() else None
        self.history = History()
        self.stats = None
        self.sid = None
        self.current_ids = []
        self.trash_mode = False

        self.nav = QListWidget()
        self.nav.setObjectName("nav")
        self.nav.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.nav.addItems(self.SECTIONS)
        self.nav.currentRowChanged.connect(self.nav_changed)
        open_btn = QPushButton("➕ Adicionar demos")
        open_btn.setObjectName("primary")
        open_btn.setStyleSheet("font-size:14px;padding:8px 6px")
        open_btn.clicked.connect(self.open_demos)
        side = QFrame()
        side.setObjectName("side")
        side.setFixedWidth(212)
        sl = QVBoxLayout(side)
        sl.setContentsMargins(14, 20, 14, 16)
        self.avatar_phase = 0.0
        self.avatar_timer = QTimer(self)
        self.avatar_timer.setInterval(50)
        self.avatar_timer.timeout.connect(self.animate_avatar)
        self.avatar_btn = QToolButton()
        self.avatar_btn.setObjectName("avatar")
        self.avatar_btn.setIconSize(QSize(72, 72))
        self.avatar_btn.setToolTip("Editar perfil")
        self.avatar_btn.clicked.connect(self.edit_profile)
        self.profile_name = prof.NameLabel()
        self.fav_label = label("", 11, MUTED)
        self.fav_label.setAlignment(Qt.AlignCenter)
        self.weapon_icon, self.weapon_name = QLabel(), label("", 11, MUTED)
        self.weapon_row = QWidget()
        wrow = QHBoxLayout(self.weapon_row)
        wrow.setContentsMargins(0, 0, 0, 0)
        wrow.setSpacing(6)
        wrow.addStretch()
        wrow.addWidget(self.weapon_icon)
        wrow.addWidget(self.weapon_name)
        wrow.addStretch()
        edit = QPushButton("Editar perfil")
        edit.setObjectName("link")
        edit.clicked.connect(self.edit_profile)
        updates = QPushButton(f"v{current_version()} · Atualizações")
        updates.setObjectName("link")
        updates.clicked.connect(lambda: UpdateDialog(self).exec())
        themes = QPushButton("🎨 Tema")
        themes.setObjectName("link")
        themes.clicked.connect(lambda: ThemeDialog(self).exec())
        sl.addWidget(label("CS2 Analytics", 13, ACCENT, True))
        sl.addSpacing(10)
        sl.addWidget(self.avatar_btn, alignment=Qt.AlignCenter)
        sl.addWidget(self.profile_name)
        sl.addWidget(self.fav_label)
        sl.addWidget(self.weapon_row)
        sl.addWidget(edit, alignment=Qt.AlignCenter)
        sl.addSpacing(10)
        sl.addWidget(self.nav, 1)
        sl.addWidget(open_btn)
        sl.addWidget(themes, alignment=Qt.AlignCenter)
        sl.addWidget(updates, alignment=Qt.AlignCenter)
        self.refresh_profile()

        self.name = label("", 22, bold=True)
        self.sub = label("", 12, MUTED)
        self.viewing = QComboBox()
        self.viewing.setMinimumWidth(240)
        self.viewing.setItemDelegate(StripeDelegate(self.viewing))
        self.viewing.setToolTip("Digite parte do nick para buscar, ou abra a lista · Dourado = você · Azul = aliado · Vermelho = inimigo")
        self.viewing.currentIndexChanged.connect(self.select_player)
        searchable(self.viewing)
        self.back = QPushButton("← Voltar para mim")
        self.back.clicked.connect(lambda: self.show_player(self.me))
        self.set_me = QPushButton("Este sou eu")
        self.set_me.clicked.connect(lambda: self.define_me(self.sid))
        head = QFrame()
        hl = QHBoxLayout(head)
        hl.setContentsMargins(28, 18, 28, 4)
        names = QVBoxLayout()
        names.addWidget(self.name)
        names.addWidget(self.sub)
        hl.addLayout(names, 1)
        for w in (self.back, self.set_me, label("Ver jogador", 12, MUTED), self.viewing):
            hl.addWidget(w)
        self.head = head
        head.hide()

        self.empty = QWidget()
        el = QVBoxLayout(self.empty)
        el.addStretch()
        self.empty_text = label("Arraste suas demos para cá<br>ou clique em <b>Adicionar demos</b>", 16, MUTED)
        self.empty_text.setAlignment(Qt.AlignCenter)
        el.addWidget(self.empty_text)
        el.addStretch()

        self.summary = Page("Resumo")
        self.train = Page("Seu treino", cards=0, chart=False)
        self.duels = Page("Duelos")
        self.aim = Page("Mira")
        self.util = Page("Utilitárias")
        self.evo = Page("Evolução", cards=0)
        self.social = Page("Social", cards=0, chart=False)
        self.match = Page("Partida", cards=0, chart=False)
        self.libpage = self.build_library()
        self.stack = QStackedWidget()
        self.replay = ReplayPage(self)
        self.clips_page = ClipsPage(self)
        for w in (self.empty, self.libpage, self.summary, self.replay, self.clips_page, self.train, self.duels, self.aim, self.util, self.evo, self.social, self.match):
            self.stack.addWidget(w)

        self.minutes, self.days = QComboBox(), QComboBox()
        for m in MINUTES:
            self.minutes.addItem(f"{m} min por dia", m)
        for d in range(1, 8):
            self.days.addItem(f"{d} dia{'s' if d > 1 else ''} por semana", d)
        self.minutes.setCurrentIndex(max(0, self.minutes.findData(self.cfg_int("minutes", 60))))
        self.days.setCurrentIndex(max(0, self.days.findData(self.cfg_int("days", 5))))
        self.custom_schedule = self.cfg.get("schedule_custom") is True
        for box in (self.minutes, self.days):
            box.currentIndexChanged.connect(self.schedule_edited)
        self.use_suggestion = QPushButton("↺ Usar sugestão")
        self.use_suggestion.setToolTip("Voltar ao tempo e aos dias sugeridos pelo app")
        self.use_suggestion.clicked.connect(self.reset_schedule)
        export = QPushButton("Exportar plano")
        export.clicked.connect(self.export_plan)
        copy_cfg = self.copy_button("cfg", "📋 Copiar config de treino")
        bar = QHBoxLayout()
        for w in (self.minutes, self.days, self.use_suggestion):
            bar.addWidget(w)
        bar.addStretch()
        bar.addWidget(copy_cfg)
        bar.addWidget(export)
        self.train.lay.insertLayout(1, bar)

        self.evo_metric = QComboBox()
        for key, (name, _, _) in METRICS.items():
            self.evo_metric.addItem(name, key)
        self.evo_metric.currentIndexChanged.connect(self.render_evolution)
        self.evo.extra.addWidget(self.evo_metric, alignment=Qt.AlignLeft)
        self.maps_box = QVBoxLayout()
        self.ba_split = QComboBox()
        self.ba_split.currentIndexChanged.connect(self.render_before_after)
        self.ba_chart = Chart(3.2)
        self.ba_box = QVBoxLayout()
        evo_more = QVBoxLayout()
        evo_more.setSpacing(10)
        evo_more.addWidget(label("🗺 Desempenho por mapa", 15, bold=True))
        evo_more.addLayout(self.maps_box)
        evo_more.addSpacing(8)
        evo_more.addWidget(label("↔ Antes e depois", 15, bold=True))
        evo_more.addWidget(label("Escolha a partir de qual partida começou a mudança (um treino novo, uma config nova). O app "
                                 "compara a média das partidas antes com a das partidas depois.", 12, MUTED))
        evo_more.addWidget(self.ba_split, alignment=Qt.AlignLeft)
        evo_more.addWidget(self.ba_chart)
        evo_more.addLayout(self.ba_box)
        self.evo.lay.insertLayout(self.evo.lay.count() - 1, evo_more)

        self.friend_a, self.friend_b, self.card_match = QComboBox(), QComboBox(), QComboBox()
        for box in (self.friend_a, self.friend_b):
            box.setItemDelegate(StripeDelegate(box))
            box.currentIndexChanged.connect(self.render_friend)
            searchable(box)
        self.friend_box = QVBoxLayout()
        self.card_preview = QLabel()
        self.card_preview.setAlignment(Qt.AlignLeft)
        card_btn = QPushButton("🖼 Gerar cartão")
        card_btn.setObjectName("primary")
        card_btn.clicked.connect(self.make_card)
        self.card_save = QPushButton("💾 Salvar imagem")
        self.card_save.clicked.connect(self.save_card)
        self.card_save.setEnabled(False)
        self.ach_box = QGridLayout()
        self.ach_box.setSpacing(10)
        soc = self.social.extra
        soc.addWidget(label("⚔ Comparar com um amigo", 15, bold=True))
        soc.addWidget(label("Escolha dois jogadores das partidas carregadas. Vale para você e um amigo que jogou junto, ou "
                            "contra.", 12, MUTED))
        pick = QHBoxLayout()
        pick.addWidget(self.friend_a, 1)
        pick.addWidget(label("vs", 14, MUTED, True))
        pick.addWidget(self.friend_b, 1)
        soc.addLayout(pick)
        soc.addLayout(self.friend_box)
        soc.addSpacing(8)
        soc.addWidget(label("🖼 Cartão da partida", 15, bold=True))
        soc.addWidget(label("Uma imagem com seu placar, rating, KDA e melhor jogada, com a sua borda de perfil, pronta para "
                            "postar.", 12, MUTED))
        crow = QHBoxLayout()
        crow.addWidget(self.card_match, 1)
        crow.addWidget(card_btn)
        crow.addWidget(self.card_save)
        soc.addLayout(crow)
        soc.addWidget(self.card_preview)
        soc.addSpacing(8)
        soc.addWidget(label("🪪 Cartão do perfil", 15, bold=True))
        soc.addWidget(label("Uma mini imagem do seu perfil: avatar e borda, time e jogador favoritos, sua arma favorita com "
                            "o adesivo, seus números de carreira e as qualidades que o app encontrou no seu jogo.", 12, MUTED))
        prow = QHBoxLayout()
        pcard_btn = QPushButton("🪪 Gerar cartão do perfil")
        pcard_btn.setObjectName("primary")
        pcard_btn.clicked.connect(self.make_profile_card)
        self.pcard_save = QPushButton("💾 Salvar imagem")
        self.pcard_save.clicked.connect(lambda: self.save_image(self.pcard_image, "perfil_cs2.png"))
        self.pcard_save.setEnabled(False)
        prow.addWidget(pcard_btn)
        prow.addWidget(self.pcard_save)
        prow.addStretch()
        soc.addLayout(prow)
        self.pcard_preview = QLabel()
        soc.addWidget(self.pcard_preview)
        self.pcard_image = None
        soc.addSpacing(8)
        self.ach_title = label("🏆 Conquistas", 15, bold=True)
        soc.addWidget(self.ach_title)
        holder = QWidget()
        holder.setLayout(self.ach_box)
        self.ach_box.setContentsMargins(0, 0, 0, 0)
        soc.addWidget(holder)
        self.card_image = None

        self.board = QTableWidget()
        self.board.setSortingEnabled(True)
        self.board.setEditTriggers(QTableWidget.NoEditTriggers)
        self.board.setSelectionBehavior(QTableWidget.SelectRows)
        self.board.verticalHeader().setVisible(False)
        self.board.setShowGrid(False)
        self.board.setMinimumHeight(380)
        self.board.cellDoubleClicked.connect(lambda r, _: self.show_player(self.board.item(r, 0).data(Qt.UserRole)))
        self.teams_box = QVBoxLayout()
        self.teams_box.setSpacing(10)
        self.match.extra.addLayout(self.teams_box)
        self.match.extra.addWidget(label("Duplo clique em um jogador para ver os detalhes dele.", 12, MUTED))
        self.match.extra.addWidget(self.board)
        self.match.details.hide()

        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(0)
        rl.addWidget(head)
        rl.addWidget(self.stack)
        root = QWidget()
        lay = QHBoxLayout(root)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(side)
        lay.addWidget(right, 1)
        self.setCentralWidget(root)
        self.refresh_library()
        self.set_nav_state()
        latest = library.entries()
        if latest:
            self.analyze([latest[0]["id"]])
        else:
            self.stack.setCurrentIndex(0)

    def nav_changed(self, i):
        self.stack.setCurrentIndex(i + 1)
        if self.SECTIONS[i] == "🎬  Replay":
            self.replay.refresh()
        else:
            self.replay.pause()
        if self.SECTIONS[i] == "🎞  Clipes":
            self.clips_page.refresh()

    def open_clip(self, mid, clip, action):
        self.replay.want = mid
        self.nav.setCurrentRow(self.SECTIONS.index("🎬  Replay"))
        self.replay.show_clip(mid, clip, action)

    def build_library(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(28, 20, 28, 24)
        lay.setSpacing(12)
        self.lib_title = label("Minhas demos", 20, bold=True)
        self.lib_sub = label("", 12, MUTED)
        lay.addWidget(self.lib_title)
        lay.addWidget(self.lib_sub)

        self.one_btn = QPushButton("📄  Analisar uma partida")
        self.many_btn = QPushButton("📚  Analisar várias partidas")
        self.restore_btn = QPushButton("♻  Restaurar selecionadas")
        for b in (self.one_btn, self.many_btn, self.restore_btn):
            b.setObjectName("primary")
            b.setMinimumHeight(42)
        self.one_btn.clicked.connect(self.analyze_one)
        self.many_btn.clicked.connect(self.analyze_many)
        self.restore_btn.clicked.connect(self.restore_selected)
        add = QPushButton("➕  Adicionar demos")
        add.clicked.connect(self.open_demos)
        self.add_btn = add
        top = QHBoxLayout()
        for b in (self.one_btn, self.many_btn, self.restore_btn):
            top.addWidget(b)
        top.addStretch()
        top.addWidget(add)
        lay.addLayout(top)

        self.lib = QTableWidget(0, 6)
        self.lib.setHorizontalHeaderLabels(["", "Data", "Mapa", "Seu resultado", "Rounds", "Arquivo"])
        self.lib.setEditTriggers(QTableWidget.NoEditTriggers)
        self.lib.setSelectionMode(QTableWidget.NoSelection)
        self.lib.verticalHeader().setVisible(False)
        self.lib.setShowGrid(False)
        self.lib.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.lib.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.lib.cellClicked.connect(self.toggle_row)
        self.lib.cellDoubleClicked.connect(lambda r, _: self.trash_mode or self.analyze([self.lib.item(r, 0).data(Qt.UserRole)]))
        lay.addWidget(self.lib, 1)

        self.delete_btn = QPushButton("🗑  Excluir selecionadas")
        self.delete_btn.clicked.connect(self.delete_selected)
        self.purge_btn = QPushButton("Excluir para sempre")
        self.purge_btn.clicked.connect(self.purge_selected)
        self.trash_btn = QPushButton()
        self.trash_btn.clicked.connect(self.toggle_trash)
        bottom = QHBoxLayout()
        bottom.addWidget(self.delete_btn)
        bottom.addWidget(self.purge_btn)
        bottom.addStretch()
        bottom.addWidget(self.trash_btn)
        lay.addLayout(bottom)
        return page

    def refresh_library(self):
        rows = library.entries(self.trash_mode)
        trash = library.entries(True)
        self.lib_title.setText("Lixeira" if self.trash_mode else "Minhas demos")
        self.lib_sub.setText("Demos excluídas. Restaure para voltar a analisar, ou apague de vez." if self.trash_mode else
                             "Toda demo adicionada fica salva aqui, mesmo que o CS2 apague o arquivo. "
                             "Marque as partidas e escolha como analisar. Duplo clique abre uma partida.")
        for b in (self.one_btn, self.many_btn, self.add_btn, self.delete_btn):
            b.setVisible(not self.trash_mode)
        for b in (self.restore_btn, self.purge_btn):
            b.setVisible(self.trash_mode)
        self.trash_btn.setText("←  Voltar para Minhas demos" if self.trash_mode else f"♻  Lixeira ({len(trash)})")
        self.lib.setRowCount(len(rows))
        for r, meta in enumerate(rows):
            check = QTableWidgetItem()
            check.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
            check.setCheckState(Qt.Checked if meta["id"] in self.current_ids and not self.trash_mode else Qt.Unchecked)
            check.setData(Qt.UserRole, meta["id"])
            score = meta.get("scores", {}).get(self.me) if self.me else None
            if score:
                won, lost = score
                result = QTableWidgetItem(("Vitória" if won > lost else "Derrota" if won < lost else "Empate") + f"  {won}–{lost}")
                result.setForeground(QColor(GOOD if won > lost else BAD if won < lost else MUTED))
            else:
                result = QTableWidgetItem("—")
            cells = [check, QTableWidgetItem(datetime.fromtimestamp(float(meta.get("played_at", 0))).strftime("%d/%m/%Y %H:%M")),
                     QTableWidgetItem(MAP_NAMES.get(meta.get("map"), str(meta.get("map")))), result,
                     QTableWidgetItem(str(meta.get("rounds", ""))), QTableWidgetItem(str(meta.get("source", "")))]
            for c, item in enumerate(cells):
                self.lib.setItem(r, c, item)
        if not rows:
            self.lib.setRowCount(1)
            empty = QTableWidgetItem("A lixeira está vazia." if self.trash_mode else "Nenhuma demo salva ainda. Clique em Adicionar demos.")
            empty.setFlags(Qt.ItemIsEnabled)
            self.lib.setItem(0, 0, QTableWidgetItem())
            self.lib.setSpan(0, 0, 1, 6)
            self.lib.setItem(0, 0, empty)
        else:
            self.lib.clearSpans()

    def checked_ids(self):
        out = []
        for r in range(self.lib.rowCount()):
            item = self.lib.item(r, 0)
            if item and item.data(Qt.UserRole) and item.checkState() == Qt.Checked:
                out.append(item.data(Qt.UserRole))
        return out

    def toggle_row(self, row, col):
        item = self.lib.item(row, 0)
        if col and item and item.data(Qt.UserRole):
            item.setCheckState(Qt.Unchecked if item.checkState() == Qt.Checked else Qt.Checked)

    def notice(self, text):
        QMessageBox.information(self, "CS2 Analytics", text)

    def analyze_one(self):
        ids = self.checked_ids()
        if len(ids) != 1:
            return self.notice("Marque exatamente uma partida para a análise individual." if ids else
                               "Marque a partida que você quer analisar.")
        self.analyze(ids)

    def analyze_many(self):
        ids = self.checked_ids()
        if len(ids) >= 2:
            return self.analyze(ids)
        total = len(library.entries())
        if total < 2:
            return self.notice("Você precisa de pelo menos 2 demos salvas para analisar várias partidas.")
        if not ids and QMessageBox.question(self, "CS2 Analytics", f"Nenhuma partida marcada. Analisar todas as {total}?") == QMessageBox.Yes:
            return self.analyze([m["id"] for m in library.entries()])
        if ids:
            self.notice("Marque pelo menos 2 partidas para a análise combinada.")

    def analyze(self, ids, stay=False):
        self.stay = stay
        self.start_loader(Loader(ids=ids))

    def delete_selected(self):
        ids = self.checked_ids()
        if not ids:
            return self.notice("Marque as demos que você quer excluir.")
        if QMessageBox.question(self, "Excluir demos", f"Mover {len(ids)} demo(s) para a lixeira? "
                                "Você pode restaurar depois.") != QMessageBox.Yes:
            return
        for mid in ids:
            library.set_deleted(mid, True)
            self.history.remove(mid)
        remaining = [i for i in self.current_ids if i not in ids]
        self.refresh_library()
        if self.current_ids and remaining != self.current_ids:
            if remaining:
                self.analyze(remaining, stay=True)
            elif library.entries():
                self.analyze([library.entries()[0]["id"]], stay=True)
            else:
                self.clear_analysis()

    def restore_selected(self):
        ids = self.checked_ids()
        if not ids:
            return self.notice("Marque as demos que você quer restaurar.")
        errors = []
        for mid in ids:
            try:
                library.set_deleted(mid, False)
                m = library.load(mid)
                self.history.save(m, match_stats(m))
            except library.LibraryError as e:
                errors.append(str(e))
        self.refresh_library()
        self.notice(f"{len(ids) - len(errors)} demo(s) restaurada(s)." + ("\n" + "\n".join(errors) if errors else ""))

    def purge_selected(self):
        ids = self.checked_ids()
        if not ids:
            return self.notice("Marque as demos que você quer apagar de vez.")
        if QMessageBox.question(self, "Excluir para sempre", f"Apagar {len(ids)} demo(s) de vez? "
                                "Isso não pode ser desfeito.") != QMessageBox.Yes:
            return
        for mid in ids:
            library.purge(mid)
        self.refresh_library()

    def toggle_trash(self):
        self.trash_mode = not self.trash_mode
        self.refresh_library()

    def clear_analysis(self):
        self.stats, self.sid, self.current_ids = None, None, []
        self.head.hide()
        self.set_nav_state()
        self.nav.setCurrentRow(0)

    def set_nav_state(self):
        for i in range(self.nav.count()):
            item = self.nav.item(i)
            enabled = i == 0 or self.stats is not None or self.SECTIONS[i] in ("🎬  Replay", "🎞  Clipes")
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable if enabled else Qt.NoItemFlags)

    def profile(self):
        data = self.cfg.get("profile")
        data = dict(data) if isinstance(data, dict) else {}
        if not data.get("name") and self.stats and self.me in self.stats.names:
            data["name"] = self.stats.names[self.me]
        if data.get("fav_player") not in TEAMS.get(data.get("fav_team"), []):
            data["fav_team"] = next((t for t, ps in TEAMS.items() if data.get("fav_player") in ps), data.get("fav_team"))
        if data["fav_team"] not in TEAMS:
            data["fav_team"], data["fav_player"] = "", ""
        elif data.get("fav_player") not in TEAMS[data["fav_team"]]:
            data["fav_player"] = ""
        if data.get("fav_weapon") not in wp.WEAPONS:
            data["fav_weapon"] = ""
        return data

    def refresh_profile(self):
        data = self.profile()
        if data.get("border") not in prof.unlocked(self.history.player(self.me) if self.me else [], data.get("admin")):
            data["border"] = "classic"
        self.profile_data = data
        self.avatar_btn.setIcon(QIcon(prof.avatar(144, data, self.avatar_phase)))
        self.profile_name.set_profile(data)
        fav, team = data.get("fav_player", ""), data.get("fav_team", "")
        self.fav_label.setText(f"❤ {html.escape(fav)}" + (f" · {html.escape(team)}" if team else "") if fav else "")
        self.fav_label.setVisible(bool(fav))
        weapon = data.get("fav_weapon", "")
        self.weapon_row.setVisible(bool(weapon))
        if weapon:
            self.weapon_icon.setPixmap(wp.sticker(48, weapon))
            self.weapon_name.setText(html.escape(wp.display(weapon)))
        set_favorite(fav)
        if data.get("effect", "none") != "none":
            self.avatar_timer.start()
        else:
            self.avatar_timer.stop()

    def animate_avatar(self):
        self.avatar_phase = (self.avatar_phase + 0.01) % 1.0
        self.avatar_btn.setIcon(QIcon(prof.avatar(144, self.profile_data, self.avatar_phase)))

    def edit_profile(self):
        rows = self.history.player(self.me) if self.me else []
        dlg = ProfileDialog(self, self.profile(), prof.unlocked(rows), prof.progress(rows))
        if dlg.exec():
            self.cfg["profile"] = dlg.data
            save_config(profile=dlg.data)
        self.refresh_profile()
        if self.sid:
            self.render_training()
            self.render_summary()

    def cfg_int(self, key, default):
        v = self.cfg.get(key)
        return v if isinstance(v, int) else default

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e):
        self.load([u.toLocalFile() for u in e.mimeData().urls()])

    def open_demos(self):
        last = self.cfg.get("last_dir")
        start = (last if isinstance(last, str) and os.path.isdir(last) else None) or (str(REPLAYS) if REPLAYS.exists() else str(Path.home()))
        paths, _ = QFileDialog.getOpenFileNames(self, "Escolha as demos", start,
                                                "Demos do CS2 (*.dem *.gz *.bz2 *.zst);;Todos (*)")
        if paths:
            self.cfg["last_dir"] = os.path.dirname(paths[0])
            save_config(last_dir=self.cfg["last_dir"])
            self.load(paths)

    def load(self, paths):
        if getattr(self, "loader", None) and self.loader.isRunning():
            return
        paths = [p for p in paths if os.path.isfile(p)]
        if not paths:
            return
        self.start_loader(Loader(paths=paths))

    def start_loader(self, loader):
        if getattr(self, "loader", None) and self.loader.isRunning():
            return
        self.loader = loader
        self.loader.progress.connect(self.empty_text.setText)
        self.loader.progress.connect(self.sub.setText)
        self.loader.progress.connect(self.lib_sub.setText)
        self.loader.done.connect(self.loaded)
        self.loader.start()

    def loaded(self, matches, stats, ids, errors):
        if errors:
            box = QMessageBox(QMessageBox.Warning, "Algumas demos falharam", errors, parent=self)
            box.setTextFormat(Qt.PlainText)
            box.exec()
        if not matches:
            self.empty_text.setText("Nenhuma demo carregada. Tente outro arquivo.")
            self.refresh_library()
            return
        self.trash_mode = False
        for m, s in zip(matches, stats):
            self.history.save(m, s)
        self.current_ids = ids
        self.refresh_library()
        self.stats = combine(stats)
        order = sorted(self.stats.counters, key=lambda s: -self.stats.player(s)["rating"])
        if self.me not in self.stats.counters:
            self.ask_me(order)
            self.refresh_library()
        self.fill_viewing()
        self.render_board()
        self.refresh_profile()
        self.head.show()
        self.set_nav_state()
        if not getattr(self, "stay", False):
            self.nav.setCurrentRow(self.SECTIONS.index("📊  Resumo"))
        self.stay = False
        self.show_player(self.me if self.me in self.stats.counters else order[0])

    def ask_me(self, order):
        names = [self.stats.names[s] for s in order]
        text = "Qual desses jogadores é você?" if not self.me else \
            "Você não está nesta demo. Escolha quem é você (ou cancele para só visualizar):"
        name, ok = QInputDialog.getItem(self, "Seu jogador", text, names, 0, False)
        if ok:
            self.define_me(order[names.index(name)], refresh=False)

    def define_me(self, sid, refresh=True):
        self.me = sid
        self.cfg["me"] = sid
        save_config(me=sid)
        self.refresh_profile()
        self.refresh_library()
        if refresh:
            self.fill_viewing()
            self.render_board()
            self.show_player(sid)

    def fill_viewing(self):
        rel = relations(self.stats.matches, self.me) if self.me in self.stats.counters else {}
        rank = {"me": 0, "ally": 1, "mixed": 2, "enemy": 3}
        order = sorted(self.stats.counters, key=lambda s: (rank.get(rel.get(s), 4), -self.stats.player(s)["rating"]))
        tag = {"me": "  ★ você", "ally": "  · aliado", "enemy": "  · inimigo"}
        current = self.viewing.currentData()
        self.viewing.blockSignals(True)
        self.viewing.clear()
        for s in order:
            self.viewing.addItem(self.stats.names[s] + tag.get(rel.get(s), ""), s)
            self.viewing.setItemData(self.viewing.count() - 1, REL_COLORS.get(rel.get(s), MUTED), REL_ROLE)
        if current in order:
            self.viewing.setCurrentIndex(order.index(current))
        self.viewing.blockSignals(False)

    def show_player(self, sid):
        if sid in self.stats.counters:
            self.viewing.setCurrentIndex(self.viewing.findData(sid))
            self.select_player()

    def select_player(self):
        self.sid = self.viewing.currentData()
        if not self.sid:
            return
        self.p = self.stats.player(self.sid)
        self.lobby = self.stats.lobby()
        mine = self.sid == self.me
        rel = relations(self.stats.matches, self.me) if self.me in self.stats.counters else {}
        stripe = REL_COLORS.get(rel.get(self.sid), LINE)
        self.viewing.setStyleSheet(f"QComboBox {{ border-left: 4px solid {stripe}; }}")
        self.back.setVisible(not mine and self.me in self.stats.counters)
        self.set_me.setVisible(not mine)
        kind = {"ally": ("aliado", CT_COLOR), "enemy": ("inimigo", BAD)}.get(rel.get(self.sid), ("outro jogador", MUTED))
        self.name.setText(html.escape(self.stats.names[self.sid]) + ("" if mine else f'  <span style="color:{kind[1]};font-size:15px">({kind[0]})</span>'))
        self.sub.setText(self.subtitle())
        self.render_summary()
        self.render_training()
        self.render_duels()
        self.render_aim()
        self.render_util()
        self.render_evolution()
        self.render_social()

    def subtitle(self):
        ms = self.stats.matches
        maps = ", ".join(sorted({MAP_NAMES.get(m.map_name, m.map_name) for m in ms}))
        if len(ms) > 1:
            return f"{len(ms)} partidas · {maps} · {int(self.p['rounds'])} rounds"
        m = ms[0]
        teams = dict(zip(m.roster[m.roster.sid == self.sid]["round"], m.roster[m.roster.sid == self.sid].team))
        mine = sum(teams.get(r) == w for r, w in zip(m.rounds["round"], m.rounds.winner))
        theirs = sum(r in teams and teams[r] != w for r, w in zip(m.rounds["round"], m.rounds.winner))
        result = "Vitória" if mine > theirs else "Derrota" if mine < theirs else "Empate"
        color = GOOD if mine > theirs else BAD if mine < theirs else MUTED
        who = "seu time" if self.sid == self.me else "time dele"
        return f'{maps} · <span style="color:{color}">{result}</span> · {who} {mine} × {theirs} adversários · {len(m.rounds)} rounds'

    def training(self):
        issues, strengths = diagnose(self.p, self.lobby)
        self.suggested = suggest_schedule(issues, int(self.p["rounds"]))
        mins, days, _ = self.suggested
        for box, value, unit in ((self.minutes, mins, "min por dia"), (self.days, days, "por semana")):
            box.blockSignals(True)
            for i in range(box.count()):
                box.setItemText(i, box.itemText(i).replace("  ✓ sugerido", "") + ("  ✓ sugerido" if box.itemData(i) == value else ""))
            if not self.custom_schedule:
                box.setCurrentIndex(box.findData(value))
            box.blockSignals(False)
        self.use_suggestion.setVisible(self.custom_schedule)
        return issues, strengths, weekly_plan(issues, self.main_map(), self.minutes.currentData(), self.days.currentData())

    def schedule_edited(self):
        self.custom_schedule = True
        save_config(schedule_custom=True)
        self.render_training()

    def reset_schedule(self):
        self.custom_schedule = False
        save_config(schedule_custom=False)
        self.render_training()

    def issue_box(self, issue):
        box = QFrame()
        box.setObjectName("card")
        lay = QVBoxLayout(box)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(6)
        color = BAD if issue.severity >= 0.66 else ACCENT if issue.severity >= 0.33 else MUTED
        level = "Prioridade alta" if issue.severity >= 0.66 else "Prioridade média" if issue.severity >= 0.33 else "Prioridade baixa"
        top = QHBoxLayout()
        title = label(f"<span style='color:{color}'>●</span>  {issue.rule.title}", 14, bold=True)
        title.setWordWrap(False)
        top.addWidget(title)
        name = METRICS.get(issue.rule.metric, (issue.rule.title,))[0]
        top.addWidget(HelpIcon([(name, HELP.get(issue.rule.metric, ""))] + glossary_for(issue.rule.tip)), alignment=Qt.AlignTop)
        top.addStretch(1)
        tag = label(f"{level} · {issue.rule.area}", 11, MUTED)
        tag.setWordWrap(False)
        top.addWidget(tag)
        lay.addLayout(top)
        lay.addWidget(label(f"{issue.text} {issue.compare}".strip(), 12, MUTED))
        lay.addWidget(label(f"📊 {issue.context}", 11, MUTED))
        lay.addWidget(label(f"💡 {issue.rule.tip}", 12, TEXT))
        if issue.goal:
            lay.addWidget(label(f"🏁 {issue.goal}", 12, GOOD))
        if issue.pro:
            lay.addWidget(self.pro_label(issue.pro))
        drill = drill_text(issue.rule.drills[0], self.main_map())
        lay.addWidget(label(f"🎯 Treino que ajuda: <b>{html.escape(drill.name)}</b> · {drill.minutes} min", 12, ACCENT))
        return box

    def pro_label(self, tip):
        w = label(f"🏆 <b style='color:{ACCENT}'>{html.escape(tip.player)}</b>: {html.escape(tip.text)} "
                  f"<a href='{html.escape(tip.url)}' style='color:{MUTED}'>Fonte: {html.escape(tip.source)} ↗</a>", 12, TEXT)
        w.setOpenExternalLinks(True)
        return w

    def consistency_box(self):
        box = QFrame()
        box.setObjectName("card")
        lay = QVBoxLayout(box)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(8)
        lay.addWidget(label("📅 Constância", 14, bold=True))
        c = consistency(self.history.player(self.sid))
        if c:
            steady = c["sd"] < 0.15
            lay.addWidget(label(
                f"Nas suas últimas {c['n']} partidas, o rating foi de {c['min']:.2f} a {c['max']:.2f} (média {c['mean']:.2f}, "
                f"variação ±{c['sd']:.2f}). " + ("Isso é bem estável: mantenha a rotina." if steady else
                "A variação está alta: você tem dias muito bons e muito ruins. As dicas abaixo ajudam a aproximar um do outro."),
                12, GOOD if steady else ACCENT))
        else:
            lay.addWidget(label("Com 3 partidas ou mais deste jogador, o app mostra aqui o quanto o seu rating varia de um jogo para "
                                "o outro.", 12, MUTED))
        grid = QGridLayout()
        grid.setSpacing(10)
        for i, (title, tip, pro) in enumerate(CONSISTENCY):
            card = QFrame()
            card.setObjectName("clipcard")
            cl = QVBoxLayout(card)
            cl.setContentsMargins(12, 10, 12, 10)
            cl.addWidget(label(title, 13, bold=True))
            cl.addWidget(label(tip, 12, MUTED))
            cl.addWidget(self.pro_label(pro_tip(pro)))
            cl.addStretch()
            grid.addWidget(card, i // 2, i % 2)
        holder = QWidget()
        holder.setLayout(grid)
        grid.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(holder)
        return box

    def copy_button(self, key, text=None):
        name, cmd, desc = COMMANDS[key]
        text = text or f"📋 {name}"
        btn = QPushButton(text)
        btn.setObjectName("chip")
        btn.setToolTip(f"<b>{html.escape(cmd)}</b><br>{html.escape(desc)}<br><i>Abra o console (tecla ') e cole com Ctrl+V.</i>")

        def copy():
            QGuiApplication.clipboard().setText(cmd)
            btn.setText("✓ Copiado")
            QTimer.singleShot(1500, lambda: btn.setText(text))
        btn.clicked.connect(copy)
        return btn

    def workshop_button(self, key):
        btn = QPushButton("Abrir na Oficina ↗")
        btn.setObjectName("chip")
        btn.setToolTip(COMMUNITY_MAPS[key][1])
        btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(COMMUNITY_MAPS[key][1])))
        return btn

    def main_map(self):
        return max(self.stats.matches, key=lambda m: len(m.rounds)).map_name

    def go_training(self):
        self.render_training()
        self.nav.setCurrentRow(self.SECTIONS.index("🎯  Treino"))
        self.train.verticalScrollBar().setValue(0)

    def render_summary(self):
        p, page = self.p, self.summary
        page.fill(["rating", "adr", "kast", "kd"], p, self.lobby)
        clear(page.extra)
        issues, _, _ = self.training()
        page.extra.addWidget(label("Foco principal", 14, bold=True))
        if issues:
            for issue in issues[:3]:
                page.extra.addWidget(self.issue_box(issue))
        else:
            page.extra.addWidget(label("Nenhum número abaixo da referência nesta amostra. Mantenha o aquecimento e o treino de mapa para "
                                       "segurar a forma.", 12, GOOD))
        if p["rounds"] < 15:
            page.extra.addWidget(label(f"Só {int(p['rounds'])} rounds analisados. Com tão pouco, uma partida ruim distorce os números; "
                                       "adicione mais demos para um diagnóstico confiável.", 12, BAD))
        go = QPushButton("🎯  Gerar meu treino")
        go.setObjectName("primary")
        go.setMinimumHeight(44)
        go.clicked.connect(self.go_training)
        page.extra.addWidget(go)

        pr = self.stats.per_round[self.stats.per_round.sid == self.sid]
        ax = page.chart.axes()
        if len(self.stats.matches) == 1:
            ax.bar(pr["round"], pr.damage, color=[GOOD if w else BAD for w in pr.won], width=0.7)
            ax.set_title("Seu dano em cada round  ·  verde = seu time ganhou, vermelho = perdeu", fontsize=11, loc="left")
        else:
            by = pr.groupby("match").damage.mean().reindex(range(len(self.stats.matches))).fillna(0)
            ax.bar([f"{i + 1}. {MAP_NAMES.get(m.map_name, m.map_name)}" for i, m in enumerate(self.stats.matches)],
                   by, color=ACCENT, width=0.6)
            ax.set_title("ADR por partida", fontsize=11, loc="left")
        page.chart.draw()

        page.details.set(
            f"<p class=muted>{int(p['kills'])} kills · {int(p['deaths'])} mortes · {int(p['assists'])} assists · "
            f"HS {fmt('hs_pct', p['hs_pct'])} · precisão {fmt('accuracy', p['accuracy'])}</p>"
            "<h3>Por lado</h3>" + table(
                ["", "Rounds", "K", "D", "ADR", "KAST", "Aberturas"],
                [[f'<span style="color:{CT_COLOR}">CT</span>', int(p["rounds_ct"]), int(p["kills_ct"]),
                  int(p["deaths_ct"]), fmt("adr", p["adr_ct"]), fmt("kast", p["kast_ct"]), p["open_ct"]],
                 [f'<span style="color:{T_COLOR}">TR</span>', int(p["rounds_t"]), int(p["kills_t"]),
                  int(p["deaths_t"]), fmt("adr", p["adr_t"]), fmt("kast", p["kast_t"]), p["open_t"]]])
            + "<h3>Multi-kills</h3>" + table(["2K", "3K", "4K", "ACE"], [[int(p[k]) for k in ("k2", "k3", "k4", "k5")]]))

    def render_training(self):
        if not self.sid:
            return
        issues, strengths, plan = self.training()
        save_config(minutes=self.minutes.currentData(), days=self.days.currentData())
        page = self.train
        clear(page.extra)
        today = datetime.today().weekday()
        focus = ", ".join(i.rule.title.lower() for i in issues[:3]) or "manter a forma"
        page.extra.addWidget(label(f"Montado a partir de {int(self.p['rounds'])} rounds analisados. "
                                   f"Foco desta semana: <b style='color:{TEXT}'>{html.escape(focus)}</b>. "
                                   "Depois do aquecimento, o primeiro treino de cada dia ataca o ponto de maior prioridade.",
                                   12, MUTED))
        mins, days, why = self.suggested
        sched = QFrame()
        sched.setObjectName("card")
        sl = QVBoxLayout(sched)
        sl.setContentsMargins(16, 10, 16, 10)
        sl.addWidget(label(f"⏱ Sugestão do app: {mins} min por dia, {days} dia{'s' if days > 1 else ''} por semana", 13, ACCENT, True))
        sl.addWidget(label(why, 12, MUTED))
        if self.custom_schedule:
            sl.addWidget(label(f"Você ajustou para {self.minutes.currentData()} min e {self.days.currentText().split(' por')[0]}. "
                               "O plano abaixo segue o seu ajuste; para voltar à sugestão, clique em ↺ Usar sugestão.", 12, TEXT))
        else:
            sl.addWidget(label("Quer mais ou menos? Mude o tempo e os dias nas caixas acima; o plano se ajusta na hora.", 12, TEXT))
        page.extra.addWidget(sched)
        page.extra.addWidget(self.goals_box(issues))
        page.extra.addWidget(self.checklist_box(plan))
        page.extra.addSpacing(4)
        page.extra.addWidget(label(f"Treino de hoje · {DAYS[today]}", 14, bold=True))
        if plan[today][1]:
            for d in plan[today][1]:
                box = QFrame()
                box.setObjectName("card")
                bl = QHBoxLayout(box)
                bl.setContentsMargins(16, 10, 16, 10)
                mins = label(f"{d.minutes}′", 18, ACCENT, True)
                mins.setFixedWidth(48)
                bl.addWidget(mins)
                text = QVBoxLayout()
                text.addLayout(help_row(label(f"{d.name} <span style='color:{MUTED};font-weight:normal'>· {d.where}</span>", 13, bold=True),
                                        glossary_for(f"{d.name} {d.where} {d.how}")))
                text.addWidget(label(d.how, 12, MUTED))
                if d.key in DRILL_PRO:
                    text.addWidget(self.pro_label(pro_tip(DRILL_PRO[d.key])))
                bl.addLayout(text, 1)
                side = QVBoxLayout()
                side.setSpacing(6)
                if d.workshop in COMMUNITY_MAPS:
                    side.addWidget(self.workshop_button(d.workshop))
                for key in DRILL_CMD.get(d.key, ()):
                    side.addWidget(self.copy_button(key))
                side.addStretch()
                bl.addLayout(side)
                page.extra.addWidget(box)
        else:
            page.extra.addWidget(label("Hoje é dia de descanso no seu plano. Se quiser jogar, use a partida para prestar atenção "
                                       "em um dos pontos abaixo, sem se cobrar.", 12, MUTED))
        page.extra.addSpacing(6)
        page.extra.addWidget(self.consistency_box())
        page.extra.addSpacing(6)
        page.extra.addWidget(label("Pontos a melhorar", 14, bold=True))
        for issue in issues:
            page.extra.addWidget(self.issue_box(issue))
        if not issues:
            page.extra.addWidget(label("Nenhum número abaixo da referência nesta amostra. Mantenha o aquecimento e o treino de mapa para "
                                       "segurar a forma.", 12, GOOD))
        fav = self.profile_data.get("fav_player", "")
        pros = sorted({t.player for t in PRO_TIPS.values()}, key=str.lower)
        note = (f"🏆 As dicas de pros são resumos em nossas palavras do que {', '.join(pros[:-1])} e {pros[-1]} disseram em "
                "entrevistas, vlogs e cursos. Clique em Fonte para ver o original.")
        if fav and has_tips(fav):
            note += f" Quando existe uma dica de {html.escape(fav)}, seu jogador favorito, ela aparece primeiro."
        elif fav:
            note += f" Ainda não temos falas com fonte de {html.escape(fav)}; mostramos as de outros pros."
        page.extra.addWidget(label(note, 11, MUTED))
        page.extra.addSpacing(6)
        page.extra.addWidget(label("Comandos para o console do CS2", 14, bold=True))
        page.extra.addWidget(label("Clique para copiar, abra o console no jogo (tecla ' ao lado do 1, ou ` ) e cole com Ctrl+V. "
                                   "Use só em partida privada (Jogar → Praticar com bots): os comandos com cheats não funcionam "
                                   "em partidas oficiais e não afetam seu rank. Se o console não abre, ative em Configurações → "
                                   "Jogo → Ativar console do desenvolvedor.", 12, MUTED))
        cmds = QGridLayout()
        cmds.setSpacing(8)
        for i, key in enumerate(COMMANDS):
            name, cmd, desc = COMMANDS[key]
            card = QFrame()
            card.setObjectName("card")
            cl = QVBoxLayout(card)
            cl.setContentsMargins(14, 10, 14, 10)
            cl.addWidget(label(name, 13, bold=True))
            code = label(html.escape(cmd if len(cmd) < 60 else cmd[:57] + "…"), 11, ACCENT)
            code.setStyleSheet(code.styleSheet() + ";font-family:Consolas,monospace")
            cl.addWidget(code)
            cl.addWidget(label(desc, 11, MUTED), 1)
            cl.addWidget(self.copy_button(key, "📋 Copiar"), alignment=Qt.AlignLeft)
            cmds.addWidget(card, i // 3, i % 3)
        box = QWidget()
        box.setLayout(cmds)
        cmds.setContentsMargins(0, 0, 0, 0)
        page.extra.addWidget(box)
        page.extra.addSpacing(6)
        page.extra.addWidget(label("Mapas da comunidade para treinar", 14, bold=True))
        page.extra.addWidget(label("Clique em Inscrever-se na página da Oficina e abra no CS2 em Jogar → Mapas da Oficina. "
                                   "São partidas offline, então não afetam seu rank.", 12, MUTED))
        grid = QGridLayout()
        grid.setSpacing(10)
        for i, key in enumerate(COMMUNITY_MAPS):
            name, _, desc = COMMUNITY_MAPS[key]
            card = QFrame()
            card.setObjectName("card")
            cl = QVBoxLayout(card)
            cl.setContentsMargins(14, 10, 14, 10)
            cl.addWidget(label(name, 13, bold=True))
            cl.addWidget(label(desc, 11, MUTED), 1)
            cl.addWidget(self.workshop_button(key), alignment=Qt.AlignLeft)
            grid.addWidget(card, i // 3, i % 3)
        holder = QWidget()
        holder.setLayout(grid)
        grid.setContentsMargins(0, 0, 0, 0)
        page.extra.addWidget(holder)

        extra = ""
        if strengths:
            extra += "<h3>Pontos fortes</h3>" + "".join(f"<p class=good>✔ {n}: {v}</p>" for n, v in strengths)
        extra += "<h3>Semana completa</h3>"
        for day, items in plan:
            extra += f"<p><b>{day}</b> <span class=muted>· " + (" · ".join(f"{d.name} ({d.minutes}′)" for d in items) or "Descanso") + "</span></p>"
        page.details.set(extra)

    def render_duels(self):
        p, page = self.p, self.duels
        page.fill(["opening_success", "traded_death_pct", "survival", "clutch_rate"], p, self.lobby)
        keys = ["opening_success", "traded_death_pct", "trade_kill_pct", "survival", "kast", "hs_pct"]
        ax = page.chart.axes()
        y = range(len(keys))
        ax.barh([i + 0.18 for i in y], [self.lobby.get(k, 0) * 100 for k in keys], height=0.34, color=BAR, label="Lobby")
        ax.barh([i - 0.18 for i in y], [p[k] * 100 for k in keys], height=0.34, color=ACCENT, label="Jogador")
        ax.set_yticks(list(y), [METRICS[k][0] for k in keys])
        ax.invert_yaxis()
        ax.grid(axis="y", visible=False)
        ax.grid(axis="x", color=LINE, linewidth=0.6)
        ax.legend(fontsize=10, facecolor=PANEL, labelcolor=TEXT, edgecolor=PANEL, loc="lower right")
        page.chart.draw()
        rows = [[METRICS[k][0], f"<b>{fmt(k, p[k])}</b>", compare(k, p[k], self.lobby.get(k)), f"<span class=muted>{HELP.get(k, '')}</span>"]
                for k in ("opening_success", "opening_rate", "trade_kill_pct", "traded_death_pct", "early_death_pct",
                          "nodmg_death_pct", "blind_death_pct", "survival", "multikill_rate", "clutch_rate")]
        page.details.set(table(["Métrica", "Você", "Lobby", "O que significa"], rows)
                         + f"<p>Clutches 1v1: {p['c1v1']} · 1vX: {p['c1vx']}</p>"
                         "<p class=muted>Trade = morte vingada em até 5 s. Abertura = primeira kill do round.</p>")

    def render_aim(self):
        p, page = self.p, self.aim
        page.fill(["hs_pct", "head_hit_pct", "accuracy", "rifle_accuracy"], p, self.lobby)
        groups = {"Cabeça": "head", "Peito": "chest", "Estômago": "stomach", "Braços": "arms", "Pernas": "legs"}
        vals = [p["hitgroups"][g] * 100 for g in groups.values()]
        ax = page.chart.axes()
        ax.bar(list(groups), vals, color=[ACCENT] + [BAR] * 4, width=0.6)
        for i, v in enumerate(vals):
            ax.text(i, v + 0.8, f"{v:.0f}%", ha="center", color=TEXT, fontsize=11)
        ax.set_title("Onde seus tiros acertaram (%)", fontsize=11, loc="left")
        page.chart.draw()
        w = self.stats.weapons[self.stats.weapons.sid == self.sid].sort_values("kills", ascending=False)
        w = w[(w.kills > 0) | ((w.shots > 10) & ~w.weapon.isin(NON_GUNS))]
        page.details.set(
            f"<p class=muted>{int(p['shots'])} disparos · {int(p['hits'])} acertos em inimigos</p>"
            + table(["Arma", "Kills", "HS", "Dano", "Tiros", "Precisão"],
                    [[html.escape(r.weapon), int(r.kills), f"{r.hs / r.kills:.0%}" if r.kills else "—", int(r.damage),
                      int(r.shots), f"{r.hits / r.shots:.0%}" if r.shots else "—"] for r in w.itertuples()]))

    def render_util(self):
        p, page = self.p, self.util
        page.fill(["flashes_pr", "flash_eff", "team_flash_pct", "util_dmg"], p, self.lobby)
        rounds = max(p["rounds"], 1)
        ax = page.chart.axes()
        ax.bar(["Flash", "Smoke", "HE", "Molotov"],
               [p[k] / rounds for k in ("flash_thrown", "smoke_thrown", "he_thrown", "fire_thrown")], color=ACCENT, width=0.6)
        ax.set_title("Granadas que você joga por round", fontsize=11, loc="left")
        page.chart.draw()
        page.details.set(table(["", "Total"], [
            ["Flashes lançadas", int(p["flash_thrown"])], ["Smokes lançadas", int(p["smoke_thrown"])],
            ["HEs lançadas", int(p["he_thrown"])], ["Molotovs/incendiárias", int(p["fire_thrown"])],
            ["Dano de HE", int(p["he_dmg"])], ["Dano de fogo", int(p["fire_dmg"])],
            ["Cegueira média causada", f"{p['avg_blind']:.2f} s"], ["Assistências por flash", int(p["flash_assists"])]]))

    def render_evolution(self):
        if not self.sid:
            return
        key = self.evo_metric.currentData()
        rows = self.history.player(self.sid)
        page = self.evo
        ax = page.chart.axes()
        if rows:
            scale = 100 if "%" in METRICS[key][1] else 1
            ys = [r[3].get(key, 0) * scale for r in rows]
            xs = list(range(1, len(rows) + 1))
            ax.plot(xs, ys, marker="o", color=ACCENT, linewidth=2)
            if len(ys) >= 3:
                avg = [sum(ys[max(0, i - 2):i + 1]) / len(ys[max(0, i - 2):i + 1]) for i in range(len(ys))]
                ax.plot(xs, avg, color=MUTED, linestyle="--", linewidth=1)
            ax.set_xticks(xs)
        ax.set_title(f"{METRICS[key][0]} por partida" + (" · tracejado = média das últimas 3" if len(rows) >= 3 else ""),
                     fontsize=11, loc="left")
        page.chart.draw()
        page.details.set(table(
            ["#", "Data", "Mapa", "Arquivo", "Rating", "ADR", "KAST"],
            [[i, datetime.fromtimestamp(t).strftime("%d/%m/%Y"), html.escape(MAP_NAMES.get(m, m)), html.escape(s),
              fmt("rating", js["rating"]), fmt("adr", js["adr"]), fmt("kast", js["kast"])]
             for i, (t, m, s, js) in enumerate(rows, 1)]))
        self.render_maps(rows)
        self.ba_split.blockSignals(True)
        self.ba_split.clear()
        for t, m, _, _ in rows[1:]:
            self.ba_split.addItem(f"A partir de {datetime.fromtimestamp(t).strftime('%d/%m/%Y %H:%M')} · "
                                  f"{MAP_NAMES.get(m, m)}", t)
        self.ba_split.setCurrentIndex(max(0, self.ba_split.count() // 2 - (1 if self.ba_split.count() % 2 == 0 else 0)))
        self.ba_split.blockSignals(False)
        self.render_before_after()

    def render_maps(self, rows):
        clear(self.maps_box)
        maps = prog.by_map(rows)
        if not maps:
            self.maps_box.addWidget(label("Ainda não há partidas deste jogador no histórico.", 12, MUTED))
            return
        cells = []
        for r in maps:
            wr = "—" if r["winrate"] is None else f"{r['winrate']:.0%} ({r['wins']}V {r['losses']}D)"
            cells.append([html.escape(r["name"]), r["n"], wr, fmt("rating", r["rating"]), fmt("adr", r["adr"]),
                          fmt("kast", r["kast"]), fmt("hs_pct", r["hs_pct"])])
        box = label(CSS + table(["Mapa", "Partidas", "Vitórias", "Rating", "ADR", "KAST", "HS%"], cells), 12)
        self.maps_box.addWidget(box)
        ranked = [r for r in maps if r["n"] >= 2]
        if len(ranked) >= 2:
            best, worst = max(ranked, key=lambda r: r["rating"]), min(ranked, key=lambda r: r["rating"])
            self.maps_box.addWidget(label(
                f"Seu melhor mapa é <b style='color:{GOOD}'>{html.escape(best['name'])}</b> (rating {best['rating']:.2f}) e o mais "
                f"difícil é <b style='color:{BAD}'>{html.escape(worst['name'])}</b> ({worst['rating']:.2f}). Use o melhor como mapa "
                "de conforto e coloque o outro no treino de mapa da semana.", 12, TEXT))
        else:
            self.maps_box.addWidget(label("Com 2 partidas ou mais em pelo menos dois mapas, o app aponta o seu melhor e o seu pior "
                                          "mapa.", 12, MUTED))

    def render_before_after(self):
        clear(self.ba_box)
        ax = self.ba_chart.axes()
        split = self.ba_split.currentData()
        rows = self.history.player(self.sid) if self.sid else []
        if split is None or len(rows) < 2:
            ax.set_title("Precisa de pelo menos 2 partidas no histórico", fontsize=11, loc="left")
            self.ba_chart.draw()
            return
        res = prog.before_after(rows, split)
        data = [m for m in res["metrics"] if m["pct"] is not None]
        names = [m["name"] for m in data][::-1]
        vals = [max(-100, min(100, m["pct"] * 100)) for m in data][::-1]
        colors = [GOOD if m["improved"] else BAD if m["improved"] is False else MUTED for m in data][::-1]
        ax.barh(names, vals, color=colors, height=0.6)
        ax.axvline(0, color=LINE, linewidth=1)
        ax.grid(axis="x", color=LINE, linewidth=0.6)
        ax.grid(axis="y", visible=False)
        ax.set_title(f"Variação % · {res['n_before']} partidas antes x {res['n_after']} depois · verde = melhorou",
                     fontsize=11, loc="left")
        self.ba_chart.draw()
        up = [m for m in data if m["improved"]]
        down = [m for m in data if m["improved"] is False]
        if up or down:
            top = max(up, key=lambda m: abs(m["pct"]), default=None)
            low = max(down, key=lambda m: abs(m["pct"]), default=None)
            text = f"{len(up)} números melhoraram e {len(down)} pioraram."
            if top:
                text += f" O maior avanço foi em <b style='color:{GOOD}'>{html.escape(top['name'])}</b> ({top['pct']:+.0%})."
            if low:
                text += f" A maior queda foi em <b style='color:{BAD}'>{html.escape(low['name'])}</b> ({low['pct']:+.0%})."
            if min(res["n_before"], res["n_after"]) < 3:
                text += " Com menos de 3 partidas de um dos lados, a comparação ainda oscila bastante."
            self.ba_box.addWidget(label(text, 12, TEXT))
        cells = [[html.escape(m["name"]), "—" if m["before"] is None else fmt(m["key"], m["before"]),
                  "—" if m["after"] is None else fmt(m["key"], m["after"]),
                  self.delta_cell(m)] for m in res["metrics"]]
        self.ba_box.addWidget(label(CSS + table(["Métrica", "Antes", "Depois", "Diferença"], cells), 12))

    @staticmethod
    def delta_cell(m):
        if m["delta"] is None:
            return "—"
        if m["improved"] is None:
            return f"<span style='color:{MUTED}'>= igual</span>"
        color = GOOD if m["improved"] else BAD
        sign = "+" if m["delta"] > 0 else "−"
        return f"<span style='color:{color}'>{'▲' if m['delta'] > 0 else '▼'} {sign}{fmt(m['key'], abs(m['delta']))}</span>"

    def render_social(self):
        if not self.stats:
            return
        order = sorted(self.stats.counters, key=lambda s: -self.stats.player(s)["rating"])
        rel = relations(self.stats.matches, self.me) if self.me in self.stats.counters else {}
        for box, default in ((self.friend_a, self.me if self.me in order else self.sid),
                             (self.friend_b, next((s for s in order if rel.get(s) == "ally" and s != self.me),
                                                  next((s for s in order if s != self.sid), self.sid)))):
            current = box.currentData() if box.currentData() in order else default
            box.blockSignals(True)
            box.clear()
            for sid in order:
                box.addItem(self.stats.names.get(sid, sid) + (" ★" if sid == self.me else ""), sid)
                box.setItemData(box.count() - 1, REL_COLORS.get(rel.get(sid)), REL_ROLE)
            box.setCurrentIndex(max(0, box.findData(current)))
            box.blockSignals(False)
        self.card_match.clear()
        for i, m in enumerate(self.stats.matches):
            when = datetime.fromtimestamp(float(m.played_at or 0)).strftime("%d/%m %H:%M")
            self.card_match.addItem(f"{MAP_NAMES.get(m.map_name, m.map_name)} · {when}", i)
        self.render_friend()
        self.render_achievements()

    def render_friend(self):
        clear(self.friend_box)
        a, b = self.friend_a.currentData(), self.friend_b.currentData()
        if not a or not b or a not in self.stats.counters or b not in self.stats.counters:
            return
        if a == b:
            self.friend_box.addWidget(label("Escolha dois jogadores diferentes.", 12, MUTED))
            return
        rows, (wa, wb) = prog.compare_players(self.stats, a, b)
        na, nb = (html.escape(self.stats.names.get(x, x)) for x in (a, b))
        lead = GOOD if wa > wb else BAD if wa < wb else MUTED
        self.friend_box.addWidget(label(f"<span style='color:{lead}'>{na} {wa} x {wb} {nb}</span> "
                                        f"<span style='color:{MUTED};font-size:{fs(12)}px'>· em {len(rows)} números</span>",
                                        18, TEXT, True))
        mark = lambda w, side, v, k: (f"<b style='color:{GOOD}'>{fmt(k, v)} ◀</b>" if side == "a" else
                                      f"<b style='color:{GOOD}'>▶ {fmt(k, v)}</b>") if w == side else fmt(k, v)
        cells = [[mark(r["winner"], "a", r["a"], r["key"]), html.escape(r["name"]), mark(r["winner"], "b", r["b"], r["key"])]
                 for r in rows]
        self.friend_box.addWidget(label(CSS + table([na, "Métrica", nb], cells), 12))

    def make_card(self):
        i = self.card_match.currentData()
        if i is None or not self.sid:
            return
        m = self.stats.matches[i]
        sid = self.sid if self.sid in set(m.roster.sid) else None
        if sid is None:
            QMessageBox.information(self, "Cartão", "Esse jogador não está nessa partida.")
            return
        p = combine([match_stats(m)]).player(sid)
        prof_data = self.profile() if sid == self.me else {"name": self.stats.names.get(sid, sid)}
        self.card_image = match_card(m, sid, p, prof_data, self.stats.names.get(sid, sid))
        self.card_preview.setPixmap(QPixmap.fromImage(self.card_image).scaledToWidth(600, Qt.SmoothTransformation))
        self.card_save.setEnabled(True)

    def save_card(self):
        self.save_image(self.card_image, "cartao_cs2.png")

    def save_image(self, image, default):
        if image is None:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Salvar cartão", str(Path.home() / default), "Imagem PNG (*.png)")
        if path:
            if not path.lower().endswith(".png"):
                path += ".png"
            if not image.save(path, "PNG"):
                QMessageBox.warning(self, "Cartão", "Não foi possível salvar a imagem.")

    def profile_card_image(self):
        sid = self.me or self.sid
        data = self.profile() if sid == self.me else {"name": self.stats.names.get(sid, sid) if self.stats else ""}
        rows = self.history.player(sid) if sid else []
        qualities = []
        weapons = self.stats.weapons if self.stats else None
        if self.stats and sid in self.stats.counters:
            qualities = diagnose(self.stats.player(sid), self.stats.lobby())[1]
        weapon = data.get("fav_weapon") or prog.top_weapon(weapons, sid) or ""
        items = prog.achievements(rows, self.checklist(), len(self.goals_history())) if sid == self.me else []
        name = data.get("name") or (self.stats.names.get(sid, sid) if self.stats and sid else "Jogador")
        return profile_card(data, name, prog.career(rows), qualities, weapon, prog.weapon_line(weapons, sid, weapon),
                            (sum(a.done for a in items), len(items)))

    def make_profile_card(self):
        self.pcard_image = self.profile_card_image()
        self.pcard_preview.setPixmap(QPixmap.fromImage(self.pcard_image).scaledToWidth(600, Qt.SmoothTransformation))
        self.pcard_save.setEnabled(True)

    def render_achievements(self):
        clear(self.ach_box)
        sid = self.me if self.me else self.sid
        items = prog.achievements(self.history.player(sid) if sid else [], self.checklist(), len(self.goals_history()))
        done = sum(a.done for a in items)
        self.ach_title.setText(f"🏆 Conquistas · {done} de {len(items)}")
        for i, a in enumerate(items):
            card = QFrame()
            card.setObjectName("clipcard")
            cl = QVBoxLayout(card)
            cl.setContentsMargins(12, 10, 12, 10)
            cl.addWidget(label(f"{a.icon}  {a.title}" + ("  ✓" if a.done else ""), 13, ACCENT if a.done else TEXT, True))
            cl.addWidget(label(a.desc, 11, MUTED))
            bar = QProgressBar()
            bar.setRange(0, int(a.total))
            bar.setValue(int(min(a.current, a.total)))
            bar.setFormat(f"{int(min(a.current, a.total))}/{int(a.total)}")
            bar.setFixedHeight(16)
            cl.addWidget(bar)
            self.ach_box.addWidget(card, i // 3, i % 3)

    def checklist(self):
        return prog.clean_checklist(self.cfg.get("checklist"))

    def goals_history(self):
        h = self.cfg.get("goals_done")
        return [x for x in h if isinstance(x, str)][-500:] if isinstance(h, list) else []

    def week_goals(self, issues):
        g = self.cfg.get("goals")
        week = prog.week_id()
        if not (isinstance(g, dict) and g.get("week") == week and g.get("sid") == self.sid and isinstance(g.get("items"), list)):
            g = {"week": week, "sid": self.sid, "since": prog.week_start(), "items": prog.make_goals(issues)}
            self.cfg["goals"] = g
            save_config(goals=g)
        return g

    def goals_box(self, issues):
        box = QFrame()
        box.setObjectName("card")
        lay = QVBoxLayout(box)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(8)
        lay.addWidget(label("🏁 Metas da semana", 14, bold=True))
        if self.sid != self.me:
            lay.addWidget(label("As metas e o checklist são só seus: escolha você na lista de jogadores para ver.", 12, MUTED))
            return box
        g = self.week_goals(issues)
        rows = self.history.player(self.sid)
        hist = self.goals_history()
        if not g["items"]:
            lay.addWidget(label("Nenhum ponto abaixo da referência: a meta da semana é manter o nível.", 12, GOOD))
        for goal in g["items"]:
            key = goal.get("metric")
            if key not in METRICS:
                continue
            current, done, n = prog.goal_status(goal, rows, prog.num(g, "since"))
            gid = f"{g['week']}:{key}"
            if done and gid not in hist:
                hist.append(gid)
                self.cfg["goals_done"] = hist
                save_config(goals_done=hist)
            now = "sem partidas nesta semana ainda" if current is None else f"agora {fmt(key, current)} em {n} partida(s)"
            cb = QCheckBox(f"{goal.get('title', key)}: chegar a {fmt(key, prog.num(goal, 'target'))} "
                           f"(começou em {fmt(key, prog.num(goal, 'start'))}, {now})")
            cb.setChecked(done)
            cb.setEnabled(False)
            cb.setStyleSheet(f"color:{GOOD if done else TEXT}")
            lay.addWidget(cb)
        lay.addWidget(label("As metas marcam sozinhas quando a média das suas partidas desta semana chega ao alvo. Toda "
                            "segunda-feira o app monta metas novas com base no diagnóstico.", 11, MUTED))
        return box

    def checklist_box(self, plan):
        box = QFrame()
        box.setObjectName("card")
        lay = QVBoxLayout(box)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(6)
        today = datetime.now().date()
        items = plan[today.weekday()][1]
        data = self.checklist()
        done = set(data.get(today.isoformat(), []))
        self.streak_label = label("", 13, ACCENT, True)
        lay.addWidget(label("✅ Checklist de hoje", 14, bold=True))
        if not items:
            lay.addWidget(label("Hoje é dia de descanso no seu plano.", 12, MUTED))
        for d in items:
            cb = QCheckBox(f"{d.name} · {d.minutes} min")
            cb.setChecked(d.key in done)
            cb.toggled.connect(lambda on, k=d.key: self.tick_drill(k, on))
            lay.addWidget(cb)
        lay.addWidget(self.streak_label)
        self.update_streak()
        return box

    def tick_drill(self, key, on):
        data = self.checklist()
        day = datetime.now().date().isoformat()
        keys = [k for k in data.get(day, []) if k != key] + ([key] if on else [])
        if keys:
            data[day] = keys
        else:
            data.pop(day, None)
        self.cfg["checklist"] = data
        save_config(checklist=data)
        self.update_streak()

    def update_streak(self):
        data = self.checklist()
        n, best = prog.streak(data), prog.best_streak(data)
        self.streak_label.setText(f"🔥 Sequência: {n} dia(s) seguidos · recorde {best}" if n else
                                  f"Marque um treino para começar uma sequência · recorde {best}")

    def render_board(self):
        cols = [("Jogador", None), ("Time", None), ("K", "kills"), ("D", "deaths"), ("A", "assists"),
                ("ADR", "adr"), ("KAST %", "kast"), ("HS %", "hs_pct"), ("Rating", "rating")]
        rel = relations(self.stats.matches, self.me) if self.me in self.stats.counters else {}
        rank = {"me": 0, "ally": 0, "mixed": 1, "enemy": 2}
        order = sorted(self.stats.counters, key=lambda s: (rank.get(rel.get(s), 3), -self.stats.player(s)["rating"]))
        tags = {"me": ("Você", ACCENT), "ally": ("Seu time", CT_COLOR), "enemy": ("Inimigo", BAD), "mixed": ("Os dois", MUTED)}
        self.board.setSortingEnabled(False)
        self.board.clear()
        self.board.setColumnCount(len(cols))
        self.board.setHorizontalHeaderLabels([c for c, _ in cols])
        self.board.setRowCount(len(order))
        for r, sid in enumerate(order):
            p = self.stats.player(sid)
            tag, color = tags.get(rel.get(sid), ("—", MUTED))
            for c, (name, key) in enumerate(cols):
                item = QTableWidgetItem()
                if key is None:
                    item.setText(self.stats.names[sid] + (" ★" if sid == self.me else "") if c == 0 else tag)
                    item.setData(Qt.UserRole, sid)
                    if c == 1:
                        item.setForeground(QColor(color))
                else:
                    v = p[key] * 100 if name.endswith("%") else p[key]
                    item.setData(Qt.DisplayRole, round(float(v), 2 if key == "rating" else 1))
                if sid == self.me:
                    item.setBackground(QColor(SELECTED))
                elif rel.get(sid) == "enemy":
                    item.setBackground(QColor(mix(PANEL, BAD, 0.1)))
                elif rel.get(sid) == "ally":
                    item.setBackground(QColor(mix(PANEL, CT_COLOR, 0.1)))
                self.board.setItem(r, c, item)
        self.board.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.board.horizontalHeader().setSortIndicator(-1, Qt.AscendingOrder)
        self.board.setSortingEnabled(True)
        self.render_teams(rel)

    def render_teams(self, rel):
        clear(self.teams_box)
        if not rel:
            self.teams_box.addWidget(label("Escolha quem é você para separar seu time e o time inimigo.", 12, MUTED))
            return
        won = lost = 0
        for m in self.stats.matches:
            teams = dict(zip(m.roster[m.roster.sid == self.me]["round"], m.roster[m.roster.sid == self.me].team))
            won += sum(teams.get(r) == w for r, w in zip(m.rounds["round"], m.rounds.winner))
            lost += sum(r in teams and teams[r] != w for r, w in zip(m.rounds["round"], m.rounds.winner))

        def side(kind, title, color, rounds):
            sids = [s for s, k in rel.items() if k in kind and s in self.stats.counters]
            ps = [self.stats.player(s) for s in sids]
            box = QFrame()
            box.setObjectName("card")
            bl = QVBoxLayout(box)
            bl.setContentsMargins(16, 12, 16, 12)
            bl.addWidget(label(title, 12, color, True))
            bl.addWidget(label(f"{rounds} rounds ganhos", 24, bold=True))
            if ps:
                bl.addWidget(label(f"{int(sum(p['kills'] for p in ps))} kills · ADR médio {sum(p['adr'] for p in ps) / len(ps):.0f} · "
                                   f"rating médio {sum(p['rating'] for p in ps) / len(ps):.2f}", 12, MUTED))
            return box

        row = QHBoxLayout()
        row.setSpacing(12)
        row.addWidget(side(("me", "ally"), "SEU TIME", CT_COLOR, won))
        row.addWidget(side(("enemy",), "TIME INIMIGO", BAD, lost))
        holder = QWidget()
        holder.setLayout(row)
        row.setContentsMargins(0, 0, 0, 0)
        self.teams_box.addWidget(holder)

        killed_by, killed = rivals(self.stats.matches, self.me)
        lines = []
        if killed_by:
            sid, n = killed_by.most_common(1)[0]
            lines.append(f"😤 Quem mais te matou: <b>{html.escape(self.stats.names.get(sid, '?'))}</b> ({n}×)")
        if killed:
            sid, n = killed.most_common(1)[0]
            lines.append(f"🎯 Quem você mais matou: <b>{html.escape(self.stats.names.get(sid, '?'))}</b> ({n}×)")
        if lines:
            self.teams_box.addWidget(label("  ·  ".join(lines), 13))

    def export_plan(self):
        if not self.sid:
            return
        name = self.stats.names[self.sid]
        safe = re.sub(r"[^\w\-]", "_", name)[:40] or "jogador"
        path, _ = QFileDialog.getSaveFileName(self, "Salvar plano", str(Path.home() / f"plano_{safe}.md"), "Markdown (*.md)")
        if path:
            Path(path).write_text(plan_markdown(name, *self.training()), encoding="utf-8")


def chevron(way):
    path = HOME / f"chevron_{way}_{SOFT[1:]}.svg"
    if not path.exists():
        HOME.mkdir(parents=True, exist_ok=True)
        d = "M6 9l6 6 6-6" if way == "down" else "M6 15l6-6 6 6"
        path.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path d="{d}" '
                        f'fill="none" stroke="{SOFT}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></svg>',
                        encoding="utf-8")
    return path.as_posix()


def searchable(combo, placeholder="🔎 Buscar nick…"):
    combo.setEditable(True)
    combo.setInsertPolicy(QComboBox.NoInsert)
    combo.lineEdit().setPlaceholderText(placeholder)
    completer = QCompleter(combo.model(), combo)
    completer.setCompletionMode(QCompleter.PopupCompletion)
    completer.setCaseSensitivity(Qt.CaseInsensitive)
    completer.setFilterMode(Qt.MatchContains)
    completer.popup().setItemDelegate(StripeDelegate(completer.popup()))
    completer.popup().setObjectName("search")
    combo.setCompleter(completer)

    def pick(text):
        i = combo.findText(text)
        if i >= 0:
            combo.setCurrentIndex(i)
        combo.lineEdit().setText(combo.currentText() if combo.currentIndex() >= 0 else "")
        combo.lineEdit().clearFocus()

    def restore():
        if combo.findText(combo.lineEdit().text()) < 0:
            matches = [i for i in range(combo.count()) if combo.lineEdit().text().lower() in combo.itemText(i).lower()]
            if len(matches) == 1 and combo.lineEdit().text():
                combo.setCurrentIndex(matches[0])
            combo.lineEdit().setText(combo.itemText(combo.currentIndex()) if combo.currentIndex() >= 0 else "")

    completer.activated.connect(pick)
    combo.lineEdit().editingFinished.connect(restore)
    return combo


class SmoothWheel(QObject):
    STEP = 110

    def __init__(self):
        super().__init__()
        self.anims = {}

    def area_of(self, w):
        while w is not None:
            if isinstance(w, QScrollArea) and w.verticalScrollBar().maximum() > 0:
                return w
            w = w.parentWidget()
        return None

    def eventFilter(self, obj, event):
        if event.type() != QEvent.Wheel or not isinstance(obj, QWidget):
            return False
        swallow = isinstance(obj, (Chart, QComboBox)) and not (isinstance(obj, QComboBox) and obj.view().isVisible())
        if not swallow and not (obj.parentWidget() is not None and isinstance(obj.parentWidget(), QScrollArea)
                                and obj is obj.parentWidget().viewport()):
            return False
        area = self.area_of(obj.parentWidget() if obj.parentWidget() else obj)
        if area is None:
            return swallow
        bar = area.verticalScrollBar()
        pixel = event.pixelDelta().y()
        if pixel:
            bar.setValue(bar.value() - pixel)
            return True
        steps = event.angleDelta().y() / 120
        if not steps:
            return swallow
        anim = self.anims.get(area)
        if anim is None:
            anim = QVariantAnimation(area)
            anim.setDuration(160)
            anim.setEasingCurve(QEasingCurve.OutCubic)
            anim.valueChanged.connect(lambda v, b=bar: b.setValue(int(v)))
            anim.target = bar.value()
            self.anims[area] = anim
            area.destroyed.connect(lambda *_, a=area: self.anims.pop(a, None))
        base = anim.target if anim.state() == QVariantAnimation.Running else bar.value()
        anim.target = max(bar.minimum(), min(bar.maximum(), int(base - steps * self.STEP)))
        anim.stop()
        anim.setStartValue(bar.value())
        anim.setEndValue(anim.target)
        anim.start()
        return True


def check_icon(color):
    path = HOME / f"check_{color[1:]}.svg"
    if not path.exists():
        HOME.mkdir(parents=True, exist_ok=True)
        path.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path d="M5 12.5l4.5 4.5L19 7.5" '
                        f'fill="none" stroke="{color}" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
                        encoding="utf-8")
    return path.as_posix()


def dark(app):
    app.setStyle("Fusion")
    pal = QPalette()
    for role, color in [(QPalette.Window, BG), (QPalette.WindowText, TEXT), (QPalette.Base, PANEL),
                        (QPalette.AlternateBase, BG), (QPalette.Text, TEXT), (QPalette.Button, PANEL),
                        (QPalette.ButtonText, TEXT), (QPalette.Highlight, ACCENT), (QPalette.HighlightedText, BG),
                        (QPalette.ToolTipBase, PANEL), (QPalette.ToolTipText, TEXT), (QPalette.PlaceholderText, MUTED)]:
        pal.setColor(role, QColor(color))
    app.setPalette(pal)
    app.setStyleSheet(f"""
        QWidget {{ font-size: 15px; }}
        QToolTip {{ background: {PANEL}; color: {TEXT}; border: 1px solid {LINE}; padding: 6px; }}
        #side {{ background: {PANEL}; border-right: 1px solid {LINE}; }}
        #nav {{ background: transparent; border: none; outline: none; font-size: 16px; }}
        #nav::item {{ padding: 11px 12px; margin: 1px 0; border-radius: 8px; color: {SOFT}; }}
        #nav::item:selected {{ background: {SELECTED}; color: {ACCENT}; border-left: 3px solid {ACCENT}; }}
        #nav::item:hover:!selected {{ background: {LINE}; color: {TEXT}; }}
        #card {{ background: {PANEL}; border: 1px solid {LINE}; border-radius: 10px; }}
        #help {{ color: {MUTED}; border: 1px solid {MUTED}; border-radius: 10px; font-size: {fs(11)}px; font-weight: 600; }}
        #help:hover {{ color: {ACCENT}; border-color: {ACCENT}; }}
        QPushButton {{ background: {BUTTON}; border: 1px solid {BORDER}; border-radius: 8px; padding: 8px 16px;
                       color: {TEXT}; font-weight: 600; }}
        QPushButton:hover {{ background: {HOVER}; border-color: {ACCENT}; }}
        QPushButton:pressed {{ background: {PRESSED}; }}
        QPushButton:disabled {{ color: {MUTED}; border-color: {LINE}; }}
        QPushButton:checked {{ border-color: {ACCENT}; color: {ACCENT}; }}
        #chip {{ border-radius: 15px; padding: 5px 12px; min-height: 18px; font-weight: normal; }}
        #chip:checked {{ background: {SELECTED}; }}
        #primary {{ background: {ACCENT}; color: {ON_ACCENT}; border: none; font-weight: 700; font-size: 14px; }}
        #primary:hover {{ background: {ACCENT_HOVER}; }}
        #primary:pressed {{ background: {ACCENT_PRESSED}; }}
        #toggle {{ background: transparent; border: 1px solid {LINE}; color: {SOFT}; padding: 6px 14px; }}
        #toggle:hover {{ border-color: {ACCENT}; color: {TEXT}; }}
        #link {{ background: transparent; border: none; color: {SOFT}; padding: 4px 0; font-weight: 600; }}
        #link:hover {{ color: {ACCENT}; }}
        #avatar {{ background: transparent; border: none; padding: 0; }}
        QToolButton:checked {{ background: {LINE}; border-radius: 8px; }}
        QToolButton:disabled {{ color: {MUTED}; }}
        QLineEdit {{ background: {PANEL}; border: 1px solid {LINE}; border-radius: 8px; padding: 6px 10px; }}
        QDialog {{ background: {BG}; }}
        QComboBox {{ background: {INPUT}; border: 1px solid {BORDER}; border-radius: 8px; padding: 7px 36px 7px 12px;
                     color: {TEXT}; font-weight: 600; }}
        QComboBox:hover {{ border-color: {ACCENT}; }}
        QComboBox QLineEdit {{ background: transparent; border: none; padding: 0; color: {TEXT}; font-weight: 600; }}
        #search {{ background: {PANEL}; border: 1px solid {BORDER}; border-radius: 8px; padding: 4px; color: {TEXT}; outline: none; }}
        #search::item {{ min-height: 28px; padding: 2px 8px; border-radius: 6px; }}
        #search::item:selected {{ background: {HOVER}; }}
        QComboBox:on {{ border-color: {ACCENT}; }}
        QComboBox::drop-down {{ subcontrol-origin: padding; subcontrol-position: center right; width: 30px; border: none; }}
        QComboBox::down-arrow {{ image: url({chevron("down")}); width: 14px; height: 14px; }}
        QComboBox::down-arrow:on {{ image: url({chevron("up")}); }}
        QComboBox QAbstractItemView {{ background: {PANEL}; border: 1px solid {BORDER}; border-radius: 8px; padding: 4px;
                                      outline: none; selection-background-color: {HOVER}; color: {TEXT}; }}
        QComboBox QAbstractItemView::item {{ min-height: 30px; padding: 4px 10px; border-radius: 6px; }}
        QComboBox QAbstractItemView::item:hover {{ background: {HOVER}; }}
        #killrow {{ background: transparent; border: none; text-align: left; padding: 6px 6px; font-weight: 600; }}
        #killrow:hover {{ background: {LINE}; }}
        #besttab, #cliptab {{ font-size: {fs(14)}px; border-radius: 10px; }}
        #besttab {{ border: 2px solid {ACCENT}; color: {ACCENT}; font-size: {fs(16)}px; font-weight: 700; }}
        #besttab:checked {{ background: {ACCENT}; color: {ON_ACCENT}; }}
        #besttab:hover {{ background: {SELECTED}; }}
        #besttab:checked:hover {{ background: {ACCENT_HOVER}; }}
        #cliptab:checked {{ background: {SELECTED}; }}
        #clipcard {{ background: {INPUT}; border: 1px solid {BORDER}; border-radius: 10px; }}
        #feed {{ background: transparent; border: none; outline: none; }}
        #feed::item {{ padding: 6px 6px; border-radius: 6px; }}
        #feed::item:selected {{ background: {SELECTED}; color: {TEXT}; }}
        #feed::item:hover {{ background: {LINE}; }}
        QSlider::groove:horizontal {{ height: 6px; background: {LINE}; border-radius: 3px; }}
        QSlider::sub-page:horizontal {{ background: {ACCENT}; border-radius: 3px; }}
        QSlider::handle:horizontal {{ background: {TEXT}; width: 14px; margin: -5px 0; border-radius: 7px; }}
        QTableWidget {{ background: {PANEL}; border: 1px solid {LINE}; border-radius: 10px; }}
        QTableWidget::indicator {{ width: 16px; height: 16px; border: 1px solid {MUTED}; border-radius: 4px; background: {BG}; }}
        QTableWidget::indicator:checked {{ background: {ACCENT}; border-color: {ACCENT}; }}
        QTableWidget::item {{ padding: 6px 4px; }}
        QHeaderView::section {{ background: {PANEL}; color: {MUTED}; border: none; padding: 8px; }}
        QScrollArea {{ background: {BG}; }}
        QProgressBar {{ background: {LINE}; border: none; border-radius: 8px; color: {TEXT}; text-align: center;
                        font-size: {fs(10)}px; }}
        QProgressBar::chunk {{ background: {ACCENT}; border-radius: 8px; }}
        QCheckBox {{ spacing: 10px; padding: 3px 0; font-size: {fs(13)}px; }}
        QCheckBox::indicator {{ width: 20px; height: 20px; border: 2px solid {SOFT}; border-radius: 6px; background: {INPUT}; }}
        QCheckBox::indicator:hover {{ border-color: {ACCENT}; }}
        QCheckBox::indicator:checked {{ background: {ACCENT}; border-color: {ACCENT}; image: url({check_icon(ON_ACCENT)}); }}
        QCheckBox::indicator:disabled {{ border-color: {MUTED}; background: {INPUT}; }}
        QCheckBox::indicator:checked:disabled {{ background: {GOOD}; border-color: {GOOD}; image: url({check_icon(ON_ACCENT)}); }}
        QCheckBox:disabled {{ color: {TEXT}; }}
        QScrollBar:vertical {{ background: transparent; width: 8px; }}
        QScrollBar::handle:vertical {{ background: {LINE}; border-radius: 4px; }}
        QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
    """)


def run():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(str(ICON)))
    dark(app)
    wheel = SmoothWheel()
    app.installEventFilter(wheel)
    w = Main()
    w.show()
    if len(sys.argv) > 1:
        w.load(sys.argv[1:])
    sys.exit(app.exec())
