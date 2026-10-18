import json,sys,collections,glob,csv
season=sys.argv[1]; tcsv=sys.argv[2]
ids=json.load(open(f'ids_{season}.json')); good=set(json.load(open(f'good_{season}.json')))
P=[json.loads(l) for fn in glob.glob(f'poss_{season}*.jsonl') for l in open(fn)]
B=[json.loads(l) for fn in glob.glob(f'box_{season}*.jsonl') for l in open(fn)]
_seen=set(); _P=[]
for q in P:
    k=(q['gid'],q['team'],q['period'],q['t0'],q['start'],q['pts'],q['first_fga_t'])
    if k in _seen: continue
    _seen.add(k); _P.append(q)
P=_P
_seen=set(); _B=[]
for b in B:
    k=(b['gid'],b['team'])
    if k in _seen: continue
    _seen.add(k); _B.append(b)
B=_B
plen=lambda per:1200 if per<=2 else 300
b10={}
for g in ids.values():
    for t in g['teams']:
        if t[2]=='7': b10[t[0]]=t[1]
# torvik tempo
rows=list(csv.reader(open(tcsv,encoding='utf-8',errors='replace')))
tv={r[1]:(float(r[-1]),r[2]) for r in rows[1:] if len(r)>5}
allt=sorted([v[0] for v in tv.values()],reverse=True)
name_map={'Michigan State':'Michigan St.','Ohio State':'Ohio St.','Penn State':'Penn St.'}
opp_of={}
for gid,g in ids.items():
    a,b=g['teams'][0][0],g['teams'][1][0]; opp_of[(gid,a)]=b; opp_of[(gid,b)]=a
box={(b['gid'],b['team']):b for b in B}
S=collections.defaultdict(lambda:collections.Counter())
def early(q): return q['first_fga_t'] is not None and q['first_fga_t']-q['t0']<=10
live={'steal','dreb_fg','dreb_ft','dreb_fg_team','dreb_ft_team'}
def tfc(q):
    if q['start'] not in live or q['foul_t'] is None: return False
    d=q['foul_t']-q['t0']
    if not (1<=d<=4): return False
    if q['first_fga_t'] is not None and q['first_fga_t']<=q['foul_t']: return False
    if q.get('foul_after_fga_same_t') or q.get('ft_at_foul'): return False
    if q['period']>=2 and plen(q['period'])-q['foul_t']<=120: return False
    return True
for q in P:
    if q['gid'] not in good: continue
    o=q['team']; d=opp_of.get((q['gid'],o))
    for tm,side in ((o,'o'),(d,'d')):
        if tm not in b10: continue
        s=S[tm]; s[side+'poss']+=1; s[side+'pts']+=q['pts']
        st=q['start']
        if st=='steal': s[side+'steal']+=1
        if st=='dreb_fg':
            s[side+'dreb']+=1
            if q['first_fga_t'] is not None: s[side+'dreb_f']+=1; s[side+'dreb_e']+=early(q)
        if st in ('made_fg','made_ft'):
            s[side+'make']+=1
            if q['first_fga_t'] is not None: s[side+'make_f']+=1; s[side+'make_e']+=early(q)
        if q['first_fga_t'] is not None:
            s[side+'f']+=1; s[side+'e']+=early(q)
            if early(q): s[side+'e_pts']+=q['pts']
        if side=='d' and tfc(q): s['tf_comm']+=1
        if side=='o' and tfc(q): s['tf_drawn']+=1
games=collections.defaultdict(set)
for (gid,tm),b in box.items():
    if gid in good and tm in b10:
        games[tm].add(gid); s=S[tm]; ob=box.get((gid,opp_of.get((gid,tm))))
        try:
            s['fbp']+=int(b['fbp'] or 0); s['ofbp']+=int(ob['fbp'] or 0) if ob else 0
            s['orb']+=int(b['stats'].get('offensiveRebounds',0)); s['odrb']+=int(ob['stats'].get('defensiveRebounds',0))
            s['drb']+=int(b['stats'].get('defensiveRebounds',0)); s['oorb']+=int(ob['stats'].get('offensiveRebounds',0))
        except Exception as e: pass
print('Team | G | AdjT (T-Rank, rank of',len(allt),') | poss/G | FBP/G | Opp FBP/G | OR% | Opp OR% | Off PPP | Def PPP | Off early-shot rate (first FGA <=10 s, all poss with FGA) | Push rate after DREB off / allowed | Push rate after make off / allowed | Steal-start % off / def | Take-foul candidates committed per G | drawn per G')
for tm,name in sorted(b10.items(), key=lambda x:x[1]):
    s=S[tm]; G=len(games[tm])
    if not G: continue
    tn=name_map.get(name,name); t=tv.get(tn)
    rk=allt.index(t[0])+1 if t else None
    f=lambda a,b: 100*s[a]/s[b] if s[b] else float('nan')
    print(f"{name} | {G} | {t[0]:.1f} ({rk}) | {s['oposs']/G:.1f} | {s['fbp']/G:.1f} | {s['ofbp']/G:.1f} | {f('orb','orb')*s['orb']/(s['orb']+s['odrb']):.1f} | {100*s['oorb']/(s['oorb']+s['drb']):.1f} | {s['opts']/s['oposs']:.3f} | {s['dpts']/s['dposs']:.3f} | {f('oe','of'):.1f} | {f('odreb_e','odreb_f'):.1f} / {f('ddreb_e','ddreb_f'):.1f} | {f('omake_e','omake_f'):.1f} / {f('dmake_e','dmake_f'):.1f} | {f('osteal','oposs'):.1f} / {f('dsteal','dposs'):.1f} | {s['tf_comm']/G:.2f} | {s['tf_drawn']/G:.2f}")
