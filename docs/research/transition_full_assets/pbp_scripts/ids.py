import json,datetime,time,sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from fetch import get
season=sys.argv[1]  # e.g. 2026
start=datetime.date(int(season)-1,11,1); end=datetime.date(int(season),4,10)
out={}
d=start
while d<=end:
    u=f"https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard?dates={d:%Y%m%d}&groups=50&limit=500"
    j=get(u) or {'events':[]}
    for e in j.get('events',[]):
        c=e['competitions'][0]
        if c['status']['type'].get('completed'):
            teams=[(t['team']['id'],t['team'].get('location'),t['team'].get('conferenceId'),t.get('homeAway')) for t in c['competitors']]
            out[e['id']]={'date':str(d),'teams':teams,'season_type':e.get('season',{}).get('type')}
    d+=datetime.timedelta(days=1); time.sleep(0.1); print(d,len(out),flush=True)
json.dump(out,open(f'ids_{season}.json','w'))
print(len(out))
