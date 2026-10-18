import json,glob,statistics,sys
season=sys.argv[1]
good=set(json.load(open(f'good_{season}.json')))
P=[json.loads(l) for fn in glob.glob(f'poss_{season}*.jsonl') for l in open(fn)]
seen=set(); G=[]
for q in P:
    k=(q['gid'],q['team'],q['period'],q['t0'],q['start'],q['pts'],q['first_fga_t'])
    if q['gid'] in good and k not in seen: seen.add(k); G.append(q)
plen=lambda p:1200 if p<=2 else 300
live={'steal','dreb_fg','dreb_ft','dreb_fg_team','dreb_ft_team'}
def tfc(q):
    if q['start'] not in live or q['foul_t'] is None: return False
    d=q['foul_t']-q['t0']
    if not (1<=d<=4): return False
    if q['first_fga_t'] is not None and q['first_fga_t']<=q['foul_t']: return False
    if q.get('foul_after_fga_same_t') or q.get('ft_at_foul'): return False
    if q['period']>=2 and plen(q['period'])-q['foul_t']<=120: return False
    return True
c=[q for q in G if tfc(q)]
# comparison: live-start possessions not late, with no foul in 1-4s, that reached 4 s without FGA or TO? approximate: first FGA >4s after t0 or none, and no foul before 4 s
comp=[q for q in G if q['start'] in live and not tfc(q) and not (q['period']>=2 and plen(q['period'])-q['t0']<=120) and (q['first_fga_t'] is None or q['first_fga_t']-q['t0']>=1)]
comp_early=[q for q in comp if q['first_fga_t'] is not None and q['first_fga_t']-q['t0']<=6]
m=lambda L: sum(q['pts'] for q in L)/len(L)
print('cand n',len(c),'PPP',round(m(c),3))
print('live-start comparison (no cand) n',len(comp),'PPP',round(m(comp),3))
print('live-start with first FGA 1-6 s n',len(comp_early),'PPP',round(m(comp_early),3))
bys={}
for q in c: bys[q['start']]=bys.get(q['start'],0)+1
print(bys)
allpts=[q['pts'] for q in G]
print('SD pts per possession all',round(statistics.pstdev(allpts),3),'mean',round(statistics.mean(allpts),3))
e=[q['pts'] for q in G if q['first_fga_t'] is not None and q['first_fga_t']-q['t0']<=10]
print('SD early poss',round(statistics.pstdev(e),3),'mean',round(statistics.mean(e),3),'n',len(e))
