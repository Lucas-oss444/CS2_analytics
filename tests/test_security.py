import glob
import gzip
import os
import socket
import sqlite3
import tempfile

import pandas as pd
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from cs2coach.demo import DemoError, _clean_text, _decompress, _sid, _weapon, load_demo
from cs2coach.stats import match_stats
from cs2coach.storage import History
from tests.fake_match import fake_match


@pytest.fixture
def no_network(monkeypatch):
    def blocked(*a, **k):
        raise AssertionError("tentativa de acesso à rede")
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket, "getaddrinfo", blocked)


def leftovers():
    return glob.glob(os.path.join(tempfile.gettempdir(), "cs2coach_*"))


@pytest.mark.parametrize("content", [b"", b"PBDEMS2\0", b"HL2DEMO\0" + b"x" * 100, os.urandom(50000)])
def test_rejects_invalid_demos(tmp_path, content, no_network):
    f = tmp_path / "x.dem"
    f.write_bytes(content)
    with pytest.raises(DemoError):
        load_demo(str(f))


def test_rejects_corrupt_archives(tmp_path):
    f = tmp_path / "x.dem.gz"
    f.write_bytes(b"isto nao e gzip")
    with pytest.raises(DemoError):
        load_demo(str(f))
    assert not leftovers()


def test_decompression_bomb(tmp_path):
    f = tmp_path / "bomb.dem.gz"
    with gzip.open(f, "wb") as out:
        out.write(b"PBDEMS2\0" + b"\0" * (8 * 1024 * 1024))
    with pytest.raises(DemoError, match="grande demais"):
        _decompress(str(f), limit=1024 * 1024)
    zeros = tmp_path / "zeros.dem.gz"
    with gzip.open(zeros, "wb") as out:
        out.write(b"\0" * (8 * 1024 * 1024))
    with pytest.raises(DemoError, match="não é uma demo"):
        _decompress(str(zeros))
    assert not leftovers()


def test_sanitizes_demo_text():
    names = _clean_text(pd.Series(["ok\x00\x1b[31m", "a" * 500, None]))
    assert names.tolist() == ["ok[31m", "a" * 64, ""]
    assert _weapon(pd.Series(["weapon_ak47", "<script>x"])).tolist() == ["ak47", "scriptx"]
    assert _sid(pd.Series(["76561198000000001", "../../etc", 0])).tolist() == ["76561198000000001", "", ""]


def test_ui_escapes_player_names(tmp_path, monkeypatch, no_network):
    from PySide6.QtWidgets import QApplication, QInputDialog
    from cs2coach import ui

    monkeypatch.setattr(ui, "History", lambda: History(tmp_path / "h.db"))
    monkeypatch.setattr(ui.library, "LIB", tmp_path / "lib")
    monkeypatch.setattr(ui, "save_config", lambda **k: None)
    monkeypatch.setattr(ui, "load_config", lambda: {})
    monkeypatch.setattr(QInputDialog, "getItem", staticmethod(lambda *a: (a[3][0], True)))
    app = QApplication.instance() or QApplication([])
    m = fake_match(7)
    evil = '<img src="file:///C:/x.png"><a href="http://x">clique</a>'
    m.roster["name"] = m.roster["name"].where(m.roster.sid != m.roster.sid.iloc[0], evil)
    w = ui.Main()
    w.loaded([m], [match_stats(m)], [], "")
    w.show_player(m.roster.sid.iloc[0])
    assert "<img" not in w.name.text() and "&lt;img" in w.name.text()
    w.close()
    app.processEvents()


def test_corrupt_history_is_recovered(tmp_path):
    db = tmp_path / "h.db"
    db.write_bytes(b"lixo" * 1000)
    h = History(db)
    assert h.player("1") == []
    assert (tmp_path / "h.corrompido.db").exists()


def test_history_uses_parameters(tmp_path):
    h = History(tmp_path / "h.db")
    m = fake_match(3)
    s = match_stats(m)
    h.save(m, s)
    assert h.player("1' OR '1'='1") == []
    assert sqlite3.connect(tmp_path / "h.db").execute("SELECT count(*) FROM results").fetchone()[0] == 10


