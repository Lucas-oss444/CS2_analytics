from collections import defaultdict

import numpy as np

from .demo import CT, T, TICKRATE

LABELS = {5: "ACE", 4: "4 kills", 3: "3 kills"}


def _clip(kind, name, rnd, start, end, sid, score):
    return {"id": f"auto-{kind}-{rnd}-{sid}", "name": name, "round": int(rnd), "start": int(start),
            "end": int(end), "sid": sid, "auto": True, "score": score}


def highlights(m, sid=None, limit=12):
    out = []
    k = m.kills
    valid = k[(k.attacker != "") & (k.attacker != k.victim) & (k.attacker_team != k.victim_team)]
    bounds = {r: (s, e) for r, s, e in zip(m.rounds["round"], m.rounds.start_tick, m.rounds.end_tick)}
    winners = dict(zip(m.rounds["round"], m.rounds.winner))
    roster = {r: dict(zip(g.sid, g.team)) for r, g in m.roster.groupby("round")}
    for rnd, g in valid.groupby("round"):
        start, end = bounds[rnd]
        for who, kills in g.groupby("attacker"):
            if sid and who != sid:
                continue
            ticks = kills.tick.to_list()
            n = len(ticks)
            hs = int(kills.headshot.sum())
            if n >= 3:
                name = LABELS[min(n, 5)] + (f" ({hs} HS)" if hs else "")
                out.append(_clip(f"k{n}", name, rnd, max(start, ticks[0] - 4 * TICKRATE), ticks[-1] + 2 * TICKRATE,
                                 who, {3: 60, 4: 80}.get(n, 100) + hs))
            else:
                for a, b in zip(ticks, ticks[1:]):
                    if b - a <= 3 * TICKRATE:
                        out.append(_clip("fast", f"2 kills em {(b - a) / TICKRATE:.1f} s", rnd, max(start, a - 4 * TICKRATE),
                                         b + 2 * TICKRATE, who, 30 + hs))
                        break
    for rnd, side in roster.items():
        alive = {T: {s for s, t in side.items() if t == T}, CT: {s for s, t in side.items() if t == CT}}
        done = set()
        for row in k[k["round"] == rnd].itertuples(index=False):
            vt = side.get(row.victim, row.victim_team)
            if vt in alive:
                alive[vt].discard(row.victim)
            for team, other in ((T, CT), (CT, T)):
                if len(alive[team]) == 1 and len(alive[other]) >= 2 and team not in done:
                    done.add(team)
                    (who,) = alive[team]
                    if winners.get(rnd) == team and (not sid or who == sid):
                        n = len(alive[other])
                        start, end = bounds[rnd]
                        out.append(_clip("clutch", f"Clutch 1v{n}", rnd, max(start, row.tick - 2 * TICKRATE),
                                         end + 2 * TICKRATE, who, 40 + 15 * n))
    out.sort(key=lambda c: (-c["score"], c["round"]))
    return out[:limit]


class RoundTrack:
    def __init__(self, positions, start, end):
        p = positions[(positions.tick >= start) & (positions.tick <= end)]
        self.ticks = np.sort(p.tick.unique())
        self.players = {}
        for sid, g in p.groupby("sid"):
            g = g.set_index("tick").reindex(self.ticks)
            g["alive"] = g["alive"].fillna(False).astype(bool)
            g[["x", "y", "yaw"]] = g[["x", "y", "yaw"]].ffill().bfill()
            g["hp"] = g["hp"].fillna(0)
            self.players[sid] = {c: g[c].to_numpy() for c in ("x", "y", "yaw", "alive", "hp")}

    def at(self, tick):
        if not len(self.ticks):
            return {}
        i = int(np.clip(np.searchsorted(self.ticks, tick, side="right") - 1, 0, len(self.ticks) - 1))
        j = min(i + 1, len(self.ticks) - 1)
        span = self.ticks[j] - self.ticks[i]
        f = 0.0 if span == 0 else float(np.clip((tick - self.ticks[i]) / span, 0, 1))
        out = {}
        for sid, d in self.players.items():
            yaw_a, yaw_b = d["yaw"][i], d["yaw"][j]
            diff = (yaw_b - yaw_a + 180) % 360 - 180
            out[sid] = (d["x"][i] + (d["x"][j] - d["x"][i]) * f, d["y"][i] + (d["y"][j] - d["y"][i]) * f,
                        yaw_a + diff * f, bool(d["alive"][i]), int(d["hp"][i]))
        return out


def bounds(positions, margin=0.04):
    x, y = positions.x.to_numpy(), positions.y.to_numpy()
    lo_x, hi_x = np.nanpercentile(x, [0.5, 99.5])
    lo_y, hi_y = np.nanpercentile(y, [0.5, 99.5])
    size = max(hi_x - lo_x, hi_y - lo_y) * (1 + margin * 2)
    cx, cy = (lo_x + hi_x) / 2, (lo_y + hi_y) / 2
    return cx - size / 2, cy - size / 2, size


def density(positions, box, n=512):
    x0, y0, size = box
    alive = positions[positions.alive]
    gx = ((alive.x.to_numpy() - x0) / size * (n - 1)).astype(int)
    gy = ((1 - (alive.y.to_numpy() - y0) / size) * (n - 1)).astype(int)
    ok = (gx >= 0) & (gx < n) & (gy >= 0) & (gy < n)
    grid = np.zeros((n, n), dtype=np.float32)
    np.add.at(grid, (gy[ok], gx[ok]), 1)
    grid = np.log1p(grid)
    for _ in range(3):
        grid = (grid + np.roll(grid, 1, 0) + np.roll(grid, -1, 0) + np.roll(grid, 1, 1) + np.roll(grid, -1, 1)) / 5
    return grid / grid.max() if grid.max() > 0 else grid


def sites(positions):
    if "site" not in positions:
        return {}
    alive = positions[positions.alive & (positions.site != "")]
    return {k: (float(g.x.median()), float(g.y.median())) for k, g in alive.groupby("site") if len(g) >= 20}
