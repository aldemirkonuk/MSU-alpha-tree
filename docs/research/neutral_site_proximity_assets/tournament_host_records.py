"""Host vs neutral records of top-4 seeds in NCAA tournament rounds 1-2 (men and women).

Added 2026-10-18 for docs/research/neutral_site_proximity.md ("Additions 2026-10-18", item G).
Source: English Wikipedia tournament pages, read through the MediaWiki API
(action=parse&prop=wikitext), 2008-2019 and 2021-2025, both sexes.
Usage: python3 -I tournament_host_records.py <cache_dir>
Wikitext is cached in <cache_dir> as YEAR_[mw].txt; fetches are retried slowly
because the API rate-limits bursts. Results are descriptive (no quality control
beyond seed line); see the doc for caveats.
"""
import json, os, re, sys, time, math, statistics as st, subprocess

YEARS = list(range(2008, 2020)) + list(range(2021, 2026))
HOST_YEARS = [2015, 2016, 2017, 2018, 2019, 2022, 2023, 2024, 2025]  # women's top-16 campus hosting (2020 cancelled, 2021 San Antonio)
DEF = [1, 16, 8, 9, 5, 12, 4, 13, 6, 11, 3, 14, 7, 10, 2, 15]  # bracket slot order when seeds are not written out

def fetch(cache):
    os.makedirs(cache, exist_ok=True)
    for y in YEARS:
        for sex, k in (("women%27s", "w"), ("men%27s", "m")):
            fn = os.path.join(cache, f"{y}_{k}.txt")
            if os.path.exists(fn) and os.path.getsize(fn) > 0:
                continue
            url = ("https://en.wikipedia.org/w/api.php?action=parse&page="
                   f"{y}_NCAA_Division_I_{sex}_basketball_tournament&prop=wikitext&format=json&formatversion=2&redirects=1")
            for _ in range(5):
                out = subprocess.run(["curl", "-s", "-A", "MSUAlpha3-research/0.1", url], capture_output=True, text=True).stdout
                try:
                    open(fn, "w").write(json.loads(out)["parse"]["wikitext"]); break
                except Exception:
                    time.sleep(5)
            time.sleep(1.5)

def clean(t):
    t = t.replace("'''", "")
    m = re.search(r"title=([^}|]+)", t)
    if m: return m.group(1).strip()
    m = re.search(r"\[\[(?:[^\]|]*\|)?([^\]]+)\]\]", t)
    if m: return m.group(1).strip()
    return re.sub(r"<.*?>|\{\{.*?\}\}", "", t).strip()

def num(s):
    s = re.sub(r"[^0-9]", "", s.split("<")[0]) if s else ""
    return int(s) if s else None

def games(cache):
    rows = []
    for y in YEARS:
        for k in "wm":
            txt = open(os.path.join(cache, f"{y}_{k}.txt")).read()
            for reg, m in enumerate(re.finditer(r"\{\{16TeamBracket", txt)):
                blk = txt[m.start():m.start() + 20000]
                e = blk.find("\n}}"); blk = blk[:e] if e > 0 else blk
                d = {a.strip(): b.strip() for a, b in re.findall(r"\|\s*([A-Za-z0-9\-]+)\s*=\s*([^\n]*)", blk)}
                for rd, n in (("RD1", 16), ("RD2", 8)):
                    for i in range(1, n + 1, 2):
                        a, b = f"{i:02d}", f"{i+1:02d}"
                        sa, sb = num(d.get(f"{rd}-seed{a}", "")), num(d.get(f"{rd}-seed{b}", ""))
                        if rd == "RD1" and sa is None:
                            sa, sb = DEF[i - 1], DEF[i]
                        rows.append(dict(year=y, sex=k, region=reg, rd=rd, sa=sa, sb=sb,
                                         ta=clean(d.get(f"{rd}-team{a}", "")), tb=clean(d.get(f"{rd}-team{b}", "")),
                                         pa=num(d.get(f"{rd}-score{a}", "")), pb=num(d.get(f"{rd}-score{b}", ""))))
    return rows

