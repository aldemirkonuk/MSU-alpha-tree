import json,urllib.request,time,sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from parse import parse_game
from fetch import get
season=sys.argv[1]; shard=int(sys.argv[2]) if len(sys.argv)>2 else 0; ns=int(sys.argv[3]) if len(sys.argv)>3 else 1; sfx=f'_{shard}' if ns>1 else ''
ids=json.load(open(f'ids_{season}.json'))
outp=open(f'poss_{season}{sfx}.jsonl','a'); outb=open(f'box_{season}{sfx}.jsonl','a')
import glob
done=set()
for fn in glob.glob(f'done_{season}*.txt'): done|=set(open(fn).read().split())
dn=open(f'done_{season}{sfx}.txt','a')
for i,(gid,meta) in enumerate(ids.items()):
    if gid in done or (i%ns)!=shard: continue
    u=f"https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/summary?event={gid}"
    g=None
    g=get(u)
    if g is None: continue
    try:
        p=parse_game(g)
    except Exception as e:
        p=[]
    comp=g['header']['competitions'][0]
    score={c['id']:c.get('score') for c in comp['competitors']}
    for q in p:
        q['gid']=gid; outp.write(json.dumps(q)+'\n')
    for t in g.get('boxscore',{}).get('teams',[]):
        st={s['name']:s['displayValue'] for s in t.get('statistics',[])}
        outb.write(json.dumps({'gid':gid,'date':meta['date'],'team':t['team']['id'],'name':t['team'].get('displayName'),'score':score.get(t['team']['id']),'fbp':st.get('fastBreakPoints'),'stats':st,'n_plays':len(g.get('plays',[])),'season_type':meta.get('season_type')})+'\n')
    dn.write(gid+'\n'); dn.flush(); outp.flush(); outb.flush()
    time.sleep(0.15)
print('done')