def test_admin_unlocks_all_borders_and_name_renders():
    from PySide6.QtWidgets import QApplication
    from cs2coach import profile as prof

    app = QApplication.instance() or QApplication([])
    assert prof.unlocked([]) < prof.unlocked([], True) == {b.key for b in prof.BORDERS}
    for style, _ in prof.NAME_STYLES:
        w = prof.NameLabel()
        w.resize(170, 36)
        w.set_profile({"name": "<b>Lucas</b>" * 3, "name_style": style, "font": "Fonte Inexistente"})
        assert not w.grab().isNull()
        assert w.timer.isActive() == (style == "rainbow")
    app.processEvents()


def test_workshop_links_are_fixed_steam_urls():
    from cs2coach.coach import COMMUNITY_MAPS, DRILLS
    for name, url, _ in COMMUNITY_MAPS.values():
        assert url.startswith(("https://steamcommunity.com/sharedfiles/filedetails/?id=",
                               "https://steamcommunity.com/workshop/browse/?appid=730&searchtext="))
    assert all(d.workshop in COMMUNITY_MAPS or not d.workshop for d in DRILLS.values())


def test_cs2_cfg_is_sanitized(tmp_path):
    from cs2coach.replay_ui import write_cs2_cfg
    csgo = tmp_path / "Steam" / "game" / "csgo"
    (csgo / "replays").mkdir(parents=True)
    demo = csgo / "replays" / "match730_1.dem"
    demo.write_bytes(b"x")
    rel = write_cs2_cfg(str(demo), 12345, 'evil"; quit; bind w "kill')
    assert rel == "replays/match730_1"
    lance = (csgo / "cfg" / "cs2analytics_lance.cfg").read_text(encoding="utf-8").splitlines()
    assert lance[0] == "demo_gototick 12345" and lance[1] == 'spec_player "evil quit bind w kill"'
    assert all(line.count('"') in (0, 2) for line in lance)
    main = (csgo / "cfg" / "cs2analytics.cfg").read_text(encoding="utf-8")
    assert main.startswith("playdemo replays/match730_1\n")
    outside = tmp_path / "x.dem"
    outside.write_bytes(b"x")
    import pytest
    from cs2coach import replay_ui
    replay_ui.CS2_DEFAULT = csgo
    with pytest.raises(ValueError):
        write_cs2_cfg(str(outside), 1, "a")
    bad = csgo / "replays" / "a b;quit.dem"
    bad.write_bytes(b"x")
    with pytest.raises(ValueError):
        write_cs2_cfg(str(bad), 1, "a")


def test_launch_cs2_paths(monkeypatch):
    from cs2coach import replay_ui
    calls = []
    monkeypatch.setattr(replay_ui, "cs2_running", lambda: True)
    assert replay_ui.launch_cs2() == "running"
    monkeypatch.setattr(replay_ui, "cs2_running", lambda: False)
    monkeypatch.setattr(replay_ui, "steam_exe", lambda: "C:/Steam/steam.exe")
    monkeypatch.setattr(replay_ui.subprocess, "Popen", lambda args, **k: calls.append(args))
    assert replay_ui.launch_cs2() == "launched"
    assert calls == [["C:/Steam/steam.exe", "-applaunch", "730", "+exec", "cs2analytics"]]


def test_record_cfg_hides_hud_and_starts_earlier(tmp_path):
    from cs2coach.demo import TICKRATE
    from cs2coach.replay_ui import write_cs2_cfg
    base = tmp_path / "game" / "csgo"
    (base / "replays").mkdir(parents=True)
    (base / "gameinfo.gi").write_text("x")
    demo = base / "replays" / "m.dem"
    demo.write_bytes(b"PBDEMS2\0")
    write_cs2_cfg(str(demo), 10 * TICKRATE, "me", record=True)
    lance = (base / "cfg" / "cs2analytics_lance.cfg").read_text()
    assert "cl_drawhud 0" in lance and f"demo_gototick {7 * TICKRATE}" in lance
    assert "cl_drawhud 1" in (base / "cfg" / "cs2analytics_normal.cfg").read_text()
    assert "demo_togglepause" in (base / "cfg" / "cs2analytics.cfg").read_text()
    write_cs2_cfg(str(demo), 10 * TICKRATE, "me")
    assert "cl_drawhud" not in (base / "cfg" / "cs2analytics_lance.cfg").read_text()
