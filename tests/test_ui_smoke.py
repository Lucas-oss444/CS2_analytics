import os
import random
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest
from PySide6.QtWidgets import QApplication, QCheckBox, QFileDialog, QInputDialog, QMessageBox

from cs2coach import library, ui
from cs2coach.progress import achievements as prog_achievements
from cs2coach.dialogs import ProfileDialog, ThemeDialog, UpdateDialog
from cs2coach.stats import match_stats
from cs2coach.storage import History
from cs2coach.theme import THEMES
from tests.fake_match import fake_match

ROOT = Path(__file__).resolve().parents[1]


def fake_positions(m, step=64):
    rng = random.Random(3)
    rows = []
    for r in m.rounds.itertuples():
        for tick in range(int(r.start_tick), int(r.end_tick), step):
            for sid in m.roster[m.roster["round"] == r.round].sid:
                x, y = rng.uniform(-2000, 2000), rng.uniform(-2000, 2000)
                rows.append((tick, sid, x, y, 0.0, rng.uniform(-180, 180), True, 100, "A" if x > 1500 else ""))
    return pd.DataFrame(rows, columns=["tick", "sid", "x", "y", "z", "yaw", "alive", "hp", "site"])


@pytest.fixture
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def main(app, tmp_path, monkeypatch):
    monkeypatch.setattr(ui, "History", lambda: History(tmp_path / "h.db"))
    monkeypatch.setattr(library, "LIB", tmp_path / "lib")
    monkeypatch.setattr(ui, "save_config", lambda **k: None)
    monkeypatch.setattr(ui, "load_config", lambda: {})
    monkeypatch.setattr(QInputDialog, "getItem", staticmethod(lambda *a, **k: (a[3][0], True)))
    for name in ("information", "warning", "critical", "question"):
        monkeypatch.setattr(QMessageBox, name, staticmethod(lambda *a, **k: QMessageBox.No))
    w = ui.Main()
    yield w
    w.replay.pause()
    w.close()
    app.processEvents()


def load(w, *seeds):
    ms = [fake_match(s) for s in seeds]
    ids = [library.save(m, f"fake_{s}.dem")[0] for m, s in zip(ms, seeds)]
    w.loaded(ms, [match_stats(m) for m in ms], ids, "")
    return ms, ids


def test_every_section_renders_without_data(main, app):
    for i in range(len(main.SECTIONS)):
        main.nav.setCurrentRow(i)
        app.processEvents()


def test_every_section_renders_for_every_player(main, app):
    ms, _ = load(main, 1, 2)
    for sid in list(dict.fromkeys(ms[0].roster.sid))[:4]:
        main.show_player(sid)
        for i in range(len(main.SECTIONS)):
            main.nav.setCurrentRow(i)
            app.processEvents()


@pytest.mark.parametrize("minutes,days", [(20, 1), (45, 3), (90, 5), (180, 7)])
def test_training_plan_fits_any_schedule(main, minutes, days):
    load(main, 3)
    main.custom_schedule = True
    main.minutes.setCurrentIndex(main.minutes.findData(minutes))
    main.days.setCurrentIndex(main.days.findData(days))
    _, _, plan = main.training()
    assert len(plan) == 7 and sum(1 for _, items in plan if items) == days
    assert all(sum(d.minutes for d in items) <= minutes for _, items in plan)


def test_replay_and_clips_work_with_positions(main, app):
    ms, ids = load(main, 4)
    main.nav.setCurrentRow(main.SECTIONS.index("🎬  Replay"))
    main.replay.loaded(ids[0], ms[0], fake_positions(ms[0]), "")
    for r in ms[0].rounds["round"][:3]:
        main.replay.round_box.setCurrentIndex(main.replay.round_box.findData(int(r)))
        main.replay.view.repaint()
    assert main.replay.view.sites
    for mode in ("auto", "mine", "all"):
        main.clips_page.set_mode(mode)
        app.processEvents()


def test_replay_reports_missing_positions(main):
    ms, ids = load(main, 5)
    main.replay.loaded(ids[0], None, None, "a demo original não está mais no PC")
    assert "demo original" in main.replay.status.text()


def test_dialogs_survive_strange_profiles(app, main):
    for data in ({}, {"border": "nao_existe", "avatar": "nao_existe", "font": "x", "fav_team": "Spirit",
                      "fav_player": "ninguem"}, {"name": "<b>x</b>" * 50, "neon": True, "neon_color": "#zzzzzz"}):
        dlg = ProfileDialog(main, data, set(), {})
        dlg.show()
        app.processEvents()
        dlg.close()
    for dlg in (ThemeDialog(main), UpdateDialog(main)):
        dlg.show()
        app.processEvents()
        dlg.close()


