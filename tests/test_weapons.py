import os

import pandas as pd
import pytest
from PySide6.QtWidgets import QApplication

from cs2coach import progress as prog
from cs2coach import weapons as wp
from cs2coach.card import profile_card

app = QApplication.instance() or QApplication([])


@pytest.mark.parametrize("weapon", list(wp.WEAPONS) + ["nao_existe", ""])
def test_every_sticker_draws_something(weapon):
    for width in (8, 48, 240):
        pm = wp.sticker(width, weapon)
        img = pm.toImage()
        assert pm.width() >= 16 and pm.height() >= 8
        assert any(img.pixelColor(x, y).alpha() > 0 for x in range(img.width()) for y in range(img.height()))


def test_categories_have_colors():
    assert {c for _, c in wp.WEAPONS.values()} <= set(wp.COLORS)


def weapons_df():
    return pd.DataFrame({"sid": ["a", "a", "b"], "weapon": ["ak47", "awp", "ak47"], "kills": [10.0, 3.0, 50.0],
                         "hs": [5.0, 0.0, 1.0], "damage": [0.0] * 3, "hits": [20.0, 4.0, 1.0], "shots": [80, 10, 0]})


def test_weapon_line_and_top_weapon():
    df = weapons_df()
    assert prog.weapon_line(df, "a", "ak47") == {"kills": 10, "hs_pct": 0.5, "accuracy": 0.25}
    assert prog.weapon_line(df, "b", "ak47")["accuracy"] is None
    assert prog.weapon_line(df, "a", "deagle") == {"kills": 0, "hs_pct": 0.0, "accuracy": None}
    assert prog.weapon_line(None, "a", "ak47") is None and prog.weapon_line(df, "a", "") is None
    assert prog.top_weapon(df, "a") == "ak47" and prog.top_weapon(df, "z") is None and prog.top_weapon(None, "a") is None


def test_career_handles_empty_and_odd_rows():
    empty = prog.career([])
    assert empty["matches"] == 0 and empty["rating"] is None and empty["best_map"] is None
    rows = [(1, "de_mirage", "x", {"rating": 1.2, "won": 1, "k5": 1}), (2, "de_mirage", "x", {"rating": "lixo", "won": 0}),
            (3, "de_nuke", "x", {"rating": 2.0}), (4, "de_inferno", "x", {})]
    c = prog.career(rows)
    assert c["matches"] == 4 and c["winrate"] == 0.5 and c["aces"] == 1 and c["best_map"] == "Mirage"


@pytest.mark.parametrize("profile", [{}, {"name": "x" * 300, "fav_player": "FalleN", "fav_team": "Lendas do Brasil",
                                          "border": "nao_existe", "avatar": "?"}])
def test_profile_card_renders(profile, tmp_path):
    qualities = [("Rating", "1.30"), ("Dano por round (ADR)" * 4, "99"), ("HS", "60%"), ("extra", "1")]
    for weapon, stats in ((None, None), ("awp", {"kills": 3, "hs_pct": 0.0, "accuracy": None}), ("m4a1", prog.weapon_line(weapons_df(), "a", "m4a1"))):
        img = profile_card(profile, profile.get("name"), prog.career([]), qualities, weapon, stats, (3, 14))
        assert (img.width(), img.height()) == (1200, 630)
    img = profile_card({}, "", prog.career([]), [], None, None, (0, 0))
    assert img.save(str(tmp_path / "p.png"), "PNG") and os.path.getsize(tmp_path / "p.png") > 5_000
