import pandas as pd
import pytest

from cs2coach import library
from cs2coach.stats import match_stats
from tests.fake_match import fake_match


@pytest.fixture(autouse=True)
def lib(tmp_path, monkeypatch):
    monkeypatch.setattr(library, "LIB", tmp_path / "lib")


def test_roundtrip_delete_restore_purge():
    m = fake_match(4)
    mid, new = library.save(m, "C:/x.dem")
    assert new and library.save(m)[1] is False
    back = library.load(mid)
    for t in library.TABLES:
        pd.testing.assert_frame_equal(getattr(m, t).reset_index(drop=True), getattr(back, t), check_dtype=False)
    assert match_stats(back).counters == match_stats(m).counters
    assert [e["id"] for e in library.entries()] == [mid]
    with pytest.raises(library.LibraryError):
        library.purge(mid)
    library.set_deleted(mid, True)
    assert not library.entries() and [e["id"] for e in library.entries(True)] == [mid]
    library.save(m)
    assert library.entries()
    library.set_deleted(mid, True)
    library.purge(mid)
    assert not library.entries(True) and not library.entries()


def test_scores_per_team():
    m = fake_match(5)
    mid, _ = library.save(m)
    scores = library.entries()[0]["scores"]
    assert all(won + lost == len(m.rounds) for won, lost in scores.values())


@pytest.mark.parametrize("bad", ["../../etc", "a" * 40, "", None, "0" * 39])
def test_rejects_bad_ids(bad):
    with pytest.raises(library.LibraryError):
        library.load(bad)


def test_clips_are_sanitized_and_positions_need_original():
    m = fake_match(6)
    mid, _ = library.save(m)
    library.save_clips(mid, [{"id": "x", "name": "<b>" * 40, "round": "3", "start": 10, "end": 20},
                             {"id": "y"}, "lixo", {"id": "z", "name": "ok", "round": 1, "start": "a", "end": 2}])
    got = library.clips(mid)
    assert len(got) == 1 and got[0]["round"] == 3 and len(got[0]["name"]) == 60 and got[0]["auto"] is False
    with pytest.raises(library.LibraryError, match="original"):
        library.positions(mid)


def test_highlights_and_tracks():
    import numpy as np
    from cs2coach.replay import RoundTrack, highlights
    m = fake_match(9)
    clips = highlights(m)
    assert clips and all(c["start"] < c["end"] and c["auto"] for c in clips)
    assert clips == sorted(clips, key=lambda c: (-c["score"], c["round"]))
    sid = m.roster.sid.iloc[0]
    assert all(c["sid"] == sid for c in highlights(m, sid))
    r = m.rounds.iloc[0]
    ticks = np.arange(r.start_tick, r.end_tick, 8)
    pos = pd.DataFrame({"tick": np.repeat(ticks, 2), "sid": ["a", "b"] * len(ticks), "x": np.repeat(ticks, 2).astype(float),
                        "y": 0.0, "z": 0.0, "yaw": 350.0, "alive": True, "hp": 100})
    track = RoundTrack(pos, r.start_tick, r.end_tick)
    x, y, yaw, alive, hp = track.at(ticks[0] + 4)["a"]
    assert abs(x - (ticks[0] + 4)) < 1e-3 and alive and hp == 100
