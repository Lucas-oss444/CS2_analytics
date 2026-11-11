from dataclasses import dataclass
from datetime import date, datetime, timedelta

from .coach import MAP_NAMES, num
from .stats import METRICS

COMPARE = ["rating", "adr", "kast", "kd", "hs_pct", "opening_success", "trade_kill_pct", "traded_death_pct",
           "early_death_pct", "survival", "clutch_rate", "util_dmg", "flash_eff", "rifle_accuracy"]
FRIEND = ["rating", "kd", "adr", "kast", "hs_pct", "opening_success", "clutch_rate", "multikill_rate", "util_dmg",
          "flash_eff", "survival", "rifle_accuracy"]


def mean(values):
    values = list(values)
    return sum(values) / len(values) if values else None


def by_map(rows):
    groups = {}
    for _, m, _, js in rows:
        groups.setdefault(m, []).append(js)
    out = []
    for m, games in groups.items():
        results = [num(js, "won") for js in games if "won" in js]
        out.append({
            "map": m, "name": MAP_NAMES.get(m, m), "n": len(games),
            "wins": sum(r == 1 for r in results), "losses": sum(r == 0 for r in results),
            "winrate": mean(results) if results else None,
            **{k: mean(num(js, k) for js in games) for k in ("rating", "adr", "kast", "hs_pct", "kd")},
        })
    return sorted(out, key=lambda r: (-r["n"], -r["rating"]))


def better(key, delta):
    return delta > 0 if METRICS[key][2] else delta < 0


def before_after(rows, split, keys=COMPARE):
    before = [js for t, _, _, js in rows if t < split]
    after = [js for t, _, _, js in rows if t >= split]
    out = []
    for k in keys:
        a, b = mean(num(js, k) for js in before), mean(num(js, k) for js in after)
        delta = None if a is None or b is None else b - a
        pct = None if delta is None or not a else delta / abs(a)
        out.append({"key": k, "name": METRICS[k][0], "before": a, "after": b, "delta": delta, "pct": pct,
                    "improved": None if delta is None or abs(delta) < 1e-9 else better(k, delta)})
    return {"n_before": len(before), "n_after": len(after), "metrics": out}


def week_id(day=None):
    y, w, _ = (day or date.today()).isocalendar()
    return f"{y}-W{w:02d}"


def week_start(day=None):
    day = day or date.today()
    return datetime.combine(day - timedelta(days=day.weekday()), datetime.min.time()).timestamp()


def make_goals(issues, limit=3):
    goals = []
    for i in issues:
        if not i.rule.ok or i.rule.metric not in METRICS:
            continue
        target = i.value + (i.rule.ok - i.value) / 2
        goals.append({"metric": i.rule.metric, "title": i.rule.title, "start": float(i.value), "target": float(target)})
        if len(goals) == limit:
            break
    return goals


def goal_status(goal, rows, since):
    key = goal.get("metric")
    if key not in METRICS:
        return None, False, 0
    recent = [num(js, key) for t, _, _, js in rows if t >= since]
    current = mean(recent)
    target = num(goal, "target")
    done = current is not None and (current >= target if METRICS[key][2] else current <= target)
    return current, done, len(recent)


def clean_checklist(data, keep_days=90, today=None):
    today = today or date.today()
    out = {}
    if not isinstance(data, dict):
        return out
    for day, keys in data.items():
        try:
            d = date.fromisoformat(day)
        except (TypeError, ValueError):
            continue
        if isinstance(keys, list) and 0 <= (today - d).days <= keep_days:
            out[day] = [str(k) for k in keys if isinstance(k, str)][:20]
    return out


def streak(checklist, today=None):
    today = today or date.today()
    day = today if checklist.get(today.isoformat()) else today - timedelta(days=1)
    n = 0
    while checklist.get(day.isoformat()):
        n += 1
        day -= timedelta(days=1)
    return n


def best_streak(checklist):
    days = sorted(date.fromisoformat(d) for d, keys in checklist.items() if keys)
    best = run = 0
    for a, b in zip([None] + days, days):
        run = run + 1 if a and (b - a).days == 1 else 1
        best = max(best, run)
    return best


@dataclass
class Achievement:
    key: str
    icon: str
    title: str
    desc: str
    current: float
    total: float

    @property
    def done(self):
        return self.current >= self.total


