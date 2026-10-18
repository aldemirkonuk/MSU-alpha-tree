# Possession parser for ESPN men's college basketball play-by-play (public site API).
import json,re
def secs(clock):
    m,s=clock.split(':') if ':' in clock else ('0',clock)
    return int(m)*60+float(s)
def plen(period):  # NCAA men: 2 halves of 1200 s, OT 300 s
    return 1200 if period<=2 else 300
def parse_game(g):
    plays=g.get('plays',[])
    comp=g['header']['competitions'][0]
    tids=[c['id'] for c in comp['competitors']]
    if len(tids)!=2: return []
    other={tids[0]:tids[1],tids[1]:tids[0]}
    poss=[]; cur=None
    pending='period_start'; pending_t=0.0; last_shot=None
    tech_team=None; tech_clock=None; tech_period=None
    def new_poss(team,start,period,t):
        nonlocal cur
        if start in ('made_fg','made_ft','dead_to','period_start','dreb_fg_unrec','dreb_ft_unrec') and pending_t is not None: t=pending_t
        if cur: poss.append(cur)
        cur={'team':team,'start':start,'period':period,'t0':t,'pts':0,'first_fga_t':None,'n_fga':0,'oreb':0,'end':None,'foul_t':None,'foul_after_fga_same_t':None,'last_fga_t':None}
    prev_period=None
    for x in plays:
        ty=x['type']['text']; txt=x.get('text','') or ''
        per=x['period']['number']; 
        try: t_rem=secs(x['clock']['displayValue'])
        except: continue
        t=plen(per)-t_rem  # elapsed in period
        team=(x.get('team') or {}).get('id')
        if per!=prev_period:
            if cur: poss.append(cur); cur=None
            pending='period_start'; pending_t=0.0; prev_period=per; last_shot=None
        if ty in ('Substitution','OfficialTVTimeOut','ShortTimeOut','RegularTimeOut','FullTimeOut','End Period','End Game','PersonalFoul_') : continue
        if ty=='PersonalFoul' or ty=='Flagrant Foul' or 'Foul' in ty and ty!='Technical Foul':
            if cur and team==other.get(cur['team']) and cur['foul_t'] is None:
                cur['foul_t']=t; cur['foul_after_fga_same_t']= (cur['last_fga_t'] is not None and abs(cur['last_fga_t']-t)<=1.0)
                cur['foul_type']=ty
            continue
        if ty=='Technical Foul':
            tech_team=team; tech_clock=t; tech_period=per; continue
        if team not in other: continue
        is_ft='Free Throw' in txt or 'FreeThrow' in ty
        if x.get('shootingPlay') and is_ft and tech_team and tech_period==per and abs(t-tech_clock)<0.5 and team==other[tech_team]:
            continue  # technical FT: excluded (as Inpredictable does)
        if ty=='Steal':
            new_poss(team,'steal',per,t); pending=None; continue
        if 'Turnover' in ty:
            if cur is None or cur['team']!=team: new_poss(team,pending or 'unknown',per,t)
            cur['end']='to'; pending='dead_to'; pending_t=t; continue
        if ty in ('Defensive Rebound',):
            teamreb = not (x.get('participants'))
            st=('dreb_ft' if last_shot=='ft' else 'dreb_fg')+('_team' if teamreb else '')
            new_poss(team,st,per,t); pending=None; continue
        if ty=='Dead Ball Rebound':
            if cur and cur['team']==team: continue   # FT artifact or own dead-ball OREB
            st='dreb_ft_dead' if last_shot=='ft' else 'dreb_fg_dead'
            new_poss(team,st,per,t); pending=None; continue
        if ty=='Offensive Rebound':
            if cur is None or cur['team']!=team: new_poss(team,pending or 'unknown',per,t)
            cur['oreb']+=1; continue
        if x.get('shootingPlay'):
            if cur is None or cur['team']!=team: new_poss(team,pending or 'unknown',per,t)
            if x.get('scoringPlay'): cur['pts']+=x.get('scoreValue',0)
            if is_ft and cur.get('foul_t') is not None and abs(cur['foul_t']-t)<=0.5: cur['ft_at_foul']=True
            if is_ft:
                last_shot='ft'; pending='made_ft' if x.get('scoringPlay') else 'dreb_ft_unrec'; pending_t=t
            else:
                last_shot='fg'; cur['n_fga']+=1; cur['last_fga_t']=t
                if cur['first_fga_t'] is None: cur['first_fga_t']=t
                pending='made_fg' if x.get('scoringPlay') else 'dreb_fg_unrec'; pending_t=t
            continue
        if ty=='Jumpball':
            continue
    if cur: poss.append(cur)
    return poss
