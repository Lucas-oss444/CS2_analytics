import bz2
import gzip
import os
import re
import tempfile
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

TICKRATE = 64
T, CT = 2, 3
GRENADES = {"hegrenade", "flashbang", "smokegrenade", "molotov", "incgrenade", "decoy"}
FIRE = {"inferno", "molotov", "incgrenade"}
NON_GUNS = GRENADES | FIRE | {"knife", "knife_t", "bayonet", "taser", "c4", "world", ""}
MAX_BYTES = 2 * 1024 ** 3
MAGIC = b"PBDEMS2\0"
HITGROUPS = {0: "generic", 1: "head", 2: "chest", 3: "stomach", 4: "left_arm",
             5: "right_arm", 6: "left_leg", 7: "right_leg", 8: "neck", 10: "gear"}


@dataclass
class Match:
    source: str
    map_name: str
    played_at: float
    rounds: pd.DataFrame
    roster: pd.DataFrame
    kills: pd.DataFrame
    hurts: pd.DataFrame
    shots: pd.DataFrame
    blinds: pd.DataFrame
    positions: pd.DataFrame = field(default=None, repr=False)

    @property
    def score(self):
        ct = int((self.rounds.winner == CT).sum())
        return ct, len(self.rounds) - ct


class DemoError(Exception):
    pass


def _check_header(path):
    with open(path, "rb") as f:
        _check_magic(f.read(8))


def _check_magic(head):
    if head.startswith(b"HL2DEMO"):
        raise DemoError("é uma demo do CS:GO antigo, não do CS2.")
    if head != MAGIC:
        raise DemoError("não é uma demo do CS2 válida.")


def _decompress(path, limit=MAX_BYTES):
    if os.path.getsize(path) > limit:
        raise DemoError("arquivo grande demais (limite de 2 GB).")
    lower = path.lower()
    if not lower.endswith((".gz", ".bz2", ".zst")):
        return path, None
    raw = open(path, "rb")
    if lower.endswith(".gz"):
        src = gzip.GzipFile(fileobj=raw)
    elif lower.endswith(".bz2"):
        src = bz2.BZ2File(raw)
    else:
        import zstandard
        src = zstandard.ZstdDecompressor().stream_reader(raw)
    fd, tmp = tempfile.mkstemp(prefix="cs2coach_", suffix=".dem")
    try:
        with raw, src, os.fdopen(fd, "wb") as out:
            total = 0
            while chunk := src.read(1 << 20):
                if not total:
                    _check_magic(chunk[:8])
                total += len(chunk)
                if total > limit:
                    raise DemoError("arquivo descompactado grande demais (limite de 2 GB).")
                out.write(chunk)
    except BaseException as e:
        os.remove(tmp)
        if isinstance(e, (DemoError, KeyboardInterrupt, SystemExit)):
            raise
        raise DemoError(f"não foi possível descompactar ({e}).") from e
    return tmp, tmp


def _clean_text(s, limit=64):
    return s.fillna("").astype(str).map(lambda v: re.sub(r"[\x00-\x1f\x7f]", "", v)[:limit])


def _sid(s):
    def conv(v):
        if v is None or (isinstance(v, float) and np.isnan(v)):
            return ""
        if isinstance(v, str):
            return "" if v in ("0", "nan", "None") else v
        return "" if int(v) == 0 else str(int(v))
    return s.map(conv).map(lambda v: v if v.isdigit() else "")


def _weapon(s):
    w = s.fillna("").astype(str).str.replace("weapon_", "", regex=False).str.lower()
    return w.str.replace(r"[^a-z0-9_]", "", regex=True).str[:32]


def _col(df, name, default=np.nan):
    return df[name] if name in df.columns else pd.Series(default, index=df.index)


def _team(v):
    if isinstance(v, str):
        return {"CT": CT, "T": T, "TERRORIST": T, "3": CT, "2": T}.get(v.upper(), 0)
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


def _hitgroup(v):
    if isinstance(v, str):
        return v.lower().replace(" ", "_")
    try:
        return HITGROUPS.get(int(v), "generic")
    except (TypeError, ValueError):
        return "generic"


class _Reader:
    def __init__(self, parser, events):
        self.p = parser
        self.events = set(events)

    def event(self, name, player=None, other=None):
        if name not in self.events:
            return pd.DataFrame()
        df = self.p.parse_event(name, player=player or [], other=other or [])
        df = pd.DataFrame(df) if not isinstance(df, pd.DataFrame) else df
        if "is_warmup_period" in df.columns:
            df = df[~df["is_warmup_period"].fillna(False).astype(bool)]
        return df.reset_index(drop=True)


def _ends_from_events(r):
    re = r.event("round_end", other=["is_warmup_period"])
    if re.empty:
        return []
    re = re.assign(winner=_col(re, "winner").map(_team)).sort_values("tick")
    re = re[re.winner.isin([T, CT])]
    return list(zip(re.tick.astype(int), re.winner.astype(int)))