def achievements(rows, checklist, goals_done=0):
    games = [js for *_, js in rows]
    s = lambda k: sum(num(js, k) for js in games)
    count = lambda cond: sum(1 for js in games if cond(js))
    hot = run = 0
    for js in games:
        run = run + 1 if num(js, "rating") >= 1.1 and num(js, "rounds") >= 10 else 0
        hot = max(hot, run)
    maps = len({m for _, m, _, _ in rows})
    days = best_streak(checklist)
    return [
        Achievement("first", "🎮", "Primeira análise", "Analise sua primeira partida", len(games), 1),
        Achievement("matches_25", "📚", "Estudioso", "Analise 25 partidas", len(games), 25),
        Achievement("matches_100", "🏛", "Centenário", "Analise 100 partidas", len(games), 100),
        Achievement("ace", "💀", "Primeiro ACE", "Mate os 5 inimigos num round", s("k5"), 1),
        Achievement("aces_5", "☠", "Colecionador de ACEs", "Faça 5 ACEs", s("k5"), 5),
        Achievement("quads_10", "🔥", "Quatro de uma vez", "Faça 10 rounds com 4 kills ou mais", s("k4") + s("k5"), 10),
        Achievement("clutch_10", "🧊", "Sangue frio", "Vença 10 clutches 1v2 ou maior", s("c1vx"), 10),
        Achievement("hot_3", "📈", "Fase boa", "Rating 1.10+ em 3 partidas seguidas", hot, 3),
        Achievement("adr_100", "💥", "Dano puro", "ADR 100+ numa partida", count(lambda js: num(js, "adr") >= 100), 1),
        Achievement("hs_5", "🎯", "Cabeça fria", "HS 50%+ em 5 partidas", count(lambda js: num(js, "hs_pct") >= 0.5), 5),
        Achievement("maps_5", "🗺", "Viajante", "Jogue 5 mapas diferentes", maps, 5),
        Achievement("streak_7", "📅", "Uma semana firme", "Treine 7 dias seguidos no checklist", days, 7),
        Achievement("streak_30", "🏅", "Disciplina de pro", "Treine 30 dias seguidos no checklist", days, 30),
        Achievement("goals_5", "🏁", "Batedor de metas", "Cumpra 5 metas semanais", goals_done, 5),
    ]


def compare_players(stats, a, b, keys=FRIEND):
    pa, pb = stats.player(a), stats.player(b)
    out = []
    for k in keys:
        va, vb = float(pa.get(k, 0)), float(pb.get(k, 0))
        winner = None if abs(va - vb) < 1e-9 else ("a" if better(k, va - vb) else "b")
        out.append({"key": k, "name": METRICS[k][0], "a": va, "b": vb, "winner": winner})
    wins = sum(r["winner"] == "a" for r in out), sum(r["winner"] == "b" for r in out)
    return out, wins


def career(rows):
    games = [js for *_, js in rows]
    results = [num(js, "won") for js in games if "won" in js]
    maps = [m for m in by_map(rows) if m["n"] >= 2] or by_map(rows)
    best = max(maps, key=lambda m: m["rating"] or 0, default=None)
    return {
        "matches": len(games), "rating": mean(num(js, "rating") for js in games),
        "adr": mean(num(js, "adr") for js in games), "hs_pct": mean(num(js, "hs_pct") for js in games),
        "winrate": mean(results), "kills": sum(num(js, "kills") for js in games),
        "aces": sum(num(js, "k5") for js in games), "best_map": best["name"] if best else None,
        "best_map_rating": best["rating"] if best else None,
    }


def weapon_line(weapons, sid, weapon):
    if weapons is None or not weapon or not len(weapons):
        return None
    w = weapons[(weapons.sid == sid) & (weapons.weapon == weapon)]
    if not len(w):
        return {"kills": 0, "hs_pct": 0.0, "accuracy": None}
    kills, hs = float(w.kills.sum()), float(w.hs.sum())
    shots, hits = float(w.shots.sum()), float(w.hits.sum())
    return {"kills": int(kills), "hs_pct": hs / kills if kills else 0.0, "accuracy": hits / shots if shots else None}


def top_weapon(weapons, sid):
    if weapons is None or not len(weapons):
        return None
    w = weapons[weapons.sid == sid].groupby("weapon").kills.sum()
    w = w[w > 0]
    return str(w.idxmax()) if len(w) else None
