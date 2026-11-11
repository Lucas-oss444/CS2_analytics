import json
import re
import shutil
import time
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

from .demo import Match, extract_positions
from .stats import team_scores
from .storage import HOME, match_id

LIB = HOME / "library"
TABLES = ("rounds", "roster", "kills", "hurts", "shots", "blinds")
ID = re.compile(r"[0-9a-f]{40}")


class LibraryError(Exception):
    pass


def _dir(mid):
    if not isinstance(mid, str) or not ID.fullmatch(mid):
        raise LibraryError("identificador de demo inválido.")
    return LIB / mid


def save(m, original=""):
    mid = match_id(m)
    d = _dir(mid)
    if (d / "meta.json").exists():
        set_deleted(mid, False)
        return mid, False
    tmp = d.with_name(mid + ".tmp")
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    for t in TABLES:
        getattr(m, t).to_parquet(tmp / f"{t}.parquet", index=False)
    if m.positions is not None:
        m.positions.to_parquet(tmp / "positions.parquet", index=False)
    meta = {"id": mid, "source": m.source, "map": m.map_name, "played_at": m.played_at, "rounds": len(m.rounds),
            "original": str(original), "added_at": time.time(), "deleted": False, "scores": team_scores(m)}
    (tmp / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
    tmp.replace(d)
    return mid, True


def _meta(d):
    try:
        meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
        return meta if isinstance(meta, dict) and meta.get("id") == d.name else None
    except (OSError, ValueError):
        return None


def entries(deleted=False):
    if not LIB.exists():
        return []
    metas = [_meta(d) for d in LIB.iterdir() if d.is_dir() and ID.fullmatch(d.name)]
    metas = [m for m in metas if m and bool(m.get("deleted")) == deleted]
    return sorted(metas, key=lambda m: -float(m.get("played_at", 0)))


def load(mid):
    d = _dir(mid)
    meta = _meta(d)
    if not meta:
        raise LibraryError("demo não encontrada na biblioteca.")
    try:
        frames = {t: pd.read_parquet(d / f"{t}.parquet") for t in TABLES}
    except Exception as e:
        raise LibraryError(f"arquivos da demo danificados ({e}).") from e
    return Match(source=meta["source"], map_name=meta["map"], played_at=float(meta["played_at"]), **frames)


def set_deleted(mid, flag):
    d = _dir(mid)
    meta = _meta(d)
    if not meta:
        raise LibraryError("demo não encontrada na biblioteca.")
    meta["deleted"] = bool(flag)
    meta["deleted_at"] = time.time() if flag else None
    (d / "meta.json").write_text(json.dumps(meta), encoding="utf-8")


def purge(mid):
    d = _dir(mid)
    meta = _meta(d)
    if not meta or not meta.get("deleted"):
        raise LibraryError("só é possível apagar de vez uma demo que está na lixeira.")
    shutil.rmtree(d)


def meta(mid):
    data = _meta(_dir(mid))
    if not data:
        raise LibraryError("demo não encontrada na biblioteca.")
    return data


def positions(mid):
    d = _dir(mid)
    f = d / "positions.parquet"
    original = meta(mid).get("original") or ""
    if f.exists() and "site" not in pq.read_schema(f).names and Path(original).is_file():
        f.unlink()
    if not f.exists():
        if not original or not Path(original).is_file():
            raise LibraryError("o arquivo original da demo não está mais no PC, então não dá para montar o replay. "
                               "Adicione a demo de novo para ativar o replay.")
        extract_positions(original, load(mid).rounds).to_parquet(f, index=False)
    try:
        return pd.read_parquet(f)
    except Exception as e:
        raise LibraryError(f"posições danificadas ({e}).") from e


def _clean_clip(c):
    if not isinstance(c, dict):
        return None
    try:
        return {"id": str(c["id"])[:40], "name": str(c.get("name", "Clipe"))[:60], "round": int(c["round"]),
                "start": int(c["start"]), "end": int(c["end"]), "sid": str(c.get("sid", ""))[:20], "auto": False}
    except (KeyError, TypeError, ValueError):
        return None


def clips(mid):
    try:
        data = json.loads((_dir(mid) / "clips.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return [c for c in map(_clean_clip, data if isinstance(data, list) else []) if c]


def save_clips(mid, items):
    meta(mid)
    clean = [c for c in map(_clean_clip, items) if c]
    (_dir(mid) / "clips.json").write_text(json.dumps(clean), encoding="utf-8")