def winners_from_scores(scores):
    out, prev = [], (0, 0)
    for t, ct in scores:
        direct, swapped = (t - prev[0], ct - prev[1]), (t - prev[1], ct - prev[0])
        if sorted(direct) == [0, 1]:
            out.append(T if direct[0] == 1 else CT)
        elif sorted(swapped) == [0, 1]:
            out.append(CT if swapped[0] == 1 else T)
        else:
            out.append(None)
        prev = (t, ct)
    return out


def _ends_from_scores(parser, r):
    ends = sorted(set(r.event("round_officially_ended", other=["is_warmup_period"]).get("tick", pd.Series(dtype=int))))
    final = r.event("cs_win_panel_match")
    if not final.empty:
        ends.append(int(final.tick.min()))
    ends = sorted(set(int(t) for t in ends))
    if not ends:
        return []
    df = parser.parse_ticks(["team_rounds_total", "team_num"], ticks=ends)
    df = df.assign(team=_col(df, "team_num", 0).map(_team))
    df = df[df.team.isin([T, CT])]
    table = df.groupby(["tick", "team"]).team_rounds_total.max().unstack().reindex(columns=[T, CT])
    table = table.reindex(ends).ffill().fillna(0).astype(int)
    winners = winners_from_scores(list(zip(table[T], table[CT])))
    return [(t, w) for t, w in zip(ends, winners) if w is not None]


def _build_rounds(parser, r):
    ends = _ends_from_events(r) or _ends_from_scores(parser, r)
    if not ends:
        raise DemoError("a demo não tem nenhum round completo.")
    fe = r.event("round_freeze_end", other=["is_warmup_period"])
    starts = np.sort(fe.tick.to_numpy()) if not fe.empty else np.array([])
    rows, prev_end = [], -1
    for end, winner in ends:
        cand = starts[(starts > prev_end) & (starts < end)]
        start = int(cand[-1]) if len(cand) else prev_end + 1
        rows.append((start, int(end), int(winner)))
        prev_end = end
    rounds = pd.DataFrame(rows, columns=["start_tick", "end_tick", "winner"])
    rounds.insert(0, "round", np.arange(1, len(rounds) + 1))
    return rounds


def assign_round(ticks, rounds):
    idx = np.searchsorted(rounds.start_tick.to_numpy(), ticks.to_numpy(), side="right") - 1
    return pd.Series(np.where(idx >= 0, idx + 1, 0), index=ticks.index)


POS_STEP = 8


SITES = {"BombsiteA": "A", "BombsiteB": "B"}


def parse_positions(parser, rounds):
    ticks = sorted({t for s, e in zip(rounds.start_tick, rounds.end_tick) for t in range(int(s), int(e) + 1, POS_STEP)})
    if not ticks:
        return pd.DataFrame(columns=["tick", "sid", "x", "y", "z", "yaw", "alive", "hp", "site"])
    df = parser.parse_ticks(["X", "Y", "Z", "yaw", "is_alive", "health", "last_place_name"], ticks=ticks)
    out = pd.DataFrame({
        "tick": df["tick"].astype("int32"),
        "sid": _sid(df["steamid"]),
        "x": pd.to_numeric(_col(df, "X", 0), errors="coerce").astype("float32"),
        "y": pd.to_numeric(_col(df, "Y", 0), errors="coerce").astype("float32"),
        "z": pd.to_numeric(_col(df, "Z", 0), errors="coerce").astype("float32"),
        "yaw": pd.to_numeric(_col(df, "yaw", 0), errors="coerce").astype("float32"),
        "alive": _col(df, "is_alive", False).fillna(False).astype(bool),
        "hp": pd.to_numeric(_col(df, "health", 0), errors="coerce").fillna(0).astype("int16"),
        "site": _col(df, "last_place_name", "").map(SITES).fillna("").astype(str),
    })
    return out[(out.sid != "") & out.x.notna() & out.y.notna()].reset_index(drop=True)


def extract_positions(path, rounds):
    from demoparser2 import DemoParser

    real, tmp = _decompress(path)
    try:
        _check_header(real)
        return parse_positions(DemoParser(real), rounds)
    except (DemoError, KeyboardInterrupt, SystemExit):
        raise
    except BaseException as e:
        raise DemoError(f"não foi possível ler as posições ({str(e)[:200]}).") from e
    finally:
        if tmp:
            os.remove(tmp)


def load_demo(path):
    real, tmp = _decompress(path)
    try:
        _check_header(real)
        match = _parse(real, path)
    except (DemoError, KeyboardInterrupt, SystemExit):
        raise
    except BaseException as e:
        raise DemoError(f"demo corrompida ou incompleta ({str(e)[:200]}).") from e
    finally:
        if tmp:
            os.remove(tmp)
    return finalize(match)


