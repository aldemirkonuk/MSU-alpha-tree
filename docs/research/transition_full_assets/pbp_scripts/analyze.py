import json,sys,collections,glob,statistics,math
season=sys.argv[1]
ids=json.load(open(f'ids_{season}.json'))
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
# game quality filter: both teams' parsed points equal box score (+/- technical FTs <=2) and possessions balanced
pts=collections.defaultdict(lambda:collections.Counter()); npos=collections.defaultdict(lambda:collections.Counter())
for q in P: pts[q['gid']][q['team']]+=q['pts']; npos[q['gid']][q['team']]+=1
score={}
for b in B:
    try: score[(b['gid'],b['team'])]=int(b['score'])
    except: pass
good=set()
for gid in pts:
    ok=True; teams=list(npos[gid].keys())
    if len(teams)!=2: continue
    for t in teams:
        s=score.get((gid,t))
        if s is None or not (0<=s-pts[gid][t]<=3): ok=False
    if abs(npos[gid][teams[0]]-npos[gid][teams[1]])>4: ok=False
    if ok: good.add(gid)
print('games parsed',len(pts),'good',len(good), 'ids',len(ids))
G=[q for q in P if q['gid'] in good]
def late(q): return plen(q['period'])-q['t0']<=60
groups={'steal':['steal'],'dead_to':['dead_to'],'dreb_fg (player)':['dreb_fg'],'dreb_fg team/dead':['dreb_fg_team','dreb_fg_dead'],'dreb_ft (all)':['dreb_ft','dreb_ft_team','dreb_ft_dead'],'made_fg':['made_fg'],'made_ft':['made_ft'],'period_start':['period_start'],'other/unknown':['unknown','dreb_fg_unrec','dreb_ft_unrec']}
inv={v:k for k,vs in groups.items() for v in vs}
def table(rows,label):
    agg=collections.defaultdict(lambda:[0,0,0,0,0,0]) # n, pts, n_early, pts_early, n_withfga
    for q in rows:
        g=inv.get(q['start'],'other/unknown'); a=agg[g]
        a[0]+=1; a[1]+=q['pts']
        if q['first_fga_t'] is not None:
            a[4]+=1
            if q['first_fga_t']-q['t0']<=10: a[2]+=1; a[3]+=q['pts']
    N=sum(a[0] for a in agg.values()); T=sum(a[1] for a in agg.values())
    print(f'\n== {label}: possessions {N}, PPP {T/N:.3f}')
    print('start | n | share % | PPP | 95% CI half-width | first FGA <=10 s (% of poss with FGA) | PPP early-shot poss | PPP other poss')
    out={}
    for g in groups:
        if g not in agg: continue
        n,p,ne,pe,nf,_=agg[g]
        # SD of points per possession approx from sample
        ppp=p/n
        rows_g=[q['pts'] for q in rows if inv.get(q['start'],'other/unknown')==g]
        sd=statistics.pstdev(rows_g); hw=1.96*sd/math.sqrt(n)
        oth=(p-pe)/(n-ne) if n-ne else float('nan')
        print(f'{g} | {n} | {100*n/N:.1f} | {ppp:.3f} | {hw:.3f} | {100*ne/nf if nf else 0:.1f} | {pe/ne if ne else float("nan"):.3f} | {oth:.3f}')
        out[g]=(n,ppp)
    return out
table(G,'D-I all good games, all possessions')
table([q for q in G if not late(q)],'D-I excluding possessions starting in final 60 s of a period')
# take-foul candidates
tf=collections.Counter(); tgames=collections.Counter()
live={'steal','dreb_fg','dreb_ft','dreb_fg_team','dreb_ft_team'}
def tfc(q,lo,hi,need_noft):
    if q['start'] not in live or q['foul_t'] is None: return False
    d=q['foul_t']-q['t0']
    if not (lo<=d<=hi): return False
    if q['first_fga_t'] is not None and q['first_fga_t']<=q['foul_t']: return False
    if q.get('foul_after_fga_same_t'): return False
    if q['period']>=2 and plen(q['period'])-q['foul_t']<=120: return False
    if need_noft and q.get('ft_at_foul'): return False
    return True
ngames=len(good)
for lo,hi,nf in [(0,4,True),(1,4,True),(0,4,False),(0,6,True),(0,6,False)]:
    c=sum(1 for q in G if tfc(q,lo,hi,nf))
    print(f'take-foul candidates window {lo}-{hi}s noFT={nf}: {c} in {ngames} games = {c/ngames:.2f} per game (both teams), {c/(2*ngames):.2f} per team-game')
json.dump(sorted(good),open(f'good_{season}.json','w'))
