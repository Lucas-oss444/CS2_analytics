from collections import Counter, defaultdict
from dataclasses import dataclass, field

import pandas as pd

from .demo import CT, FIRE, NON_GUNS, T, TICKRATE

TRADE_WINDOW = 5 * TICKRATE
EARLY_WINDOW = 30 * TICKRATE
SIDE = {T: "t", CT: "ct"}
RIFLES = {"ak47", "m4a1", "m4a1_silencer", "m4a1_silencer_off", "famas", "galilar", "aug", "sg556"}
LIMBS = {"left_arm": "arms", "right_arm": "arms", "left_leg": "legs", "right_leg": "legs", "neck": "head"}

METRICS = {
    "rating": ("Rating 1.0", "{:.2f}", True),
    "adr": ("ADR", "{:.1f}", True),
    "kpr": ("Kills/round", "{:.2f}", True),
    "dpr": ("Mortes/round", "{:.2f}", False),
    "kd": ("K/D", "{:.2f}", True),
    "kast": ("KAST", "{:.0%}", True),
    "hs_pct": ("HS% (kills)", "{:.0%}", True),
    "accuracy": ("Precisão", "{:.1%}", True),
    "rifle_accuracy": ("Precisão de rifle", "{:.1%}", True),
    "head_hit_pct": ("Tiros na cabeça", "{:.1%}", True),
    "opening_success": ("Duelos de abertura vencidos", "{:.0%}", True),
    "opening_rate": ("Participação em aberturas", "{:.0%}", True),
    "trade_kill_pct": ("Kills de trade", "{:.0%}", True),
    "traded_death_pct": ("Mortes tradadas", "{:.0%}", True),
    "early_death_pct": ("Mortes nos 30s iniciais", "{:.0%}", False),
    "nodmg_death_pct": ("Mortes sem causar dano", "{:.0%}", False),
    "blind_death_pct": ("Mortes cego", "{:.0%}", False),
    "survival": ("Sobrevivência", "{:.0%}", True),
    "clutch_rate": ("Clutches vencidos", "{:.0%}", True),
    "multikill_rate": ("Rounds com 2+ kills", "{:.0%}", True),
    "util_dmg": ("Dano de utilitária/round", "{:.1f}", True),
    "flashes_pr": ("Flashes/round", "{:.2f}", True),
    "flash_eff": ("Inimigos cegos/flash", "{:.2f}", True),
    "avg_blind": ("Cegueira média (s)", "{:.2f}", True),
    "team_flash_pct": ("Flashes no time", "{:.0%}", False),
    "smokes_pr": ("Smokes/round", "{:.2f}", True),
    "adr_ct": ("ADR CT", "{:.1f}", True),
    "adr_t": ("ADR TR", "{:.1f}", True),
    "kast_ct": ("KAST CT", "{:.0%}", True),
    "kast_t": ("KAST TR", "{:.0%}", True),
}


@dataclass
class Stats:
    counters: dict
    names: dict
    weapons: pd.DataFrame
    per_round: pd.DataFrame
    matches: list = field(default_factory=list)

    def player(self, sid):
        return derive(self.counters[sid])

    def lobby(self):
        rows = [derive(c) for c in self.counters.values() if c.get("rounds", 0) >= 5]
        return pd.DataFrame(rows).mean(numeric_only=True).to_dict() if rows else {}


def _div(a, b):
    return a / b if b else 0.0