ALIAS = {"UConn": "Connecticut", "NC State": "North Carolina State", "LSU": "Louisiana State", "USC": "Southern California",
         "UCLA": "Los Angeles", "Miami (FL)": "University of Miami", "California": "Berkeley", "TCU": "Texas Christian",
         "Texas": "University of Texas", "Michigan": "University of Michigan", "Iowa": "University of Iowa",
         "Oregon": "University of Oregon", "North Carolina": "Chapel Hill", "Arizona": "University of Arizona",
         "Washington": "University of Washington", "Indiana": "Indiana University"}

def hosts(cache):
    H = {}
    for y in HOST_YEARS:
        t = open(os.path.join(cache, f"{y}_w.txt")).read()
        hs = [m.group(1) for m in re.finditer(r"\(hosts?: \[\[([^\]|]+)(?:\|[^\]]*)?\]\]", t, flags=re.I)]
        H[y] = hs[4:20] if y == 2025 else hs[:16]  # 2025 page lists the First Four sites first
    return H

def is_host(team, hs):
    key = ALIAS.get(team, team)
    for h in hs:
        if key == "University of Texas":
            if h in ("University of Texas", "University of Texas at Austin"): return True
            continue
        if key == "University of Iowa":
            if h == "University of Iowa": return True
            continue
        if key in h or team == h: return True
    return False

def top(x):
    if x["pa"] is None or x["pb"] is None: return None
    a, b = (x["sa"], x["pa"], x["ta"]), (x["sb"], x["pb"], x["tb"])
    if a[0] > b[0]: a, b = b, a
    if a[0] not in (1, 2, 3, 4) or b[0] in (1, 2, 3, 4): return None
    return a[0], b[0], a[1] - b[1], a[2]

def line(rows, label):
    if not rows: return
    m = [t[2] for t in rows]; w = sum(v > 0 for v in m)
    se = st.pstdev(m) / math.sqrt(len(m))
    print(f"{label:48s} n={len(m):4d}  W-L {w}-{len(m)-w} ({100*w/len(m):.1f}%)  mean margin {st.mean(m):+.2f} (SE {se:.2f})")

if __name__ == "__main__":
    cache = sys.argv[1]
    fetch(cache)
    R = games(cache); H = hosts(cache)
    flag = {}
    for x in R:
        if x["sex"] == "w" and x["year"] in H and x["rd"] == "RD1" and x["sa"] in (1, 2, 3, 4):
            flag[(x["year"], x["ta"])] = is_host(x["ta"], H[x["year"]])
    print("Top-4 women's seeds not hosting:", [k for k, v in flag.items() if not v])
    for rd in ("RD1", "RD2"):
        print("==", rd)
        sel = lambda c: [top(x) for x in R if x["rd"] == rd and c(x) and top(x)]
        home, away = [], []
        for x in R:
            if x["sex"] == "w" and x["year"] in HOST_YEARS and x["rd"] == rd and top(x):
                t = top(x); (home if flag.get((x["year"], t[3])) else away).append(t)
        line(home, "Women 2015-25 (no 2021), top-4 seed hosting")
        line(away, "Women 2015-25, top-4 seed not hosting")
        line(sel(lambda x: x["sex"] == "w" and x["year"] == 2021), "Women 2021 (all neutral, San Antonio)")
        line(sel(lambda x: x["sex"] == "w" and 2008 <= x["year"] <= 2014), "Women 2008-14 (pre-assigned sites, mixed)")
        line(sel(lambda x: x["sex"] == "m" and x["year"] in HOST_YEARS), "Men 2015-25 (no 2021), neutral pods")
        line(sel(lambda x: x["sex"] == "m" and x["year"] == 2021), "Men 2021 (Indiana, no pods)")
        line(sel(lambda x: x["sex"] == "m" and 2008 <= x["year"] <= 2014), "Men 2008-14, neutral pods")
