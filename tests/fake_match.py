import random

import pandas as pd

from cs2coach.demo import CT, T, Match, finalize

WEAPONS = ["ak47", "m4a1", "awp", "glock", "usp_silencer", "deagle", "m4a1_silencer"]


def fake_match(seed=1, rounds=24, skill=None):
    rng = random.Random(seed)
    players = [(str(76561198000000000 + i), f"Jogador{i}") for i in range(10)]
    skill = skill or {sid: rng.uniform(0.6, 1.4) for sid, _ in players}
    rr, roster, kills, hurts, shots, blinds = [], [], [], [], [], []
    tick = 1000
    for r in range(1, rounds + 1):
        start = tick
        swap = r > rounds // 2
        team = {sid: (CT if (i < 5) != swap else T) for i, (sid, _) in enumerate(players)}
        for sid, name in players:
            roster.append((r, sid, name, team[sid]))
        alive = {T: [s for s in team if team[s] == T], CT: [s for s in team if team[s] == CT]}
        t = start + rng.randint(200, 2000)
        for sid in team:
            for _ in range(rng.randint(0, 2)):
                shots.append((start + rng.randint(0, 500), sid, rng.choice(["flashbang", "smokegrenade", "hegrenade", "molotov"])))
        while alive[T] and alive[CT]:
            ta = rng.choice([T, CT])
            a = max(rng.sample(alive[ta], min(2, len(alive[ta]))), key=lambda s: skill[s] * rng.random())
            v = rng.choice(alive[CT if ta == T else T])
            w = rng.choice(WEAPONS)
            for _ in range(rng.randint(5, 14)):
                shots.append((t - rng.randint(1, 60), a, w))
            hp = 100
            while hp > 0:
                grp = rng.choice([1, 2, 2, 3, 4, 6]) if rng.random() > 0.3 * skill[a] else 1
                d = 100 if grp == 1 and w == "awp" else rng.randint(20, 110 if grp == 1 else 35)
                hurts.append((t - rng.randint(0, 40), a, ta, v, team[v], d, w, grp))
                hp -= d
            if rng.random() < 0.3:
                fl = rng.choice(alive[ta])
                blinds.append((t - 100, fl, ta, v, team[v], rng.uniform(0.3, 3.0)))
                if rng.random() < 0.3:
                    blinds.append((t - 100, fl, ta, a, ta, rng.uniform(0.5, 2.0)))
            assister = rng.choice(alive[ta] + [""] * 4)
            kills.append((t, a, ta, v, team[v], assister if assister != a else "", rng.random() < 0.1,
                          rng.random() < 0.45 * skill[a], w, False, rng.uniform(100, 2000)))
            alive[team[v]].remove(v)
            t += rng.randint(30, 900)
        winner = T if alive[T] else CT
        rr.append((r, start, t + 50, winner))
        tick = t + 700
    m = Match(
        source=f"fake_{seed}.dem", map_name="de_mirage", played_at=1_700_000_000 + seed * 86400,
        rounds=pd.DataFrame(rr, columns=["round", "start_tick", "end_tick", "winner"]),
        roster=pd.DataFrame(roster, columns=["round", "sid", "name", "team"]),
        kills=pd.DataFrame(kills, columns=["tick", "attacker", "attacker_team", "victim", "victim_team", "assister",
                                           "flash_assist", "headshot", "weapon", "thrusmoke", "distance"]),
        hurts=pd.DataFrame(hurts, columns=["tick", "attacker", "attacker_team", "victim", "victim_team", "dmg",
                                           "weapon", "hitgroup"]).assign(
            hitgroup=lambda d: d.hitgroup.map({1: "head", 2: "chest", 3: "stomach", 4: "left_arm", 6: "left_leg"})),
        shots=pd.DataFrame(shots, columns=["tick", "sid", "weapon"]),
        blinds=pd.DataFrame(blinds, columns=["tick", "attacker", "attacker_team", "victim", "victim_team", "duration"]),
    )
    return finalize(m)