def derive(c):
    g = lambda k: c.get(k, 0)
    rounds = g("rounds")
    multi = g("k1") + 4 * g("k2") + 9 * g("k3") + 16 * g("k4") + 25 * g("k5")
    rating = (_div(g("kills"), rounds) / 0.679 + 0.7 * _div(rounds - g("deaths"), rounds) / 0.317
              + _div(multi, rounds) / 1.277) / 2.7 if rounds else 0
    return {
        "rounds": rounds,
        "kills": g("kills"), "deaths": g("deaths"), "assists": g("assists"),
        "rating": rating,
        "adr": _div(g("damage"), rounds),
        "kpr": _div(g("kills"), rounds),
        "dpr": _div(g("deaths"), rounds),
        "kd": _div(g("kills"), g("deaths")) if g("deaths") else float(g("kills")),
        "kast": _div(g("kast"), rounds),
        "hs_pct": _div(g("hs_kills"), g("kills")),
        "accuracy": _div(g("hits"), g("shots")),
        "rifle_accuracy": _div(g("rifle_hits"), g("rifle_shots")),
        "head_hit_pct": _div(g("hit_head"), g("hits")),
        "opening_success": _div(g("open_win"), g("open_win") + g("open_loss")),
        "opening_rate": _div(g("open_win") + g("open_loss"), rounds),
        "opening_attempts": g("open_win") + g("open_loss"),
        "trade_kill_pct": _div(g("trade_kills"), g("kills")),
        "traded_death_pct": _div(g("traded_deaths"), g("deaths")),
        "early_death_pct": _div(g("early_deaths"), g("deaths")),
        "nodmg_death_pct": _div(g("nodmg_deaths"), g("deaths")),
        "blind_death_pct": _div(g("blind_deaths"), g("deaths")),
        "survival": _div(rounds - g("deaths"), rounds),
        "clutch_rate": _div(g("clutch_won"), g("clutch_att")),
        "clutch_att": g("clutch_att"), "clutch_won": g("clutch_won"),
        "c1v1": f"{int(g('c1v1_won'))}/{int(g('c1v1_att'))}",
        "c1vx": f"{int(g('c1vx_won'))}/{int(g('c1vx_att'))}",
        "multikill_rate": _div(g("k2") + g("k3") + g("k4") + g("k5"), rounds),
        "k2": g("k2"), "k3": g("k3"), "k4": g("k4"), "k5": g("k5"),
        "util_dmg": _div(g("he_dmg") + g("fire_dmg"), rounds),
        "he_dmg": g("he_dmg"), "fire_dmg": g("fire_dmg"),
        "he_thrown": g("he_thrown"), "fire_thrown": g("fire_thrown"),
        "flash_thrown": g("flash_thrown"), "smoke_thrown": g("smoke_thrown"),
        "flashes_pr": _div(g("flash_thrown"), rounds),
        "smokes_pr": _div(g("smoke_thrown"), rounds),
        "flash_eff": _div(g("enemies_flashed"), g("flash_thrown")),
        "avg_blind": _div(g("enemy_blind_time"), g("enemies_flashed")),
        "team_flash_pct": _div(g("team_flashed"), g("team_flashed") + g("enemies_flashed")),
        "flash_assists": g("flash_assists"),
        "blinded_total": g("team_flashed") + g("enemies_flashed"),
        "shots": g("shots"), "hits": g("hits"), "rifle_shots": g("rifle_shots"),
        "hitgroups": {k: _div(g(f"hit_{k}"), g("hits")) for k in ("head", "chest", "stomach", "arms", "legs")},
        "rounds_ct": g("rounds_ct"), "rounds_t": g("rounds_t"),
        "adr_ct": _div(g("damage_ct"), g("rounds_ct")),
        "adr_t": _div(g("damage_t"), g("rounds_t")),
        "kast_ct": _div(g("kast_ct"), g("rounds_ct")),
        "kast_t": _div(g("kast_t"), g("rounds_t")),
        "kills_ct": g("kills_ct"), "kills_t": g("kills_t"),
        "deaths_ct": g("deaths_ct"), "deaths_t": g("deaths_t"),
        "open_ct": f"{int(g('open_win_ct'))}/{int(g('open_win_ct') + g('open_loss_ct'))}",
        "open_t": f"{int(g('open_win_t'))}/{int(g('open_win_t') + g('open_loss_t'))}",
        "rounds_won": g("rounds_won"),
    }


