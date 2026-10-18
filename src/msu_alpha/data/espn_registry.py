"""Build the game registry and roster registry for Michigan State from ESPN's public site API.

Run: python -m msu_alpha.data.espn_registry --seasons 2022 2023 2024 2025 2026 --out registry
ESPN's season year is the year the season ends (2026 = 2025-26).
Units follow the project rule: height in cm, weight in kg.
"""
from __future__ import annotations

import argparse
import csv
import json
import time
import urllib.request
from pathlib import Path

BASE = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball"
MSU_ID = "127"
SEASON_TYPES = {"2": "regular", "3": "postseason"}


def get(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.load(r)


def games(season: int) -> list[dict]:
    rows = []
    for st, st_name in SEASON_TYPES.items():
        data = get(f"{BASE}/teams/{MSU_ID}/schedule?season={season}&seasontype={st}")
        for e in data.get("events", []):
            c = e["competitions"][0]
            msu = next(x for x in c["competitors"] if x["team"]["id"] == MSU_ID)
            opp = next(x for x in c["competitors"] if x["team"]["id"] != MSU_ID)
            notes = "; ".join(n.get("headline", "") for n in c.get("notes", []))
            score = lambda x: (x.get("score") or {}).get("value")
            ms, os_ = score(msu), score(opp)
            rows.append({
                "game_id": e["id"],
                "season": season,
                "season_type": st_name,
                "date_utc": e["date"],
                "site": "neutral" if c.get("neutralSite") else msu["homeAway"],
                "venue": (c.get("venue") or {}).get("fullName", ""),
                "city": ((c.get("venue") or {}).get("address") or {}).get("city", ""),
                "opponent": opp["team"]["displayName"],
                "opponent_id": opp["team"]["id"],
                "msu_score": int(ms) if ms is not None else "",
                "opp_score": int(os_) if os_ is not None else "",
                "result": ("W" if ms > os_ else "L") if ms is not None and os_ is not None else "",
                "attendance": c.get("attendance", ""),
                "broadcast": "; ".join((b.get("media") or {}).get("shortName", "") for b in c.get("broadcasts", [])),
                "notes": notes,
                "status": ((c.get("status") or {}).get("type") or {}).get("name", ""),
                "footage_source": "",
                "footage_path": "",
            })
        time.sleep(0.3)
    return rows


def roster(season: int) -> list[dict]:
    data = get(f"{BASE}/teams/{MSU_ID}/roster?season={season}")
    rows = []
    for a in data.get("athletes", []):
        h, w = a.get("height"), a.get("weight")
        rows.append({
            "season": season,
            "espn_id": a["id"],
            "name": a.get("displayName", ""),
            "jersey": a.get("jersey", ""),
            "position": (a.get("position") or {}).get("abbreviation", ""),
            "height_cm": round(h * 2.54, 1) if h else "",
            "weight_kg": round(w * 0.45359237, 1) if w else "",
            "class": (a.get("experience") or {}).get("displayValue", ""),
            "hometown": (a.get("birthPlace") or {}).get("displayText", ""),
            "headshot_url": (a.get("headshot") or {}).get("href", ""),
        })
    return rows


def write(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seasons", type=int, nargs="+", default=[2022, 2023, 2024, 2025, 2026])
    ap.add_argument("--out", default="registry")
    args = ap.parse_args()
    out = Path(args.out)
    all_games, all_roster = [], []
    for s in args.seasons:
        all_games += games(s)
        all_roster += roster(s)
        time.sleep(0.3)
    all_games.sort(key=lambda r: r["date_utc"], reverse=True)
    write(out / "games.csv", all_games)
    write(out / "rosters.csv", all_roster)
    print(f"{len(all_games)} games, {len(all_roster)} roster rows -> {out}")


if __name__ == "__main__":
    main()
