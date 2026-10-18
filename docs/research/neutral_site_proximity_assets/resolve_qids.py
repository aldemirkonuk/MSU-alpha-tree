"""Resolve Wikipedia titles to Wikidata QIDs, then read P625 from Wikidata.
Usage: python3 -I resolve_qids.py entities_seed.tsv entities.tsv
Standard library only. Network: en.wikipedia.org and www.wikidata.org APIs."""
import csv, json, subprocess, sys, time, urllib.parse
UA = "MSU-Alpha-3-research/0.1 (research script)"
def get(url):
    # curl is used because the local Python build lacks a CA bundle.
    out = subprocess.run(["curl", "-sS", "--max-time", "30", "-A", UA, url],
                         check=True, capture_output=True).stdout
    return json.loads(out)
rows = list(csv.DictReader(open(sys.argv[1]), delimiter="\t"))
title2qid = {}
for i in range(0, len(rows), 40):
    titles = "|".join(r["wikipedia_title"] for r in rows[i:i+40])
    q = urllib.parse.urlencode({"action": "query", "format": "json", "redirects": 1,
                                "prop": "pageprops", "ppprop": "wikibase_item", "titles": titles})
    d = get("https://en.wikipedia.org/w/api.php?" + q)["query"]
    alias = {}
    for k in ("normalized", "redirects"):
        for n in d.get(k, []): alias[n["from"]] = n["to"]
    bytitle = {p["title"]: p.get("pageprops", {}).get("wikibase_item") for p in d["pages"].values()}
    for r in rows[i:i+40]:
        t = r["wikipedia_title"]
        while t in alias: t = alias[t]
        title2qid[r["wikipedia_title"]] = bytitle.get(t)
    time.sleep(1)
qids = [q for q in title2qid.values() if q]
coords = {}
for i in range(0, len(qids), 45):
    q = urllib.parse.urlencode({"action": "wbgetentities", "format": "json", "props": "claims",
                                "ids": "|".join(qids[i:i+45])})
    for qid, ent in get("https://www.wikidata.org/w/api.php?" + q)["entities"].items():
        c = ent.get("claims", {}).get("P625")
        if c:
            v = c[0]["mainsnak"]["datavalue"]["value"]
            coords[qid] = (v["latitude"], v["longitude"])
    time.sleep(1)
w = csv.writer(open(sys.argv[2], "w"), delimiter="\t")
w.writerow(["key", "role", "wikipedia_title", "qid", "lat", "lon", "tz"])
for r in rows:
    qid = title2qid.get(r["wikipedia_title"])
    lat, lon = coords.get(qid, ("", ""))
    w.writerow([r["key"], r["role"], r["wikipedia_title"], qid or "", lat, lon, r["tz"]])