def test_profile_fixes_or_rejects_favorites(main):
    for saved, team, player in ((("Inventado", "x"), "", ""), (("Lendas", "coldzera"), "Lendas do Brasil", "coldzera"),
                                (("MOUZ", "donk"), "Spirit", "donk"), (("FURIA", "x"), "FURIA", ""), ((None, None), "", ""),
                                (("Lendas do Brasil", "FalleN"), "Lendas do Brasil", "FalleN"), (("FURIA", "FalleN"), "FURIA", "FalleN")):
        main.cfg = {"profile": {"fav_team": saved[0], "fav_player": saved[1]}}
        data = main.profile()
        assert (data["fav_team"], data["fav_player"]) == (team, player), saved


@pytest.mark.parametrize("theme", list(THEMES))
def test_app_opens_in_every_theme(tmp_path, theme):
    home = tmp_path / "home"
    (home / ".cs2coach").mkdir(parents=True)
    (home / ".cs2coach" / "config.json").write_text(f'{{"theme": "{theme}"}}', encoding="utf-8")
    code = ("from PySide6.QtWidgets import QApplication\n"
            "from cs2coach import ui, theme\n"
            f"assert theme.THEME == {theme!r}\n"
            "app = QApplication([]); ui.dark(app); w = ui.Main(); w.show(); app.processEvents()\n"
            "for i in range(len(w.SECTIONS)): w.nav.setCurrentRow(i); app.processEvents()\n")
    env = os.environ | {"HOME": str(home), "USERPROFILE": str(home), "QT_QPA_PLATFORM": "offscreen"}
    r = subprocess.run([sys.executable, "-c", code], cwd=ROOT, env=env, capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr[-2000:]


def test_evolution_maps_and_before_after(main, app):
    ms, _ = load(main, 1, 2, 3, 4)
    main.show_player(main.me)
    main.nav.setCurrentRow(main.SECTIONS.index("📈  Evolução"))
    assert main.ba_split.count() == 3
    for i in range(main.ba_split.count()):
        main.ba_split.setCurrentIndex(i)
        app.processEvents()
    assert main.maps_box.count() >= 1 and main.ba_box.count() >= 1


def test_goals_and_checklist(main, app):
    load(main, 5)
    main.show_player(main.me)
    goals = main.cfg.get("goals")
    assert goals and goals["sid"] == main.me and len(goals["items"]) <= 3
    boxes = [b for b in main.train.widget().findChildren(QCheckBox) if b.isEnabled()]
    if boxes:
        boxes[0].setChecked(True)
        assert main.checklist() and "Sequência: 1" in main.streak_label.text()
        boxes[0].setChecked(False)
        assert not main.checklist()
    main.cfg["goals"] = {"week": "lixo", "items": "x"}
    main.cfg["checklist"] = {"nao-e-data": 5}
    main.cfg["goals_done"] = "x"
    main.render_training()
    main.render_social()


def test_goals_hidden_for_other_players(main):
    ms, _ = load(main, 6)
    other = next(s for s in ms[0].roster.sid if s != main.me)
    main.show_player(other)
    assert main.cfg.get("goals", {}).get("sid") in (None, main.me)


def test_social_compare_card_and_achievements(main, app, tmp_path, monkeypatch):
    ms, _ = load(main, 7, 8)
    main.show_player(main.me)
    main.nav.setCurrentRow(main.SECTIONS.index("👥  Social"))
    assert main.friend_a.count() == main.friend_b.count() >= 10
    main.friend_b.setCurrentIndex(main.friend_b.findData(main.friend_a.currentData()))
    main.friend_b.setCurrentIndex(3)
    assert main.friend_box.count() == 2
    assert main.card_match.count() == 2
    main.make_card()
    assert main.card_image is not None and main.card_save.isEnabled()
    out = tmp_path / "cartao"
    monkeypatch.setattr(QFileDialog, "getSaveFileName", staticmethod(lambda *a, **k: (str(out), "")))
    main.save_card()
    assert (tmp_path / "cartao.png").stat().st_size > 10_000
    total = len(prog_achievements([], {}))
    main.render_social()
    assert main.ach_box.count() == total and f"de {total}" in main.ach_title.text()


def wheel(app, widget, notches=1, pixel=0):
    from PySide6.QtCore import QPoint, QPointF, Qt
    from PySide6.QtGui import QWheelEvent
    pos = QPointF(widget.width() / 2, min(widget.height() / 2, 10))
    for _ in range(notches):
        ev = QWheelEvent(pos, widget.mapToGlobal(pos.toPoint()).toPointF(), QPoint(0, -pixel),
                         QPoint(0, -120 if not pixel else 0), Qt.NoButton, Qt.NoModifier, Qt.NoScrollPhase, False)
        app.sendEvent(widget, ev)


def settle(app, ms=400):
    import time
    end = time.time() + ms / 1000
    while time.time() < end:
        app.processEvents()
        time.sleep(0.01)


@pytest.fixture
def smooth(app):
    f = ui.SmoothWheel()
    app.installEventFilter(f)
    yield f
    app.removeEventFilter(f)


def test_wheel_over_chart_and_combo_scrolls_the_page(main, app, smooth):
    load(main, 1, 2, 3)
    main.show_player(main.me)
    main.nav.setCurrentRow(main.SECTIONS.index("📈  Evolução"))
    main.resize(1200, 500)
    main.show()
    settle(app, 50)
    bar = main.evo.verticalScrollBar()
    assert bar.maximum() > 0
    bar.setValue(0)
    wheel(app, main.evo.chart)
    settle(app)
    assert bar.value() > 0
    bar.setValue(0)
    idx = main.evo_metric.currentIndex()
    wheel(app, main.evo_metric, 3)
    settle(app)
    assert main.evo_metric.currentIndex() == idx and bar.value() > 0


def test_fast_wheel_accumulates_and_stays_in_range(main, app, smooth):
    load(main, 4)
    main.show_player(main.me)
    main.nav.setCurrentRow(main.SECTIONS.index("🎯  Treino"))
    main.resize(1200, 500)
    main.show()
    settle(app, 50)
    bar = main.train.verticalScrollBar()
    bar.setValue(0)
    wheel(app, main.train.viewport(), 5)
    settle(app)
    assert bar.value() == min(bar.maximum(), 5 * ui.SmoothWheel.STEP)
    wheel(app, main.train.viewport(), 500)
    settle(app)
    assert bar.value() == bar.maximum()
    wheel(app, main.train.viewport(), pixel=-40)
    assert bar.value() == bar.maximum() - 40


def test_player_search_by_nick(main, app):
    ms, _ = load(main, 9)
    combo = main.viewing
    target = next(s for s in ms[0].roster.sid if s != main.me)
    nick = main.stats.names[target]
    combo.completer().activated.emit(combo.itemText(combo.findData(target)))
    assert main.sid == target and combo.currentText().startswith(nick)
    combo.lineEdit().setText("zzz-nao-existe")
    combo.lineEdit().editingFinished.emit()
    assert main.sid == target and combo.lineEdit().text().startswith(nick)
    other = next(s for s in ms[0].roster.sid if s not in (main.me, target))
    combo.lineEdit().setText(main.stats.names[other].lower())
    combo.lineEdit().editingFinished.emit()
    assert main.sid == other
    assert combo.count() == len(main.stats.counters)
    main.fill_viewing()
    assert combo.count() == len(main.stats.counters)


def test_profile_card_and_favorite_weapon(main, app, tmp_path, monkeypatch):
    load(main, 7, 8)
    main.show_player(main.me)
    for weapon in ("awp", "nao_existe", None, "knife"):
        main.cfg = {"profile": {"name": "<b>Lucas</b>" * 20, "fav_weapon": weapon, "fav_team": "FURIA", "fav_player": "yuurih"}}
        main.refresh_profile()
        assert main.profile_data["fav_weapon"] == (weapon if weapon in ("awp", "knife") else "")
        assert main.weapon_row.isHidden() == (main.profile_data["fav_weapon"] == "")
        main.make_profile_card()
        assert main.pcard_image.width() == 1200 and main.pcard_save.isEnabled()
    out = tmp_path / "perfil"
    monkeypatch.setattr(QFileDialog, "getSaveFileName", staticmethod(lambda *a, **k: (str(out), "")))
    main.pcard_save.click()
    assert (tmp_path / "perfil.png").stat().st_size > 10_000
    main.show_player(next(s for s in main.stats.counters if s != main.me))
    main.make_profile_card()
    assert main.pcard_image is not None


def test_profile_dialog_picks_weapon(app, main):
    dlg = ProfileDialog(main, {"fav_weapon": "ak47"}, set(), {})
    assert dlg.weapon_box.currentData() == "ak47" and not dlg.weapon_preview.pixmap().isNull()
    dlg.weapon_box.setCurrentIndex(dlg.weapon_box.findData("deagle"))
    assert dlg.data["fav_weapon"] == "deagle"
    dlg.weapon_box.setCurrentIndex(0)
    assert dlg.data["fav_weapon"] == ""
    assert dlg.weapon_box.count() == 1 + len(__import__("cs2coach.weapons").weapons.WEAPONS)
    dlg.close()
