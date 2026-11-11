import json
import re
import math

import pandas as pd
import pytest
from PySide6.QtWidgets import QApplication

from cs2coach import coach, library, profile as prof, storage, theme
from cs2coach.replay import RoundTrack, highlights, sites
from cs2coach.stats import METRICS, combine, match_stats
from tests.fake_match import fake_match


def finite(d):
    return {k: v for k, v in d.items() if isinstance(v, float) and not math.isfinite(v)}


@pytest.mark.parametrize("rounds", [1, 2, 13, 30])
def test_stats_have_no_nan_or_inf(rounds):
    m = fake_match(9, rounds=rounds)
    s = combine([match_stats(m)])
    for sid in s.counters:
        assert not finite(s.player(sid)), sid


def test_stats_survive_a_match_without_kills():
    m = fake_match(10, rounds=3)
    m.kills, m.hurts, m.blinds, m.shots = (df.iloc[0:0] for df in (m.kills, m.hurts, m.blinds, m.shots))
    s = combine([match_stats(m)])
    for sid in s.counters:
        p = s.player(sid)
        assert not finite(p) and p["kills"] == 0


def test_every_metric_has_help_and_valid_format():
    for key, (name, fmt, *_) in METRICS.items():
        assert name and coach.HELP.get(key), key
        assert fmt.format(0.5) and fmt.format(0)


@pytest.mark.parametrize("level", [0.0, 1.0, 1e6])
def test_diagnose_and_plan_with_extreme_numbers(level):
    p = {k: level for k in METRICS} | {"rounds": 100}
    issues, strengths = coach.diagnose(p, p)
    for i in issues:
        assert i.text and i.context and i.compare is not None and i.goal is not None
        assert 0 <= i.severity <= 1
    minutes, days, why = coach.suggest_schedule(issues, 100)
    assert minutes in coach.MINUTES and 1 <= days <= 6 and why
    plan = coach.weekly_plan(issues, "de_mirage", minutes, days)
    md = coach.plan_markdown("Lucas", issues, strengths, plan)
    assert not re.search(r"\bNone\b|\bnan\b|\binf\b", md)


def test_drills_and_tips_reference_real_keys():
    for key in coach.DRILLS:
        assert coach.drill_text(key, "de_mirage").name
    for keys in [*coach.RULE_PRO.values(), *coach.DRILL_PRO.values()]:
        assert coach.pro_tip(keys) is not None
    active = [p for t, ps in coach.TEAMS.items() if not t.startswith("Lendas") for p in ps]
    legends = [p for t, ps in coach.TEAMS.items() if t.startswith("Lendas") for p in ps]
    assert len(set(active)) == len(active) and len(set(legends)) == len(legends)


def test_all_avatars_borders_and_effects_render():
    app = QApplication.instance() or QApplication([])
    for size in (24, 96, 180):
        for b in prof.BORDERS:
            for a, _ in prof.AVATARS:
                for e, *_ in prof.EFFECTS:
                    pm = prof.avatar(size, {"name": "Lucas", "border": b.key, "avatar": a, "effect": e}, 0.37)
                    assert pm.width() > 0
    app.processEvents()


@pytest.mark.parametrize("rows", [[], [(0, "m", "s", {})], [(0, "m", "s", {"rounds": "x", "k4": None})]])
def test_unlocks_tolerate_odd_history(rows):
    prof.unlocked(rows)
    prof.progress(rows)
    coach.consistency(rows)


def test_corrupt_config_falls_back_to_defaults(monkeypatch, tmp_path):
    cfg = tmp_path / "config.json"
    monkeypatch.setattr(storage, "CONFIG", cfg)
    for content in ("", "{", "[]", '"texto"', "null", json.dumps({"theme": 5, "minutes": "muito"})):
        cfg.write_text(content, encoding="utf-8")
        assert isinstance(storage.load_config(), dict)


def test_unknown_theme_falls_back(monkeypatch, tmp_path):
    home = tmp_path
    (home / ".cs2coach").mkdir()
    (home / ".cs2coach" / "config.json").write_text('{"theme": "nao_existe"}', encoding="utf-8")
    monkeypatch.setattr(theme.Path, "home", staticmethod(lambda: home))
    assert theme.chosen() == theme.DEFAULT


@pytest.mark.parametrize("damage", ["meta", "parquet", "clips"])
def test_damaged_library_entry_does_not_break_listing(tmp_path, monkeypatch, damage):
    monkeypatch.setattr(library, "LIB", tmp_path / "lib")
    good, _ = library.save(fake_match(11), "a.dem")
    bad, _ = library.save(fake_match(12), "b.dem")
    d = tmp_path / "lib" / bad
    if damage == "meta":
        (d / "meta.json").write_text("{quebrado", encoding="utf-8")
    elif damage == "parquet":
        next(d.glob("*.parquet")).write_bytes(b"lixo")
    else:
        (d / "clips.json").write_text('[{"name": 5}, "x", null]', encoding="utf-8")
    ids = [e["id"] for e in library.entries()]
    assert good in ids
    library.load(good)
    if damage == "clips":
        assert isinstance(library.clips(bad), list)
    elif damage == "parquet":
        with pytest.raises(library.LibraryError):
            library.load(bad)


def test_replay_helpers_on_edge_cases():
    m = fake_match(13, rounds=2)
    assert isinstance(highlights(m, None, limit=6), list)
    assert isinstance(highlights(m, "nao_existe", limit=6), list)
    empty = pd.DataFrame(columns=["tick", "sid", "x", "y", "z", "yaw", "alive", "hp", "site"])
    assert sites(empty) == {}
    r = m.rounds.iloc[0]
    track = RoundTrack(empty, int(r.start_tick), int(r.end_tick))
    assert track.at(int(r.start_tick)) is not None