def _parse(real, path):
    from demoparser2 import DemoParser

    parser = DemoParser(real)
    header = parser.parse_header()
    r = _Reader(parser, parser.list_game_events())
    rounds = _build_rounds(parser, r)
    positions = parse_positions(parser, rounds)

    ticks = parser.parse_ticks(["team_num"], ticks=rounds.start_tick.tolist())
    roster = pd.DataFrame({
        "tick": ticks["tick"],
        "sid": _sid(ticks["steamid"]),
        "name": _clean_text(_col(ticks, "name", "")),
        "team": _col(ticks, "team_num", 0).map(_team),
    })
    roster = roster[(roster.sid != "") & roster.team.isin([T, CT])]
    roster["round"] = roster.tick.map(dict(zip(rounds.start_tick, rounds["round"])))
    roster = roster.dropna(subset=["round"]).astype({"round": int})
    roster = roster.drop_duplicates(["round", "sid"])[["round", "sid", "name", "team"]]

    pl = ["team_num"]
    d = r.event("player_death", player=pl, other=["is_warmup_period"])
    kills = pd.DataFrame({
        "tick": _col(d, "tick", 0),
        "attacker": _sid(_col(d, "attacker_steamid")),
        "attacker_team": _col(d, "attacker_team_num", 0).map(_team),
        "victim": _sid(_col(d, "user_steamid")),
        "victim_team": _col(d, "user_team_num", 0).map(_team),
        "assister": _sid(_col(d, "assister_steamid")),
        "flash_assist": _col(d, "assistedflash", False).fillna(False).astype(bool),
        "headshot": _col(d, "headshot", False).fillna(False).astype(bool),
        "weapon": _weapon(_col(d, "weapon", "")),
        "thrusmoke": _col(d, "thrusmoke", False).fillna(False).astype(bool),
        "distance": pd.to_numeric(_col(d, "distance", 0), errors="coerce").fillna(0),
    })

    h = r.event("player_hurt", player=pl, other=["is_warmup_period"])
    hurts = pd.DataFrame({
        "tick": _col(h, "tick", 0),
        "attacker": _sid(_col(h, "attacker_steamid")),
        "attacker_team": _col(h, "attacker_team_num", 0).map(_team),
        "victim": _sid(_col(h, "user_steamid")),
        "victim_team": _col(h, "user_team_num", 0).map(_team),
        "dmg": pd.to_numeric(_col(h, "dmg_health", 0), errors="coerce").fillna(0),
        "weapon": _weapon(_col(h, "weapon", "")),
        "hitgroup": _col(h, "hitgroup", 0).map(_hitgroup),
    })

    f = r.event("weapon_fire", player=pl, other=["is_warmup_period"])
    shots = pd.DataFrame({
        "tick": _col(f, "tick", 0),
        "sid": _sid(_col(f, "user_steamid")),
        "weapon": _weapon(_col(f, "weapon", "")),
    })

    b = r.event("player_blind", player=pl, other=["is_warmup_period"])
    blinds = pd.DataFrame({
        "tick": _col(b, "tick", 0),
        "attacker": _sid(_col(b, "attacker_steamid")),
        "attacker_team": _col(b, "attacker_team_num", 0).map(_team),
        "victim": _sid(_col(b, "user_steamid")),
        "victim_team": _col(b, "user_team_num", 0).map(_team),
        "duration": pd.to_numeric(_col(b, "blind_duration", 0), errors="coerce").fillna(0),
    })
    return Match(
        source=os.path.basename(path)[:120],
        map_name=re.sub(r"[^A-Za-z0-9_]", "", str(header.get("map_name", "")))[:40] or "desconhecido",
        played_at=os.path.getmtime(path),
        rounds=rounds, roster=roster, kills=kills, hurts=hurts, shots=shots, blinds=blinds, positions=positions,
    )


def finalize(m):
    for name in ("kills", "hurts", "shots", "blinds"):
        df = getattr(m, name)
        df = df.assign(round=assign_round(df.tick, m.rounds)) if not df.empty else df.assign(round=pd.Series(dtype=int))
        df = df[df["round"] > 0]
        end = df["round"].map(dict(zip(m.rounds["round"], m.rounds.end_tick)))
        keep = df.tick <= end + 7 * TICKRATE
        if name == "kills":
            keep &= ~((df.tick > end) & ((df.attacker == "") | (df.attacker == df.victim)))
        setattr(m, name, df[keep].sort_values("tick").reset_index(drop=True))
    teams = {(r, s): t for r, s, t in zip(m.roster["round"], m.roster.sid, m.roster.team)}
    for df in (m.kills, m.hurts, m.blinds):
        for role in ("attacker", "victim"):
            col = f"{role}_team"
            missing = df[col] == 0
            if missing.any():
                df.loc[missing, col] = [teams.get(k, 0) for k in zip(df.loc[missing, "round"], df.loc[missing, role])]
    h = m.hurts
    if not h.empty:
        h["dmg"] = h.dmg.clip(upper=100)
        before = h.groupby(["round", "victim"]).dmg.cumsum() - h.dmg
        h["dmg"] = np.minimum(h.dmg, (100 - before).clip(lower=0))
    return m
