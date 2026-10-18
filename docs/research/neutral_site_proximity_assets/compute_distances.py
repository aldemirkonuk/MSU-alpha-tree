"""Neutral-site distances, time-zone shifts and COOPER-form edges for MSU games
and Big Ten tournament venues. Standard library only.
Usage: python3 -I compute_distances.py entities.tsv
Canonical distance: WGS84 geodesic (Vincenty inverse; falls back to haversine
if Vincenty fails to converge). Check: haversine, R = 6371.0088 km.
tz shift: venue UTC offset minus origin UTC offset at local noon on the game
date (IANA zones, so DST is handled); positive = travelled east. Stored in
seconds, printed in hours."""
import csv, math, sys
from datetime import datetime
from zoneinfo import ZoneInfo

E = {r["key"]: r for r in csv.DictReader(open(sys.argv[1]), delimiter="\t")}

def haversine_m(a, b, R=6371008.8):
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    h = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(b[1] - a[1]) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))

def vincenty_m(a, b):
    A, F = 6378137.0, 1 / 298.257223563
    B = (1 - F) * A
    L = math.radians(b[1] - a[1])
    U1 = math.atan((1 - F) * math.tan(math.radians(a[0])))
    U2 = math.atan((1 - F) * math.tan(math.radians(b[0])))
    sU1, cU1, sU2, cU2 = math.sin(U1), math.cos(U1), math.sin(U2), math.cos(U2)
    lam = L
    for _ in range(200):
        sl, cl = math.sin(lam), math.cos(lam)
        ss = math.hypot(cU2 * sl, cU1 * sU2 - sU1 * cU2 * cl)
        if ss == 0:
            return 0.0
        cs = sU1 * sU2 + cU1 * cU2 * cl
        sig = math.atan2(ss, cs)
        sa = cU1 * cU2 * sl / ss
        c2a = 1 - sa * sa
        c2sm = cs - 2 * sU1 * sU2 / c2a if c2a else 0.0
        C = F / 16 * c2a * (4 + F * (4 - 3 * c2a))
        prev = lam
        lam = L + (1 - C) * F * sa * (sig + C * ss * (c2sm + C * cs * (-1 + 2 * c2sm * c2sm)))
        if abs(lam - prev) < 1e-12:
            break
    else:
        return haversine_m(a, b)
    u2 = c2a * (A * A - B * B) / (B * B)
    Ak = 1 + u2 / 16384 * (4096 + u2 * (-768 + u2 * (320 - 175 * u2)))
    Bk = u2 / 1024 * (256 + u2 * (-128 + u2 * (74 - 47 * u2)))
    ds = Bk * ss * (c2sm + Bk / 4 * (cs * (-1 + 2 * c2sm * c2sm) - Bk / 6 * c2sm * (-3 + 4 * ss * ss) * (-3 + 4 * c2sm * c2sm)))
    return B * Ak * (sig - ds)

def pt(k):
    return float(E[k]["lat"]), float(E[k]["lon"])

def tz_shift_s(venue, origin, date):
    y, m, d = map(int, date.split("-"))
    t = datetime(y, m, d, 12, tzinfo=ZoneInfo(E[venue]["tz"]))
    return int(t.utcoffset().total_seconds() - t.astimezone(ZoneInfo(E[origin]["tz"])).utcoffset().total_seconds())

def cooper_pts(d_m):
    # COOPER: 5 * miles^(1/3) Elo, 28.5 Elo per point; equivalently 0.1497 * km^(1/3).
    return 5 * (d_m / 1609.344) ** (1 / 3) / 28.5

