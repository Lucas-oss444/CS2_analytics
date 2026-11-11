import sys

from PySide6.QtCore import QProcess, QSize, Qt, QThread, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QIcon, QPixmap
from PySide6.QtWidgets import (QApplication, QCheckBox, QColorDialog, QDialog, QFileDialog, QFontDialog, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
                               QMessageBox, QPushButton, QScrollArea, QToolButton, QVBoxLayout, QWidget)

from . import profile as prof
from . import weapons as wp
from .coach import TEAMS, TEAMS_UPDATED
from .storage import save_config
from . import updater
from .theme import ACCENT, BAD, BG, GOOD, MUTED, THEME, THEMES, fs


def text(value, color=None, size=13, bold=False):
    w = QLabel(value)
    w.setWordWrap(True)
    w.setTextFormat(Qt.PlainText)
    style = f"font-size:{fs(size)}px;"
    if color:
        style += f"color:{color};"
    if bold:
        style += "font-weight:600;"
    w.setStyleSheet(style)
    return w


class ProfileDialog(QDialog):
    def __init__(self, parent, data, earned, progress=None):
        super().__init__(parent)
        self.progress = progress or {}
        self.setWindowTitle("Editar perfil")
        self.data = dict(data)
        self.earned = earned
        self.preview = QLabel()
        self.preview.setAlignment(Qt.AlignCenter)
        self.name_preview = prof.NameLabel(44, 24)
        self.name_preview.setFixedWidth(220)
        self.name = QLineEdit(self.data.get("name", ""))
        self.name.setMaxLength(24)
        self.name.setPlaceholderText("Seu nome no perfil")
        self.name.textChanged.connect(self.changed)
        pick = QPushButton("Escolher foto…")
        pick.clicked.connect(self.pick_photo)
        drop = QPushButton("Remover foto")
        drop.clicked.connect(self.drop_photo)

        fonts = QGridLayout()
        fonts.setSpacing(8)
        self.font_btns = {}
        for i, family in enumerate(prof.available_fonts()[:8]):
            btn = QPushButton(family)
            btn.setObjectName("chip")
            btn.setCheckable(True)
            btn.setFont(QFont(family, 10))
            btn.clicked.connect(lambda _, f=family: self.set("font", f))
            fonts.addWidget(btn, i // 4, i % 4)
            self.font_btns[family] = btn
        self.other_font = QPushButton("Outra…")
        self.other_font.setObjectName("chip")
        self.other_font.setCheckable(True)
        self.other_font.clicked.connect(self.pick_font)
        n = len(self.font_btns)
        fonts.addWidget(self.other_font, n // 4, n % 4)

        styles = QHBoxLayout()
        self.style_btns = {}
        for key, label in prof.NAME_STYLES:
            btn = QPushButton(label)
            btn.setObjectName("chip")
            btn.setCheckable(True)
            btn.clicked.connect(lambda _, k=key: self.set("name_style", k))
            styles.addWidget(btn)
            self.style_btns[key] = btn
        styles.addStretch()

        self.neon_row = QWidget()
        neon = QHBoxLayout(self.neon_row)
        neon.setContentsMargins(0, 0, 0, 0)
        self.neon_btns = {}
        for c in prof.NEON_COLORS:
            b = QPushButton()
            b.setFixedSize(24, 24)
            b.clicked.connect(lambda _, c=c: self.set("neon_color", c))
            neon.addWidget(b)
            self.neon_btns[c] = b
        custom = QPushButton("+")
        custom.setFixedSize(24, 24)
        custom.setToolTip("Escolher outra cor")
        custom.setStyleSheet("border-radius:12px;padding:0;font-weight:600")
        custom.clicked.connect(self.pick_neon)
        neon.addWidget(custom)
        neon.addStretch()

        colors = QHBoxLayout()
        for c in prof.COLORS:
            b = QPushButton()
            b.setFixedSize(28, 28)
            b.setStyleSheet(f"background:{c};border-radius:14px;border:2px solid {BG}")
            b.clicked.connect(lambda _, c=c: self.set("color", c))
            colors.addWidget(b)
        colors.addStretch()

        grid = QGridLayout()
        grid.setSpacing(10)
        self.border_btns = {}
        for i, b in enumerate(prof.BORDERS):
            btn = QToolButton()
            btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            btn.setIconSize(QSize(52, 52))
            btn.setFixedSize(96, 92)
            btn.setCheckable(True)
            btn.clicked.connect(lambda _, k=b.key: self.set("border", k))
            grid.addWidget(btn, i // 5, i % 5)
            self.border_btns[b.key] = btn

        self.admin = QCheckBox("Modo administrador: liberar todas as bordas")
        self.admin.setChecked(bool(self.data.get("admin")))
        self.admin.toggled.connect(lambda on: self.set("admin", on))

        avatars = QGridLayout()
        avatars.setSpacing(6)
        self.avatar_btns = {}
        for key, name in prof.AVATARS:
            btn = QToolButton()
            btn.setIconSize(QSize(40, 40))
            btn.setFixedSize(52, 52)
            btn.setCheckable(True)
            btn.setToolTip(name)
            btn.clicked.connect(lambda _, k=key: self.set("avatar", k))
            avatars.addWidget(btn, len(self.avatar_btns) // 10, len(self.avatar_btns) % 10)
            self.avatar_btns[key] = btn
        avatars.setColumnStretch(10, 1)
        effects = QHBoxLayout()
        self.effect_btns = {}
        for key, name in prof.EFFECTS:
            btn = QPushButton(name)
            btn.setObjectName("chip")
            btn.setCheckable(True)
            btn.clicked.connect(lambda _, k=key: self.set("effect", k))
            effects.addWidget(btn)
            self.effect_btns[key] = btn
        effects.addStretch()
        self.phase = 0.0
        self.anim = QTimer(self)
        self.anim.setInterval(50)
        self.anim.timeout.connect(self.animate)
        self.anim.start()

        self.team_box, self.player_box = QComboBox(), QComboBox()
        self.team_box.addItem("Nenhum", "")
        for team in TEAMS:
            self.team_box.addItem(team, team)
        self.team_box.setCurrentIndex(max(0, self.team_box.findData(self.data.get("fav_team", ""))))
        self.team_box.currentIndexChanged.connect(self.team_changed)
        self.player_box.currentIndexChanged.connect(lambda: self.set("fav_player", self.player_box.currentData() or ""))
        self.fill_players()
        fav = QHBoxLayout()
        fav.addWidget(self.team_box, 1)
        fav.addWidget(self.player_box, 1)
        self.weapon_box = QComboBox()
        self.weapon_box.setIconSize(QSize(56, 24))
        self.weapon_box.addItem("Nenhuma", "")
        for key, (name, _) in sorted(wp.WEAPONS.items(), key=lambda kv: kv[1][0].lower()):
            self.weapon_box.addItem(QIcon(wp.sticker(56, key)), name, key)
        self.weapon_box.setCurrentIndex(max(0, self.weapon_box.findData(self.data.get("fav_weapon", ""))))
        self.weapon_box.currentIndexChanged.connect(self.weapon_changed)
        self.weapon_preview = QLabel()
        self.weapon_preview.setFixedSize(120, 52)
        weapon_row = QHBoxLayout()
        weapon_row.addWidget(self.weapon_box, 1)
        weapon_row.addWidget(self.weapon_preview)
        self.weapon_changed()

        save = QPushButton("Salvar")
        save.setObjectName("primary")
        save.clicked.connect(self.accept)
        cancel = QPushButton("Cancelar")
        cancel.clicked.connect(self.reject)

        left = QVBoxLayout()
        left.addWidget(self.preview, alignment=Qt.AlignCenter)
        left.addWidget(self.name_preview, alignment=Qt.AlignCenter)
        left.addWidget(pick)
        left.addWidget(drop)
        left.addStretch()
        right = QVBoxLayout()
        right.addWidget(text("Nome", MUTED, 12))
        right.addWidget(self.name)
        right.addWidget(text("Fonte do nome", MUTED, 12))
        right.addLayout(fonts)
        right.addWidget(text("Estilo do nome", MUTED, 12))
        right.addLayout(styles)
        right.addWidget(self.neon_row)
        right.addWidget(text("Cor", MUTED, 12))
        right.addLayout(colors)
        right.addWidget(text("Avatar (usado quando não há foto)", MUTED, 12))
        right.addLayout(avatars)
        right.addWidget(text("Borda", MUTED, 12))
        right.addLayout(grid)
        right.addWidget(text("Efeito animado", MUTED, 12))
        right.addLayout(effects)
        right.addWidget(text(f"Time e jogador favoritos ({TEAMS_UPDATED})", MUTED, 12))
        right.addLayout(fav)
        right.addWidget(text("Arma favorita", MUTED, 12))
        right.addLayout(weapon_row)
        right.addWidget(self.admin)
        holder = QWidget()
        holder.setLayout(right)
        right.setContentsMargins(0, 0, 12, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidget(holder)
        body = QHBoxLayout()
        body.setSpacing(24)
        body.addLayout(left)
        body.addWidget(scroll, 1)
        buttons = QHBoxLayout()
        buttons.addStretch()
        buttons.addWidget(cancel)
        buttons.addWidget(save)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 20)
        lay.addLayout(body)
        lay.addLayout(buttons)
        self.resize(880, 720)
        self.refresh()

    def set(self, key, value):
        self.data[key] = value
        self.refresh()

    def weapon_changed(self):
        key = self.weapon_box.currentData() or ""
        self.data["fav_weapon"] = key
        self.weapon_preview.setPixmap(wp.sticker(120, key) if key else QPixmap())

    def team_changed(self):
        self.data["fav_team"] = self.team_box.currentData() or ""
        self.data["fav_player"] = ""
        self.fill_players()

    def fill_players(self):
        team = self.team_box.currentData()
        self.player_box.blockSignals(True)
        self.player_box.clear()
        self.player_box.addItem("Escolha o jogador" if team else "Escolha um time primeiro", "")
        for name in TEAMS.get(team, []):
            self.player_box.addItem(name, name)
        self.player_box.setCurrentIndex(max(0, self.player_box.findData(self.data.get("fav_player", ""))))
        self.player_box.setEnabled(bool(team))
        self.player_box.blockSignals(False)

    def changed(self, value):
        self.data["name"] = value.strip()
        self.refresh()

    def refresh(self):
        allowed = prof.unlocked([], True) if self.data.get("admin") else self.earned
        if self.data.get("border", "classic") not in allowed:
            self.data["border"] = "classic"
        self.preview.setPixmap(prof.avatar(150, self.data, self.phase))
        for key, btn in self.avatar_btns.items():
            btn.setIcon(QIcon(prof.avatar(40, self.data | {"avatar": key, "photo": False, "border": "none", "effect": "none"})))
            btn.setChecked(self.data.get("avatar", "initials") == key)
        for key, btn in self.effect_btns.items():
            btn.setChecked(self.data.get("effect", "none") == key)
        self.name_preview.set_profile(self.data)
        self.admin.blockSignals(True)
        self.admin.setChecked(bool(self.data.get("admin")))
        self.admin.blockSignals(False)
        for key, btn in self.style_btns.items():
            btn.setChecked(self.data.get("name_style", "normal") == key)
        self.neon_row.setVisible(self.data.get("name_style") == "neon")
        current = self.data.get("neon_color")
        for c, b in self.neon_btns.items():
            ring = "#ffffff" if c == current and c != "#ffffff" else ACCENT if c == current else BG
            b.setStyleSheet(f"background:{c};border-radius:12px;border:2px solid {ring}")
        font = self.data.get("font")
        for family, btn in self.font_btns.items():
            btn.setChecked(font == family)
        self.other_font.setChecked(bool(font) and font not in self.font_btns)
        self.other_font.setText(f"Outra: {font}" if self.other_font.isChecked() else "Outra…")
        for b in prof.BORDERS:
            btn = self.border_btns[b.key]
            locked = b.key not in allowed
            btn.setEnabled(not locked)
            btn.setText(("🔒 " if locked else "") + b.name)
            goal = self.progress.get(b.key)
            btn.setToolTip(f"🔒 Objetivo: {b.unlock}" + (f" (progresso: {goal})" if goal else "") if locked
                           else b.name + (f" · {b.unlock} ✓" if b.unlock else ""))
            btn.setIcon(QIcon(prof.avatar(52, self.data | {"border": b.key, "effect": "none"})))
            btn.setChecked(self.data.get("border", "classic") == b.key)

    def animate(self):
        self.phase = (self.phase + 0.01) % 1.0
        self.preview.setPixmap(prof.avatar(150, self.data, self.phase))

    def pick_font(self):
        ok, font = QFontDialog.getFont(QFont(self.data.get("font") or ""), self, "Fonte do nome")
        if ok:
            self.set("font", font.family())
        else:
            self.refresh()

    def pick_neon(self):
        start = QColor(prof.valid_color(self.data.get("neon_color"), prof.NEON_COLORS[0]))
        color = QColorDialog.getColor(start, self, "Cor do neon")
        if color.isValid():
            self.set("neon_color", color.name())

    def pick_photo(self):
        path, _ = QFileDialog.getOpenFileName(self, "Escolha uma foto", "", "Imagens (*.png *.jpg *.jpeg *.bmp *.webp)")
        if not path:
            return
        try:
            prof.import_photo(path)
        except (OSError, ValueError) as e:
            QMessageBox.warning(self, "Foto", str(e))
            return
        self.set("photo", True)

    def drop_photo(self):
        prof.remove_photo()
        self.set("photo", False)


class Worker(QThread):
    done = Signal(bool, str)

    def __init__(self, job):
        super().__init__()
        self.job = job

    def run(self):
        try:
            self.done.emit(True, self.job() or "")
        except updater.UpdateError as e:
            self.done.emit(False, str(e))
        except Exception as e:
            self.done.emit(False, f"erro inesperado: {e}")


class UpdateDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Atualizações")
        self.setMinimumWidth(520)
        self.zip_path = None
        self.info = None
        self.status = text("", MUTED, 12)
        self.details = text("")
        choose = QPushButton("Escolher pacote (.zip)…")
        choose.clicked.connect(self.choose)
        self.install_btn = QPushButton("Instalar")
        self.install_btn.setObjectName("primary")
        self.install_btn.setEnabled(False)
        self.install_btn.clicked.connect(self.install)
        self.rollback_btn = QPushButton("Voltar à versão anterior")
        self.rollback_btn.clicked.connect(self.rollback)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 20)
        lay.setSpacing(12)
        lay.addWidget(text(f"Versão instalada: {updater.current_version()}", bold=True, size=15))
        lay.addWidget(text("Baixe o cs2coach.zip que o Claude enviar e escolha o arquivo aqui. "
                           "O app verifica o pacote, guarda uma cópia da versão atual e só então instala.", MUTED, 12))
        lay.addWidget(choose, alignment=Qt.AlignLeft)
        lay.addWidget(self.details)
        lay.addWidget(self.status)
        row = QHBoxLayout()
        row.addWidget(self.rollback_btn)
        row.addStretch()
        row.addWidget(self.install_btn)
        lay.addLayout(row)
        self.frozen = getattr(sys, "frozen", False)
        if self.frozen:
            choose.setEnabled(False)
            self.rollback_btn.setEnabled(False)
            self.status.setText(f"Você está usando o .exe. Para atualizar, baixe a versão nova em "
                                f"<a href='{updater.RELEASES}' style='color:{ACCENT}'>Releases do GitHub</a>, extraia e "
                                "substitua a pasta antiga. Seu histórico e perfil ficam salvos.")
            self.status.setTextFormat(Qt.RichText)
            self.status.setOpenExternalLinks(True)
        backups = updater.backups()
        self.rollback_btn.setVisible(bool(backups))
        if backups:
            self.rollback_btn.setToolTip(f"Restaura a versão {backups[0].name.split('_')[0]}")

    def choose(self):
        path, _ = QFileDialog.getOpenFileName(self, "Pacote de atualização", "", "Pacote do CS2 Analytics (*.zip)")
        if not path:
            return
        try:
            info = updater.inspect(path)
        except updater.UpdateError as e:
            self.details.setText("")
            self.status.setStyleSheet(f"color:{BAD}")
            self.status.setText(f"Pacote recusado: {e}")
            self.install_btn.setEnabled(False)
            return
        self.zip_path, self.info = path, info
        lines = [f"Versão {info['version']}  (atual {info['current']})", ""]
        lines += [info["changes"] or "Sem descrição de mudanças.", ""]
        lines.append(f"{info['files']} arquivos verificados.")
        lines.append(f"Código de verificação: {info['sha256'][:16]}")
        if info["requirements_changed"]:
            lines.append("Inclui bibliotecas novas: elas serão instaladas automaticamente (precisa de internet).")
        self.details.setText("\n".join(lines))
        self.status.setStyleSheet(f"color:{ACCENT if not info['newer'] else GOOD}")
        self.status.setText("Pacote válido." if info["newer"] else "Atenção: esta versão não é mais nova que a instalada.")
        self.install_btn.setEnabled(True)
        self.adjustSize()

    def run_job(self, job, busy):
        self.install_btn.setEnabled(False)
        self.rollback_btn.setEnabled(False)
        self.status.setStyleSheet(f"color:{MUTED}")
        self.status.setText(busy)
        self.worker = Worker(job)
        self.worker.done.connect(self.finished_job)
        self.worker.start()

    def install(self):
        if not self.info["newer"] and QMessageBox.question(self, "Atualização", "Instalar mesmo assim?") != QMessageBox.Yes:
            return
        needs_pip = self.info["requirements_changed"]

        def job():
            updater.install(self.zip_path)
            if needs_pip:
                ok, log = updater.install_requirements()
                if not ok:
                    raise updater.UpdateError("a versão foi instalada, mas as bibliotecas falharam:\n" + log[-600:])
            return f"Versão {updater.current_version()} instalada."
        self.run_job(job, "Instalando…")

    def rollback(self):
        if QMessageBox.question(self, "Voltar versão", "Restaurar a versão anterior do app?") != QMessageBox.Yes:
            return
        self.run_job(lambda: f"Versão {updater.rollback()} restaurada.", "Restaurando…")

    def finished_job(self, ok, message):
        self.status.setStyleSheet(f"color:{GOOD if ok else BAD}")
        self.status.setText(message)
        if not ok:
            self.rollback_btn.setEnabled(True)
            return
        if QMessageBox.question(self, "Pronto", message + "\n\nReiniciar o app agora?") == QMessageBox.Yes:
            QProcess.startDetached(sys.executable, [str(updater.APP_ROOT / "main.py")])
            QApplication.quit()
        self.accept()


class ThemeDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Tema")
        grid = QGridLayout()
        grid.setSpacing(12)
        for i, (key, (name, bg, panel, line, fg, muted, accent)) in enumerate(THEMES.items()):
            btn = QToolButton()
            btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            btn.setIcon(QIcon(swatch(bg, panel, line, fg, muted, accent)))
            btn.setIconSize(QSize(150, 90))
            btn.setFixedSize(176, 136)
            btn.setText(name + ("  ✓" if key == THEME else ""))
            btn.setCheckable(True)
            btn.setChecked(key == THEME)
            btn.clicked.connect(lambda _, k=key: self.pick(k))
            grid.addWidget(btn, i // 4, i % 4)
        close = QPushButton("Fechar")
        close.clicked.connect(self.reject)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.addWidget(text("Escolha um tema. O app reinicia para aplicar as cores em todas as telas.", MUTED, 12))
        lay.addLayout(grid)
        lay.addWidget(close, alignment=Qt.AlignRight)

    def pick(self, key):
        if key == THEME:
            return self.accept()
        save_config(theme=key)
        if QMessageBox.question(self, "Tema", f"Tema \"{THEMES[key][0]}\" salvo.\n\nReiniciar o app agora para aplicar?") \
                == QMessageBox.Yes:
            QProcess.startDetached(sys.executable, [str(updater.APP_ROOT / "main.py")])
            QApplication.quit()
        self.accept()


def swatch(bg, panel, line, fg, muted, accent):
    from PySide6.QtCore import QRectF
    from PySide6.QtGui import QPainter, QPixmap
    pm = QPixmap(150, 90)
    pm.fill(QColor(bg))
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(panel))
    p.drawRect(QRectF(0, 0, 38, 90))
    for i in range(4):
        p.setBrush(QColor(accent if i == 1 else muted))
        p.drawRoundedRect(QRectF(7, 12 + i * 16, 24, 6), 3, 3)
    p.setPen(QColor(line))
    p.setBrush(QColor(panel))
    p.drawRoundedRect(QRectF(46, 10, 96, 34), 6, 6)
    p.drawRoundedRect(QRectF(46, 50, 96, 30), 6, 6)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(fg))
    p.drawRoundedRect(QRectF(54, 18, 48, 6), 3, 3)
    p.setBrush(QColor(muted))
    p.drawRoundedRect(QRectF(54, 30, 70, 5), 2.5, 2.5)
    p.setBrush(QColor(accent))
    p.drawRoundedRect(QRectF(54, 58, 40, 14), 7, 7)
    p.end()
    return pm
