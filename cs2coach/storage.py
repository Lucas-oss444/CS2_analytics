import hashlib
import json
import sqlite3
from pathlib import Path

from .stats import METRICS, derive, team_scores

HOME = Path.home() / ".cs2coach"
HOME.mkdir(exist_ok=True)
CONFIG = HOME / "config.json"


def load_config():
    try:
        cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
        return cfg if isinstance(cfg, dict) else {}
    except (OSError, ValueError):
        return {}


def save_config(**values):
    cfg = load_config() | values
    CONFIG.write_text(json.dumps(cfg, indent=2), encoding="utf-8")


def match_id(match):
    key = f"{match.source}|{match.played_at}|{len(match.rounds)}|{len(match.kills)}"
    return hashlib.sha1(key.encode()).hexdigest()


def _num(v):
    return float(str(v).split("/")[0]) if isinstance(v, str) else float(v)


SAVED = ["rounds", "kills", "k4", "k5", "c1vx", "clutch_won", "flash_thrown", "opening_attempts"]


class History:
    def __init__(self, path=HOME / "historico.db"):
        try:
            self._open(path)
        except sqlite3.DatabaseError:
            Path(path).replace(Path(path).with_suffix(".corrompido.db"))
            self._open(path)

    def _open(self, path):
        self.db = sqlite3.connect(path)
        self.db.execute("PRAGMA quick_check").fetchone()
        self.db.execute("""CREATE TABLE IF NOT EXISTS results (
            match_id TEXT, played_at REAL, map TEXT, source TEXT, sid TEXT, name TEXT, metrics TEXT,
            PRIMARY KEY (match_id, sid))""")

    def save(self, match, stats):
        mid = match_id(match)
        scores = team_scores(match)
        rows = []
        for sid, c in stats.counters.items():
            d = derive(c)
            values = {k: _num(d.get(k, 0)) for k in [*METRICS, *SAVED]}
            if sid in scores:
                mine, theirs = scores[sid]
                values["won"] = 1.0 if mine > theirs else 0.0 if mine < theirs else 0.5
            rows.append((mid, match.played_at, match.map_name, match.source, sid,
                         stats.names.get(sid, sid), json.dumps(values)))
        self.db.executemany("INSERT OR REPLACE INTO results VALUES (?,?,?,?,?,?,?)", rows)
        self.db.commit()

    def remove(self, mid):
        self.db.execute("DELETE FROM results WHERE match_id=?", (mid,))
        self.db.commit()

    def player(self, sid):
        cur = self.db.execute(
            "SELECT played_at, map, source, metrics FROM results WHERE sid=? ORDER BY played_at", (sid,))
        rows = []
        for t, m, s, js in cur:
            try:
                rows.append((float(t), str(m), str(s), json.loads(js)))
            except (TypeError, ValueError):
                continue
        return rows
