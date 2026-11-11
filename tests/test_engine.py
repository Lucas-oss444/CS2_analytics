from cs2coach.coach import diagnose, plan_markdown, suggest_schedule, training_days, weekly_plan
from cs2coach.stats import combine, match_stats
from tests.fake_match import fake_match


def test_pipeline():
    matches = [fake_match(seed) for seed in (1, 2, 3)]
    stats = [match_stats(m) for m in matches]
    s = combine(stats)
    assert len(s.counters) == 10
    total_kills = sum(c.get("kills", 0) for c in stats[0].counters.values())
    assert total_kills == len(matches[0].kills)
    deaths = sum(c.get("deaths", 0) for c in stats[0].counters.values())
    assert deaths == len(matches[0].kills)
    for sid in s.counters:
        p = s.player(sid)
        assert 0 <= p["kast"] <= 1 and p["adr"] <= 200 and p["rounds"] == 72
        issues, strengths = diagnose(p, s.lobby())
        plan = weekly_plan(issues, "de_mirage", 60)
        assert all(sum(d.minutes for d in items) <= 60 for _, items in plan)
        assert "Plano de treino" in plan_markdown(s.names[sid], issues, strengths, plan)
    one = stats[0]
    opens = sum(c.get("open_win", 0) for c in one.counters.values())
    assert opens == len(matches[0].rounds)


def test_winners_from_scores_handles_halftime_swap():
    from cs2coach.demo import CT, T, winners_from_scores
    scores = [(1, 0), (2, 0), (2, 1), (7, 4), (5, 7), (6, 7), (6, 8)]
    assert winners_from_scores(scores) == [T, T, CT, None, CT, T, CT]


def test_relations_follow_sides_and_rivals():
    from cs2coach.stats import relations, rivals
    m = fake_match(8)
    me = m.roster.sid.iloc[0]
    rel = relations([m], me)
    first = m.roster[m.roster["round"] == 1]
    my_team = first[first.sid == me].team.iloc[0]
    for sid, team in zip(first.sid, first.team):
        if sid != me:
            assert rel[sid] == ("ally" if team == my_team else "enemy")
    assert list(rel.values()).count("ally") == 4 and list(rel.values()).count("enemy") == 5
    killed_by, killed = rivals([m], me)
    assert all(rel[s] == "enemy" for s in list(killed_by) + list(killed))


def test_sites_need_enough_samples():
    import pandas as pd
    from cs2coach.replay import sites
    df = pd.DataFrame({"x": [1.0] * 30 + [9.0] * 5, "y": [2.0] * 35, "alive": True, "site": ["A"] * 30 + ["B"] * 5})
    assert sites(df) == {"A": (1.0, 2.0)}
    assert sites(df.drop(columns="site")) == {}


def test_schedule_suggestion_and_rest_days():
    assert training_days(7) == set(range(7))
    assert len(training_days(5)) == 5 and len(training_days(3)) == 3
    assert suggest_schedule([], 100)[:2] == (30, 3)
    plan = weekly_plan([], "de_mirage", 45, 4)
    assert len(plan) == 7 and sum(1 for _, items in plan if items) == 4
    assert all(sum(d.minutes for d in items) <= 45 for _, items in plan)


def test_pro_tips_have_sources():
    from cs2coach.coach import DRILL_PRO, PRO_TIPS, RULE_PRO, RULES
    assert {r.metric for r in RULES} <= set(RULE_PRO)
    used = {k for keys in [*RULE_PRO.values(), *DRILL_PRO.values()] for k in keys}
    assert used <= set(PRO_TIPS)
    assert all(t.url.startswith("https://") and t.source for t in PRO_TIPS.values())


def test_favorite_player_tip_comes_first():
    from cs2coach.coach import RULE_PRO, TEAMS, pro_tip, set_favorite
    assert "donk" in TEAMS["Spirit"]
    set_favorite("NiKo")
    assert pro_tip(RULE_PRO["hs_pct"]).player == "NiKo"
    set_favorite("")
    assert pro_tip(RULE_PRO["hs_pct"]).player == "donk"


def test_glossary_matches_whole_terms():
    from cs2coach.coach import glossary_for
    names = [n for n, _ in glossary_for("Aquecimento em Deathmatch e pop flashes com HE")]
    assert names == ["Deathmatch (DM)", "Pop flash", "Utilitária"]
    assert glossary_for("ele ajuda o time") == []


def test_console_commands_are_single_line():
    from cs2coach.coach import COMMANDS, DRILL_CMD, DRILLS
    assert all("\n" not in cmd for _, cmd, _ in COMMANDS.values())
    assert COMMANDS["cfg"][1].startswith("sv_cheats 1; ")
    assert set(DRILL_CMD) <= set(DRILLS) and {k for v in DRILL_CMD.values() for k in v} <= set(COMMANDS)


def test_border_goals_and_progress():
    from cs2coach import profile as prof
    rows = [(0, "de_mirage", "x", {"rounds": 24, "k4": 1, "adr": 104, "c1vx": 1})] * 12
    got = prof.unlocked(rows)
    assert {"veteran", "quad", "carry", "clutch"} <= got and "marathon" not in got and "legend" not in got
    assert prof.progress(rows)["marathon"] == "12/25"
    assert all(b.key in prof.unlocked([], True) for b in prof.BORDERS)


def test_themes_are_valid():
    from cs2coach.theme import THEMES, light, mix
    assert mix("#000000", "#ffffff", 0.5) == "#808080"
    assert all(len(v) == 7 and all(c.startswith("#") and len(c) == 7 for c in v[1:]) for v in THEMES.values())
    assert light(THEMES["claro"][1]) and not light(THEMES["escuro"][1])


def test_consistency_tips_and_stats():
    from cs2coach.coach import CONSISTENCY, PRO_TIPS, consistency
    assert all(k in PRO_TIPS for *_, keys in CONSISTENCY for k in keys)
    rows = [(0, "m", "s", {"rounds": 20, "rating": r}) for r in (0.8, 1.0, 1.2)]
    c = consistency(rows)
    assert c["n"] == 3 and abs(c["mean"] - 1.0) < 1e-9 and c["min"] == 0.8
    assert consistency(rows[:2]) is None
