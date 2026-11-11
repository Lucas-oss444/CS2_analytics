from datetime import date, datetime, timedelta

import pytest
from PySide6.QtWidgets import QApplication

from cs2coach import coach, progress as prog
from cs2coach.card import H, W, match_card
from cs2coach.stats import combine, match_stats
from tests.fake_match import fake_match


def row(t, m, **js):
    return (float(t), m, "x.dem", {"rounds": 24, **js})


def test_by_map_groups_wins_and_averages():
    rows = [row(1, "de_mirage", rating=1.2, adr=90, won=1), row(2, "de_mirage", rating=0.8, adr=70, won=0),
            row(3, "de_inferno", rating=1.0, adr=80), row(4, "de_mirage", rating=1.0, adr=80, won=0.5)]
    maps = prog.by_map(rows)
    assert [m["map"] for m in maps] == ["de_mirage", "de_inferno"]
    mirage, inferno = maps
    assert mirage["n"] == 3 and mirage["wins"] == 1 and mirage["losses"] == 1
    assert abs(mirage["rating"] - 1.0) < 1e-9 and abs(mirage["winrate"] - 0.5) < 1e-9
    assert inferno["winrate"] is None and mirage["name"] == coach.MAP_NAMES["de_mirage"]
    assert prog.by_map([]) == []


def test_before_after_respects_metric_direction():
    rows = [row(1, "m", rating=0.8, early_death_pct=0.4), row(2, "m", rating=1.0, early_death_pct=0.3),
            row(10, "m", rating=1.2, early_death_pct=0.2)]
    res = prog.before_after(rows, 5, ["rating", "early_death_pct", "adr"])
    assert res["n_before"] == 2 and res["n_after"] == 1
    m = {x["key"]: x for x in res["metrics"]}
    assert m["rating"]["improved"] and abs(m["rating"]["delta"] - 0.3) < 1e-9
    assert m["early_death_pct"]["improved"]
    assert m["adr"]["improved"] is None and m["adr"]["pct"] is None
    empty = prog.before_after(rows, 100)
    assert empty["n_after"] == 0 and all(x["delta"] is None for x in empty["metrics"])


def test_goals_are_built_and_checked_in_the_right_direction():
    p = {k: 0.0 for k in coach.METRICS} | {"rounds": 100, "rating": 0.7, "early_death_pct": 0.6}
    issues, _ = coach.diagnose(p, p)
    goals = prog.make_goals(issues)
    assert 1 <= len(goals) <= 3
    for g in goals:
        assert g["metric"] in coach.METRICS and g["target"] != g["start"]
    low = {"metric": "early_death_pct", "target": 0.3, "start": 0.6}
    assert prog.goal_status(low, [row(10, "m", early_death_pct=0.25)], 5)[1]
    assert not prog.goal_status(low, [row(10, "m", early_death_pct=0.5)], 5)[1]
    assert prog.goal_status(low, [row(1, "m", early_death_pct=0.1)], 5) == (None, False, 0)
    assert prog.goal_status({"metric": "nao_existe"}, [], 0) == (None, False, 0)


def test_week_helpers():
    monday = date(2026, 11, 9)
    assert prog.week_id(monday) == prog.week_id(monday + timedelta(days=6)) != prog.week_id(monday + timedelta(days=7))
    assert datetime.fromtimestamp(prog.week_start(monday + timedelta(days=3))).date() == monday


def test_checklist_streaks_and_cleaning():
    today = date(2026, 11, 10)
    day = lambda n: (today - timedelta(days=n)).isoformat()
    data = {day(0): ["warmup"], day(1): ["duels"], day(2): ["warmup"], day(4): ["x"], "lixo": ["a"], day(200): ["a"],
            day(3): "nao-e-lista"}
    clean = prog.clean_checklist(data, today=today)
    assert "lixo" not in clean and day(200) not in clean and day(3) not in clean
    assert prog.streak(clean, today) == 3 and prog.best_streak(clean) == 3
    assert prog.streak({day(1): ["a"]}, today) == 1
    assert prog.streak({}, today) == 0 and prog.best_streak({}) == 0
    assert prog.clean_checklist(None) == {} and prog.clean_checklist([1, 2]) == {}


def test_achievements_progress():
    rows = [row(i, f"map{i % 6}", k5=1 if i < 2 else 0, k4=1, c1vx=1, rating=1.2, adr=105, hs_pct=0.55) for i in range(12)]
    got = {a.key: a for a in prog.achievements(rows, {}, goals_done=5)}
    assert got["first"].done and got["ace"].done and got["quads_10"].done and got["clutch_10"].done
    assert got["hot_3"].done and got["adr_100"].done and got["hs_5"].done and got["maps_5"].done and got["goals_5"].done
    assert not got["aces_5"].done and not got["matches_25"].done and not got["streak_7"].done
    assert all(not a.done for a in prog.achievements([], {}))
    odd = prog.achievements([(0, "m", "s", {"k5": "x", "rating": None})], {})
    assert odd[0].done


def test_compare_players_picks_winner_by_direction():
    m = fake_match(21)
    s = combine([match_stats(m)])
    a, b = list(s.counters)[:2]
    rows, (wa, wb) = prog.compare_players(s, a, b)
    assert wa + wb <= len(rows) == len(prog.FRIEND)
    for r in rows:
        if r["winner"]:
            better = r["a"] > r["b"] if coach.METRICS[r["key"]][2] else r["a"] < r["b"]
            assert (r["winner"] == "a") == better
    same, (x, y) = prog.compare_players(s, a, a)
    assert x == y == 0


@pytest.mark.parametrize("profile", [{}, {"name": "Lucas", "border": "legend", "avatar": "fox"},
                                     {"name": "<b>x</b>" * 30, "border": "nao_existe"}])
def test_match_card_renders_and_saves(tmp_path, profile):
    app = QApplication.instance() or QApplication([])
    m = fake_match(22)
    s = combine([match_stats(m)])
    sid = list(s.counters)[0]
    img = match_card(m, sid, s.player(sid), profile, s.names[sid])
    assert (img.width(), img.height()) == (W, H)
    out = tmp_path / "card.png"
    assert img.save(str(out), "PNG") and out.stat().st_size > 10_000
    app.processEvents()


def test_delta_cell_colors_by_direction():
    from cs2coach.ui import Main
    from cs2coach.theme import BAD, GOOD
    up = {"key": "early_death_pct", "delta": -0.1, "improved": True}
    assert GOOD in Main.delta_cell(up) and "▼ −10%" in Main.delta_cell(up)
    assert BAD in Main.delta_cell({"key": "rating", "delta": -0.2, "improved": False})
    assert Main.delta_cell({"key": "rating", "delta": None, "improved": None}) == "—"
    assert "igual" in Main.delta_cell({"key": "rating", "delta": 0.0, "improved": None})