def match_stats(m):
    c = defaultdict(Counter)
    names = {}
    winners = dict(zip(m.rounds["round"], m.rounds.winner))
    starts = dict(zip(m.rounds["round"], m.rounds.start_tick))
    roster_by_round = {r: dict(zip(g.sid, g.team)) for r, g in m.roster.groupby("round")}
    for s, n in zip(m.roster.sid, m.roster.name):
        names[s] = n

    k = m.kills
    valid = (k.attacker != "") & (k.attacker != k.victim) & (k.attacker_team != k.victim_team)
    k = k.assign(valid=valid)
    h = m.hurts
    enemy_h = h[(h.attacker != "") & (h.attacker_team != h.victim_team) & (h.attacker != h.victim)]
    kills_by_round = dict(tuple(k.groupby("round")))
    hurts_by_round = dict(tuple(enemy_h.groupby("round")))
    blinds_by_victim = dict(tuple(m.blinds[m.blinds.duration > 0].groupby("victim")))
    rows = []

    for rnd, side in roster_by_round.items():
        winner = winners[rnd]
        rk = kills_by_round.get(rnd, k.iloc[0:0])
        rh = hurts_by_round.get(rnd, enemy_h.iloc[0:0])
        alive = {T: {s for s, t in side.items() if t == T}, CT: {s for s, t in side.items() if t == CT}}
        dead, traded, involved, clutched = set(), set(), set(), set()
        kill_count = Counter()
        history = []

        for s, t in side.items():
            cc = c[s]
            cc["rounds"] += 1
            cc[f"rounds_{SIDE[t]}"] += 1
            cc["rounds_won"] += winner == t

        vk = rk[rk.valid]
        if len(vk):
            first = vk.iloc[0]
            for sid, key in ((first.attacker, "open_win"), (first.victim, "open_loss")):
                if sid in side:
                    c[sid][key] += 1
                    c[sid][f"{key}_{SIDE[side[sid]]}"] += 1

        for row in rk.itertuples(index=False):
            v, a, t = row.victim, row.attacker, row.tick
            vt = side.get(v, row.victim_team)
            if v:
                cv = c[v]
                cv["deaths"] += 1
                if vt in SIDE:
                    cv[f"deaths_{SIDE[vt]}"] += 1
                dead.add(v)
                if t - starts[rnd] <= EARLY_WINDOW:
                    cv["early_deaths"] += 1
                dealt = rh[(rh.attacker == v) & (rh.tick <= t)].dmg.sum()
                if dealt == 0:
                    cv["nodmg_deaths"] += 1
                bl = blinds_by_victim.get(v)
                if bl is not None and ((bl.tick <= t) & (t <= bl.tick + bl.duration * TICKRATE)).any():
                    cv["blind_deaths"] += 1
            if row.valid:
                at = side.get(a, row.attacker_team)
                ca = c[a]
                ca["kills"] += 1
                ca["hs_kills"] += row.headshot
                if at in SIDE:
                    ca[f"kills_{SIDE[at]}"] += 1
                kill_count[a] += 1
                involved.add(a)
                for pt, pa, pv, pteam in reversed(history):
                    if t - pt > TRADE_WINDOW:
                        break
                    if pa == v and pteam == at and pv not in traded:
                        ca["trade_kills"] += 1
                        traded.add(pv)
                        c[pv]["traded_deaths"] += 1
                        break
                history.append((t, a, v, vt))
                if row.assister and row.assister != a:
                    c[row.assister]["assists"] += 1
                    c[row.assister]["flash_assists"] += row.flash_assist
                    involved.add(row.assister)
            elif a and a != v and row.attacker_team == row.victim_team:
                c[a]["teamkills"] += 1
            if vt in alive:
                alive[vt].discard(v)
            for team, other in ((T, CT), (CT, T)):
                if len(alive[team]) == 1 and alive[other] and team not in clutched:
                    clutched.add(team)
                    (sid,) = alive[team]
                    kind = "c1v1" if len(alive[other]) == 1 else "c1vx"
                    won = winner == team
                    c[sid]["clutch_att"] += 1
                    c[sid]["clutch_won"] += won
                    c[sid][f"{kind}_att"] += 1
                    c[sid][f"{kind}_won"] += won

        dmg = rh.groupby("attacker").dmg.sum()
        for s, t in side.items():
            cc = c[s]
            n = kill_count[s]
            if n:
                cc[f"k{min(n, 5)}"] += 1
            d = float(dmg.get(s, 0))
            cc["damage"] += d
            cc[f"damage_{SIDE[t]}"] += d
            if s in involved or s not in dead or s in traded:
                cc["kast"] += 1
                cc[f"kast_{SIDE[t]}"] += 1
            rows.append((rnd, s, SIDE[t], n, d, s in dead, winner == t))

    guns_h = enemy_h[~enemy_h.weapon.isin(NON_GUNS)]
    guns_s = m.shots[~m.shots.weapon.isin(NON_GUNS)]
    for s, n in guns_s.sid.value_counts().items():
        c[s]["shots"] += n
    for s, n in guns_s[guns_s.weapon.isin(RIFLES)].sid.value_counts().items():
        c[s]["rifle_shots"] += n
    for s, n in guns_h.attacker.value_counts().items():
        c[s]["hits"] += n
    for s, n in guns_h[guns_h.weapon.isin(RIFLES)].attacker.value_counts().items():
        c[s]["rifle_hits"] += n
    groups = guns_h.hitgroup.map(lambda g: LIMBS.get(g, g))
    for (s, g), n in guns_h.groupby([guns_h.attacker, groups]).size().items():
        c[s][f"hit_{g}"] += n

    nades = {"flashbang": "flash_thrown", "smokegrenade": "smoke_thrown", "hegrenade": "he_thrown",
             "molotov": "fire_thrown", "incgrenade": "fire_thrown"}
    for (s, w), n in m.shots[m.shots.weapon.isin(nades)].groupby(["sid", "weapon"]).size().items():
        c[s][nades[w]] += n
    for s, d in enemy_h[enemy_h.weapon == "hegrenade"].groupby("attacker").dmg.sum().items():
        c[s]["he_dmg"] += d
    for s, d in enemy_h[enemy_h.weapon.isin(FIRE)].groupby("attacker").dmg.sum().items():
        c[s]["fire_dmg"] += d

    b = m.blinds[(m.blinds.duration >= 0.5) & (m.blinds.attacker != "")]
    enemy_b = b[b.attacker_team != b.victim_team]
    team_b = b[(b.attacker_team == b.victim_team) & (b.attacker != b.victim)]
    for s, g in enemy_b.groupby("attacker"):
        c[s]["enemies_flashed"] += len(g)
        c[s]["enemy_blind_time"] += g.duration.sum()
    for s, g in team_b.groupby("attacker"):
        c[s]["team_flashed"] += len(g)

    vk = k[k.valid]
    weapons = pd.concat([
        vk.groupby(["attacker", "weapon"]).size().rename("kills"),
        vk[vk.headshot].groupby(["attacker", "weapon"]).size().rename("hs"),
        enemy_h.groupby(["attacker", "weapon"]).dmg.sum().rename("damage"),
        enemy_h.groupby(["attacker", "weapon"]).size().rename("hits"),
        m.shots.rename(columns={"sid": "attacker"}).groupby(["attacker", "weapon"]).size().rename("shots"),
    ], axis=1).fillna(0)
    weapons.index.names = ["sid", "weapon"]
    weapons = weapons.reset_index()
    weapons = weapons[~weapons.weapon.isin({"", "world", "c4"})]

    per_round = pd.DataFrame(rows, columns=["round", "sid", "side", "kills", "damage", "died", "won"])
    known = set(names)
    counters = {s: dict(v) for s, v in c.items() if s in known}
    return Stats(counters, names, weapons, per_round.assign(match=0), [m])


