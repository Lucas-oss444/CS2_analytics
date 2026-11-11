from datetime import datetime

from PySide6.QtWidgets import (QButtonGroup, QFrame, QGridLayout, QHBoxLayout, QInputDialog, QLabel, QMessageBox,
                               QPushButton, QScrollArea, QVBoxLayout, QWidget)

from . import library
from .coach import MAP_NAMES
from .demo import TICKRATE
from .replay import highlights
from .replay_ui import launch_pov
from .theme import ACCENT, MUTED, TEXT, fs

FILTERS = [("auto", "⭐  Melhores jogadas", "ACE, 4K, 3K, clutches e kills rápidas que o app achou sozinho"),
           ("mine", "✂  Meus clipes", "Os lances que você clipou no Replay"), ("all", "Todos", "")]


def label(text, size=13, color=TEXT, bold=False):
    w = QLabel(text)
    w.setWordWrap(True)
    w.setStyleSheet(f"color:{color};font-size:{fs(size)}px;{'font-weight:600;' if bold else ''}background:transparent")
    return w


class ClipsPage(QScrollArea):
    def __init__(self, main):
        super().__init__()
        self.main = main
        self.cache = {}
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        inner = QWidget()
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(28, 20, 28, 28)
        lay.setSpacing(12)
        lay.addWidget(label("Clipes salvos", 20, bold=True))
        tabs = QHBoxLayout()
        tabs.setSpacing(10)
        self.group = QButtonGroup(self)
        self.mode = FILTERS[0][0]
        for key, name, tip in FILTERS:
            btn = QPushButton(name)
            btn.setObjectName("cliptab" if key != "auto" else "besttab")
            btn.setCheckable(True)
            btn.setChecked(key == self.mode)
            btn.setMinimumHeight(48)
            btn.setToolTip(tip)
            btn.clicked.connect(lambda _, k=key: self.set_mode(k))
            self.group.addButton(btn)
            tabs.addWidget(btn, 2 if key == "auto" else 1)
        lay.addLayout(tabs)
        lay.addWidget(label("Todos os clipes das suas demos num só lugar. Para criar um clipe, vá em 🎬 Replay e clique em ✂ "
                            "ao lado de uma kill.", 12, MUTED))
        self.grid = QGridLayout()
        self.grid.setSpacing(12)
        lay.addLayout(self.grid)
        lay.addStretch()
        self.setWidget(inner)

    def set_mode(self, key):
        self.mode = key
        self.refresh()

    def match(self, mid):
        if mid not in self.cache:
            self.cache[mid] = library.load(mid)
        return self.cache[mid]

    def items(self):
        mode = self.mode
        out = []
        for e in library.entries():
            mid = e["id"]
            clips = library.clips(mid)[::-1] if mode in ("mine", "all") else []
            if mode in ("auto", "all"):
                m = self.match(mid)
                me = self.main.me if self.main.me in set(m.roster.sid) else None
                clips += highlights(m, me, limit=6)
            out += [(e, c) for c in clips]
        return out

    def refresh(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        try:
            items = self.items()
        except library.LibraryError as e:
            items = []
            self.grid.addWidget(label(str(e), 12, MUTED), 0, 0)
        for i, (e, c) in enumerate(items):
            self.grid.addWidget(self.card(e, c), i // 2, i % 2)
        if not items:
            msg = ("Você ainda não salvou nenhum clipe. Abra 🎬 Replay, escolha um round e clique em ✂ ao lado de uma kill."
                   if self.mode == "mine" else "Nenhuma jogada encontrada ainda. Adicione demos em 🗂 Minhas demos: o app procura ACE, 4K, "
                   "3K, clutches e kills rápidas sozinho.")
            self.grid.addWidget(label(msg, 13, MUTED), 0, 0, 1, 2)

    def card(self, e, c):
        box = QFrame()
        box.setObjectName("clipcard")
        lay = QVBoxLayout(box)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(6)
        when = datetime.fromtimestamp(float(e.get("played_at", 0))).strftime("%d/%m/%Y")
        mapa = MAP_NAMES.get(e.get("map"), str(e.get("map")))
        kind = "⭐ Melhor jogada" if c.get("auto") else "✂ Seu clipe"
        lay.addWidget(label(c["name"], 15, bold=True))
        lay.addWidget(label(f"{kind} · {mapa} · {when} · Round {c['round']} · {(c['end'] - c['start']) / TICKRATE:.0f} s",
                            12, ACCENT if c.get("auto") else MUTED))
        row = QHBoxLayout()
        row.setSpacing(6)
        buttons = [("▶ Ver no Replay", lambda: self.main.open_clip(e["id"], c, "play")),
                   ("👁 No CS2", lambda: launch_pov(self, e["id"], c["start"], c["round"], c.get("sid") or self.main.me)),
                   ("🎥 Gravar", lambda: launch_pov(self, e["id"], c["start"], c["round"], c.get("sid") or self.main.me, True))]
        if not c.get("auto"):
            buttons += [("✏", lambda: self.rename(e["id"], c)), ("🗑", lambda: self.delete(e["id"], c))]
        for text, fn in buttons:
            b = QPushButton(text)
            if text in ("✏", "🗑"):
                b.setFixedWidth(44)
                b.setToolTip("Renomear" if text == "✏" else "Apagar")
            b.clicked.connect(fn)
            row.addWidget(b)
        lay.addLayout(row)
        return box

    def rename(self, mid, clip):
        name, ok = QInputDialog.getText(self, "Renomear clipe", "Novo nome:", text=clip["name"])
        if ok and name.strip():
            items = library.clips(mid)
            for c in items:
                if c["id"] == clip["id"]:
                    c["name"] = name.strip()
            library.save_clips(mid, items)
            self.refresh()

    def delete(self, mid, clip):
        if QMessageBox.question(self, "Apagar clipe", f"Apagar o clipe \"{clip['name']}\"?") == QMessageBox.Yes:
            library.save_clips(mid, [c for c in library.clips(mid) if c["id"] != clip["id"]])
            self.refresh()