GAMES = [  # date, event, venue key, opponent, opponent origin key, result (MSU-Opp)
    ("2022-11-11", "Armed Forces Classic", "nas_north_island", "Gonzaga", "mccarthey", "63-64"),
    ("2022-11-15", "Champions Classic", "gainbridge", "Kentucky", "rupp", "86-77"),
    ("2022-11-24", "Phil Knight Inv. QF", "moda", "Alabama", "coleman", "70-81"),
    ("2022-11-25", "PKI consolation", "vmc_portland", "Oregon", "knight", "74-70"),
    ("2023-02-04", "B1G Super Saturday", "msg", "Rutgers", "jersey_mikes", "55-61"),
    ("2023-03-10", "B1G Tourn QF", "united_center", "Ohio State", "value_city", "58-68"),
    ("2023-03-17", "NCAA R64", "nationwide", "USC", "galen", "72-62"),
    ("2023-03-19", "NCAA R32", "nationwide", "Marquette", "fiserv", "69-60"),
    ("2023-03-23", "NCAA S16", "msg", "Kansas State", "bramlage", "93-98"),
    ("2023-11-14", "Champions Classic", "united_center", "Duke", "cameron", "65-74"),
    ("2023-11-23", "Acrisure Classic", "acrisure", "Arizona", "mckale", "68-74"),
    ("2023-12-16", "Motor City Inv.", "lca", "Baylor", "ferrell", "88-64"),
    ("2024-03-14", "B1G Tourn R2", "target_center", "Minnesota", "williams_arena", "77-67"),
    ("2024-03-15", "B1G Tourn QF", "target_center", "Purdue", "mackey", "62-67"),
    ("2024-03-21", "NCAA R64", "spectrum", "Mississippi State", "humphrey", "69-51"),
    ("2024-03-23", "NCAA R32", "spectrum", "North Carolina", "dean_smith", "69-85"),
    ("2024-11-12", "Champions Classic", "state_farm_arena", "Kansas", "allen", "69-77"),
    ("2024-11-25", "Maui QF", "lahaina", "Colorado", "cu_events", "72-56"),
    ("2024-11-26", "Maui SF", "lahaina", "Memphis", "fedexforum", "63-71"),
    ("2024-11-27", "Maui 3rd", "lahaina", "North Carolina", "dean_smith", "94-91"),
    ("2024-12-17", "Detroit neutral", "lca", "Oakland", "orena", "77-58"),
    ("2025-03-14", "B1G Tourn QF", "gainbridge", "Oregon", "knight", "74-64"),
    ("2025-03-15", "B1G Tourn SF", "gainbridge", "Wisconsin", "kohl", "74-77"),
    ("2025-03-21", "NCAA R64", "rocket_arena", "Bryant", "chace", "87-62"),
    ("2025-03-23", "NCAA R32", "rocket_arena", "New Mexico", "the_pit", "71-63"),
    ("2025-03-28", "NCAA S16", "state_farm_arena", "Ole Miss", "sjb", "73-70"),
    ("2025-03-30", "NCAA E8", "state_farm_arena", "Auburn", "neville", "64-70"),
    ("2025-11-18", "Champions Classic", "msg", "Kentucky", "rupp", "83-66"),
    ("2025-11-25", "Fort Myers Tip-Off", "suncoast", "East Carolina", "minges", "89-56"),
    ("2025-11-27", "Fort Myers Tip-Off", "suncoast", "North Carolina", "dean_smith", "74-58"),
    ("2025-12-20", "Motown Showdown", "lca", "Oakland", "orena", "79-70"),
    ("2026-03-13", "B1G Tourn QF", "united_center", "UCLA", "pauley", "84-88"),
    ("2026-03-19", "NCAA R64", "keybank", "North Dakota State", "scheels", "92-67"),
    ("2026-03-21", "NCAA R32", "keybank", "Louisville", "yum", "77-69"),
    ("2026-03-27", "NCAA S16", "capital_one", "UConn", "gampel", "63-67"),
]

print("## MSU games (km; tz in h; edge in points)")
print("date|event|venue|opp|d_MSU|d_opp|diff|tzMSU_h|tzOpp_h|edge|hav_MSU|hav_opp|result")
for date, ev, v, opp, o, res in GAMES:
    dm, do = vincenty_m(pt("breslin"), pt(v)), vincenty_m(pt(o), pt(v))
    print(f"{date}|{ev}|{E[v]['wikipedia_title']}|{opp}|{dm/1000:.0f}|{do/1000:.0f}|{(do-dm)/1000:+.0f}|"
          f"{tz_shift_s(v,'breslin',date)/3600:+.0f}|{tz_shift_s(v,o,date)/3600:+.0f}|"
          f"{cooper_pts(do)-cooper_pts(dm):+.2f}|{haversine_m(pt('breslin'),pt(v))/1000:.1f}|{haversine_m(pt(o),pt(v))/1000:.1f}|{res}")

print("## Big Ten arenas to tournament venues (km)")
B1G = ["state_farm_center", "assembly_hall", "carver", "xfinity", "crisler", "breslin", "williams_arena", "pinnacle",
       "welsh_ryan", "value_city", "knight", "bryce_jordan", "mackey", "jersey_mikes", "pauley", "galen", "hec_ed", "kohl"]
for k in B1G:
    print(k, *[f"{vincenty_m(pt(k), pt(v))/1000:.0f}" for v in ("united_center", "gainbridge", "tmobile", "target_center")])