def combine(stats_list):
    if len(stats_list) == 1:
        return stats_list[0]
    counters, names = defaultdict(Counter), {}
    for s in stats_list:
        names.update(s.names)
        for sid, c in s.counters.items():
            counters[sid].update(c)
    weapons = pd.concat([s.weapons for s in stats_list]).groupby(["sid", "weapon"], as_index=False).sum()
    per_round = pd.concat([s.per_round.assign(match=i) for i, s in enumerate(stats_list)], ignore_index=True)
    return Stats({k: dict(v) for k, v in counters.items()}, names, weapons, per_round,
                 [m for s in stats_list for m in s.matches])


def relations(matches, me):
    votes = defaultdict(Counter)
    for m in matches:
        mine = dict(zip(m.roster[m.roster.sid == me]["round"], m.roster[m.roster.sid == me].team))
        if not mine:
            continue
        same = Counter()
        for r, sid, team in zip(m.roster["round"], m.roster.sid, m.roster.team):
            if sid != me and r in mine:
                same[sid] += 1 if team == mine[r] else -1
        for sid, score in same.items():
            votes[sid]["ally" if score > 0 else "enemy"] += 1
    out = {me: "me"}
    for sid, v in votes.items():
        out[sid] = "ally" if not v["enemy"] else "enemy" if not v["ally"] else "mixed"
    return out


def rivals(matches, me):
    killed_by, killed = Counter(), Counter()
    for m in matches:
        k = m.kills[(m.kills.attacker != "") & (m.kills.attacker != m.kills.victim)
                    & (m.kills.attacker_team != m.kills.victim_team)]
        killed_by.update(k[k.victim == me].attacker)
        killed.update(k[k.attacker == me].victim)
    return killed_by, killed


def team_scores(m):
    out = {}
    for sid, g in m.roster.groupby("sid"):
        teams = dict(zip(g["round"], g.team))
        mine = sum(teams.get(r) == w for r, w in zip(m.rounds["round"], m.rounds.winner))
        theirs = sum(r in teams and teams[r] != w for r, w in zip(m.rounds["round"], m.rounds.winner))
        out[sid] = [int(mine), int(theirs)]
    return out
